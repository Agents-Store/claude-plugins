import contextlib
import io
import json
import os
import shutil
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, SCRIPTS_DIR, load_plugin  # noqa: E402

sys.path.insert(0, SCRIPTS_DIR)
import plugin_test_l2plan  # noqa: E402
from plugin_test import l2plan  # noqa: E402
from plugin_test.model import L2_FAILED, L2_MISFIRE, L2_NOT_RUN, L2_STOPPED  # noqa: E402

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

    def state_of(self):
        with open(os.path.join(self.state, l2plan.STATE)) as fh:
            return json.load(fh)["repos"][os.path.basename(self.repo.root)]

    def latest(self):
        with open(l2plan.latest_path(self.state, self.repo.root)) as fh:
            return json.load(fh)

    def night(self, plugins, findings):
        return l2plan.record(self.repo.root, self.state, {"version": 1, "mode": "server", "repo": "r",
                                                          "started": "2026-10-05T01:00:00Z",
                                                          "plugins": plugins, "findings": findings})

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
        self.assertEqual(names, l2plan.slices({"a-dev": 10})[0])

    def test_broken_state_is_empty(self):
        self.add("a-dev", trig=10)
        os.makedirs(self.state)
        with open(os.path.join(self.state, l2plan.STATE), "w") as fh:
            fh.write("{broken")
        names, notes = l2plan.select(self.repo.root, self.state, 0)
        self.assertEqual((names, notes), (l2plan.slices({"a-dev": 10})[0], []))
        l2plan.defer(self.repo.root, self.state, ["a-dev"])
        self.assertEqual(self.state_of()["carry"], ["a-dev"])

    def test_malformed_repo_entry_is_empty(self):
        self.add("a-dev", trig=10)
        key = os.path.basename(self.repo.root)
        for entry in ([1, 2], "x", None, {"carry": "a-dev", "failed": [1], "commit": 5}, {"carry": [None, 3, "a-dev"]}):
            with self.subTest(entry=entry):
                os.makedirs(self.state, exist_ok=True)
                with open(os.path.join(self.state, l2plan.STATE), "w") as fh:
                    json.dump({"version": 1, "repos": {key: entry, "other": [0]}}, fh)
                names, notes = l2plan.select(self.repo.root, self.state, 0)
                self.assertEqual(notes, [])
                self.assertEqual(names[-1:], ["a-dev"])
                l2plan.defer(self.repo.root, self.state, ["b-dev"])
                self.assertIn("b-dev", self.state_of()["carry"])
                self.night(["a-dev"], [])
                self.assertEqual(self.state_of()["carry"], [])

    def test_catalog_removed_plugin_is_dropped(self):
        for name in ("a-dev", "b-dev", "c-dev"):
            self.add(name, trig=10)
        self.repo.init_git()
        self.repo.commit_all("base")
        self.night(["a-dev", "b-dev", "c-dev"], [finding("c-dev", "%s: окно" % L2_NOT_RUN)])
        self.repo.write("plugins/b-dev/skills/s/SKILL.md", SKILL % "s" + "\nmore\n")
        self.repo.commit_all("change b")
        shutil.rmtree(os.path.join(self.repo.root, "plugins", "b-dev"))
        shutil.rmtree(os.path.join(self.repo.root, "plugins", "c-dev"))
        self.repo.commit_all("remove b and c")
        names, notes = l2plan.select(self.repo.root, self.state, 0)
        self.assertEqual((names, notes), (l2plan.slices({"a-dev": 10})[0], []))

    def test_record_keeps_previous_commit_without_head(self):
        self.add("a-dev", trig=10)
        os.makedirs(self.state)
        key = os.path.basename(self.repo.root)
        with open(os.path.join(self.state, l2plan.STATE), "w") as fh:
            json.dump({"version": 1, "repos": {key: {"commit": "abc123", "carry": []}}}, fh)
        self.night(["a-dev"], [])      # не git-репозиторий: HEAD не определить
        self.assertEqual(self.state_of()["commit"], "abc123")

    def test_save_failure_leaves_no_temp_file(self):
        self.add("a-dev", trig=10)
        os.makedirs(self.state)
        with mock.patch.object(l2plan.json, "dump", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                l2plan.defer(self.repo.root, self.state, ["a-dev"])
        self.assertEqual(os.listdir(self.state), [])

    def test_record_carries_not_run(self):
        self.add("a-dev", trig=10)
        self.add("b-dev", trig=10)
        self.repo.init_git()
        head = self.repo.commit_all("base")
        stop = l2plan.record(self.repo.root, self.state, {"findings": [
            finding("a-dev", "%s: лимит подписки: status=rejected (срабатывание)" % L2_NOT_RUN),
            finding("b-dev", "%s: лимит подписки: status=rejected" % L2_NOT_RUN),
            finding("b-dev", "промах срабатывания: …", level="warn")]})
        self.assertEqual(stop, "")     # «не прогнан» — только перенос; остановка ночи — только «L2 остановлен»
        st = self.state_of()
        self.assertEqual((st["commit"], st["carry"]), (head, ["a-dev", "b-dev"]))
        self.assertEqual(l2plan.record(self.repo.root, self.state, {"findings": []}), "")
        self.assertEqual(self.state_of()["carry"], [])

    def test_failed_plugin_is_carried_for_two_nights_only(self):
        self.add("a-dev", trig=10)
        self.add("b-dev", trig=10)
        fail = finding("a-dev", "%s: кейс q без оценки" % L2_FAILED)
        for night, carried in ((1, ["a-dev"]), (2, ["a-dev"]), (3, []), (4, [])):
            with self.subTest(night=night):
                self.assertEqual(self.night(["a-dev", "b-dev"], [fail]), "")
                self.assertEqual((self.state_of()["carry"], self.state_of()["failed"]),
                                 (carried, {"a-dev": night}))
        self.night(["a-dev", "b-dev"], [])      # прогнан без сбоя — счётчик обнулён
        self.assertEqual((self.state_of()["carry"], self.state_of()["failed"]), ([], {}))
        self.night(["a-dev"], [fail])
        self.assertEqual((self.state_of()["carry"], self.state_of()["failed"]), (["a-dev"], {"a-dev": 1}))

    def test_failed_count_survives_nights_without_a_run(self):
        self.add("a-dev", trig=10)
        self.add("b-dev", trig=10)
        self.night(["a-dev"], [finding("a-dev", "%s: x" % L2_FAILED)])
        self.night(["b-dev"], [])                                   # a-dev не прогонялся
        self.assertEqual(self.state_of()["failed"], {"a-dev": 1})
        self.night(["a-dev"], [finding("a-dev", "%s: окно" % L2_NOT_RUN)])   # прогона не было и тут
        self.assertEqual((self.state_of()["carry"], self.state_of()["failed"]), (["a-dev"], {"a-dev": 1}))
        self.night(["a-dev"], [finding("a-dev", "%s: q" % L2_MISFIRE, level="warn")])   # прогнан, сбоя нет
        self.assertEqual((self.state_of()["carry"], self.state_of()["failed"]), ([], {}))

    def test_latest_keeps_verdicts_of_plugins_not_run_tonight(self):
        self.add("a-dev", trig=10)
        self.add("b-dev", trig=10)
        miss = finding("a-dev", "%s: q 1" % L2_MISFIRE, level="warn")
        self.night(["a-dev", "b-dev"], [miss])
        self.night(["b-dev"], [])
        latest = self.latest()
        self.assertEqual(latest["findings"], [miss])
        self.assertEqual((latest["plugins"], latest["mode"], latest["repo"], latest["started"], latest["version"]),
                         (["a-dev"], "server", "r", "2026-10-05T01:00:00Z", 1))
        self.assertEqual(latest["summary"], {"fail": 0, "warn": 1, "infra": 0, "skipped": 0, "info": 0, "suppressed": 0})

    def test_latest_drops_a_plugin_that_ran_clean(self):
        self.add("a-dev", trig=10)
        self.night(["a-dev"], [finding("a-dev", "%s: q 1" % L2_MISFIRE, level="warn")])
        self.night(["a-dev"], [])
        latest = self.latest()
        self.assertEqual((latest["findings"], latest["plugins"]), ([], []))
        self.assertEqual(latest["summary"]["warn"], 0)

    def test_latest_not_run_keeps_old_verdict_and_replaces_old_notes(self):
        self.add("a-dev", trig=10)
        miss = finding("a-dev", "%s: q 1" % L2_MISFIRE, level="warn")
        self.night(["a-dev"], [miss])
        note = finding("a-dev", "%s: окно ночи закончилось" % L2_NOT_RUN)
        self.night(["a-dev"], [note])
        self.assertEqual(self.latest()["findings"], [miss, note])
        stop = finding("a-dev", "%s: порог" % L2_STOPPED, level="info")
        self.night(["a-dev"], [stop, note])
        self.assertEqual(self.latest()["findings"], [miss, stop, note])
        self.assertEqual(self.latest()["summary"], {"fail": 0, "warn": 1, "infra": 1, "skipped": 0, "info": 1,
                                                     "suppressed": 0})
        fresh = finding("a-dev", "%s: q 2" % L2_MISFIRE, level="warn")
        self.night(["a-dev"], [fresh])                  # настоящий прогон заменяет всё
        self.assertEqual(self.latest()["findings"], [fresh])

    def test_latest_drops_a_plugin_removed_from_the_catalog(self):
        self.add("a-dev", trig=10)
        self.add("b-dev", trig=10)
        miss = finding("a-dev", "%s: q" % L2_MISFIRE, level="warn")
        self.night(["a-dev", "b-dev"], [miss, finding("b-dev", "%s: q" % L2_MISFIRE, level="warn")])
        shutil.rmtree(os.path.join(self.repo.root, "plugins", "b-dev"))
        self.night([], [])                              # ночью не прогонялся никто: a-dev остаётся, b-dev нет в каталоге
        latest = self.latest()
        self.assertEqual((latest["findings"], latest["plugins"]), ([miss], ["a-dev"]))

    def test_latest_ignores_non_behavior_findings_and_a_broken_file(self):
        self.add("a-dev", trig=10)
        os.makedirs(self.state)
        with open(l2plan.latest_path(self.state, self.repo.root), "w") as fh:
            fh.write("{broken")
        other = dict(finding("a-dev", "x", level="fail"), check="manifest")
        miss = finding("a-dev", "%s: q" % L2_MISFIRE, level="warn")
        self.night(["a-dev"], [other, miss])
        self.assertEqual(self.latest()["findings"], [miss])

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
        self.repo.init_git()
        head = self.repo.commit_all("base")
        self.night(["a-dev"], [finding("a-dev", "%s: q" % L2_FAILED)])
        l2plan.defer(self.repo.root, self.state, ["a-dev", "x-dev"])
        l2plan.defer(self.repo.root, self.state, ["a-dev"])
        st = self.state_of()
        self.assertEqual((st["carry"], st["commit"], st["failed"]), (["a-dev", "x-dev"], head, {"a-dev": 1}))

    def test_defer_on_empty_state_sets_no_commit(self):
        self.add("a-dev", trig=10)
        l2plan.defer(self.repo.root, self.state, ["a-dev"])
        self.assertEqual(self.state_of(), {"carry": ["a-dev"]})

    def test_cli(self):
        self.add("a-dev", trig=10)
        self.repo.init_git()
        self.repo.commit_all("base")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = plugin_test_l2plan.main(["select", "--repo", self.repo.root, "--state", self.state, "--weekday", "0"])
        self.assertEqual((code, out.getvalue()), (0, "a-dev\n"))
        listed = [n for d in range(7) for n in l2plan.select(self.repo.root, self.state, d)[0]]
        self.assertEqual(listed, ["a-dev"])
        report = self.repo.write("r.json", json.dumps({"findings": [finding("a-dev", "%s: окно" % L2_NOT_RUN)]}))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(plugin_test_l2plan.main(["record", "--repo", self.repo.root, "--state", self.state, report]), 0)
        self.assertEqual(self.state_of()["carry"], ["a-dev"])
        stopped = self.repo.write("s.json", json.dumps({"findings": [finding("a-dev", "%s: окно 5 часов занято" % L2_STOPPED,
                                                                              level="info")]}))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(plugin_test_l2plan.main(["record", "--repo", self.repo.root, "--state", self.state, stopped]), 3)
        self.assertEqual(out.getvalue(), "L2 остановлен: окно 5 часов занято\n")
        with contextlib.redirect_stdout(io.StringIO()):
            clean = self.repo.write("c.json", json.dumps({"findings": []}))
            self.assertEqual(plugin_test_l2plan.main(["record", "--repo", self.repo.root, "--state", self.state, clean]), 0)
            self.assertEqual(plugin_test_l2plan.main(["defer", "--repo", self.repo.root, "--state", self.state, "a-dev"]), 0)
        self.assertEqual(self.state_of()["carry"], ["a-dev"])
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(plugin_test_l2plan.main(["record", "--repo", self.repo.root, "--state", self.state,
                                                      os.path.join(self.repo.root, "missing.json")]), 1)


if __name__ == "__main__":
    unittest.main()
