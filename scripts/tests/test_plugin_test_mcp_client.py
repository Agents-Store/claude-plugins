import http.server
import json
import os
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SCRIPTS)
FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "plugin_test")

from plugin_test import mcp_client  # noqa: E402
from plugin_test.mcp_client import McpError  # noqa: E402

STUB = os.path.join(FIXTURES, "stub_mcp_server.py")


def stub_env(mode, **extra):
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "STUB_MODE": mode, **extra}


def gone(pid):
    """Процесс исчез или стал зомби (его ещё не подобрал init)."""
    try:
        with open("/proc/%d/stat" % pid) as fh:
            return fh.read().rsplit(")", 1)[1].split()[0] == "Z"
    except FileNotFoundError:
        return True


class StdioTest(unittest.TestCase):
    def list(self, mode, timeout=10, **extra):
        return mcp_client.list_tools_stdio(sys.executable, [STUB], stub_env(mode, **extra), FIXTURES, timeout)

    def test_paginated_list(self):
        self.assertEqual([t["name"] for t in self.list("ok")], ["beta", "alpha"])

    def test_noisy_stdout_is_skipped(self):
        self.assertEqual(len(self.list("noisy")), 2)

    def test_hang_times_out_as_infra(self):
        started = time.monotonic()
        with self.assertRaises(McpError) as cm:
            self.list("hang", timeout=2)
        self.assertEqual(cm.exception.kind, "infra")
        self.assertLess(time.monotonic() - started, 15)

    def test_crash_is_infra_with_stderr_tail(self):
        with self.assertRaises(McpError) as cm:
            self.list("crash", STUB_SECRET="shown-in-stderr")
        self.assertEqual(cm.exception.kind, "infra")
        self.assertIn("код 3", str(cm.exception))
        self.assertIn("shown-in-stderr", str(cm.exception))

    def test_jsonrpc_error_is_protocol(self):
        with self.assertRaises(McpError) as cm:
            self.list("error")
        self.assertEqual(cm.exception.kind, "protocol")

    def test_missing_command_is_infra(self):
        with self.assertRaises(McpError) as cm:
            mcp_client.list_tools_stdio("/nonexistent/server", [], stub_env("ok"), FIXTURES, 5)
        self.assertEqual(cm.exception.kind, "infra")

    def test_children_are_killed(self):
        with tempfile.TemporaryDirectory() as tmp:
            pidfile = os.path.join(tmp, "pid")
            with self.assertRaises(McpError):
                self.list("spawn", timeout=2, STUB_PIDFILE=pidfile)
            with open(pidfile) as fh:
                pid = int(fh.read())
        for _ in range(30):
            if gone(pid):
                break
            time.sleep(0.1)
        self.assertTrue(gone(pid), "дочерний процесс заглушки пережил сервер")


class Handler(http.server.BaseHTTPRequestHandler):
    mode = "ok"
    seen = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        msg = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Handler.seen.append((msg.get("method"), self.headers.get("Mcp-Session-Id"),
                             self.headers.get("MCP-Protocol-Version"), self.headers.get("Authorization")))
        if Handler.mode == "401":
            self.send_response(401)
            self.end_headers()
            return
        if "id" not in msg:
            self.send_response(202)
            self.end_headers()
            return
        if msg["method"] == "initialize":
            body = json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": {"protocolVersion": "2025-06-18"}})
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Mcp-Session-Id", "sess-1")
            self.end_headers()
            self.wfile.write(body.encode())
            return
        cursor = (msg.get("params") or {}).get("cursor")
        result = {"tools": [{"name": "one"}], "nextCursor": "c2"} if cursor is None else {"tools": [{"name": "two"}]}
        event = "event: message\ndata: %s\n\n" % json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": result})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        self.wfile.write((": ping\n\n" + event).encode())


class HttpTest(unittest.TestCase):
    def setUp(self):
        Handler.mode, Handler.seen = "ok", []
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = "http://127.0.0.1:%d/mcp" % self.server.server_address[1]

    def test_session_sse_and_pagination(self):
        tools = mcp_client.list_tools_http(self.url, {"Authorization": "Bearer x"}, 10)
        self.assertEqual([t["name"] for t in tools], ["one", "two"])
        self.assertEqual(Handler.seen[0], ("initialize", None, None, "Bearer x"))
        self.assertEqual(Handler.seen[1][:3], ("notifications/initialized", "sess-1", "2025-06-18"))
        self.assertEqual(Handler.seen[2][1], "sess-1")

    def test_401_is_infra(self):
        Handler.mode = "401"
        with self.assertRaises(McpError) as cm:
            mcp_client.list_tools_http(self.url, {}, 10)
        self.assertEqual(cm.exception.kind, "infra")

    def test_connection_refused_is_infra(self):
        port = self.server.server_address[1]
        self.server.shutdown()
        self.server.server_close()
        with self.assertRaises(McpError) as cm:
            mcp_client.list_tools_http("http://127.0.0.1:%d/mcp" % port, {}, 5)
        self.assertEqual(cm.exception.kind, "infra")


if __name__ == "__main__":
    unittest.main()
