import contextlib
import io
import json
import os
import shutil
import sys
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import (Repo, context, eval_case, eval_result, load_plugin, stub_calls,  # noqa: E402
                                  stub_claude)

from plugin_test import evalgen, history, manifest  # noqa: E402
from plugin_test.checks import REGISTRY, behavior  # noqa: E402
from plugin_test import evalrun  # noqa: E402
from plugin_test.model import (ADVISORY, CHECK_IDS, DEFAULT_CHECKS, FAIL, INFO, INFRA, L2_BELOW,  # noqa: E402
                               L2_FAILED, L2_FLAKY, L2_MISFIRE, L2_NOT_RUN, L2_REGRESS, L2_STOPPED, L2_UNHELPFUL,
                               STATUS)

SKILL = "---\nname: %s\ndescription: d\n---\n"
YES, NO = "need the thing done", "do some other thing"
QUALITY = [{"id": 1, "prompt": "how to do it", "expected_output": "e", "files": [], "expectations": ["says how"]}]
REJECTED = {"status": "rejected", "unifiedWindows": {"five_hour": {"utilization": 1.0}}}


def T(query):
    return evalgen.trigger_name("web", query)


class BehaviorTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.state = os.path.join(self.repo.root, "state")

    def add_plugin(self, name="b-dev", queries=((YES, True), (NO, False)), quality=None, mcp=None, commands=None):
        files = {"skills/web/SKILL.md": SKILL % "web"}
        for command, text in (commands or {}).items():
            files["commands/%s.md" % command] = text
        if queries:
            files["skills/web/evals/triggers.json"] = json.dumps([{"query": q, "should_trigger": t} for q, t in queries])
        if quality:
            files["skills/web/evals/evals.json"] = json.dumps({"skill_name": "web", "evals": quality})
        self.repo.plugin(name, files=files, mcp=mcp)

    def ctx(self, mode="server"):
        c = context(self.repo.root, mode=mode)
        c.state_dir = self.state
        return c

    def check(self, plan, name="b-dev", ctx=None, auth=None):
        shutil.rmtree(os.path.join(self.repo.root, "s-" + name), ignore_errors=True)   # журнал и счётчик заглушки — с нуля
        claude, log = stub_claude(os.path.join(self.repo.root, "s-" + name), plan, auth=auth)
        ctx = ctx or self.ctx()
        plugin = load_plugin(self.repo.root, name)
        loaded, _ = manifest.load(plugin)
        with mock.patch.object(behavior.shutil, "which", return_value=claude):
            got = behavior.run(plugin, ctx, loaded)
        calls = stub_calls(log)
        return got, [c for c in calls if c["argv"][:2] == ["plugin", "eval"]], calls, ctx

    def hist(self):
        path = os.path.join(self.state, history.FILE)
        if not os.path.exists(path):
            return []
        with open(path) as fh:
            return [json.loads(line) for line in fh]

    def test_registered_status_and_opt_in(self):
        self.assertIs(REGISTRY["behavior"], behavior.run)
        self.assertEqual(STATUS["behavior"], ADVISORY)
        self.assertIn("behavior", CHECK_IDS)
        self.assertNotIn("behavior", DEFAULT_CHECKS)

    def test_ci_mode_does_nothing(self):
        self.add_plugin()
        got, evals, calls, _ = self.check([], ctx=self.ctx("ci"))
        self.assertEqual((got, calls), ([], []))

    def test_plugin_without_sources(self):
        self.add_plugin(queries=())
        got, _, calls, _ = self.check([])
        self.assertEqual((got, calls), ([], []))

    def test_triggers_pass_and_history(self):
        self.add_plugin()
        got, evals, _, _ = self.check([{"result": eval_result(eval_case(T(YES), 1.0), eval_case(T(NO), 1.0))}])
        self.assertEqual(got, [])
        self.assertEqual(len(evals), 1)
        argv = evals[0]["argv"]
        pairs = dict(zip(argv, argv[1:]))
        self.assertEqual((pairs["--eval-dir"], pairs["--ablation"], pairs["--runs"]), ("evals-trigger", "none", "1"))
        self.assertFalse(any(f.startswith("mocks") for f in evals[0]["files"]))
        rows = self.hist()
        self.assertEqual(sorted(r["case"] for r in rows), sorted([T(YES), T(NO)]))
        self.assertTrue(all(r["ok"] and r["plugin"] == "b-dev" and r["model"] == "claude-sonnet-5-5" for r in rows))

    def test_command_routing_to_a_skill_counts_as_the_skill(self):
        self.add_plugin(quality=QUALITY, commands={"explain": "Read `${CLAUDE_PLUGIN_ROOT}/skills/web/SKILL.md` first.\n",
                                                   "unrelated": "does its own thing\n"})
        first = eval_result(eval_case(T(YES), 0.0), eval_case(T(NO), 1.0))
        rerun = eval_result(eval_case(T(YES), 1.0, runs=[{"score": 1.0, "error": None}, {"score": 1.0, "error": None}]))
        quality = eval_result(eval_case("q-web-1", 1.0, delta=0.5))
        with mock.patch.object(evalgen, "skill_routes", wraps=evalgen.skill_routes) as routes:
            got, evals, _, _ = self.check([{"result": first}, {"result": rerun}, {"result": quality}])
        self.assertEqual(routes.call_count, 1)                       # раз на плагин, не на каждый вызов claude
        self.assertEqual(routes.call_args.args[1], "b-dev")
        want = evalgen.input_match("b-dev", "web", ("explain",))
        by_dir = {}
        for call in evals:
            argv = call["argv"]
            by_dir[argv[argv.index("--eval-dir") + 1]] = call["fired"]
        self.assertEqual(sorted(by_dir), [evalgen.QUALITY_DIR, evalgen.RERUN_DIR, evalgen.TRIGGER_DIR])
        for eval_dir, fired in by_dir.items():
            self.assertTrue(fired, eval_dir)
            for rel, text in fired.items():
                self.assertIn(json.dumps(want)[1:-1], text, (eval_dir, rel))    # input_match в YAML — JSON-строка
                self.assertNotIn("unrelated", text)

    def test_plugin_without_commands_keeps_plain_graders(self):
        self.add_plugin()
        _, evals, _, _ = self.check([{"result": eval_result(eval_case(T(YES), 1.0), eval_case(T(NO), 1.0))}])
        want = evalgen.input_match("b-dev", "web")
        self.assertEqual(len(evals[0]["fired"]), 2)
        self.assertTrue(all(json.dumps(want)[1:-1] in text for text in evals[0]["fired"].values()))

    def test_confirmed_misfire(self):
        self.add_plugin()
        first = eval_result(eval_case(T(YES), 0.0, runs=[{"score": 0.0, "error": "exit 1: Reached maximum number of turns (1)"}]),
                            eval_case(T(NO), 1.0))
        rerun = eval_result(eval_case(T(YES), 0.5, runs=[{"score": 0.0, "error": None}, {"score": 1.0, "error": None}]))
        got, evals, _, _ = self.check([{"result": first}, {"result": rerun}])
        self.assertEqual([(f.level, f.file) for f in got], [(FAIL, "plugins/b-dev/skills/web/evals/triggers.json")])
        self.assertTrue(got[0].message.startswith(L2_MISFIRE))
        self.assertIn("2 из 3", got[0].message)
        argv = evals[1]["argv"]
        pairs = dict(zip(argv, argv[1:]))
        self.assertEqual((pairs["--eval-dir"], pairs["--runs"]), ("evals-rerun", "2"))
        self.assertEqual({f.split(os.sep)[0] for f in evals[1]["files"]}, {T(YES)})
        scores = {r["case"]: r["score"] for r in self.hist()}
        self.assertAlmostEqual(scores[T(YES)], 1 / 3)

    def test_flaky_is_info(self):
        self.add_plugin()
        first = eval_result(eval_case(T(YES), 0.0), eval_case(T(NO), 1.0))
        rerun = eval_result(eval_case(T(YES), 1.0, runs=[{"score": 1.0, "error": None}, {"score": 1.0, "error": None}]))
        got, _, _, _ = self.check([{"result": first}, {"result": rerun}])
        self.assertEqual([f.level for f in got], [INFO])
        self.assertTrue(got[0].message.startswith(L2_FLAKY))

    def test_quality_below_threshold_and_unhelpful(self):
        self.add_plugin(queries=(), quality=QUALITY)
        got, evals, _, _ = self.check([{"result": eval_result(eval_case("q-web-1", 0.5, delta=-0.1))}])
        self.assertEqual(sorted((f.level, f.message.split(":")[0]) for f in got),
                         sorted([(FAIL, L2_BELOW), (INFO, L2_UNHELPFUL)]))
        self.assertEqual({f.file for f in got}, {"plugins/b-dev/skills/web/evals/evals.json"})
        argv = evals[0]["argv"]
        pairs = dict(zip(argv, argv[1:]))
        self.assertEqual((pairs["--eval-dir"], pairs["--ablation"]), ("evals-quality", "with-without"))
        self.assertNotIn("--runs", argv)

    def test_case_threshold_from_manifest(self):
        self.add_plugin(queries=(), quality=QUALITY)
        self.repo.tests("b-dev", {"plugin-test.toml": '[behavior.case."q-web-1"]\nthreshold = 0.4  # судья строг\n'})
        got, _, _, _ = self.check([{"result": eval_result(eval_case("q-web-1", 0.5, delta=0.2))}])
        self.assertEqual(got, [])

    def test_regression_from_history(self):
        self.add_plugin(queries=(), quality=QUALITY)
        self.repo.tests("b-dev", {"plugin-test.toml": "[behavior]\nthreshold = 0.6\n"})
        repo_name = os.path.basename(self.repo.root)
        history.append(self.state, [{"repo": repo_name, "plugin": "b-dev", "case": "q-web-1", "score": 1.0, "ok": True,
                                     "model": evalrun.MODEL} for _ in range(4)])
        got, _, _, _ = self.check([{"result": eval_result(eval_case("q-web-1", 0.7, delta=0.3))}])
        self.assertEqual([(f.level, f.message.split(":")[0]) for f in got], [(FAIL, L2_REGRESS)])
        self.assertIn("медиана", got[0].message)

    def test_history_of_another_model_is_not_a_baseline(self):
        self.add_plugin(queries=(), quality=QUALITY)
        self.repo.tests("b-dev", {"plugin-test.toml": "[behavior]\nthreshold = 0.6\n"})
        repo_name = os.path.basename(self.repo.root)
        history.append(self.state, [{"repo": repo_name, "plugin": "b-dev", "case": "q-web-1", "score": 1.0, "ok": True,
                                     "model": "claude-older"} for _ in range(4)]
                       + [{"repo": repo_name, "plugin": "b-dev", "case": "q-web-1", "score": 1.0, "ok": True}] * 2)
        got, _, _, _ = self.check([{"result": eval_result(eval_case("q-web-1", 0.7, delta=0.3))}])
        self.assertEqual(got, [])

    def test_mocks_only_in_quality_tree(self):
        self.add_plugin(queries=(), quality=QUALITY, mcp={"srv": {"command": "srv-bin"}})
        self.repo.tests("b-dev", {"snapshots/mcp/srv.tools.json": {"tools": [
            {"name": "t1", "description": "d", "inputSchema": {"type": "object"}}]}})
        _, evals, _, _ = self.check([{"result": eval_result(eval_case("q-web-1", 1.0, delta=0.5))}])
        files = evals[0]["files"]
        for f in ("mocks/srv/_tools.json", "mocks/srv/_server.md", "q-web-1/prompt.md"):
            self.assertIn(f.replace("/", os.sep), files)

    def test_limit_stops_following_plugins(self):
        self.add_plugin("a-dev")
        self.add_plugin("b-dev")
        ctx = self.ctx()
        first = eval_result(eval_case(T(YES), 0.0, runs=[{"score": 0.0, "error": None, "trace": [REJECTED]}]),
                            eval_case(T(NO), 1.0))
        got_a, evals_a, _, ctx = self.check([{"result": first}], name="a-dev", ctx=ctx)
        self.assertEqual([f.level for f in got_a], [INFRA, INFO])
        self.assertTrue(got_a[0].message.startswith(L2_NOT_RUN))
        self.assertTrue(got_a[1].message.startswith(L2_STOPPED))
        self.assertIn("rejected", ctx.l2_stop)
        self.assertEqual(len(evals_a), 1)
        self.assertEqual(self.hist(), [])
        got_b, _, calls_b, _ = self.check([{"result": eval_result()}], name="b-dev", ctx=ctx)
        self.assertEqual([f.level for f in got_b], [INFRA])
        self.assertTrue(got_b[0].message.startswith(L2_NOT_RUN))
        self.assertEqual(calls_b, [])

    def test_deadline_passed(self):
        self.add_plugin()
        ctx = self.ctx()
        ctx.deadline = time.time() - 1
        got, _, calls, _ = self.check([], ctx=ctx)
        self.assertEqual([f.level for f in got], [INFRA])
        self.assertIn("окно", got[0].message)
        self.assertEqual(calls, [])

    def test_preflight_refusal_sets_stop(self):
        self.add_plugin()
        got, evals, _, ctx = self.check([], auth='{"loggedIn": true, "authMethod": "apiKey"}')
        self.assertEqual([f.level for f in got], [INFRA, INFO])
        self.assertTrue(got[0].message.startswith(L2_NOT_RUN))
        self.assertIn("не по подписке", got[0].message)
        self.assertTrue(got[1].message.startswith(L2_STOPPED))
        self.assertIn("не по подписке", got[1].message)
        self.assertTrue(ctx.l2_stop)
        self.assertEqual(evals, [])

    def test_eval_error_is_one_infra(self):
        self.add_plugin()
        (got, _, _, _), err = self.err_check([{"stdout": "<<garbage>>"}])
        self.assertEqual([f.level for f in got], [INFRA])
        self.assertTrue(got[0].message.startswith(L2_FAILED))
        self.assertIn("[evalrun]", err)

    def test_threshold_stop_with_valid_results_is_reported(self):
        self.add_plugin()
        hot = {"status": "allowed", "unifiedWindows": {"five_hour": {"utilization": 0.95}}}
        res = eval_result(eval_case(T(YES), 1.0, runs=[{"score": 1.0, "error": None, "trace": [hot]}]),
                          eval_case(T(NO), 1.0))
        got, _, _, ctx = self.check([{"result": res}])
        self.assertEqual([(f.level, f.message.split(":")[0]) for f in got], [(INFO, L2_STOPPED)])
        self.assertIn("5 часов", ctx.l2_stop)
        self.assertEqual(len(self.hist()), 2)

    def test_call_timeout_clamped_to_deadline(self):
        self.add_plugin()
        ctx = self.ctx()
        ctx.deadline = time.time() + 100
        seen = {}

        def fake_run(*args, **kw):
            seen.update(kw)
            raise evalrun.EvalError("stop here")

        with mock.patch.object(behavior.evalrun, "preflight", return_value=""), \
                mock.patch.object(behavior.evalrun, "run", side_effect=fake_run), \
                mock.patch.object(behavior.shutil, "which", return_value="/bin/true"):
            behavior.run(load_plugin(self.repo.root, "b-dev"), ctx, manifest.load(load_plugin(self.repo.root, "b-dev"))[0])
        self.assertLessEqual(seen["timeout"], 100 + behavior.GRACE_AFTER_DEADLINE)
        self.assertGreaterEqual(seen["timeout"], behavior.MIN_CALL_TIMEOUT)

    def test_env_file_key_never_reaches_child(self):
        self.add_plugin()
        ctx = self.ctx()
        ctx.env = {"ANTHROPIC_API_KEY": "sk-test-not-real"}
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-not-real"}):
            _, _, calls, _ = self.check([{"result": eval_result(eval_case(T(YES), 1.0), eval_case(T(NO), 1.0))}],
                                        ctx=ctx)
        self.assertTrue(calls)
        for c in calls:
            self.assertNotIn("ANTHROPIC_API_KEY", c["env"])

    def err_check(self, plan, **kw):
        """check() с перехватом stderr: подробности сбоев уходят туда, в находки — только классификация."""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            out = self.check(plan, **kw)
        return out, err.getvalue()

    def assert_no_text(self, found, *sentinels):
        for f in found:
            blob = json.dumps(f.to_dict(), ensure_ascii=False)
            for sentinel in sentinels:
                self.assertNotIn(sentinel, blob)

    def test_free_text_never_reaches_findings(self):
        # 1. текст ошибки прогона: все прогоны кейса с ошибкой
        self.add_plugin(queries=(), quality=QUALITY)
        (got, _, _, _), err = self.err_check([{"result": eval_result(eval_case("q-web-1", 0.0, runs=[
            {"score": 0.0, "error": "SENTINEL_RUN_ERR token=abc"}, {"score": 0.0, "error": "SENTINEL_RUN_ERR again"}]))}])
        self.assertEqual([(f.level, f.message) for f in got], [(INFRA, "%s: q-web-1 — все 2 прогона с ошибкой" % L2_FAILED)])
        self.assertIn("[behavior]", err)
        self.assertIn("SENTINEL_RUN_ERR", err)
        self.assert_no_text(got, "SENTINEL_RUN_ERR")
        # 2. stderr CLI при коде 1 и при отсутствии результата
        self.add_plugin("c-dev")
        results = eval_result(eval_case(T(YES), 1.0), eval_case(T(NO), 1.0))
        (got, _, _, _), err = self.err_check([{"exit": 1, "stderr": "SENTINEL_STDERR boom at some path", "result": results}],
                                             name="c-dev")
        self.assertEqual([f.message for f in got], ["%s: срабатывание: claude plugin eval, код 1" % L2_FAILED])
        self.assertIn("SENTINEL_STDERR", err)
        self.assert_no_text(got, "SENTINEL_STDERR")
        self.add_plugin("d-dev")
        (got, _, _, _), err = self.err_check([{"stdout": "<<garbage>>", "stderr": "SENTINEL_STDERR2 boom"}], name="d-dev")
        self.assertEqual([f.message for f in got], ["%s: срабатывание: claude plugin eval: нет результата (код 0)" % L2_FAILED])
        self.assertIn("SENTINEL_STDERR2", err)
        self.assert_no_text(got, "SENTINEL_STDERR2")
        # 3. текст ошибки лимита
        self.add_plugin("e-dev")
        limited = eval_result(eval_case(T(YES), 0.0, runs=[{"score": 0.0, "error": "429 rate limit SENTINEL_LIMIT"}]),
                              eval_case(T(NO), 1.0))
        (got, _, _, ctx), err = self.err_check([{"result": limited}], name="e-dev")
        self.assertEqual(ctx.l2_stop, "ошибка лимита в прогоне")
        self.assertTrue(got)
        self.assertIn("SENTINEL_LIMIT", err)
        self.assert_no_text(got, "SENTINEL_LIMIT")

    def test_runs_phrase_plural_forms(self):
        for n, want in ((1, "единственный прогон"), (2, "все 2 прогона"), (4, "все 4 прогона"), (5, "все 5 прогонов"),
                        (11, "все 11 прогонов"), (12, "все 12 прогонов"), (21, "все 21 прогон"),
                        (22, "все 22 прогона"), (25, "все 25 прогонов")):
            self.assertEqual(behavior._runs_phrase(n), want)

    def test_window_closed_before_a_following_call(self):
        self.add_plugin()
        ctx = self.ctx()
        ctx.deadline = time.time() + 1000
        real, runs = evalrun.run, []

        def run_then_close_window(*args, **kw):
            runs.append(kw.get("runs"))
            res = real(*args, **kw)
            ctx.deadline = time.time() - behavior.GRACE_AFTER_DEADLINE + 10   # до конца вызова осталось 10 с
            return res

        first = eval_result(eval_case(T(YES), 0.0), eval_case(T(NO), 1.0))
        with mock.patch.object(evalrun, "run", side_effect=run_then_close_window):
            got, evals, _, ctx = self.check([{"result": first}], ctx=ctx)
        self.assertEqual(runs, [1])
        self.assertEqual(len(evals), 1)
        self.assertEqual({f.level for f in got}, {INFRA})
        self.assertTrue(all(f.message.startswith(L2_NOT_RUN) for f in got))
        self.assertIn("%s: окно ночи закончилось (повтор срабатывания)" % L2_NOT_RUN, [f.message for f in got])
        self.assertEqual(ctx.l2_stop, "")

    def test_eval_error_after_the_window_is_carried_not_a_failure(self):
        self.add_plugin()
        ctx = self.ctx()
        ctx.deadline = time.time() + 1000

        def fake_run(*args, **kw):
            ctx.deadline = time.time() - 1
            raise evalrun.EvalError("claude plugin eval не завершился за 5400 с")

        with mock.patch.object(behavior.evalrun, "preflight", return_value=""), \
                mock.patch.object(behavior.evalrun, "run", side_effect=fake_run), \
                mock.patch.object(behavior.shutil, "which", return_value="/bin/true"):
            plugin = load_plugin(self.repo.root, "b-dev")
            got = behavior.run(plugin, ctx, manifest.load(plugin)[0])
        self.assertEqual([(f.level, f.message) for f in got],
                         [(INFRA, "%s: окно ночи закончилось во время прогона (срабатывание)" % L2_NOT_RUN)])

    def test_unwritable_history_keeps_the_findings(self):
        self.add_plugin()
        blocker = os.path.join(self.repo.root, "state-is-a-file")
        with open(blocker, "w") as fh:
            fh.write("x")
        ctx = self.ctx()
        ctx.state_dir = blocker
        first = eval_result(eval_case(T(YES), 0.0, runs=[{"score": 0.0, "error": None}]), eval_case(T(NO), 1.0))
        rerun = eval_result(eval_case(T(YES), 0.0, runs=[{"score": 0.0, "error": None}, {"score": 0.0, "error": None}]))
        got, _, _, _ = self.check([{"result": first}, {"result": rerun}], ctx=ctx)
        self.assertEqual(sorted((f.level, f.message.split(":")[0]) for f in got),
                         sorted([(FAIL, L2_MISFIRE), (INFRA, L2_FAILED)]))
        self.assertTrue([f for f in got if "история не записана" in f.message])

    def test_skip_behavior_stops_the_run_not_only_the_findings(self):
        self.add_plugin(quality=QUALITY)
        self.repo.tests("b-dev", {"plugin-test.toml": '[skip]\n"behavior" = ["skills/web/evals/triggers.json"]\n'})
        got, evals, _, _ = self.check([{"result": eval_result(eval_case("q-web-1", 1.0, delta=0.5))}])
        self.assertEqual(got, [])
        self.assertEqual([dict(zip(c["argv"], c["argv"][1:]))["--eval-dir"] for c in evals], ["evals-quality"])

    def test_skip_quality_file_and_native_case_and_everything(self):
        self.add_plugin(quality=QUALITY)
        self.repo.tests("b-dev", {"evals/smoke/prompt.md": "p", "evals/smoke/graders/g.md": "g",
                                  "plugin-test.toml": '[skip]\n"behavior" = ["skills/web/evals/evals.json", "n-smoke"]\n'})
        _, evals, _, _ = self.check([{"result": eval_result(eval_case(T(YES), 1.0), eval_case(T(NO), 1.0))}])
        self.assertEqual([dict(zip(c["argv"], c["argv"][1:]))["--eval-dir"] for c in evals], ["evals-trigger"])
        self.repo.tests("b-dev", {"plugin-test.toml": '[skip]\n"behavior" = ["*"]\n'})
        got, evals, calls, _ = self.check([], name="b-dev")
        self.assertEqual((got, evals, calls), ([], [], []))
        both = eval_result(eval_case("q-web-1", 1.0, delta=0.5), eval_case("n-smoke", 1.0, delta=0.5))
        self.repo.tests("b-dev", {"plugin-test.toml": '[skip]\n"behavior" = ["skills/web/evals/*"]\n'})
        _, evals, _, _ = self.check([{"result": both}], name="b-dev")   # родной кейс остаётся
        self.assertEqual([dict(zip(c["argv"], c["argv"][1:]))["--eval-dir"] for c in evals], ["evals-quality"])
        top = {f.split(os.sep)[0] for f in evals[0]["files"]}
        self.assertIn("n-smoke", top)
        self.assertNotIn("q-web-1", top)
        self.repo.tests("b-dev", {"plugin-test.toml": '[skip]\n"behavior" = ["skills/web/evals/triggers.json"]\n'})
        _, evals, _, _ = self.check([{"result": both}], name="b-dev")
        self.assertEqual([dict(zip(c["argv"], c["argv"][1:]))["--eval-dir"] for c in evals], ["evals-quality"])
        self.assertTrue({"n-smoke", "q-web-1"} <= {f.split(os.sep)[0] for f in evals[0]["files"]})


if __name__ == "__main__":
    unittest.main()
