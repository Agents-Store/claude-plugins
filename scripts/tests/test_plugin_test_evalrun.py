import os
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, eval_case, eval_result, stub_calls, stub_claude  # noqa: E402

from plugin_test import evalrun  # noqa: E402

OK = {"status": "allowed", "isUsingOverage": False,
      "unifiedWindows": {"five_hour": {"utilization": 0.2}, "seven_day": {"utilization": 0.3}}}


class EvalrunTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.copy = os.path.join(self.repo.root, "copy")
        os.makedirs(self.copy)
        self.out = os.path.join(self.repo.root, "out")

    def run_stub(self, plan, **kw):
        claude, log = stub_claude(self.repo.root, plan)
        res = evalrun.run(claude, self.copy, "evals-quality", self.out, ablation="with-without",
                          env=evalrun.environment(), **kw)
        return res, stub_calls(log)

    def test_environment_drops_api_keys(self):
        fake = {"PATH": "/usr/bin", "HOME": "/tmp/test-home", "ANTHROPIC_API_KEY": "sk-test", "ANTHROPIC_BASE_URL": "u",
                "ANTHROPIC_AUTH_TOKEN": "t", "CLAUDE_CODE_USE_BEDROCK": "1", "FOO": "bar", "USER": "x"}
        with mock.patch.dict(os.environ, fake, clear=True):
            env = evalrun.environment()
        self.assertEqual(env, {"PATH": "/usr/bin", "HOME": "/tmp/test-home", "USER": "x", "LANG": "C.UTF-8"})

    def test_preflight_ok(self):
        claude, _ = stub_claude(self.repo.root, [])
        self.assertEqual(evalrun.preflight(claude, evalrun.environment()), "")

    def test_preflight_refuses_api_key_login(self):
        claude, _ = stub_claude(self.repo.root, [], auth='{"loggedIn": true, "authMethod": "apiKey"}')
        reason = evalrun.preflight(claude, evalrun.environment())
        self.assertIn("не по подписке", reason)

    def test_preflight_not_logged_in_and_garbage(self):
        claude, _ = stub_claude(self.repo.root, [], auth='{"loggedIn": false}')
        self.assertIn("нет входа", evalrun.preflight(claude, evalrun.environment()))
        claude2, _ = stub_claude(os.path.join(self.repo.root, "g"), [], auth="not json")
        self.assertIn("не JSON", evalrun.preflight(claude2, evalrun.environment()))

    def test_preflight_timeout(self):
        claude, _ = stub_claude(self.repo.root, [], auth="SLEEP")
        with mock.patch.object(evalrun, "AUTH_TIMEOUT", 1):
            self.assertIn("не ответил", evalrun.preflight(claude, evalrun.environment()))

    def test_preflight_never_prints_account(self):
        claude, _ = stub_claude(self.repo.root, [], auth='{"loggedIn": true, "authMethod": "apiKey", '
                                                          '"email": "owner@example.com"}')
        self.assertNotIn("owner@example.com", evalrun.preflight(claude, evalrun.environment()))

    def test_command_flags(self):
        args = evalrun.command("claude", "/c", "evals-trigger", "/o", ablation="none", runs=2)
        self.assertEqual(args[:4], ["claude", "plugin", "eval", "/c"])
        for flag in ("--trust-plugin", "--no-publish", "--keep-temp"):
            self.assertIn(flag, args)
        pairs = dict(zip(args, args[1:]))
        self.assertEqual((pairs["--eval-dir"], pairs["--mocks"], pairs["--threshold"], pairs["--ablation"],
                          pairs["--runs"], pairs["--output-dir"], pairs["--model"], pairs["--judge-model"],
                          pairs["--concurrency"]),
                         ("evals-trigger", "record", "0", "none", "2", "/o", evalrun.MODEL, evalrun.JUDGE_MODEL, "4"))
        for forbidden in ("--allow-tools", "--scaffold", "--allow-real-servers", "--max-cost-usd", "--json"):
            self.assertNotIn(forbidden, args)
        self.assertNotIn("--runs", evalrun.command("claude", "/c", "e", "/o", ablation="with-without"))

    def test_run_parses_result_and_child_env_has_no_key(self):
        plan = [{"result": eval_result(eval_case("q-a-1", 1.0, delta=0.5))}]
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-not-real"}):
            res, calls = self.run_stub(plan)
        self.assertEqual(res.returncode, 0)
        self.assertEqual(evalrun.cases(res.data)["q-a-1"]["delta"], 0.5)
        self.assertEqual((res.stop, res.invalid, res.problems), ("", False, []))
        self.assertNotIn("ANTHROPIC_API_KEY", calls[-1]["env"])

    def test_eval_hangs_is_eval_error(self):
        started = time.time()
        with self.assertRaises(evalrun.EvalError) as ctx:
            self.run_stub([{"sleep": 30, "result": eval_result()}], timeout=1)
        self.assertIn("не завершился", str(ctx.exception))
        self.assertLess(time.time() - started, 20)

    def test_garbage_output_is_eval_error(self):
        with self.assertRaises(evalrun.EvalError) as ctx:
            self.run_stub([{"stdout": "<<garbage>>", "stderr": "boom\nlast line", "exit": 0}])
        self.assertIn("нет результата", str(ctx.exception))
        self.assertIn("last line", str(ctx.exception))

    def test_exit_1_with_result_is_a_problem(self):
        res, _ = self.run_stub([{"exit": 1, "stderr": "invalid case.yaml: graders", "result": eval_result()}])
        self.assertEqual(len(res.problems), 1)
        self.assertIn("invalid case.yaml", res.problems[0])
        self.assertFalse(res.invalid)

    def test_interrupted_is_invalid(self):
        res, _ = self.run_stub([{"exit": 143, "result": eval_result(partial=True, reason="interrupted")}])
        self.assertTrue(res.invalid)
        self.assertTrue(res.stop)

    def test_limit_status_in_trace_stops_and_invalidates(self):
        rejected = dict(OK, status="rejected")
        res, _ = self.run_stub([{"result": eval_result(eval_case("q-a-1", 0.0, runs=[
            {"score": 0.0, "error": None, "trace": [OK, rejected]}]))}])
        self.assertIn("status=rejected", res.stop)
        self.assertTrue(res.invalid)

    def test_usage_thresholds_stop_but_keep_results(self):
        hot = {"status": "allowed", "unifiedWindows": {"five_hour": {"utilization": 0.95},
                                                       "seven_day": {"utilization": 0.1}}}
        res, _ = self.run_stub([{"result": eval_result(eval_case("q-a-1", 1.0, runs=[
            {"score": 1.0, "error": None, "trace": [hot]}]))}])
        self.assertIn("5 часов", res.stop)
        self.assertFalse(res.invalid)
        self.assertEqual(res.usage["five_hour"], 0.95)

    def test_weekly_threshold_and_overage(self):
        week = {"status": "allowed", "unifiedWindows": {"seven_day": {"utilization": 0.85}}}
        res, _ = self.run_stub([{"result": eval_result(eval_case("q", 1.0, runs=[
            {"score": 1.0, "error": None, "trace": [week]}]))}])
        self.assertIn("недельный", res.stop)
        os.remove(os.path.join(self.repo.root, "stub", "plan.json.n"))
        over = dict(OK, isUsingOverage=True)
        res2, _ = self.run_stub([{"result": eval_result(eval_case("q", 1.0, runs=[
            {"score": 1.0, "error": None, "trace": [over]}]))}])
        self.assertIn("overage", res2.stop)
        self.assertFalse(res2.invalid)

    def test_quiet_usage_keeps_going(self):
        res, _ = self.run_stub([{"result": eval_result(eval_case("q", 1.0, runs=[
            {"score": 1.0, "error": None, "trace": [OK]}]))}])
        self.assertEqual(res.stop, "")

    def test_auth_failed_partial(self):
        res, _ = self.run_stub([{"exit": 2, "result": eval_result(partial=True, reason="auth_failed")}])
        self.assertIn("auth_failed", res.stop)
        self.assertTrue(res.invalid)

    def test_limit_error_text_but_not_turn_cap(self):
        res, _ = self.run_stub([{"result": eval_result(eval_case("q", 0.0, runs=[
            {"score": 0.0, "error": "API Error: 429 rate limit reached"}]))}])
        self.assertTrue(res.stop and res.invalid)
        os.remove(os.path.join(self.repo.root, "stub", "plan.json.n"))
        res2, _ = self.run_stub([{"result": eval_result(eval_case("t", 1.0, runs=[
            {"score": 1.0, "error": "exit 1: Reached maximum number of turns (1)"}]))}])
        self.assertEqual((res2.stop, res2.invalid), ("", False))

    def test_temp_dirs_removed_only_by_pattern(self):
        keep = tempfile.mkdtemp(prefix="not-claude-eval-")
        self.addCleanup(lambda: os.path.isdir(keep) and os.rmdir(keep))
        res, _ = self.run_stub([{"result": eval_result(
            eval_case("q", 1.0, runs=[{"score": 1.0, "error": None, "trace": [OK]},
                                      {"score": 1.0, "error": None, "tracePath": os.path.join(keep, "trace.jsonl")}]))}])
        made = res.data["cases"][0]["arms"]["with"][0]["tracePath"]
        self.assertIn("claude-eval-", made)
        self.assertFalse(os.path.exists(os.path.dirname(os.path.dirname(made))))
        self.assertTrue(os.path.isdir(keep))

    def test_cases_and_run_scores(self):
        data = eval_result(eval_case("t-x", 0.5, runs=[{"score": 1.0, "error": None}, {"score": 0.0, "error": "e"}]),
                           {"name": "broken"})
        got = evalrun.cases(data)
        self.assertEqual(sorted(got), ["broken", "t-x"])
        self.assertEqual(evalrun.run_scores(got["t-x"]), [1.0, 0.0])
        self.assertEqual((got["broken"]["score"], evalrun.run_scores(got["broken"])), (None, []))


if __name__ == "__main__":
    unittest.main()
