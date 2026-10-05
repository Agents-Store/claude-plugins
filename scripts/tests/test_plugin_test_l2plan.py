import contextlib
import io
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, SCRIPTS_DIR, load_plugin  # noqa: E402

sys.path.insert(0, SCRIPTS_DIR)
import plugin_test_l2plan  # noqa: E402
from plugin_test import l2plan  # noqa: E402
from plugin_test.model import L2_NOT_RUN, L2_STOPPED  # noqa: E402

SKILL = "---\nname: %s\ndescription: d\n---\n"


def triggers(n):
    return json.dumps([{"query": "q %d" % i, "should_trigger": i % 2 == 0} for i in range(n)])


def quality(n):
    return json.dumps({"skill_name": "s", "evals": [{"id": i, "prompt": "p", "expected_output": "e", "files": []}
                                                    for i in range(n)]})


def finding(plugin, message, level="infra"):
    return {"plugin": plugin, "check": "behavior", "level": level, "message": message, "file": "", "line": 0}


class L2PlanTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.state = os.path.join(self.repo.root, "state")

    def add(self, name, trig=0, qual=0):
        files = {"skills/s/SKILL.md": SKILL % "s"}
        if trig:
            files["skills/s/evals/triggers.json"] = triggers(trig)
        if qual:
            files["skills/s/evals/evals.json"] = quality(qual)
        self.repo.plugin(name, files=files)

    def test_weight(self):
        self.add("a-dev", trig=10, qual=2)
        self.add("b-dev")
        self.assertEqual(l2plan.weight(load_plugin(self.repo.root, "a-dev")), 10 + 2 * 6)
        self.assertEqual(l2plan.weight(load_plugin(self.repo.root, "b-dev")), 0)

    def test_slices_greedy_and_deterministic(self):
        self.assertEqual(l2plan.slices({"a": 10, "b": 9, "c": 1, "d": 1}, n=2), [["a", "d"], ["b", "c"]])
        got = l2plan.slices({"p%d" % i: i + 1 for i in range(20)})
        self.assertEqual(len(got), 7)
        self.assertEqual(sorted(sum(got, [])), sorted("p%d" % i for i in range(20)))
        self.assertEqual(got, l2plan.slices({"p%d" % i: i + 1 for i in range(20)}))

    def test_first_run_rotation_covers_catalog_in_a_week(self):
        for i in range(9):
            self.add("p%d-dev" % i, trig=10)
        self.add("bare-dev")
        seen = []
        for day in range(7):
            names, notes = l2plan.select(self.repo.root, self.state, day)
            self.assertEqual(notes, [])
            seen += names
        self.assertEqual(sorted(seen), sorted("p%d-dev" % i for i in range(9)))

    def test_carry_then_changed_then_rotation(self):
        for name in ("a-dev", "b-dev", "c-dev"):
            self.add(name, trig=10)
        self.repo.init_git()
        self.repo.commit_all("base")
        l2plan.record(self.repo.root, self.state, {"findings": [finding("c-dev", "%s: окно ночи закончилось" % L2_NOT_RUN)]})
        self.repo.write("plugins/b-dev/skills/s/SKILL.md", SKILL % "s" + "\nmore\n")
        self.repo.commit_all("change b")
        names, _ = l2plan.select(self.repo.root, self.state, 0)
        self.assertEqual(names[:2], ["c-dev", "b-dev"])
        self.assertEqual(len(names), len(set(names)))

    def test_bad_commit_is_a_note(self):
        self.add("a-dev", trig=10)
        self.repo.init_git()
        self.repo.commit_all("base")
        os.makedirs(self.state)
        with open(os.path.join(self.state, l2plan.STATE), "w") as fh:
            json.dump({"version": 1, "repos": {os.path.basename(self.repo.root): {"commit": "deadbeef", "carry": []}}}, fh)
        names, notes = l2plan.select(self.repo.root, self.state, 0)
        self.assertEqual(len(notes), 1)
        self.assertIsInstance(names, list)

    def test_broken_state_is_empty(self):
        self.add("a-dev", trig=10)
        os.makedirs(self.state)
        with open(os.path.join(self.state, l2plan.STATE), "w") as fh:
            fh.write("{broken")
        names, _ = l2plan.select(self.repo.root, self.state, 0)
        self.assertIsInstance(names, list)

    def test_record_carries_not_run(self):
        self.add("a-dev", trig=10)
        self.add("b-dev", trig=10)
        self.repo.init_git()
        head = self.repo.commit_all("base")
        stop = l2plan.record(self.repo.root, self.state, {"findings": [
            finding("a-dev", "%s: лимит подписки: status=rejected (срабатывание)" % L2_NOT_RUN),
            finding("b-dev", "%s: лимит подписки: status=rejected" % L2_NOT_RUN),
            finding("b-dev", "промах срабатывания: …", level="warn")]})
        self.assertIn("status=rejected", stop)
        with open(os.path.join(self.state, l2plan.STATE)) as fh:
            st = json.load(fh)["repos"][os.path.basename(self.repo.root)]
        self.assertEqual((st["commit"], st["carry"]), (head, ["a-dev", "b-dev"]))
        self.assertEqual(l2plan.record(self.repo.root, self.state, {"findings": []}), "")
        with open(os.path.join(self.state, l2plan.STATE)) as fh:
            self.assertEqual(json.load(fh)["repos"][os.path.basename(self.repo.root)]["carry"], [])

    def test_runner_change_does_not_select_every_plugin(self):
        for name in ("a-dev", "b-dev", "c-dev"):
            self.add(name, trig=10)
        self.repo.write("scripts/plugin_test/x.py", "a = 1\n")
        self.repo.init_git()
        self.repo.commit_all("base")
        l2plan.record(self.repo.root, self.state, {"findings": []})
        self.repo.write("scripts/plugin_test_l2plan.py", "# runner change\n")
        self.repo.commit_all("runner")
        names, _ = l2plan.select(self.repo.root, self.state, 0)
        self.assertEqual(names, l2plan.slices({"a-dev": 10, "b-dev": 10, "c-dev": 10})[0])

    def test_record_returns_stop_without_carry(self):
        self.add("a-dev", trig=10)
        stop = l2plan.record(self.repo.root, self.state, {"findings": [
            finding("a-dev", "%s: окно 5 часов занято на 95%%" % L2_STOPPED, level="info")]})
        self.assertEqual(stop, "окно 5 часов занято на 95%")
        with open(os.path.join(self.state, l2plan.STATE)) as fh:
            self.assertEqual(json.load(fh)["repos"][os.path.basename(self.repo.root)]["carry"], [])

    def test_defer(self):
        self.add("a-dev", trig=10)
        l2plan.defer(self.repo.root, self.state, ["a-dev", "x-dev"])
        l2plan.defer(self.repo.root, self.state, ["a-dev"])
        with open(os.path.join(self.state, l2plan.STATE)) as fh:
            self.assertEqual(json.load(fh)["repos"][os.path.basename(self.repo.root)]["carry"], ["a-dev", "x-dev"])

    def test_cli(self):
        self.add("a-dev", trig=10)
        self.repo.init_git()
        self.repo.commit_all("base")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = plugin_test_l2plan.main(["select", "--repo", self.repo.root, "--state", self.state, "--weekday", "0"])
        self.assertEqual(code, 0)
        listed = [n for d in range(7) for n in l2plan.select(self.repo.root, self.state, d)[0]]
        self.assertEqual(listed, ["a-dev"])
        report = self.repo.write("r.json", json.dumps({"findings": [finding("a-dev", "%s: окно" % L2_NOT_RUN)]}))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(plugin_test_l2plan.main(["record", "--repo", self.repo.root, "--state", self.state, report]), 3)
            clean = self.repo.write("c.json", json.dumps({"findings": []}))
            self.assertEqual(plugin_test_l2plan.main(["record", "--repo", self.repo.root, "--state", self.state, clean]), 0)
            self.assertEqual(plugin_test_l2plan.main(["defer", "--repo", self.repo.root, "--state", self.state, "a-dev"]), 0)


if __name__ == "__main__":
    unittest.main()
