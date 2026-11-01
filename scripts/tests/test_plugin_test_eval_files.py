import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, context, load_plugin, run_check  # noqa: E402

from plugin_test import runner  # noqa: E402
from plugin_test.checks import REGISTRY, eval_coverage, eval_files  # noqa: E402
from plugin_test.model import BLOCKING, FAIL, STATUS, WARN  # noqa: E402

SKILL = "---\nname: %s\ndescription: d\n---\n"
DMI = "---\nname: %s\ndescription: d\ndisable-model-invocation: true\n---\n"


def trig(pos, neg):
    return json.dumps([{"query": "yes %d" % i, "should_trigger": True} for i in range(pos)]
                      + [{"query": "no %d" % i, "should_trigger": False} for i in range(neg)])


def trig_ru(ru, en, neg):
    """ru запросов «должен» с кириллицей, en — без неё, neg — «не должен» (кириллица у них не в счёт)."""
    return json.dumps([{"query": "сделай %d" % i, "should_trigger": True} for i in range(ru)]
                      + [{"query": "do it %d" % i, "should_trigger": True} for i in range(en)]
                      + [{"query": "не то %d" % i, "should_trigger": False} for i in range(neg)])


class EvalFilesTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)

    def test_registered_and_status(self):
        self.assertIs(REGISTRY["eval-files"], eval_files.run)
        self.assertIs(REGISTRY["eval-coverage"], eval_coverage.run)
        self.assertEqual((STATUS["eval-files"], STATUS["eval-coverage"]), (BLOCKING, BLOCKING))

    def test_no_evals_no_findings(self):
        self.repo.plugin("p-dev", files={"skills/a/SKILL.md": SKILL % "a"})
        self.assertEqual(run_check(eval_files, self.repo.root, "p-dev"), [])

    def test_broken_evals_is_fail_on_its_path(self):
        self.repo.plugin("p-dev", files={"skills/a/SKILL.md": SKILL % "a", "skills/a/evals/evals.json": "{"})
        got = run_check(eval_files, self.repo.root, "p-dev")
        self.assertEqual([(f.level, f.file) for f in got], [(FAIL, "plugins/p-dev/skills/a/evals/evals.json")])

    def test_case_with_files_is_warn(self):
        self.repo.plugin("p-dev", files={"skills/a/SKILL.md": SKILL % "a", "skills/a/evals/evals.json": json.dumps(
            {"skill_name": "a", "evals": [{"id": 1, "prompt": "p", "expected_output": "e", "files": ["x.csv"]}]})})
        got = run_check(eval_files, self.repo.root, "p-dev")
        self.assertEqual([f.level for f in got], [WARN])
        self.assertIn("files", got[0].message)

    def test_bad_triggers_is_fail(self):
        self.repo.plugin("p-dev", files={"skills/a/SKILL.md": SKILL % "a",
                                          "skills/a/evals/triggers.json": '[{"query": "x"}]'})
        got = run_check(eval_files, self.repo.root, "p-dev")
        self.assertEqual([(f.level, f.file) for f in got], [(FAIL, "plugins/p-dev/skills/a/evals/triggers.json")])

    def test_native_case_without_graders(self):
        self.repo.plugin("p-dev")
        self.repo.tests("p-dev", {"evals/c1/prompt.md": "hi\n"})
        got = run_check(eval_files, self.repo.root, "p-dev")
        self.assertEqual([(f.level, f.file) for f in got], [(FAIL, "tests/plugins/p-dev/evals/c1")])

    def ru_findings(self, triggers, skill=SKILL):
        self.repo.plugin("p-dev", files={"skills/a/SKILL.md": skill % "a", "skills/a/evals/triggers.json": triggers})
        return run_check(eval_files, self.repo.root, "p-dev")

    def test_no_russian_positives_warns_with_the_count(self):   # русские «не должен» не в счёт
        got = self.ru_findings(trig_ru(0, 5, 5))
        self.assertEqual([(f.level, f.file) for f in got], [(WARN, "plugins/p-dev/skills/a/evals/triggers.json")])
        self.assertEqual(got[0].message, "запросов «должен» по-русски: 0 — нужно не меньше 2")
        self.assertEqual(got[0].fix, "добавь русский запрос «должен» (правило наборов, /plugin-creator:evals)")

    def test_one_russian_positive_warns_with_the_count(self):
        got = self.ru_findings(trig_ru(1, 4, 5))
        self.assertEqual([f.level for f in got], [WARN])
        self.assertEqual(got[0].message, "запросов «должен» по-русски: 1 — нужно не меньше 2")

    def test_two_russian_positives_is_enough(self):
        self.assertEqual(self.ru_findings(trig_ru(2, 3, 5)), [])

    def test_yo_counts_as_cyrillic(self):
        triggers = json.dumps([{"query": "ёлка", "should_trigger": True}, {"query": "Ёж", "should_trigger": True},
                               {"query": "no", "should_trigger": False}])
        self.assertEqual(self.ru_findings(triggers), [])

    def test_set_without_positives_does_not_warn(self):
        triggers = json.dumps([{"query": "не то", "should_trigger": False}])
        self.assertEqual(self.ru_findings(triggers), [])

    def test_skill_without_model_invocation_does_not_warn(self):
        self.assertEqual(self.ru_findings(trig(0, 5), skill=DMI), [])

    def test_set_with_load_errors_gets_only_the_load_fail(self):
        broken = json.dumps([{"query": "yes", "should_trigger": True}, {"query": "x"}])
        got = self.ru_findings(broken)
        self.assertEqual([f.level for f in got], [FAIL])


class EvalCoverageTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)

    def test_missing_triggers_warns_on_skill_md(self):
        self.repo.plugin("p-dev", files={"skills/a/SKILL.md": SKILL % "a"})
        got = run_check(eval_coverage, self.repo.root, "p-dev")
        self.assertEqual([(f.level, f.file) for f in got], [(WARN, "plugins/p-dev/skills/a/SKILL.md")])

    def test_too_few_queries(self):
        self.repo.plugin("p-dev", files={"skills/a/SKILL.md": SKILL % "a", "skills/a/evals/triggers.json": trig(4, 5)})
        got = run_check(eval_coverage, self.repo.root, "p-dev")
        self.assertEqual([(f.level, f.file) for f in got], [(WARN, "plugins/p-dev/skills/a/evals/triggers.json")])
        self.assertIn("4", got[0].message)

    def test_enough_queries(self):
        self.repo.plugin("p-dev", files={"skills/a/SKILL.md": SKILL % "a", "skills/a/evals/triggers.json": trig(5, 5)})
        self.assertEqual(run_check(eval_coverage, self.repo.root, "p-dev"), [])

    def test_dmi_skill_needs_no_triggers(self):
        self.repo.plugin("p-dev", files={"skills/a/SKILL.md": DMI % "a"})
        self.assertEqual(run_check(eval_coverage, self.repo.root, "p-dev"), [])

    def test_broken_triggers_left_to_eval_files(self):
        self.repo.plugin("p-dev", files={"skills/a/SKILL.md": SKILL % "a", "skills/a/evals/triggers.json": "{"})
        self.assertEqual(run_check(eval_coverage, self.repo.root, "p-dev"), [])

    def test_skip_glob_for_vendored_skills(self):
        self.repo.plugin("p-dev", files={"skills/gws-drive/SKILL.md": SKILL % "gws-drive",
                                          "skills/own/SKILL.md": SKILL % "own"})
        self.repo.tests("p-dev", {"plugin-test.toml": '[skip]\n"eval-coverage" = ["skills/gws-*"]  # vendored\n'})
        plugin = load_plugin(self.repo.root, "p-dev")
        findings, suppressed = runner.run_plugin(plugin, context(self.repo.root), ["eval-coverage"])
        self.assertEqual([f.file for f in findings], ["plugins/p-dev/skills/own/SKILL.md"])
        self.assertEqual(suppressed, 1)


if __name__ == "__main__":
    unittest.main()
