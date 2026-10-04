#!/usr/bin/env python3
"""stdio MCP-сервер-заглушка для тестов mcp_client и mcp-list.

Поведение — переменная STUB_MODE:
  ok     два инструмента на двух страницах tools/list (по умолчанию)
  noisy  то же, но перед каждым ответом пишет в stdout строку лога
  hang   читает запросы и не отвечает
  crash  печатает STUB_SECRET в stderr и выходит с кодом 3
  error  на tools/list отвечает JSON-RPC ошибкой
  spawn  запускает дочерний `sleep 300`, пишет его pid в STUB_PIDFILE и не отвечает
"""
import json
import os
import subprocess
import sys

MODE = os.environ.get("STUB_MODE", "ok")
TOOLS = [
    {"name": "beta", "description": "second", "annotations": {"readOnlyHint": True},
     "inputSchema": {"type": "object", "properties": {"b": {"type": "string"}}, "required": ["b"]}},
    {"name": "alpha", "description": "first",
     "inputSchema": {"type": "object", "properties": {"y": {}, "x": {}}, "required": ["y", "x"]}},
]


def reply(obj):
    if MODE == "noisy":
        sys.stdout.write("log: handling request\n")
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def main():
    if MODE == "crash":
        sys.stderr.write("fatal: bad credentials %s\n" % os.environ.get("STUB_SECRET", ""))
        sys.stderr.flush()
        sys.exit(3)
    if MODE == "spawn":
        child = subprocess.Popen(["sleep", "300"])
        with open(os.environ["STUB_PIDFILE"], "w") as fh:
            fh.write(str(child.pid))
    for line in sys.stdin:
        msg = json.loads(line)
        if MODE in ("hang", "spawn") or "id" not in msg:
            continue
        rid, method = msg["id"], msg.get("method")
        if method == "initialize":
            reply({"jsonrpc": "2.0", "id": rid, "result": {
                "protocolVersion": "2025-06-18", "capabilities": {"tools": {}},
                "serverInfo": {"name": "stub", "version": "0"}}})
        elif method == "tools/list" and MODE == "error":
            reply({"jsonrpc": "2.0", "id": rid, "error": {"code": -32603, "message": "boom"}})
        elif method == "tools/list":
            if (msg.get("params") or {}).get("cursor") is None:
                reply({"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS[:1], "nextCursor": "p2"}})
            else:
                reply({"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS[1:]}})
        else:
            reply({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "unknown method"}})


main()
