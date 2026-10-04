import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plugin_test_fixtures  # noqa: E402,F401  (кладёт scripts/ в sys.path)

from plugin_test import report  # noqa: E402
from plugin_test.model import ADVISORY, BLOCKING, FAIL, INFO, INFRA, SKIPPED, WARN, Finding  # noqa: E402

# Значение собирается из кусков, чтобы scrub_check не принял сам тест за утечку.
FAKE = "tok" + "en-" + "4f9c2b7d1e"


def f(level, check="skill-links", msg="m", **kw):
    return Finding("p", check, level, msg, **kw)


class StatusTest(unittest.TestCase):
    STATUS = {"a": ADVISORY, "b": BLOCKING}

    def test_advisory_downgrades_fail(self):
        out = report.apply_status([f(FAIL, "a")], strict=True, status=self.STATUS)
        self.assertEqual((out[0].level, out[0].original), (WARN, FAIL))

    def test_blocking_strict_upgrades_warn(self):
        out = report.apply_status([f(WARN, "b"), f(INFRA, "b")], strict=True, status=self.STATUS)
        self.assertEqual([x.level for x in out], [FAIL, INFRA])
        out = report.apply_status([f(WARN, "b")], strict=False, status=self.STATUS)
        self.assertEqual(out[0].level, WARN)

    def test_exit_codes(self):
        self.assertEqual(report.exit_code([]), 0)
        self.assertEqual(report.exit_code([f(SKIPPED), f(INFO)]), 0)
        self.assertEqual(report.exit_code([f(INFRA)]), 2)
        self.assertEqual(report.exit_code([f(WARN), f(FAIL)]), 1)


class RedactorTest(unittest.TestCase):
    def test_env_values_become_names(self):
        r = report.Redactor({"API_TOKEN": FAKE, "SHORT": "abc"})
        self.assertEqual(r.text("bad credentials %s abc" % FAKE), "bad credentials ${API_TOKEN} abc")

    def test_short_value_is_redacted_as_a_whole_token_only(self):
        # Имя схемы или namespace — обычное слово в именах и описаниях инструментов (решение владельца 2026-10-04).
        r = report.Redactor({"SCHEMA": "public", "T": "trigger"})
        self.assertEqual(r.text("list_publication_tables"), "list_publication_tables")
        self.assertEqual(r.text("schema public here"), "schema ${SCHEMA} here")
        self.assertEqual(r.text("trigger_task"), "trigger_task")
        self.assertEqual(r.text("triggered by (trigger)"), "triggered by (${T})")

    def test_hyphenated_identifier_is_one_token(self):
        # Имена MCP-инструментов — идентификаторы [A-Za-z0-9_-]: trigger-flow остаётся одним токеном (решение контроллера).
        r = report.Redactor({"NS": "trigger"})
        self.assertEqual(r.text("trigger-flow"), "trigger-flow")
        self.assertEqual(r.text("flow-trigger and my-trigger-x"), "flow-trigger and my-trigger-x")
        self.assertEqual(r.text("ns trigger here"), "ns ${NS} here")

    def test_long_value_is_redacted_inside_a_longer_word(self):
        r = report.Redactor({"K": FAKE})
        self.assertEqual(r.text("prefix%ssuffix" % FAKE), "prefix${K}suffix")

    def test_substitution_is_a_single_pass(self):
        # Имя переменной само бывает значением другой: уже вставленное ${ИМЯ} повторно не разбирается.
        r = report.Redactor({"API_TOKEN": FAKE, "FOO": "API_TOKEN"})
        self.assertEqual(r.text("invalid key %s" % FAKE), "invalid key ${API_TOKEN}")
        self.assertEqual(r.text("name API_TOKEN"), "name ${FOO}")

    def test_longest_value_wins_when_values_overlap(self):
        r = report.Redactor({"SHORT": "example", "LONG": "example.internal"})
        self.assertEqual(r.text("host example.internal and example"), "host ${LONG} and ${SHORT}")

    def test_secret_shaped_line_is_hidden(self):
        r = report.Redactor({})
        # join во время выполнения: компилятор не склеит строку в константу .pyc
        jwt = "".join(["eyJ", "a" * 12, ".eyJ", "b" * 12, ".", "c" * 12])
        self.assertNotIn(jwt, r.text("ok line\nAuthorization: Bearer %s" % jwt))
        self.assertIn("ok line", r.text("ok line"))

    def test_kv_shaped_line_is_hidden(self):
        r = report.Redactor({})
        # значение собирается во время выполнения, чтобы gate не принял тест за утечку
        value = "abcd1234" + "efgh5678" + "ijkl"
        line = "API_KEY=" + '"' + value + '"'
        self.assertNotIn(value, r.text(line))
        self.assertEqual(r.text("api_token: ${API_TOKEN}"), "api_token: ${API_TOKEN}")

    def test_missing_secret_rule_fails_loud(self):
        rules = {k: v for k, v in report.scrub_check.RULES_BY_ID.items() if k != "secret-kv"}
        with mock.patch.dict(report.scrub_check.RULES_BY_ID, rules, clear=True):
            with self.assertRaises(KeyError):
                report.Redactor({})

    def test_host_of_a_url_value_is_masked_as_the_name(self):
        # Адрес в сообщении ошибки (ECONNREFUSED host:port) не совпадает с URL целиком, но выдаёт инстанс.
        r = report.Redactor({"NOCODB_URL": "https://nocodb.corp-internal.example/api"})
        self.assertEqual(r.text("ECONNREFUSED nocodb.corp-internal.example:443"), "ECONNREFUSED ${NOCODB_URL}:443")
        self.assertEqual(r.text("GET https://nocodb.corp-internal.example/api/v1 failed"), "GET ${NOCODB_URL}/v1 failed")

    def test_short_host_is_a_whole_token_and_hostless_values_add_nothing(self):
        r = report.Redactor({"DB": "http://dbhost.local:5432", "PLAIN": "production-x", "BAD": "http://[oops"})
        self.assertEqual(r.text("connect dbhost.local ok; dbhost.localnet"), "connect ${DB} ok; dbhost.localnet")
        self.assertEqual(r.text("mode production-y"), "mode production-y")
        self.assertEqual(r.names.get("dbhost.local"), "DB")
        self.assertNotIn("oops", r.names)

    def test_value_wins_over_host_of_another_url(self):
        r = report.Redactor({"A_URL": "https://api.example.internal/x", "B_HOST": "api.example.internal"})
        self.assertEqual(r.text("api.example.internal"), "${B_HOST}")

    def test_absolute_prefixes_become_placeholders(self):
        repo = os.path.join(tempfile.gettempdir(), "work", "claude-plugins")
        home = os.path.join(os.sep, "home", "runner")
        with mock.patch.dict(os.environ, {"HOME": home}):
            r = report.Redactor({}, repo=repo)
        tmp = tempfile.gettempdir()
        self.assertEqual(r.text("cwd=%s/plugins/x and %s/a.md" % (repo, repo)), "cwd=<repo>/plugins/x and <repo>/a.md")
        self.assertEqual(r.text("see %s/.cache/x, %s" % (home, home)), "see ~/.cache/x, ~")
        self.assertEqual(r.text("wrote %s/pt-abc/out.json" % tmp), "wrote <tmp>/pt-abc/out.json")
        self.assertEqual(r.text("open '%s/plugins/x'" % repo), "open '<repo>/plugins/x'")
        self.assertEqual(r.text("file://%s/plugins/x" % repo), "file://<repo>/plugins/x")

    def test_prefixes_only_at_a_path_boundary(self):
        home = os.path.join(os.sep, "home", "runner")
        with mock.patch.dict(os.environ, {"HOME": home}):
            r = report.Redactor({}, repo="/work/claude-plugins")
        self.assertEqual(r.text("/work/claude-plugins-private/x"), "/work/claude-plugins-private/x")
        self.assertEqual(r.text("/mnt/work/claude-plugins/x"), "/mnt/work/claude-plugins/x")
        neighbours = "%s2/x and a%s" % (home, home)  # другой каталог с тем же началом; префикс внутри слова
        self.assertEqual(r.text(neighbours), neighbours)

    def test_closing_tag_is_not_a_home_path(self):
        # В описании drawio-инструмента есть </root>; при HOME=/root снимок не должен превратиться в <~>.
        with mock.patch.dict(os.environ, {"HOME": "/root"}):
            r = report.Redactor({})
        self.assertEqual(r.text("</root>\n</mxGraphModel>"), "</root>\n</mxGraphModel>")
        self.assertEqual(r.text("cache in /root/.cache"), "cache in ~/.cache")

    def test_without_repo_only_home_and_tmp_are_replaced(self):
        r = report.Redactor({})
        self.assertEqual(r.text("/work/claude-plugins/x"), "/work/claude-plugins/x")
        self.assertEqual(r.text(tempfile.gettempdir() + "/x"), "<tmp>/x")

    def test_longest_prefix_wins(self):
        # репозиторий лежит внутри временного каталога: путь внутри него — <repo>, а не <tmp>/…/…
        repo = os.path.join(tempfile.gettempdir(), "pt-repo")
        r = report.Redactor({}, repo=repo)
        self.assertEqual(r.text(repo + "/plugins"), "<repo>/plugins")
        self.assertEqual(r.text(os.path.join(tempfile.gettempdir(), "other")), "<tmp>/other")

    def test_env_value_beats_path_prefix(self):
        r = report.Redactor({"SRC_DIR": "/work/claude-plugins/plugins"}, repo="/work/claude-plugins")
        self.assertEqual(r.text("in /work/claude-plugins/plugins/x"), "in ${SRC_DIR}/x")

    def test_obj_and_finding(self):
        r = report.Redactor({"K": FAKE})
        self.assertEqual(r.obj({"a": [FAKE, 1]}), {"a": ["${K}", 1]})
        g = r.finding(f(FAIL, msg="x %s" % FAKE, fix=FAKE))
        self.assertEqual((g.message, g.fix), ("x ${K}", "${K}"))


class RenderTest(unittest.TestCase):
    def test_text(self):
        out = report.render_text([f(WARN, file="plugins/p/a.md", line=3, fix="do"), f(SKIPPED)], 2)
        self.assertIn("WARN p [skill-links] plugins/p/a.md:3 — m (fix: do)", out)
        self.assertNotIn("SKIP", out)
        self.assertIn("plugin-test: 2 plugins, 0 fail, 1 warn, 0 infra, 1 skipped", out)

    def test_build_and_markdown(self):
        data = report.build([f(FAIL, file="plugins/p/a.md", line=1), f(INFRA, check="mcp-list")],
                            mode="server", repo="/x/claude-public-plugins", plugins=["p"],
                            started="2026-10-04T03:00:00Z", suppressed=2)
        self.assertEqual(data["repo"], "claude-public-plugins")
        self.assertEqual(data["summary"]["suppressed"], 2)
        md = report.render_markdown(data, title="Nightly plugin tests")
        self.assertIn("## Nightly plugin tests — claude-public-plugins", md)
        self.assertIn("### Провалы (1)", md)
        self.assertIn("### Сбои окружения (1)", md)
        self.assertIn("`plugins/p/a.md:1`", md)

    def test_markdown_shows_only_the_first_line_of_a_message(self):
        # Полный текст (stdout проверки, pwd, адреса) остаётся в JSON-отчёте и журнале прогона, но не в публичном issue.
        message = "тест упал (код 1)\n/srv/secret-place\nECONNREFUSED internal-host:443"
        data = report.build([f(FAIL, check="unit", msg=message)], mode="server", repo="/x/r", plugins=["p"],
                            started="2026-10-04T03:00:00Z")
        self.assertEqual(data["findings"][0]["message"], message)
        md = report.render_markdown(data)
        self.assertIn("- `unit` тест упал (код 1)", md)
        self.assertNotIn("secret-place", md)
        self.assertNotIn("ECONNREFUSED", md)
        self.assertNotIn("⏎", md)


class StatusPolicyTest(unittest.TestCase):
    def test_skill_budget_never_blocks(self):
        from plugin_test.model import STATUS
        self.assertEqual(STATUS["skill-budget"], ADVISORY)
        self.assertEqual((STATUS["manifest"], STATUS["unit"]), (BLOCKING, BLOCKING))

    def test_every_check_has_a_status(self):
        from plugin_test.model import CHECK_IDS, STATUS
        self.assertEqual(set(STATUS), set(CHECK_IDS))


if __name__ == "__main__":
    unittest.main()
