"""subprocess в своей группе процессов: тайм-аут убивает и детей, а не только лидера.

subprocess.run(timeout=…) убивает один процесс и ждёт, пока закроются его pipe-ы;
фоновый внук (`server &` в тесте, `sleep` в hook-е) держит pipe и растягивает
тайм-аут на всё своё время жизни. Здесь вся группа получает SIGKILL — и при
тайм-ауте, и после нормального возврата: то, что команда оставила в фоне
(`server &`, демон), не должно пережить проверку.
"""
from __future__ import annotations

import os
import signal
import subprocess

DRAIN_TIMEOUT = 5  # сколько ждать закрытия pipe-ов после SIGKILL группы, секунды


def _kill_group(pid):
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def _close_pipes(proc):
    for pipe in (proc.stdin, proc.stdout, proc.stderr):
        try:
            if pipe is not None:
                pipe.close()
        except OSError:
            pass


def run_group(args, *, input=None, env, cwd, timeout):
    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, errors="replace", env=env, cwd=cwd, start_new_session=True)
    try:
        try:
            out, err = proc.communicate(input, timeout=timeout)
        except subprocess.TimeoutExpired as expired:
            _kill_group(proc.pid)
            try:
                proc.communicate(timeout=DRAIN_TIMEOUT)
            except subprocess.TimeoutExpired:
                # pipe держит процесс вне группы (setsid): не ждём его, отдаём исходный тайм-аут
                _close_pipes(proc)
                try:
                    proc.wait(timeout=DRAIN_TIMEOUT)
                except subprocess.TimeoutExpired:
                    pass
            raise expired
    finally:
        _kill_group(proc.pid)
    return subprocess.CompletedProcess(args, proc.returncode, out, err)
