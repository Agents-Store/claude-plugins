import os
import shutil
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, run_check  # noqa: E402

from plugin_test.checks import REGISTRY, skill_budget  # noqa: E402
from plugin_test.model import INFRA, WARN  # noqa: E402


class Proc:
    def __init__(self, stdout, returncode=0):
        self.stdout, self.stderr, self.returncode = stdout, "", returncode


class SkillBudgetTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)

    def test_registered(self):
        self.assertIs(REGISTRY["skill-budget"], skill_budget.run)

    def test_parse_tokens(self):
        self.assertEqual(skill_budget.parse_tokens("  Always-on:   ~2,761 tok   added"), 2761)
        self.assertEqual(skill_budget.parse_tokens("Always-on: ~3.8k tok"), 3800)
        self.assertIsNone(skill_budget.parse_tokens("nothing here"))

    def test_long_skill_and_budget(self):
        self.repo.plugin("p-dev", files={"skills/long/SKILL.md": "x\n" * 501, "skills/short/SKILL.md": "x\n"})
        with mock.patch.object(skill_budget.shutil, "which", return_value="/bin/claude"), \
             mock.patch.object(skill_budget.subprocess, "run", return_value=Proc("Always-on:   ~4,100 tok")):
            found = run_check(skill_budget, self.repo.root, "p-dev")
        self.assertEqual(sorted((f.level, f.file) for f in found), [
            (WARN, "plugins/p-dev/.claude-plugin/plugin.json"),
            (WARN, "plugins/p-dev/skills/long/SKILL.md")])

    def test_manifest_raises_budget(self):
        self.repo.plugin("p-dev")
        self.repo.tests("p-dev", {"plugin-test.toml": "[budget]\nalways_on_tokens = 5000\n"})
        with mock.patch.object(skill_budget.shutil, "which", return_value="/bin/claude"), \
             mock.patch.object(skill_budget.subprocess, "run", return_value=Proc("Always-on:   ~4,100 tok")):
            self.assertEqual(run_check(skill_budget, self.repo.root, "p-dev"), [])

    def test_no_claude_or_bad_output_is_infra(self):
        self.repo.plugin("p-dev")
        with mock.patch.object(skill_budget.shutil, "which", return_value=None):
            self.assertEqual([f.level for f in run_check(skill_budget, self.repo.root, "p-dev")], [INFRA])
        with mock.patch.object(skill_budget.shutil, "which", return_value="/bin/claude"), \
             mock.patch.object(skill_budget.subprocess, "run", return_value=Proc("garbage", 1)):
            self.assertEqual([f.level for f in run_check(skill_budget, self.repo.root, "p-dev")], [INFRA])

    @unittest.skipUnless(shutil.which("claude"), "claude CLI не установлен")
    def test_real_cli_on_fixture(self):
        self.repo.plugin("tiny-dev", files={"skills/s/SKILL.md": "---\nname: s\ndescription: tiny\n---\nbody\n"})
        self.assertEqual(run_check(skill_budget, self.repo.root, "tiny-dev"), [])


if __name__ == "__main__":
    unittest.main()
