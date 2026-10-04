import http.server
import json
import os
import shutil
import socket
import ssl
import subprocess
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

    def test_instant_death_keeps_exit_code_and_stderr(self):
        # Сервер умирает раньше, чем клиент пишет в stdin: BrokenPipe не должен съесть диагностику.
        for i in range(10):
            with self.subTest(run=i):
                with self.assertRaises(McpError) as cm:
                    mcp_client.list_tools_stdio("/bin/sh", ["-c", "echo fatal-stderr-line >&2; exit 4"],
                                                stub_env("ok"), FIXTURES, 10)
                self.assertEqual(cm.exception.kind, "infra")
                self.assertIn("код 4", str(cm.exception))
                self.assertIn("fatal-stderr-line", str(cm.exception))

    def test_stdout_eof_waits_for_exit_code_and_late_stderr(self):
        # stdout закрыт сразу, процесс живёт ещё 0.4 с, пишет в stderr и выходит с кодом 5. Ожидание процесса и
        # потока stderr убирает детерминированную гонку (фиксированная пауза 0.1 с перед чтением кода выхода и stderr
        # давала «код None» без хвоста stderr).
        with self.assertRaises(McpError) as cm:
            mcp_client.list_tools_stdio("/bin/sh", ["-c", "exec 1>&-; sleep 0.4; echo late-stderr-line >&2; exit 5"],
                                        stub_env("ok"), FIXTURES, 10)
        self.assertEqual(cm.exception.kind, "infra")
        self.assertIn("код 5", str(cm.exception))
        self.assertIn("late-stderr-line", str(cm.exception))

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


HUGE = 10 * 1024 * 1024 + 1


class Handler(http.server.BaseHTTPRequestHandler):
    mode = "ok"
    seen = []
    agents = []
    redirect_code = 302
    redirect_to = ""
    stop = threading.Event()

    def log_message(self, *args):
        pass

    def do_POST(self):
        msg = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        Handler.agents.append(self.headers.get("User-Agent"))
        Handler.seen.append((msg.get("method"), self.headers.get("Mcp-Session-Id"),
                             self.headers.get("MCP-Protocol-Version"), self.headers.get("Authorization")))
        if Handler.mode == "401":
            self.send_response(401)
            self.end_headers()
            return
        if Handler.mode == "redirect":
            self.send_response(Handler.redirect_code)
            self.send_header("Location", Handler.redirect_to)
            self.end_headers()
            return
        if Handler.mode == "huge":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(HUGE))
            self.end_headers()
            try:
                self.wfile.write(b" " * HUGE)
            except OSError:
                pass
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
        if Handler.mode == "chunked-split":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            reply = {"jsonrpc": "2.0", "id": msg["id"], "result": {"tools": [{"name": "chunked"}]}}
            event = ("event: message\ndata: %s\n\n" % json.dumps(reply)).encode()
            half = len(event) // 2
            try:
                for part in (event[:half], event[half:]):  # событие разрезано посреди строки
                    self.wfile.write(b"%x\r\n%s\r\n" % (len(part), part))
                    self.wfile.flush()
                    time.sleep(0.1)
                while not Handler.stop.is_set():
                    self.wfile.write(b"8\r\n: ping\n\n\r\n")
                    self.wfile.flush()
                    time.sleep(0.5)
            except OSError:
                pass
            return
        if Handler.mode in ("ping-only", "event-then-ping"):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            try:
                if Handler.mode == "event-then-ping":
                    reply = {"jsonrpc": "2.0", "id": msg["id"], "result": {"tools": [{"name": "one"}]}}
                    self.wfile.write(("event: message\ndata: %s\n\n" % json.dumps(reply)).encode())
                    self.wfile.flush()
                while not Handler.stop.is_set():
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    time.sleep(0.5)
            except OSError:
                pass
            return
        cursor = (msg.get("params") or {}).get("cursor")
        result = {"tools": [{"name": "one"}], "nextCursor": "c2"} if cursor is None else {"tools": [{"name": "two"}]}
        event = "event: message\ndata: %s\n\n" % json.dumps({"jsonrpc": "2.0", "id": msg["id"], "result": result})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        self.wfile.write((": ping\n\n" + event).encode())


class Target(http.server.BaseHTTPRequestHandler):
    """Цель редиректа: любой запрос к ней — ошибка клиента."""
    seen = []

    def log_message(self, *args):
        pass

    def record(self):
        Target.seen.append((self.command, self.headers.get("Authorization")))
        self.send_response(200)
        self.end_headers()

    do_GET = do_POST = record


class HttpTest(unittest.TestCase):
    def setUp(self):
        Handler.mode, Handler.seen, Handler.agents, Target.seen = "ok", [], [], []
        Handler.stop.clear()
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.addCleanup(Handler.stop.set)
        self.url = "http://127.0.0.1:%d/mcp" % self.server.server_address[1]

    def call(self, *args, limit=10):
        """list_tools_http в потоке: зависание — провал теста, а не зависший прогон."""
        box = {}

        def target():
            try:
                box["tools"] = mcp_client.list_tools_http(*args)
            except BaseException as exc:  # noqa: BLE001 — тест разбирает любое исключение
                box["exc"] = exc

        started = time.monotonic()
        worker = threading.Thread(target=target, daemon=True)
        worker.start()
        worker.join(limit)
        box["elapsed"] = time.monotonic() - started
        self.assertFalse(worker.is_alive(), "вызов завис дольше %d с" % limit)
        return box

    def assert_mcp_error(self, box, kind, *secrets):
        exc = box.get("exc")
        self.assertIsInstance(exc, McpError, "ожидался McpError, получено %r" % (exc if exc else box))
        self.assertEqual(exc.kind, kind, str(exc))
        for secret in secrets:
            self.assertNotIn(secret, str(exc))
        return exc

    def raw_server(self, reply):
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        self.addCleanup(srv.close)

        def serve():
            try:
                conn, _ = srv.accept()
                with conn:
                    conn.settimeout(5)
                    conn.recv(65536)
                    conn.sendall(reply)
            except OSError:
                pass

        threading.Thread(target=serve, daemon=True).start()
        return "http://127.0.0.1:%d/mcp" % srv.getsockname()[1]

    def test_session_sse_and_pagination(self):
        tools = mcp_client.list_tools_http(self.url, {"Authorization": "Bearer x"}, 10)
        self.assertEqual([t["name"] for t in tools], ["one", "two"])
        self.assertEqual(Handler.seen[0], ("initialize", None, None, "Bearer x"))
        self.assertEqual(Handler.seen[1][:3], ("notifications/initialized", "sess-1", "2025-06-18"))
        self.assertEqual(Handler.seen[2][1], "sess-1")

    def test_user_agent_is_sent_and_caller_can_override_it(self):
        # Cloudflare отвечает 403 (error 1010) на Python-urllib/x.y — у draw.io это блокировало снимок.
        mcp_client.list_tools_http(self.url, {}, 10)
        self.assertEqual(set(Handler.agents), {"agents-store-plugin-test/1"})
        Handler.agents.clear()
        mcp_client.list_tools_http(self.url, {"user-agent": "custom/2"}, 10)
        self.assertEqual(set(Handler.agents), {"custom/2"})

    def test_401_is_infra(self):
        Handler.mode = "401"
        with self.assertRaises(McpError) as cm:
            mcp_client.list_tools_http(self.url, {}, 10)
        self.assertEqual(cm.exception.kind, "infra")

    def test_connection_refused_is_infra(self):
        port = self.server.server_address[1]
        self.server.shutdown()
        self.server.server_close()
        url = "http://127.0.0.1:%d/mcp" % port
        exc = self.assert_mcp_error(self.call(url, {"Authorization": "Bearer secret-token"}, 5), "infra",
                                    url, "127.0.0.1", "secret-token")
        self.assertIn("Connection refused", str(exc))

    def test_non_http_url_is_protocol_and_not_echoed(self):
        for url in ("${NOCODB_MCP_URL}", "file:///etc/passwd", "ftp://example.com/mcp", "http://", "mcp.example.com/x"):
            with self.subTest(url=url):
                box = self.call(url, {"Authorization": "Bearer secret-token"}, 5)
                self.assert_mcp_error(box, "protocol", url, "NOCODB_MCP_URL", "secret-token")

    def test_header_with_newline_is_protocol_and_not_echoed(self):
        for bad in ("Bearer secret-token\nX-Evil: 1", "Bearer secret-token\r\nX-Evil: 1"):
            with self.subTest(value=repr(bad)):
                box = self.call(self.url, {"Authorization": bad}, 5)
                exc = self.assert_mcp_error(box, "protocol", self.url, "secret-token", "X-Evil")
                self.assertIn("Authorization", str(exc))
        self.assertEqual(Handler.seen, [], "запрос с битым заголовком не должен уйти на сервер")

    def test_garbage_status_line_is_infra_and_not_echoed(self):
        url = self.raw_server(b"this is not http\r\n\r\n")
        exc = self.assert_mcp_error(self.call(url, {"Authorization": "Bearer secret-token"}, 5), "infra",
                                    url, "127.0.0.1", "secret-token", "this is not http")
        self.assertIn("BadStatusLine", str(exc))

    def test_overall_deadline_covers_a_stream_that_only_pings(self):
        Handler.mode = "ping-only"
        box = self.call(self.url, {}, 2, limit=10)
        self.assert_mcp_error(box, "infra", self.url)
        self.assertLess(box["elapsed"], 10)

    def test_stops_reading_at_the_expected_id(self):
        Handler.mode = "event-then-ping"
        box = self.call(self.url, {}, 5, limit=10)
        self.assertEqual([t["name"] for t in box.get("tools", [])], ["one"], box)
        self.assertLess(box["elapsed"], 5)

    def test_chunked_sse_event_split_across_chunks(self):
        Handler.mode = "chunked-split"
        box = self.call(self.url, {}, 5, limit=10)
        self.assertEqual([t["name"] for t in box.get("tools", [])], ["chunked"], box)
        self.assertLess(box["elapsed"], 5)

    @unittest.skipUnless(shutil.which("openssl"), "нужен openssl для самоподписанного сертификата")
    def test_tls_failure_reports_only_the_reason_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            key, crt = os.path.join(tmp, "k.pem"), os.path.join(tmp, "c.pem")
            subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", crt,
                            "-days", "1", "-subj", "/CN=secret-host.invalid"], check=True, capture_output=True)
            tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            tls.load_cert_chain(crt, key)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.socket = tls.wrap_socket(server.socket, server_side=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = "https://127.0.0.1:%d/mcp" % server.server_address[1]
        exc = self.assert_mcp_error(self.call(url, {"Authorization": "Bearer secret-token"}, 5), "infra",
                                    url, "127.0.0.1", "secret-host", "secret-token")
        self.assertIn("CERTIFICATE_VERIFY_FAILED", str(exc))

    def test_oversized_body_is_protocol(self):
        Handler.mode = "huge"
        exc = self.assert_mcp_error(self.call(self.url, {}, 20, limit=30), "protocol", self.url)
        self.assertIn("10 МиБ", str(exc))

    def test_redirects_are_not_followed(self):
        target = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Target)
        threading.Thread(target=target.serve_forever, daemon=True).start()
        self.addCleanup(target.server_close)
        self.addCleanup(target.shutdown)
        location = "http://127.0.0.1:%d/elsewhere" % target.server_address[1]
        Handler.mode, Handler.redirect_to = "redirect", location
        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code):
                Handler.redirect_code = code
                box = self.call(self.url, {"Authorization": "Bearer secret-token"}, 5)
                exc = self.assert_mcp_error(box, "protocol", location, self.url, "secret-token", "elsewhere")
                self.assertIn("HTTP %d" % code, str(exc))
                self.assertIn("перенаправляет", str(exc))
        self.assertEqual(Target.seen, [], "редирект не должен привести к запросу (и к утечке Authorization)")


if __name__ == "__main__":
    unittest.main()
