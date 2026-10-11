"""Живой smoke L2: настоящий claude plugin eval на smoke-плагине. Тратит подписку — только PLUGIN_TEST_L2_LIVE=1."""
import contextlib
import glob
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import FIXTURES  # noqa: E402

from plugin_test import cli, evalgen, evalrun, history  # noqa: E402
from plugin_test.checks import behavior  # noqa: E402

LIVE = os.environ.get("PLUGIN_TEST_L2_LIVE") == "1"
SMOKE = os.path.join(FIXTURES, "l2_smoke")
HAIKU_TRIGGER = evalgen.trigger_name("haiku-writer", "write me a haiku about autumn rain on a tin roof")
OTHER_TRIGGER = evalgen.trigger_name("haiku-writer", "what is the capital of france")
# Дельта «с плагином минус без» должна быть > 0: ответ держится на правилах skill, без него их не угадать.
# q-haiku-writer-2 держится ещё и на моке notes: диагностика 2026-10-05 видела в трейсе цепочку
# Skill → ToolSearch → mcp__plugin_smoke-dev_notes__save_note (мок вызван), а строку «Saved to notes.»
# в ответе задаёт правило skill и сохранение — без плагина у модели нет ни того, ни другого.
DELTA_CASES = ("q-haiku-writer-1", "q-haiku-writer-2", "q-smoke-ref-1")


def _eval_dirs(base):
    return set(glob.glob(os.path.join(base, "claude-eval-*")))


@unittest.skipUnless(LIVE, "живой прогон L2 за счёт подписки: PLUGIN_TEST_L2_LIVE=1")
class L2LiveSmokeTest(unittest.TestCase):
    def test_smoke_plugin_end_to_end(self):
        tmp = tempfile.mkdtemp(prefix="l2-smoke-")
        self.addCleanup(shutil.rmtree, tmp, True)
        out = os.path.join(tmp, "report.json")
        # Свой каталог для временных файлов: CLI берёт его из TMPDIR (он проходит allowlist окружения),
        # evalrun — из tempfile.tempdir. claude-eval-* считаются только в нём: чужие прогоны L2 на этой
        # машине (волны, ночной) пишут в общий /tmp и проверку не ломают.
        private = os.path.realpath(tempfile.mkdtemp(prefix="l2-smoke-tmp-"))
        self.addCleanup(shutil.rmtree, private, True)
        for patch in (mock.patch.dict(os.environ, {"TMPDIR": private}), mock.patch.object(tempfile, "tempdir", private)):
            patch.start()
            self.addCleanup(patch.stop)
        for var in (behavior.SKILLS_VAR, behavior.QUICK_VAR):    # smoke меряет полный режим: дельту и оба плеча
            os.environ.pop(var, None)                              # (os.environ восстановит patch.dict выше)
        cleaned = []
        real_root = evalrun._temp_root

        def spy(path):
            root = real_root(path)
            if root:
                cleaned.append(root)
            return root

        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), mock.patch.object(evalrun, "_temp_root", spy):
            code = cli.main(["--repo", SMOKE, "--check", "behavior", "--mode", "server", "--state-dir", tmp,
                             "--json", out, "--verbose"])
        print(buf.getvalue())
        with open(out, encoding="utf-8") as fh:
            report = json.load(fh)
        self.assertEqual([f for f in report["findings"] if f["level"] == "infra"], [])
        self.assertIn(code, (0, 2))
        self.assertTrue(cleaned, "CLI не писал в TMPDIR прогона: проверка каталогов ниже была бы пустой")
        self.assertTrue(all(root.startswith(private + os.sep) for root in cleaned), cleaned)
        self.assertEqual(sorted(_eval_dirs(private)), [], "движок оставил каталоги claude-eval-*")
        rows = {}
        with open(os.path.join(tmp, history.FILE), encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                rows[row["case"]] = row
        for name in (HAIKU_TRIGGER, OTHER_TRIGGER, *DELTA_CASES):
            self.assertIn(name, rows)
        for name in (HAIKU_TRIGGER, OTHER_TRIGGER):
            self.assertEqual(rows[name]["score"], 1.0, "срабатывание %s: %r" % (name, rows[name]))
        for name in DELTA_CASES:
            delta = rows[name]["delta"]
            self.assertTrue(isinstance(delta, float) and delta > 0, "дельта %s: %r" % (name, rows[name]))


if __name__ == "__main__":
    unittest.main()
