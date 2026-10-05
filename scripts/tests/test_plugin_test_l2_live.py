"""Живой smoke L2: настоящий claude plugin eval на smoke-плагине. Тратит подписку — только PLUGIN_TEST_L2_LIVE=1."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import FIXTURES  # noqa: E402

from plugin_test import cli, evalgen, history  # noqa: E402

LIVE = os.environ.get("PLUGIN_TEST_L2_LIVE") == "1"
SMOKE = os.path.join(FIXTURES, "l2_smoke")


@unittest.skipUnless(LIVE, "живой прогон L2 за счёт подписки: PLUGIN_TEST_L2_LIVE=1")
class L2LiveSmokeTest(unittest.TestCase):
    def test_smoke_plugin_end_to_end(self):
        tmp = tempfile.mkdtemp(prefix="l2-smoke-")
        self.addCleanup(shutil.rmtree, tmp, True)
        out = os.path.join(tmp, "report.json")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cli.main(["--repo", SMOKE, "--check", "behavior", "--mode", "server", "--state-dir", tmp,
                             "--json", out, "--verbose"])
        print(buf.getvalue())
        with open(out, encoding="utf-8") as fh:
            report = json.load(fh)
        self.assertEqual([f for f in report["findings"] if f["level"] == "infra"], [])
        self.assertIn(code, (0, 2))
        with open(os.path.join(tmp, history.FILE), encoding="utf-8") as fh:
            cases = {json.loads(line)["case"] for line in fh}
        for name in (evalgen.trigger_name("haiku-writer", "write me a haiku about autumn rain on a tin roof"),
                     evalgen.trigger_name("haiku-writer", "what is the capital of france"),
                     "q-haiku-writer-1", "q-haiku-writer-2", "q-smoke-ref-1"):
            self.assertIn(name, cases)


if __name__ == "__main__":
    unittest.main()
