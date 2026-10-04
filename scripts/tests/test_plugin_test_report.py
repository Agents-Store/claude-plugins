import os
import sys
import unittest

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

    def test_secret_shaped_line_is_hidden(self):
        r = report.Redactor({})
        # join во время выполнения: компилятор не склеит строку в константу .pyc
        jwt = "".join(["eyJ", "a" * 12, ".eyJ", "b" * 12, ".", "c" * 12])
        self.assertNotIn(jwt, r.text("ok line\nAuthorization: Bearer %s" % jwt))
        self.assertIn("ok line", r.text("ok line"))

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


if __name__ == "__main__":
    unittest.main()
