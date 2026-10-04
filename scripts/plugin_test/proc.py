"""subprocess в своей группе процессов: тайм-аут убивает и детей, а не только лидера.

subprocess.run(timeout=…) убивает один процесс и ждёт, пока закроются его pipe-ы;
фоновый внук (`server &` в тесте, `sleep` в hook-е) держит pipe и растягивает
тайм-аут на всё своё время жизни. Здесь вся группа получает SIGKILL.
"""
from __future__ import annotations

import os
import signal
import subprocess


def run_group(args, *, input=None, env, cwd, timeout):
    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, env=env, cwd=cwd, start_new_session=True)
    try:
        out, err = proc.communicate(input, timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        proc.communicate()
        raise
    return subprocess.CompletedProcess(args, proc.returncode, out, err)
