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
from plugin_test_fixtures import (Repo, context, eval_case, eval_result, isolate_l2_env, load_plugin,  # noqa: E402
                                  stub_calls, stub_claude)

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


YES2, NO2 = "also need the other thing done", "tell me another story"
CAP = "exit 1: Reached maximum number of turns (1)"
OUTAGE = "API Error: 500 SENTINEL_OUTAGE"
API_YES, API_NO = "call the endpoint for me", "tell me a joke"
QUALITY_API = [{"id": 1, "prompt": "how to call it", "expected_output": "e", "files": [], "expectations": ["says how"]}]
SKILLS_LINE = "[behavior] b-dev: %s — %s\n"


def T(query):
    return evalgen.trigger_name("web", query)


def TA(query):
    return evalgen.trigger_name("api", query)


def clean(score):
    return {"score": score, "error": None}


def failed_run(error=OUTAGE):
    return {"score": 0.0, "error": error}


class BehaviorTest(unittest.TestCase):
    def setUp(self):
        isolate_l2_env(self)
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.state = os.path.join(self.repo.root, "state")

    def add_plugin(self, name="b-dev", queries=((YES, True), (NO, False)), quality=None, mcp=None, commands=None,
                   files=None, plugin_json=None):
        files = dict({"skills/web/SKILL.md": SKILL % "web"}, **(files or {}))
        for command, text in (commands or {}).items():
            files["commands/%s.md" % command] = text
        if queries:
            files["skills/web/evals/triggers.json"] = json.dumps([{"query": q, "should_trigger": t} for q, t in queries])
        if quality:
            files["skills/web/evals/evals.json"] = json.dumps({"skill_name": "web", "evals": quality})
        self.repo.plugin(name, files=files, mcp=mcp, plugin_json=plugin_json)

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

    AGENT = {"agents/helper.md": "---\nname: helper\ndescription: d\n---\nbody\n"}
    WITH_AGENTS = {"name": "b-dev", "version": "1.0.0", "description": "fixture", "agents": ["./agents/helper.md"]}

    def by_eval_dir(self, evals):
        out = {}
        for call in evals:
            argv = call["argv"]
            out[argv[argv.index("--eval-dir") + 1]] = call
        return out

    def test_every_run_uses_one_copy_without_agents(self):
        # L2 меряет skills: агент плагина в песочнице забирает ход у Skill (срабатывание) и портит ответ (качество)
        self.add_plugin(quality=QUALITY, files=self.AGENT, plugin_json=self.WITH_AGENTS)
        first = eval_result(eval_case(T(YES), 0.0), eval_case(T(NO), 1.0))
        rerun = eval_result(eval_case(T(YES), 1.0, runs=[{"score": 1.0, "error": None}, {"score": 1.0, "error": None}]))
        quality = eval_result(eval_case("q-web-1", 1.0, delta=0.5))
        with mock.patch.object(evalgen, "copy_plugin", wraps=evalgen.copy_plugin) as copies:
            _, evals, _, _ = self.check([{"result": first}, {"result": rerun}, {"result": quality}])
        calls = self.by_eval_dir(evals)
        self.assertEqual(sorted(calls), [evalgen.QUALITY_DIR, evalgen.RERUN_DIR, evalgen.TRIGGER_DIR])
        for eval_dir, call in calls.items():
            self.assertNotIn(os.path.join("agents", "helper.md"), call["copy_files"], eval_dir)
            self.assertFalse([f for f in call["copy_files"] if f.startswith("agents" + os.sep)], eval_dir)
            self.assertNotIn("agents", json.loads(call["manifest"]), eval_dir)
            self.assertEqual(os.path.basename(call["argv"][2]), "b-dev", eval_dir)     # имя каталога копии — каталог плагина
        self.assertEqual({c["argv"][2] for c in calls.values()}, {calls[evalgen.TRIGGER_DIR]["argv"][2]})   # одна копия на все
        self.assertEqual(copies.call_count, 1)                                           # раз на плагин
        self.assertTrue(copies.call_args.kwargs.get("drop_agents"))
        self.assertTrue(os.path.isfile(os.path.join(self.repo.root, "plugins", "b-dev", "agents", "helper.md")))   # источник цел

    def test_trigger_only_and_quality_only_plugins_build_one_agentless_copy(self):
        for queries, quality, result in (((YES, True), (NO, False)), None, eval_result(eval_case(T(YES), 1.0), eval_case(T(NO), 1.0))), \
                                        ((), QUALITY, eval_result(eval_case("q-web-1", 1.0, delta=0.5))):
            with self.subTest(queries=bool(queries)):
                self.repo.cleanup()
                self.repo = Repo()
                self.add_plugin(queries=queries, quality=quality, files=self.AGENT, plugin_json=self.WITH_AGENTS)
                with mock.patch.object(evalgen, "copy_plugin", wraps=evalgen.copy_plugin) as copies:
                    _, evals, _, _ = self.check([{"result": result}])
                self.assertEqual(copies.call_count, 1)
                self.assertTrue(copies.call_args.kwargs.get("drop_agents"))
                self.assertNotIn(os.path.join("agents", "helper.md"), evals[0]["copy_files"])

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

    def test_score_within_float_noise_of_threshold_is_not_below(self):
        self.add_plugin(queries=(), quality=QUALITY)
        for score in (0.7999999999999999, 0.8 - 1e-12):    # среднее трёх оценок в двоичной арифметике
            got, _, _, _ = self.check([{"result": eval_result(eval_case("q-web-1", score, delta=0.2))}])
            self.assertEqual(got, [], score)

    def test_score_below_threshold_by_more_than_noise_is_below(self):
        self.add_plugin(queries=(), quality=QUALITY)
        for score in (0.79, 0.8 - 1e-8):
            got, _, _, _ = self.check([{"result": eval_result(eval_case("q-web-1", score, delta=0.2))}])
            self.assertEqual([(f.level, f.message.split(":")[0]) for f in got], [(FAIL, L2_BELOW)], score)

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


    # --- волны: фильтр skills (PLUGIN_TEST_L2_SKILLS) и быстрый режим качества (PLUGIN_TEST_L2_QUICK) ---

    def add_two_skills(self):
        """web и api, у каждого срабатывание и качество; плюс родной кейс smoke."""
        self.add_plugin(quality=QUALITY, files={
            "skills/api/SKILL.md": SKILL % "api",
            "skills/api/evals/triggers.json": json.dumps([{"query": API_YES, "should_trigger": True},
                                                          {"query": API_NO, "should_trigger": False}]),
            "skills/api/evals/evals.json": json.dumps({"skill_name": "api", "evals": QUALITY_API})})
        self.repo.tests("b-dev", {"evals/smoke/prompt.md": "p", "evals/smoke/graders/g.md": "g"})

    def api_plan(self):
        return [{"result": eval_result(eval_case(TA(API_YES), 1.0), eval_case(TA(API_NO), 1.0))},
                {"result": eval_result(eval_case("q-api-1", 1.0, delta=0.5))}]

    def tops(self, call):
        return {f.split(os.sep)[0] for f in call["files"]}

    def test_skill_filter_keeps_only_the_named_skill_and_drops_native_cases(self):
        self.add_two_skills()
        with mock.patch.dict(os.environ, {behavior.SKILLS_VAR: " api ,, "}):
            (got, evals, _, _), err = self.err_check(self.api_plan())
        self.assertEqual(got, [])
        self.assertEqual(err, "")
        calls = self.by_eval_dir(evals)
        self.assertEqual(sorted(calls), [evalgen.QUALITY_DIR, evalgen.TRIGGER_DIR])
        self.assertEqual(self.tops(calls[evalgen.TRIGGER_DIR]), {TA(API_YES), TA(API_NO)})
        self.assertEqual(self.tops(calls[evalgen.QUALITY_DIR]), {"q-api-1"})     # ни q-web-1, ни n-smoke
        self.assertEqual(sorted(r["case"] for r in self.hist()), sorted([TA(API_YES), TA(API_NO), "q-api-1"]))

    def test_skill_filter_accepts_several_names(self):
        self.add_two_skills()
        both = [{"result": eval_result(*[eval_case(n, 1.0) for n in (T(YES), T(NO), TA(API_YES), TA(API_NO))])},
                {"result": eval_result(eval_case("q-web-1", 1.0, delta=0.5), eval_case("q-api-1", 1.0, delta=0.5))}]
        with mock.patch.dict(os.environ, {behavior.SKILLS_VAR: "api,web"}):
            (got, evals, _, _), err = self.err_check(both)
        self.assertEqual((got, err), ([], ""))
        calls = self.by_eval_dir(evals)
        self.assertEqual(len(self.tops(calls[evalgen.TRIGGER_DIR])), 4)
        self.assertEqual(self.tops(calls[evalgen.QUALITY_DIR]), {"q-web-1", "q-api-1"})

    def test_skill_filter_unset_or_empty_changes_nothing(self):
        for value in (None, "", " , ,"):
            with self.subTest(value=value):
                self.add_two_skills()
                env = {} if value is None else {behavior.SKILLS_VAR: value}
                every = [{"result": eval_result(*[eval_case(n, 1.0) for n in (T(YES), T(NO), TA(API_YES), TA(API_NO))])},
                         {"result": eval_result(eval_case("q-web-1", 1.0, delta=0.5), eval_case("q-api-1", 1.0, delta=0.5),
                                                eval_case("n-smoke", 1.0, delta=0.5))}]
                with mock.patch.dict(os.environ, env):
                    (got, evals, _, _), err = self.err_check(every)
                self.assertEqual((got, err), ([], ""))
                calls = self.by_eval_dir(evals)
                self.assertEqual(len(self.tops(calls[evalgen.TRIGGER_DIR])), 4)
                self.assertEqual(self.tops(calls[evalgen.QUALITY_DIR]), {"q-web-1", "q-api-1", "n-smoke"})

    def test_skill_filter_without_a_skill_of_the_plugin_runs_nothing(self):
        self.add_two_skills()
        with mock.patch.dict(os.environ, {behavior.SKILLS_VAR: "nope, zzz"}):
            (got, evals, calls, ctx), err = self.err_check(self.api_plan())
        self.assertEqual((got, calls), ([], []))                # ни проверки входа, ни вызова claude, ни переноса на ночь
        self.assertEqual(err, SKILLS_LINE % (behavior.SKILLS_VAR, "нет skill плагина в фильтре"))
        self.assertEqual(self.hist(), [])
        stopped = self.ctx()
        stopped.l2_stop = "лимит"
        with mock.patch.dict(os.environ, {behavior.SKILLS_VAR: "nope"}):
            got, _, calls, _ = self.check([], ctx=stopped)
        self.assertEqual((got, calls), ([], []))                # вне фильтра плагин не «не прогнан» и на ночь не переносится

    def test_skill_filter_names_the_unknown_ones_when_another_matched(self):
        self.add_two_skills()
        with mock.patch.dict(os.environ, {behavior.SKILLS_VAR: "api, nope ,web, zzz"}):
            (got, evals, _, _), err = self.err_check(self.api_plan())
        self.assertEqual(err, SKILLS_LINE % (behavior.SKILLS_VAR, "неизвестные: nope, zzz"))
        self.assertTrue(evals)                                  # known ones ran

    def test_skill_filter_named_plugin_still_carries_over_on_stop(self):
        self.add_two_skills()
        ctx = self.ctx()
        ctx.l2_stop = "лимит"
        with mock.patch.dict(os.environ, {behavior.SKILLS_VAR: "api"}):
            got, _, calls, _ = self.check([], ctx=ctx)
        self.assertEqual([f.level for f in got], [INFRA])        # плагин в фильтре — остановка по-прежнему переносит его
        self.assertTrue(got[0].message.startswith(L2_NOT_RUN))
        self.assertEqual(calls, [])
        got, _, calls, _ = self.check(self.api_plan())           # переменной нет — полный прогон
        self.assertGreater(len(calls), 2)

    def test_quick_mode_quality_is_one_run_without_the_without_arm(self):
        self.add_plugin(queries=(), quality=QUALITY)
        with mock.patch.dict(os.environ, {behavior.QUICK_VAR: "1"}):
            (got, evals, _, _), err = self.err_check([{"result": eval_result(eval_case("q-web-1", 1.0))}])
        self.assertEqual(got, [])
        argv = evals[0]["argv"]
        pairs = dict(zip(argv, argv[1:]))
        self.assertEqual((pairs["--eval-dir"], pairs["--ablation"], pairs["--runs"]), ("evals-quality", "none", "1"))
        prompt = evals[0]["prompts"][os.path.join("q-web-1", "prompt.md")]
        self.assertIn("\nruns: 1\n", prompt)
        self.assertNotIn("runs: 3", prompt)
        self.assertEqual(err, "[behavior] b-dev: быстрый режим качества (1 прогон, без сравнения)\n")

    def test_quick_mode_leaves_the_trigger_tree_alone(self):
        self.add_plugin(quality=QUALITY)
        first = eval_result(eval_case(T(YES), 0.0), eval_case(T(NO), 1.0))
        rerun = eval_result(eval_case(T(YES), 1.0, runs=[{"score": 1.0, "error": None}, {"score": 1.0, "error": None}]))
        with mock.patch.dict(os.environ, {behavior.QUICK_VAR: "1"}):
            _, evals, _, _ = self.check([{"result": first}, {"result": rerun},
                                         {"result": eval_result(eval_case("q-web-1", 1.0))}])
        calls = {c["argv"][c["argv"].index("--eval-dir") + 1]: c for c in evals}
        for eval_dir, runs in ((evalgen.TRIGGER_DIR, "1"), (evalgen.RERUN_DIR, "2")):
            argv = calls[eval_dir]["argv"]
            pairs = dict(zip(argv, argv[1:]))
            self.assertEqual((pairs["--ablation"], pairs["--runs"]), ("none", runs), eval_dir)
        for rel, text in calls[evalgen.TRIGGER_DIR]["prompts"].items():
            self.assertIn("\nruns: 1\n", text, rel)

    def test_quick_mode_has_no_unhelpful_no_regress_but_keeps_below(self):
        self.add_plugin(queries=(), quality=QUALITY)
        self.repo.tests("b-dev", {"plugin-test.toml": "[behavior]\nthreshold = 0.6\n"})
        repo_name = os.path.basename(self.repo.root)
        history.append(self.state, [{"repo": repo_name, "plugin": "b-dev", "case": "q-web-1", "score": 1.0, "ok": True,
                                     "model": evalrun.MODEL} for _ in range(4)])
        with mock.patch.dict(os.environ, {behavior.QUICK_VAR: "1"}):
            # 0.7 при медиане 1.0 — регресс в обычном режиме; дельта <= 0 — «не помогает» в обычном
            got, _, _, _ = self.check([{"result": eval_result(eval_case("q-web-1", 0.7, delta=-0.3))}])
            self.assertEqual(got, [])
            got, _, _, _ = self.check([{"result": eval_result(eval_case("q-web-1", 0.5))}])
        self.assertEqual([(f.level, f.message.split(":")[0]) for f in got], [(FAIL, L2_BELOW)])
        self.assertEqual(got[0].message, "%s: q-web-1 — 0.50 < 0.60" % L2_BELOW)
        got, _, _, _ = self.check([{"result": eval_result(eval_case("q-web-1", 0.7, delta=0.3))}])
        self.assertEqual([f.message.split(":")[0] for f in got], [L2_REGRESS])    # без quick регресс на месте

    def test_quick_mode_writes_trigger_history_but_no_quality_history(self):
        self.add_plugin(quality=QUALITY)
        with mock.patch.dict(os.environ, {behavior.QUICK_VAR: "1"}):
            got, _, _, _ = self.check([{"result": eval_result(eval_case(T(YES), 1.0), eval_case(T(NO), 1.0))},
                                       {"result": eval_result(eval_case("q-web-1", 1.0))}])
        self.assertEqual(got, [])
        self.assertEqual(sorted(r["case"] for r in self.hist()), sorted([T(YES), T(NO)]))

    def test_quick_mode_only_the_exact_value_one(self):
        self.add_plugin(queries=(), quality=QUALITY)
        for value in ("true", "0", "", "11", " 1", "yes", "on"):
            with self.subTest(value=value):
                with mock.patch.dict(os.environ, {behavior.QUICK_VAR: value}):
                    (got, evals, _, _), err = self.err_check(
                        [{"result": eval_result(eval_case("q-web-1", 1.0, delta=0.5))}])
                argv = evals[0]["argv"]
                pairs = dict(zip(argv, argv[1:]))
                self.assertEqual(pairs["--ablation"], "with-without")
                self.assertNotIn("--runs", argv)
                self.assertIn("\nruns: 3\n", evals[0]["prompts"][os.path.join("q-web-1", "prompt.md")])
                self.assertEqual(err, "")
        self.assertEqual(len(self.hist()), 7)          # обычный режим писал историю качества каждый раз

    def test_filter_and_quick_together(self):
        self.add_two_skills()
        env = {behavior.SKILLS_VAR: "api", behavior.QUICK_VAR: "1"}
        with mock.patch.dict(os.environ, env):
            (got, evals, _, _), err = self.err_check([self.api_plan()[0],
                                                      {"result": eval_result(eval_case("q-api-1", 1.0))}])
        self.assertEqual(got, [])
        calls = self.by_eval_dir(evals)
        self.assertEqual(self.tops(calls[evalgen.QUALITY_DIR]), {"q-api-1"})
        argv = calls[evalgen.QUALITY_DIR]["argv"]
        self.assertEqual(dict(zip(argv, argv[1:]))["--ablation"], "none")
        self.assertEqual(sorted(r["case"] for r in self.hist()), sorted([TA(API_YES), TA(API_NO)]))

    # --- ошибка отдельного прогона, не лимит, не становится вердиктом ---

    def quiet(self, plan, **kw):
        """check() без журнала в stderr — для тестов, которые читают находки, а не журнал."""
        return self.err_check(plan, **kw)[0]

    def hist_by_case(self):
        return {r["case"]: r for r in self.hist()}

    def test_outage_shaped_trigger_call_is_one_infra_and_no_misfire(self):
        self.add_plugin(queries=((YES, True), (YES2, True), (NO, False)))
        first = eval_result(eval_case(T(YES), 0.0, runs=[failed_run()]), eval_case(T(YES2), 0.0, runs=[failed_run()]),
                            eval_case(T(NO), 1.0))
        (got, evals, _, ctx), err = self.err_check([{"result": first}])
        self.assertEqual([(f.level, f.message) for f in got],
                         [(INFRA, "%s: срабатывание: более половины прогонов с ошибкой" % L2_FAILED)])
        self.assertEqual(len(evals), 1)                    # повтор не нужен: оценкам этого вызова не верить
        self.assertEqual(self.hist(), [])
        self.assertEqual(ctx.l2_stop, "")                  # это не лимит: следующий плагин ночи идёт как обычно
        self.assertIn("SENTINEL_OUTAGE", err)
        self.assert_no_text(got, "SENTINEL_OUTAGE")

    def test_errored_trigger_case_without_a_clean_run_is_infra_not_a_misfire(self):
        self.add_plugin(queries=((YES, True), (YES2, True), (NO, False), (NO2, False)))
        first = eval_result(eval_case(T(YES), 0.0, runs=[failed_run()]), eval_case(T(YES2), 0.0),
                            eval_case(T(NO), 1.0), eval_case(T(NO2), 1.0))
        rerun = eval_result(eval_case(T(YES), 0.0, runs=[failed_run(), failed_run()]),     # 2 из 4 — ровно половина
                            eval_case(T(YES2), 0.0, runs=[clean(0.0), clean(0.0)]))
        (got, evals, _, _), err = self.err_check([{"result": first}, {"result": rerun}])
        file = "plugins/b-dev/skills/web/evals/triggers.json"
        self.assertEqual(sorted((f.level, f.message.split(" — ")[0].split(":")[0], f.file) for f in got),
                         sorted([(FAIL, L2_MISFIRE, file), (INFRA, L2_FAILED, file)]))
        self.assertIn("%s: %s — прогон с ошибкой" % (L2_FAILED, T(YES)), [f.message for f in got])
        self.assertEqual({f.split(os.sep)[0] for f in evals[1]["files"]}, {T(YES), T(YES2)})   # с ошибкой — на повтор
        self.assertEqual(sorted(self.hist_by_case()), sorted([T(YES2), T(NO), T(NO2)]))       # а в историю — не попал
        self.assert_no_text(got, "SENTINEL_OUTAGE")

    def test_rerun_call_where_every_run_errored_is_invalid_as_a_whole(self):
        self.add_plugin(queries=((YES, True), (NO, False), (NO2, False)))
        first = eval_result(eval_case(T(YES), 0.0, runs=[failed_run()]), eval_case(T(NO), 1.0), eval_case(T(NO2), 1.0))
        rerun = eval_result(eval_case(T(YES), 0.0, runs=[failed_run(), failed_run()]))
        got, _, _, _ = self.quiet([{"result": first}, {"result": rerun}])
        self.assertEqual(sorted(f.message for f in got), sorted([
            "%s: повтор срабатывания: более половины прогонов с ошибкой" % L2_FAILED,
            "%s: %s не перепроверен" % (L2_NOT_RUN, T(YES))]))        # без вердикта и без «прогон с ошибкой» по кейсу

    def test_errored_first_run_is_judged_on_the_clean_reruns(self):
        self.add_plugin()      # YES, NO: один прогон с ошибкой из двух — ровно половина, вызов в силе
        cases = (([clean(1.0), clean(1.0)], None, 1.0, 2), ([failed_run(), clean(1.0)], None, 1.0, 1),
                 ([clean(0.0), clean(0.0)], (FAIL, L2_MISFIRE, "2 из 2"), 0.0, 2),
                 ([clean(0.0), clean(1.0)], (INFO, L2_FLAKY, "1 из 2"), 0.5, 2),
                 ([failed_run(), clean(0.0)], (INFRA, L2_NOT_RUN, "не перепроверен"), None, 0))
        for reruns, finding, score, runs in cases:
            with self.subTest(reruns=reruns):
                shutil.rmtree(self.state, ignore_errors=True)
                first = eval_result(eval_case(T(YES), 0.0, runs=[failed_run()]), eval_case(T(NO), 1.0))
                got, evals, _, _ = self.quiet([{"result": first}, {"result": eval_result(
                    eval_case(T(YES), 0.5, runs=reruns))}])
                self.assertEqual(len(evals), 2)
                if finding is None:
                    self.assertEqual(got, [])
                else:
                    self.assertEqual([(f.level, f.message.split(":")[0]) for f in got], [finding[:2]])
                    self.assertIn(finding[2], got[0].message)
                row = self.hist_by_case().get(T(YES))
                self.assertEqual(None if row is None else (row["score"], row["runs"]), None if score is None else (score, runs))

    def test_turn_cap_error_alone_does_not_make_a_run_errored(self):
        self.add_plugin()
        first = eval_result(eval_case(T(YES), 1.0, runs=[{"score": 1.0, "error": CAP}]),
                            eval_case(T(NO), 1.0, runs=[{"score": 1.0, "error": CAP}]))
        got, evals, _, _ = self.quiet([{"result": first}])
        self.assertEqual((got, len(evals)), ([], 1))
        self.assertEqual({r["case"]: (r["score"], r["runs"]) for r in self.hist()}, {T(YES): (1.0, 1), T(NO): (1.0, 1)})
        # промах с тем же обрывом — настоящий промах: 3 из 3, а не «прогон с ошибкой»
        first = eval_result(eval_case(T(YES), 0.0, runs=[{"score": 0.0, "error": CAP}]), eval_case(T(NO), 1.0))
        rerun = eval_result(eval_case(T(YES), 0.0, runs=[{"score": 0.0, "error": CAP}, {"score": 0.0, "error": CAP}]))
        got, _, _, _ = self.quiet([{"result": first}, {"result": rerun}])
        self.assertEqual([(f.level, f.message.split(":")[0]) for f in got], [(FAIL, L2_MISFIRE)])
        self.assertIn("3 из 3", got[0].message)

    def test_a_turn_cap_of_another_size_is_an_error_not_a_miss(self):
        self.add_plugin()
        odd = "exit 1: Reached maximum number of turns (3)"
        first = eval_result(eval_case(T(YES), 0.0, runs=[failed_run(odd)]), eval_case(T(NO), 1.0))
        rerun = eval_result(eval_case(T(YES), 1.0, runs=[clean(1.0), clean(1.0)]))
        got, _, _, _ = self.quiet([{"result": first}, {"result": rerun}])
        self.assertEqual(got, [])

    def test_more_than_half_of_the_rerun_call_errored_judges_none_of_it(self):
        self.add_plugin(queries=((YES, True), (YES2, True), (NO, False)))
        first = eval_result(eval_case(T(YES), 0.0), eval_case(T(YES2), 0.0), eval_case(T(NO), 1.0))
        rerun = eval_result(eval_case(T(YES), 0.0, runs=[failed_run(), failed_run()]),
                            eval_case(T(YES2), 0.0, runs=[failed_run(), clean(0.0)]))
        got, evals, _, _ = self.quiet([{"result": first}, {"result": rerun}])     # 3 из 4 прогонов с ошибкой
        self.assertEqual(len(evals), 2)
        self.assertEqual(sorted((f.level, f.message) for f in got), sorted([
            (INFRA, "%s: повтор срабатывания: более половины прогонов с ошибкой" % L2_FAILED),
            (INFRA, "%s: %s не перепроверен" % (L2_NOT_RUN, T(YES))),
            (INFRA, "%s: %s не перепроверен" % (L2_NOT_RUN, T(YES2)))]))
        self.assertEqual(sorted(self.hist_by_case()), [T(NO)])

    def test_exactly_half_errored_call_is_still_judged(self):
        self.add_plugin(queries=((YES, True), (YES2, True)))
        first = eval_result(eval_case(T(YES), 0.0), eval_case(T(YES2), 1.0))
        rerun = eval_result(eval_case(T(YES), 0.0, runs=[failed_run(), clean(0.0)]))     # 1 из 2: не больше половины
        got, _, _, _ = self.quiet([{"result": first}, {"result": rerun}])
        self.assertEqual([(f.level, f.message.split(":")[0]) for f in got], [(FAIL, L2_MISFIRE)])
        self.assertIn("2 из 2", got[0].message)

    def quality_case(self, with_runs, without_runs=None, score=0.0, delta=0.5):
        return eval_result(eval_case("q-web-1", score, delta=delta, runs=with_runs, without=without_runs))

    def test_quality_one_errored_run_of_three_is_scored_from_the_other_two(self):
        self.add_plugin(queries=(), quality=QUALITY)
        result = self.quality_case([clean(1.0), clean(1.0), failed_run()], [clean(0.6)] * 3, score=2 / 3, delta=0.1)
        (got, _, _, _), err = self.err_check([{"result": result}])
        self.assertEqual(got, [])                                  # 2/3 из агрегата CLI дало бы «ниже порога»
        row = self.hist_by_case()["q-web-1"]
        self.assertEqual((row["score"], row["runs"]), (1.0, 2))
        self.assertAlmostEqual(row["delta"], 0.4)                  # с плагином 1.0 против 0.6 без, не 0.1 из агрегата

    def test_quality_score_and_delta_come_from_clean_runs_in_both_arms(self):
        self.add_plugin(queries=(), quality=QUALITY)
        result = self.quality_case([clean(1.0), clean(0.5), failed_run()], [clean(0.9)] * 3, score=0.5, delta=0.3)
        got, _, _, _ = self.quiet([{"result": result}])
        self.assertEqual(sorted((f.level, f.message) for f in got), sorted([
            (FAIL, "%s: q-web-1 — 0.75 < 0.80" % L2_BELOW),
            (INFO, "%s: q-web-1 — с плагином 0.75, без 0.90" % L2_UNHELPFUL)]))
        shutil.rmtree(self.state)
        result = self.quality_case([clean(1.0)] * 3, [clean(0.4), clean(0.4), failed_run()], score=1.0, delta=-0.1)
        got, _, _, _ = self.quiet([{"result": result}])
        self.assertEqual(got, [])                                  # без плагина 0.4, дельта 0.6: «не помогает» нет
        self.assertAlmostEqual(self.hist_by_case()["q-web-1"]["delta"], 0.6)

    def test_quality_delta_needs_clean_runs_in_both_arms(self):
        self.add_plugin(queries=(), quality=QUALITY)
        result = self.quality_case([clean(1.0)] * 3, [failed_run()] * 3, score=1.0, delta=-0.5)
        got, _, _, _ = self.quiet([{"result": result}])
        self.assertEqual(got, [])
        row = self.hist_by_case()["q-web-1"]
        self.assertEqual((row["score"], row["delta"], row["runs"]), (1.0, None, 3))

    def test_quality_with_fewer_than_two_clean_runs_is_infra_not_a_verdict(self):
        self.add_plugin(queries=(), quality=QUALITY)
        result = self.quality_case([clean(1.0), failed_run(), failed_run()], [clean(0.5)] * 3, score=1 / 3, delta=-0.2)
        (got, _, _, _), err = self.err_check([{"result": result}])
        self.assertEqual([(f.level, f.message, f.file) for f in got],
                         [(INFRA, "%s: q-web-1 — чистых прогонов меньше двух из 3" % L2_FAILED,
                           "plugins/b-dev/skills/web/evals/evals.json")])
        self.assertEqual(self.hist(), [])
        self.assertIn("SENTINEL_OUTAGE", err)
        self.assert_no_text(got, "SENTINEL_OUTAGE")

    def test_quality_all_runs_errored_keeps_its_own_message(self):
        self.add_plugin(queries=(), quality=QUALITY)
        got, _, _, _ = self.quiet([{"result": self.quality_case([failed_run()] * 3, [clean(0.5)] * 3)}])
        self.assertEqual([f.message for f in got], ["%s: q-web-1 — все 3 прогона с ошибкой" % L2_FAILED])
        with mock.patch.dict(os.environ, {behavior.QUICK_VAR: "1"}):
            got, _, _, _ = self.quiet([{"result": self.quality_case([failed_run()])}])
        self.assertEqual([f.message for f in got], ["%s: q-web-1 — единственный прогон с ошибкой" % L2_FAILED])

    def test_quality_errored_run_does_not_hide_a_skipped_judge_of_the_clean_ones(self):
        self.add_plugin(queries=(), quality=QUALITY)
        skipped = dict(clean(1.0), skippedPaidGraders=True)
        errored = dict(failed_run(), skippedPaidGraders=True)
        got, _, _, _ = self.quiet([{"result": self.quality_case([clean(1.0), clean(1.0), errored], [clean(0.5)] * 3,
                                                                score=1.0)}])
        self.assertEqual(got, [])                                  # судья пропущен у прогона с ошибкой — это ошибка, не несравнимость
        got, _, _, _ = self.quiet([{"result": self.quality_case([clean(1.0), clean(1.0), skipped], [clean(0.5)] * 3,
                                                                score=1.0)}])
        self.assertEqual([f.message for f in got], ["%s: q-web-1 — судья пропущен, оценка несравнима" % L2_FAILED])

    def test_quality_case_with_one_configured_run_is_not_too_few(self):
        self.add_plugin(queries=(), quality=QUALITY)    # родной кейс с runs: 1 — один чистый прогон не ошибка
        got, _, _, _ = self.quiet([{"result": self.quality_case([clean(1.0)], [clean(0.5)], score=1.0, delta=0.5)}])
        self.assertEqual(got, [])
        self.assertEqual(self.hist_by_case()["q-web-1"]["runs"], 1)

    # --- сохранённая загрузка подписки: l2-usage.json между вызовами и ночами ---

    def usage_path(self):
        return os.path.join(self.state, evalrun.USAGE_FILE)

    def put_usage(self, data, raw=None):
        os.makedirs(self.state, exist_ok=True)
        with open(self.usage_path(), "w", encoding="utf-8") as fh:
            fh.write(raw if raw is not None else json.dumps(data))

    def usage(self):
        with open(self.usage_path(), encoding="utf-8") as fh:
            return json.load(fh)

    WEEK_85 = "недельный лимит занят на 85% — запас для дневной работы"

    def test_stored_week_over_the_stop_starts_no_call(self):
        self.add_plugin("a-dev")
        self.add_plugin("b-dev")
        now = time.time()
        self.put_usage({"status": "allowed", "overage": False,
                        "seven_day": {"utilization": 0.85, "resets_at": now + 3600, "at": now - 600}})
        ctx = self.ctx()
        (got, evals, calls, ctx), err = self.err_check([{"result": eval_result()}], name="a-dev", ctx=ctx)
        self.assertEqual(calls, [])                                # ни `auth status`, ни `plugin eval`
        self.assertEqual([(f.level, f.message) for f in got],
                         [(INFRA, "%s: %s" % (L2_NOT_RUN, self.WEEK_85)), (INFO, "%s: %s" % (L2_STOPPED, self.WEEK_85))])
        self.assertEqual(ctx.l2_stop, self.WEEK_85)
        self.assertEqual(self.hist(), [])
        self.assertIn("[evalrun]", err)
        got_b, _, calls_b, _ = self.quiet([{"result": eval_result()}], name="b-dev", ctx=ctx)
        self.assertEqual(([(f.level, f.message.split(":")[0]) for f in got_b], calls_b), ([(INFRA, L2_NOT_RUN)], []))

    def test_stored_week_whose_reset_has_passed_runs_the_plugin(self):
        self.add_plugin()
        now = time.time()
        self.put_usage({"seven_day": {"utilization": 0.85, "resets_at": now - 5, "at": now - 86400}})
        got, evals, calls, ctx = self.quiet([{"result": eval_result(eval_case(T(YES), 1.0), eval_case(T(NO), 1.0))}])
        self.assertEqual((got, len(evals), ctx.l2_stop), ([], 1, ""))

    def test_stored_snapshot_with_unknown_reset_stops_only_while_young(self):
        self.add_plugin()
        now = time.time()
        self.put_usage({"five_hour": {"utilization": 0.95, "at": now - 3600}})
        got, _, calls, _ = self.quiet([])
        self.assertEqual((len(got), calls), (2, []))
        self.put_usage({"five_hour": {"utilization": 0.95, "at": now - 6 * 3600}})      # окно 5 часов давно другое
        got, evals, _, _ = self.quiet([{"result": eval_result(eval_case(T(YES), 1.0), eval_case(T(NO), 1.0))}])
        self.assertEqual((got, len(evals)), ([], 1))

    def test_corrupt_or_foreign_usage_file_runs_the_plugin(self):
        self.add_plugin()
        for raw in ("{not json", "[1, 2]", "", "\u0000\u0000"):
            with self.subTest(raw=raw):
                self.put_usage(None, raw=raw)
                got, evals, _, _ = self.quiet([{"result": eval_result(eval_case(T(YES), 1.0), eval_case(T(NO), 1.0))}])
                self.assertEqual((got, len(evals)), ([], 1))

    def test_wave_threshold_override_applies_to_the_stored_snapshot(self):
        self.add_plugin()
        now = time.time()
        self.put_usage({"seven_day": {"utilization": 0.85, "resets_at": now + 3600, "at": now}})
        with mock.patch.dict(os.environ, {evalrun.SEVEN_DAY_VAR: "1.0"}):
            got, evals, _, _ = self.quiet([{"result": eval_result(eval_case(T(YES), 1.0), eval_case(T(NO), 1.0))}])
        self.assertEqual((got, len(evals)), ([], 1))

    def test_stored_stop_is_not_consulted_for_a_plugin_that_would_not_run_anyway(self):
        self.add_plugin(queries=())
        now = time.time()
        self.put_usage({"seven_day": {"utilization": 0.99, "resets_at": now + 3600, "at": now}})
        got, _, calls, ctx = self.quiet([])
        self.assertEqual((got, calls, ctx.l2_stop), ([], [], ""))      # нет кейсов — не «не прогнан» и не остановка

    def test_snapshot_is_written_after_each_call(self):
        self.add_plugin()
        now = time.time()
        info = {"status": "allowed", "unifiedWindows": {"five_hour": {"utilization": 0.4, "resetsAt": now + 7200},
                                                         "seven_day": {"utilization": 0.55, "resetsAt": now + 86400}}}
        first = eval_result(eval_case(T(YES), 0.0, runs=[dict(clean(0.0), trace=[info])]), eval_case(T(NO), 1.0))
        later = dict(info, unifiedWindows={"five_hour": {"utilization": 0.5, "resetsAt": now + 7200}})
        rerun = eval_result(eval_case(T(YES), 1.0, runs=[dict(clean(1.0), trace=[later]), clean(1.0)]))
        got, evals, _, _ = self.quiet([{"result": first}, {"result": rerun}])
        self.assertEqual(len(evals), 2)
        data = self.usage()
        self.assertEqual((data["status"], data["overage"]), ("allowed", False))
        self.assertEqual(data["five_hour"]["utilization"], 0.5)             # последний вызов перекрыл окно, которое видел
        self.assertAlmostEqual(data["five_hour"]["resets_at"], now + 7200, places=3)
        self.assertEqual(data["seven_day"]["utilization"], 0.55)            # окно, которого он не видел, осталось
        self.assertAlmostEqual(data["seven_day"]["at"], time.time(), delta=60)

    def test_snapshot_is_written_when_the_call_ended_on_a_limit(self):
        self.add_plugin()
        first = eval_result(eval_case(T(YES), 0.0, runs=[dict(clean(0.0), trace=[REJECTED])]), eval_case(T(NO), 1.0))
        got, _, _, ctx = self.quiet([{"result": first}])
        self.assertIn("rejected", ctx.l2_stop)
        data = self.usage()
        self.assertEqual((data["status"], data["five_hour"]["utilization"]), ("rejected", 1.0))

    def test_no_rate_limit_events_leave_the_stored_snapshot_alone(self):
        self.add_plugin()
        now = time.time()
        stored = {"status": "allowed", "overage": False,
                  "seven_day": {"utilization": 0.5, "resets_at": now + 3600, "at": now - 30}}
        self.put_usage(stored)
        self.quiet([{"result": eval_result(eval_case(T(YES), 1.0), eval_case(T(NO), 1.0))}])
        self.assertEqual(self.usage(), stored)

    def test_corrupt_usage_file_is_replaced_by_the_next_snapshot(self):
        self.add_plugin()
        self.put_usage(None, raw="{not json")
        hot = {"status": "allowed", "unifiedWindows": {"seven_day": {"utilization": 0.3}}}
        self.quiet([{"result": eval_result(eval_case(T(YES), 1.0, runs=[dict(clean(1.0), trace=[hot])]),
                                           eval_case(T(NO), 1.0))}])
        self.assertEqual(self.usage()["seven_day"]["utilization"], 0.3)

    def test_unwritable_state_dir_does_not_cost_the_findings_or_add_one(self):
        self.add_plugin()
        blocker = os.path.join(self.repo.root, "state-is-a-file")
        with open(blocker, "w") as fh:
            fh.write("x")
        ctx = self.ctx()
        ctx.state_dir = blocker
        hot = {"status": "allowed", "unifiedWindows": {"five_hour": {"utilization": 0.95}}}
        res = eval_result(eval_case(T(YES), 1.0, runs=[dict(clean(1.0), trace=[hot])]), eval_case(T(NO), 1.0))
        (got, _, _, _), err = self.err_check([{"result": res}], ctx=ctx)
        self.assertEqual(sorted((f.level, f.message.split(":")[0]) for f in got),
                         sorted([(INFO, L2_STOPPED), (INFRA, L2_FAILED)]))      # остановка и «история не записана», как раньше
        self.assertIn("[evalrun]", err)


if __name__ == "__main__":
    unittest.main()
