"""Минимальный MCP-клиент для L1: initialize + tools/list по stdio и streamable HTTP.

Только то, что нужно снимку: без ресурсов, промптов и вызова инструментов.
Ошибки делятся на два вида — их по-разному считает отчёт (spec §6):
  infra    — окружение: сеть, тайм-аут, процесс не стартовал или умер, 401/403/5xx;
  protocol — сервер ответил, но не по MCP: JSON-RPC error, ответ без result.
"""
from __future__ import annotations

import json
import os
import queue
import signal
import subprocess
import threading
import time
import urllib.error
import urllib.request

PROTOCOL_VERSION = "2025-06-18"
CLIENT_INFO = {"name": "agents-store-plugin-test", "version": "1"}
MAX_PAGES = 50
INFRA_HTTP = {401, 403, 407, 408, 429}


class McpError(Exception):
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def _initialize_params():
    return {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO}


def _result(msg, method):
    if "error" in msg:
        err = msg.get("error") or {}
        raise McpError("protocol", "%s: JSON-RPC error %s: %s" % (method, err.get("code"), str(err.get("message", ""))[:200]))
    if not isinstance(msg.get("result"), dict):
        raise McpError("protocol", "%s: ответ без result" % method)
    return msg["result"]


def _paginate(request):
    tools, cursor = [], None
    for _ in range(MAX_PAGES):
        result = request("tools/list", {"cursor": cursor} if cursor else {})
        page = result.get("tools")
        if not isinstance(page, list):
            raise McpError("protocol", "tools/list: в result нет массива tools")
        tools.extend(page)
        cursor = result.get("nextCursor")
        if not cursor:
            return tools
    raise McpError("protocol", "tools/list: больше %d страниц" % MAX_PAGES)


# --- stdio ------------------------------------------------------------------

def list_tools_stdio(command, args, env, cwd, timeout):
    """Запускает сервер в своей группе процессов; после ответа или ошибки убивает всю группу."""
    try:
        proc = subprocess.Popen([command, *args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, env=env, cwd=cwd, start_new_session=True)
    except OSError as exc:
        raise McpError("infra", "не запустился %s: %s" % (command, exc.strerror or exc)) from exc
    lines = queue.Queue()
    stderr_tail = []

    def pump_stdout():
        for raw in proc.stdout:
            lines.put(raw)
        lines.put(None)

    def pump_stderr():
        for raw in proc.stderr:
            stderr_tail.append(raw.decode("utf-8", "replace").rstrip())
            del stderr_tail[:-20]

    threads = [threading.Thread(target=pump_stdout, daemon=True), threading.Thread(target=pump_stderr, daemon=True)]
    for t in threads:
        t.start()
    deadline = time.monotonic() + timeout
    counter = [0]

    def send(obj):
        try:
            proc.stdin.write((json.dumps(obj) + "\n").encode())
            proc.stdin.flush()
        except OSError as exc:
            raise McpError("infra", "сервер закрыл stdin%s" % _tail(stderr_tail)) from exc

    def request(method, params):
        counter[0] += 1
        rid = counter[0]
        send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise McpError("infra", "%s: нет ответа за %d с%s" % (method, timeout, _tail(stderr_tail)))
            try:
                raw = lines.get(timeout=left)
            except queue.Empty:
                continue
            if raw is None:
                time.sleep(0.1)  # дать stderr-потоку дочитать хвост
                raise McpError("infra", "%s: сервер завершился, код %s%s" % (method, proc.poll(), _tail(stderr_tail)))
            try:
                msg = json.loads(raw)
            except ValueError:
                continue  # лог в stdout — не наш ответ
            if not isinstance(msg, dict):
                continue
            if msg.get("id") == rid and ("result" in msg or "error" in msg):
                return _result(msg, method)
            if "method" in msg and "id" in msg:  # запрос сервера клиенту — вежливо отказать
                send({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": "not supported"}})

    try:
        request("initialize", _initialize_params())
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return _paginate(request)
    finally:
        _kill(proc, threads)


def _tail(lines):
    return "; stderr: %s" % " | ".join(lines[-3:])[:300] if lines else ""


def _kill(proc, threads):
    """SIGTERM всей группе, затем SIGKILL тому, что выжило, — включая детей npx."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass
    for t in threads:
        t.join(timeout=2)
    for stream in (proc.stdin, proc.stdout, proc.stderr):
        try:
            stream.close()
        except OSError:
            pass


# --- streamable HTTP ---------------------------------------------------------

def list_tools_http(url, headers, timeout):
    deadline = time.monotonic() + timeout
    session = {}
    counter = [0]

    def post(obj, want_reply=True):
        left = deadline - time.monotonic()
        if left <= 0:
            raise McpError("infra", "%s: нет ответа за %d с" % (obj.get("method"), timeout))
        hdrs = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream", **headers}
        if "id" in session:
            hdrs["Mcp-Session-Id"] = session["id"]
        if "version" in session:
            hdrs["MCP-Protocol-Version"] = session["version"]
        req = urllib.request.Request(url, data=json.dumps(obj).encode(), headers=hdrs, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=left) as resp:
                sid = resp.headers.get("Mcp-Session-Id")
                if sid:
                    session["id"] = sid
                body = resp.read().decode("utf-8", "replace")
                if not want_reply:
                    return None
                ctype = resp.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            kind = "infra" if exc.code in INFRA_HTTP or exc.code >= 500 else "protocol"
            raise McpError(kind, "%s: HTTP %d" % (obj.get("method"), exc.code)) from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise McpError("infra", "%s: сеть: %s" % (obj.get("method"), getattr(exc, "reason", exc))) from exc
        return _pick(body, ctype, obj["id"], obj["method"])

    def request(method, params):
        counter[0] += 1
        return _result(post({"jsonrpc": "2.0", "id": counter[0], "method": method, "params": params}), method)

    init = request("initialize", _initialize_params())
    session["version"] = str(init.get("protocolVersion") or PROTOCOL_VERSION)
    post({"jsonrpc": "2.0", "method": "notifications/initialized"}, want_reply=False)
    return _paginate(request)


def _pick(body, ctype, rid, method):
    """JSON-RPC ответ с нужным id из JSON-тела или из событий SSE."""
    candidates = []
    if "text/event-stream" in ctype:
        data = []
        for line in body.split("\n") + [""]:
            line = line.rstrip("\r")
            if line.startswith("data:"):
                data.append(line[5:].lstrip())
            elif not line and data:
                candidates.append("\n".join(data))
                data = []
    else:
        candidates.append(body)
    for chunk in candidates:
        try:
            msg = json.loads(chunk)
        except ValueError:
            continue
        for m in msg if isinstance(msg, list) else [msg]:
            if isinstance(m, dict) and m.get("id") == rid:
                return m
    raise McpError("protocol", "%s: в ответе нет JSON-RPC сообщения с id %s" % (method, rid))
