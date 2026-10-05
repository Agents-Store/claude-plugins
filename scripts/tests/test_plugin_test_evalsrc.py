import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, load_plugin  # noqa: E402

from plugin_test import evalsrc  # noqa: E402

SKILL = "---\nname: %s\ndescription: d\n---\n\nbody\n"
DMI = "---\nname: %s\ndescription: d\ndisable-model-invocation: true\n---\n\nbody\n"


def triggers(pos=5, neg=5):
    return ([{"query": "need thing %d" % i, "should_trigger": True} for i in range(pos)]
            + [{"query": "other thing %d" % i, "should_trigger": False} for i in range(neg)])


class EvalsrcTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)

    def make(self, files):
        self.repo.plugin("e-dev", files=files)
        return load_plugin(self.repo.root, "e-dev")

    def skill(self, name="alpha", files=None, dmi=False):
        all_files = {"skills/%s/SKILL.md" % name: (DMI if dmi else SKILL) % name}
        for rel, content in (files or {}).items():
            all_files["skills/%s/%s" % (name, rel)] = content if isinstance(content, str) else json.dumps(content)
        plugin = self.make(all_files)
        return next(s for s in evalsrc.skills(plugin.dir) if s.name == name)

    def test_skills_listing_and_invocable(self):
        plugin = self.make({"skills/b/SKILL.md": SKILL % "b", "skills/a/SKILL.md": DMI % "a",
                            "skills/c/notes.md": "no SKILL.md here",
                            "skills/d/SKILL.md": '---\nname: d\ndisable-model-invocation: "true"\n---\n'})
        got = [(s.name, s.invocable) for s in evalsrc.skills(plugin.dir)]
        self.assertEqual(got, [("a", False), ("b", True), ("d", False)])

    def test_skills_without_frontmatter_are_invocable(self):
        plugin = self.make({"skills/x/SKILL.md": "# just markdown\n"})
        self.assertEqual([s.invocable for s in evalsrc.skills(plugin.dir)], [True])

    def test_no_skills_dir(self):
        plugin = self.make({})
        self.assertEqual(evalsrc.skills(plugin.dir), [])

    def test_quality_expectations_variant(self):
        s = self.skill(files={"evals/evals.json": {"skill_name": "alpha", "evals": [
            {"id": 1, "prompt": "do x", "expected_output": "x done", "files": [], "expectations": ["says x", " y "]}]}})
        cases, errors = evalsrc.load_quality(s)
        self.assertEqual(errors, [])
        self.assertEqual(cases, [evalsrc.QualityCase("alpha", "1", "do x", ("says x", "y"), "x done", False)])

    def test_quality_assertions_variant(self):
        s = self.skill(files={"evals/evals.json": {"skill_name": "alpha", "evals": [
            {"id": "a-1", "prompt": "p", "expected_output": "", "files": [],
             "assertions": [{"id": "x", "text": "has x", "type": "content"}]}]}})
        cases, errors = evalsrc.load_quality(s)
        self.assertEqual(errors, [])
        self.assertEqual(cases[0].criteria, ("has x",))
        self.assertEqual(cases[0].id, "a-1")

    def test_quality_expected_output_only(self):
        s = self.skill(files={"evals/evals.json": {"skill_name": "alpha", "evals": [
            {"id": 2, "prompt": "p", "expected_output": "the answer", "files": []}]}})
        cases, errors = evalsrc.load_quality(s)
        self.assertEqual(errors, [])
        self.assertEqual((cases[0].criteria, cases[0].expected_output), ((), "the answer"))

    def test_quality_errors(self):
        s = self.skill(files={"evals/evals.json": {"skill_name": "beta", "evals": [
            {"id": 1, "prompt": "p", "expected_output": "e", "files": []},
            {"id": 1, "prompt": "p", "expected_output": "e", "files": []},
            {"id": "bad id!", "prompt": "p", "expected_output": "e"},
            {"id": 3, "prompt": "  ", "expected_output": "e"},
            {"id": 4, "prompt": "p", "expected_output": "", "expectations": []},
            {"id": 5, "prompt": "p", "expectations": ["a"], "assertions": [{"text": "b"}]},
            {"id": 6, "prompt": "p", "expectations": ["a", 7]},
            {"id": 7, "prompt": "p", "expected_output": "e", "files": "x"},
            {"id": True, "prompt": "p", "expected_output": "e"},
            "not an object"]}})
        cases, errors = evalsrc.load_quality(s)
        self.assertEqual([c.id for c in cases], ["1"])
        text = "\n".join(errors)
        for needle in ("skill_name", "повторяется", "bad id!", "prompt", "судить не по чему",
                       "оставь одно", "массив непустых строк", "files", "evals[8]", "evals[9]"):
            self.assertIn(needle, text)

    def test_quality_files_flag(self):
        s = self.skill(files={"evals/evals.json": {"skill_name": "alpha", "evals": [
            {"id": 1, "prompt": "p", "expected_output": "e", "files": ["in.csv"]}]}})
        cases, errors = evalsrc.load_quality(s)
        self.assertEqual((errors, cases[0].has_files), ([], True))

    def test_quality_broken_json_has_no_absolute_path(self):
        s = self.skill(files={"evals/evals.json": "{not json"})
        cases, errors = evalsrc.load_quality(s)
        self.assertEqual(cases, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("JSON не разбирается", errors[0])
        self.assertNotIn(self.repo.root, errors[0])

    def test_quality_empty_evals(self):
        s = self.skill(files={"evals/evals.json": {"skill_name": "alpha", "evals": []}})
        self.assertEqual(evalsrc.load_quality(s)[1], ["evals — непустой массив кейсов"])

    def test_triggers_valid(self):
        s = self.skill(files={"evals/triggers.json": triggers()})
        queries, errors = evalsrc.load_triggers(s)
        self.assertEqual(errors, [])
        self.assertEqual(len(queries), 10)
        self.assertEqual(queries[0], evalsrc.TriggerQuery("alpha", "need thing 0", True))

    def test_triggers_errors(self):
        s = self.skill(files={"evals/triggers.json": [
            {"query": "a", "should_trigger": True},
            {"query": "  A ", "should_trigger": False},
            {"query": "b", "should_trigger": "yes"},
            {"query": "", "should_trigger": True},
            {"query": "c", "should_trigger": True, "note": "x"},
            {"query": "d", "should-trigger": True}]})
        queries, errors = evalsrc.load_triggers(s)
        self.assertEqual([q.query for q in queries], ["a"])
        text = "\n".join(errors)
        self.assertIn("[1]: запрос повторяется", text)
        self.assertIn("[2]:", text)
        self.assertIn("[3]:", text)
        self.assertIn("[4]: ровно ключи", text)
        self.assertIn("[5]: ровно ключи", text)

    def test_triggers_too_many(self):
        s = self.skill(files={"evals/triggers.json": triggers(11, 10)})
        self.assertIn("больше 20", "\n".join(evalsrc.load_triggers(s)[1]))

    def test_triggers_not_array(self):
        s = self.skill(files={"evals/triggers.json": {"query": "x"}})
        self.assertEqual(evalsrc.load_triggers(s), ([], ["ожидается непустой массив [{query, should_trigger}]"]))

    def test_triggers_on_dmi_skill(self):
        s = self.skill(dmi=True, files={"evals/triggers.json": triggers(1, 1)})
        self.assertIn("disable-model-invocation", "\n".join(evalsrc.load_triggers(s)[1]))
        s2 = self.skill(name="beta", dmi=True, files={"evals/triggers.json": triggers(0, 2)})
        self.assertEqual(evalsrc.load_triggers(s2)[1], [])

    def test_lone_surrogate_is_an_error(self):
        s = self.skill(files={"evals/triggers.json": '[{"query": "bad \\ud800 q", "should_trigger": true}]',
                              "evals/evals.json": '{"skill_name": "alpha", "evals": [{"id": 1, "prompt": "p \\udfff", '
                                                 '"expected_output": "e", "files": []}]}'})
        self.assertEqual(evalsrc.load_triggers(s)[0], [])
        self.assertIn("суррогат", evalsrc.load_triggers(s)[1][0])
        self.assertEqual(evalsrc.load_quality(s)[0], [])
        self.assertIn("суррогат", evalsrc.load_quality(s)[1][0])

    def test_native_cases(self):
        self.repo.plugin("n-dev")
        self.repo.tests("n-dev", {
            "evals/good/prompt.md": "---\nruns: 1\n---\n\nhi\n",
            "evals/good/graders/g.md": "---\ntype: llm\n---\n\nPASS if hi.\n",
            "evals/yaml-only/case.yaml": "schema_version: \"1.1\"\nname: yaml-only\n",
            "evals/no-graders/prompt.md": "hi\n",
            "evals/mocks/srv/_server.md": "---\ntype: agent\n---\n",
            "evals/notes.md": "not a case",
        })
        plugin = load_plugin(self.repo.root, "n-dev")
        names, errors = evalsrc.native_cases(plugin)
        self.assertEqual(names, ["good", "yaml-only"])
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0][0].endswith(os.path.join("evals", "no-graders")))
        self.assertIn("graders", errors[0][1])

    def test_native_cases_absent(self):
        self.repo.plugin("n-dev")
        self.assertEqual(evalsrc.native_cases(load_plugin(self.repo.root, "n-dev")), ([], []))


if __name__ == "__main__":
    unittest.main()
