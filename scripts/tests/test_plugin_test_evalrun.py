import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, eval_case, eval_result, isolate_l2_env, stub_calls, stub_claude  # noqa: E402

from plugin_test import evalrun  # noqa: E402

OK = {"status": "allowed", "isUsingOverage": False,
      "unifiedWindows": {"five_hour": {"utilization": 0.2}, "seven_day": {"utilization": 0.3}}}


class EvalrunTest(unittest.TestCase):
    def setUp(self):
        isolate_l2_env(self)
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
        self.assertEqual(env, {"PATH": "/usr/bin", "HOME": "/tmp/test-home", "USER": "x", "LANG": "C.UTF-8",
                               "ENABLE_CLAUDEAI_MCP_SERVERS": "false"})

    def test_environment_always_disables_claudeai_connectors(self):
        for parent in ({}, {"ENABLE_CLAUDEAI_MCP_SERVERS": "true"}, {"ENABLE_CLAUDEAI_MCP_SERVERS": ""}):
            with self.subTest(parent=parent):
                with mock.patch.dict(os.environ, dict(parent, PATH="/usr/bin", HOME="/tmp/test-home"), clear=True):
                    self.assertEqual(evalrun.environment()["ENABLE_CLAUDEAI_MCP_SERVERS"], "false")

    def test_child_gets_claudeai_connectors_off_even_if_parent_has_them_on(self):
        with mock.patch.dict(os.environ, {"ENABLE_CLAUDEAI_MCP_SERVERS": "true"}):
            res, calls = self.run_stub([{"result": eval_result(eval_case("q-a-1", 1.0))}])
        self.assertEqual(calls[-1]["claudeai_mcp"], "false")
        self.assertIn("ENABLE_CLAUDEAI_MCP_SERVERS", calls[-1]["env"])

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

    def run_stub_stderr(self, plan, **kw):
        """(результат или EvalError, stderr процесса runner-а) — подробности уходят в журнал, не в сообщения."""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            try:
                got = self.run_stub(plan, **kw)[0]
            except evalrun.EvalError as exc:
                got = exc
        return got, err.getvalue()

    def test_garbage_output_is_eval_error(self):
        exc, err = self.run_stub_stderr([{"stdout": "<<garbage>>", "stderr": "boom\nlast line", "exit": 0}])
        self.assertIsInstance(exc, evalrun.EvalError)
        self.assertEqual(str(exc), "claude plugin eval: нет результата (код 0)")
        self.assertNotIn("last line", str(exc))
        self.assertIn("[evalrun]", err)
        self.assertIn("last line", err)
        self.assertEqual(len(err.strip().splitlines()), 1)

    def test_exit_1_with_result_is_a_problem(self):
        res, err = self.run_stub_stderr([{"exit": 1, "stderr": "invalid case.yaml: graders", "result": eval_result()}])
        self.assertEqual(res.problems, ["claude plugin eval, код 1"])
        self.assertFalse(res.invalid)
        self.assertIn("[evalrun]", err)
        self.assertIn("invalid case.yaml", err)

    def test_preflight_and_partial_text_from_cli_is_not_echoed(self):
        sentinel = "SENTINEL words with spaces"
        claude, _ = stub_claude(self.repo.root, [], auth='{"loggedIn": true, "authMethod": "%s"}' % sentinel)
        self.assertNotIn("SENTINEL", evalrun.preflight(claude, evalrun.environment()))
        res, _ = self.run_stub([{"exit": 0, "result": eval_result(partial=True, reason=sentinel)}])
        self.assertTrue(res.invalid)
        self.assertNotIn("SENTINEL", res.stop)

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

    def test_trace_status_text_is_not_echoed(self):
        weird = dict(OK, status="SENTINEL tail words")
        res, err = self.run_stub_stderr([{"result": eval_result(eval_case("q", 0.0, runs=[
            {"score": 0.0, "error": None, "trace": [weird]}]))}])
        self.assertTrue(res.invalid)
        self.assertEqual(res.stop, "лимит подписки: status=не указан")
        self.assertIn("[evalrun]", err)
        self.assertIn("SENTINEL tail words", err)
        res2, _ = self.run_stub_stderr([{"result": eval_result(eval_case("q", 0.0, runs=[
            {"score": 0.0, "error": None, "trace": [dict(OK, status="rejected")]}]))}])
        self.assertEqual(res2.stop, "лимит подписки: status=rejected")

    def test_ident_is_a_full_match(self):
        self.assertEqual(evalrun._ident("apiKey"), "apiKey")
        for bad in ("apiKey\n", "api key", "", None, 5, "x" * 41):
            self.assertEqual(evalrun._ident(bad), "не указан")
        claude, _ = stub_claude(self.repo.root, [], auth='{"loggedIn": true, "authMethod": "apiKey\\n"}')
        reason = evalrun.preflight(claude, evalrun.environment())
        self.assertIn("authMethod=не указан", reason)

    def test_non_finite_and_huge_utilization_do_not_raise(self):
        for value in (float("inf"), float("nan"), 1e308):
            with self.subTest(value=value):
                plan = [{"result": eval_result(eval_case("q", 1.0, runs=[
                    {"score": 1.0, "error": None, "trace": [
                        {"status": "allowed", "unifiedWindows": {"five_hour": {"utilization": value}}}]}]))}]
                path = os.path.join(self.repo.root, "stub", "plan.json.n")
                if os.path.exists(path):
                    os.remove(path)
                res, _ = self.run_stub(plan)
                self.assertFalse(res.invalid)
                self.assertTrue(all(0.0 <= u <= 100.0 for u in res.usage.values()))
                if value == 1e308:
                    self.assertIn("5 часов", res.stop)
                else:
                    self.assertEqual((res.stop, res.usage["five_hour"]), ("", 0.0))

    def hot(self, five=0.0, seven=0.0):
        win = {"five_hour": {"utilization": five}, "seven_day": {"utilization": seven}}
        return eval_result(eval_case("q", 1.0, runs=[
            {"score": 1.0, "error": None, "trace": [{"status": "allowed", "unifiedWindows": win}]}]))

    def stop_with(self, env, five=0.0, seven=0.0):
        """(res, stderr): прогон при переменных порогов env у самого runner-а."""
        path = os.path.join(self.repo.root, "stub", "plan.json.n")
        if os.path.exists(path):
            os.remove(path)
        with mock.patch.dict(os.environ, env):
            return self.run_stub_stderr([{"result": self.hot(five, seven)}])

    def test_isolation_hides_the_operators_threshold_variables(self):
        os.environ["PLUGIN_TEST_L2_FIVE_HOUR_STOP"] = "1.0"      # окружение восстановит изоляция из setUp
        isolate_l2_env(self)
        self.assertNotIn("PLUGIN_TEST_L2_FIVE_HOUR_STOP", os.environ)
        self.assertEqual(evalrun.five_hour_stop(), 0.9)

    def test_thresholds_default_without_overrides(self):
        self.assertEqual((evalrun.five_hour_stop(), evalrun.seven_day_stop()), (0.9, 0.8))
        res, err = self.stop_with({}, five=0.9)
        self.assertIn("5 часов", res.stop)
        self.assertEqual(err, "")

    def test_thresholds_can_be_raised_by_runner_env(self):
        env = {"PLUGIN_TEST_L2_FIVE_HOUR_STOP": "0.97", "PLUGIN_TEST_L2_SEVEN_DAY_STOP": "1.0"}
        res, err = self.stop_with(env, five=0.95, seven=0.99)
        self.assertEqual((res.stop, res.invalid, err), ("", False, ""))
        res, _ = self.stop_with(env, five=0.97)
        self.assertIn("5 часов", res.stop)
        res, _ = self.stop_with(env, seven=1.0)
        self.assertIn("недельный", res.stop)

    def test_thresholds_can_be_lowered_by_runner_env(self):
        res, _ = self.stop_with({"PLUGIN_TEST_L2_FIVE_HOUR_STOP": "0.5"}, five=0.5)
        self.assertIn("5 часов", res.stop)
        res, _ = self.stop_with({"PLUGIN_TEST_L2_SEVEN_DAY_STOP": "0.3"}, seven=0.3)
        self.assertIn("недельный", res.stop)

    def test_threshold_one_still_stops_on_the_real_limit(self):
        env = {"PLUGIN_TEST_L2_FIVE_HOUR_STOP": "1.0", "PLUGIN_TEST_L2_SEVEN_DAY_STOP": "1.0"}
        win = {"five_hour": {"utilization": 0.99}, "seven_day": {"utilization": 0.99}}
        for bad, text in ((dict(status="rejected"), "status=rejected"), (dict(isUsingOverage=True), "overage")):
            with self.subTest(text=text):
                path = os.path.join(self.repo.root, "stub", "plan.json.n")
                if os.path.exists(path):
                    os.remove(path)
                trace = dict({"status": "allowed", "unifiedWindows": win}, **bad)
                with mock.patch.dict(os.environ, env):
                    res, _ = self.run_stub([{"result": eval_result(eval_case("q", 1.0, runs=[
                        {"score": 1.0, "error": None, "trace": [trace]}]))}])
                self.assertIn(text, res.stop)

    def test_invalid_threshold_falls_back_to_default_with_a_note(self):
        for bad in ("", "abc", "0", "-0.5", "1.5", "nan", "inf", "0.9x"):
            with self.subTest(bad=bad):
                res, err = self.stop_with({"PLUGIN_TEST_L2_FIVE_HOUR_STOP": bad}, five=0.95)
                self.assertIn("5 часов", res.stop)          # осталось 0.9
                self.assertIn("[evalrun]", err)
                self.assertIn("PLUGIN_TEST_L2_FIVE_HOUR_STOP", err)
                self.assertEqual(len(err.strip().splitlines()), 1)
        res, err = self.stop_with({"PLUGIN_TEST_L2_FIVE_HOUR_STOP": "SENTINEL-VALUE"}, five=0.95)
        self.assertNotIn("SENTINEL-VALUE", err)                  # в журнал идёт имя переменной, не её значение
        res, err = self.stop_with({"PLUGIN_TEST_L2_SEVEN_DAY_STOP": "oops"}, seven=0.85)
        self.assertIn("недельный", res.stop)
        self.assertIn("PLUGIN_TEST_L2_SEVEN_DAY_STOP", err)

    def test_thresholds_are_read_at_verdict_time(self):
        with mock.patch.dict(os.environ, {"PLUGIN_TEST_L2_FIVE_HOUR_STOP": "0.95"}):
            self.assertEqual(evalrun.five_hour_stop(), 0.95)
        with mock.patch.dict(os.environ, {"PLUGIN_TEST_L2_FIVE_HOUR_STOP": "0.5"}):
            self.assertEqual(evalrun.five_hour_stop(), 0.5)

    def test_quiet_usage_keeps_going(self):
        res, _ = self.run_stub([{"result": eval_result(eval_case("q", 1.0, runs=[
            {"score": 1.0, "error": None, "trace": [OK]}]))}])
        self.assertEqual(res.stop, "")

    def test_auth_failed_partial(self):
        res, _ = self.run_stub([{"exit": 2, "result": eval_result(partial=True, reason="auth_failed")}])
        self.assertIn("auth_failed", res.stop)
        self.assertTrue(res.invalid)

    def test_limit_error_text_but_not_turn_cap(self):
        res, err = self.run_stub_stderr([{"result": eval_result(eval_case("q", 0.0, runs=[
            {"score": 0.0, "error": "API Error: 429 rate limit reached SENTINEL-DETAIL"}]))}])
        self.assertEqual((res.stop, res.invalid), ("ошибка лимита в прогоне", True))
        self.assertIn("[evalrun]", err)
        self.assertIn("SENTINEL-DETAIL", err)
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

    def test_stale_result_in_reused_out_dir_is_not_returned(self):
        os.makedirs(self.out)
        with open(os.path.join(self.out, evalrun.RESULT), "w", encoding="utf-8") as fh:
            json.dump(eval_result(eval_case("old-pass", 1.0)), fh)
        exc, _ = self.run_stub_stderr([{"exit": 1, "stderr": "died before writing"}])
        self.assertIsInstance(exc, evalrun.EvalError)
        self.assertIn("нет результата", str(exc))
        self.assertNotIn("died before writing", str(exc))
        self.assertFalse(os.path.exists(os.path.join(self.out, evalrun.RESULT)))

    def test_partial_with_unknown_reason_is_invalid_and_stops(self):
        res, _ = self.run_stub([{"exit": 0, "result": eval_result(
            eval_case("q", 1.0), partial=True, reason="budget")}])
        self.assertTrue(res.invalid)
        self.assertIn("budget", res.stop)
        res2, _ = self.run_stub([{"exit": 0, "result": eval_result(partial=True)}])
        self.assertTrue(res2.invalid)
        self.assertTrue(res2.stop)

    def test_killed_by_signal_is_interrupted(self):
        def die_by_signal(args, **kw):
            with open(os.path.join(kw["cwd"], evalrun.RESULT), "w", encoding="utf-8") as fh:
                json.dump(eval_result(eval_case("q", 1.0)), fh)
            return subprocess.CompletedProcess(args, -15, "", "")
        with mock.patch.object(evalrun, "run_group", die_by_signal):
            res = evalrun.run("claude", self.copy, "evals-quality", self.out, ablation="none",
                              env=evalrun.environment())
        self.assertTrue(res.invalid)
        self.assertIn("прерван", res.stop)

    def test_malformed_trace_events_do_not_crash_and_temp_dir_is_removed(self):
        junk = ["not-a-dict", {"status": ["allowed"]}, {"status": 5}, {"unifiedWindows": [1, 2]},
                {"unifiedWindows": {"five_hour": "high", "seven_day": {"utilization": "n/a"}}}, OK]
        res, _ = self.run_stub([{"result": eval_result(eval_case("q", 1.0, runs=[
            {"score": 1.0, "error": None, "trace": junk}]))}])
        self.assertEqual((res.stop, res.invalid), ("", False))
        made = res.data["cases"][0]["arms"]["with"][0]["tracePath"]
        self.assertFalse(os.path.exists(os.path.dirname(os.path.dirname(made))))

    def test_temp_dirs_removed_even_when_trace_scan_raises(self):
        plan = [{"result": eval_result(eval_case("q", 1.0, runs=[{"score": 1.0, "error": None, "trace": [OK]}]))}]
        with mock.patch.object(evalrun, "_scan_traces", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.run_stub(plan)
        with open(os.path.join(self.out, evalrun.RESULT), encoding="utf-8") as fh:
            made = json.load(fh)["cases"][0]["arms"]["with"][0]["tracePath"]
        self.assertFalse(os.path.exists(os.path.dirname(os.path.dirname(made))))

    def test_cases_and_run_scores(self):
        data = eval_result(eval_case("t-x", 0.5, runs=[{"score": 1.0, "error": None}, {"score": 0.0, "error": "e"}]),
                           {"name": "broken"})
        got = evalrun.cases(data)
        self.assertEqual(sorted(got), ["broken", "t-x"])
        self.assertEqual(evalrun.run_scores(got["t-x"]), [1.0, 0.0])
        self.assertEqual((got["broken"]["score"], evalrun.run_scores(got["broken"])), (None, []))

    # --- ошибки прогонов: что считается ошибкой, а что — ожидаемым обрывом срабатывания ---

    CAP = "exit 1: Reached maximum number of turns (1)"

    def test_run_error_classifies_per_run(self):
        for clean in ({}, {"error": None}, {"error": ""}, {"error": False}):
            self.assertFalse(evalrun.run_error(clean), clean)
        for failed in ({"error": "API Error: 500"}, {"error": {"message": "boom"}}, {"error": True}):
            self.assertTrue(evalrun.run_error(failed), failed)
            self.assertTrue(evalrun.run_error(failed, turn_cap_ok=True), failed)

    def test_turn_cap_of_trigger_runs_is_expected_only_in_its_pinned_form(self):
        self.assertFalse(evalrun.run_error({"error": self.CAP}, turn_cap_ok=True))
        self.assertFalse(evalrun.run_error({"error": "  %s\n" % self.CAP}, turn_cap_ok=True))
        self.assertTrue(evalrun.run_error({"error": self.CAP}))              # в кейсах качества max_turns нет
        for other in ("exit 1: Reached maximum number of turns (2)", "exit 1: Reached maximum number of turns (10)",
                      "exit 1: Reached maximum number of turns", "exit 2: Reached maximum number of turns (1)",
                      self.CAP + ": API Error: 500", "API Error: 500 " + self.CAP, "Reached maximum number of turns (1)"):
            self.assertTrue(evalrun.run_error({"error": other}, turn_cap_ok=True), other)

    def test_clean_runs_scores_and_error_count(self):
        runs = [{"score": 1.0, "error": None}, {"score": 0.0, "error": "API Error: 500"},
                {"score": 0.0, "error": self.CAP}, {"error": None}, {"score": True, "error": None}]
        entry = evalrun.cases(eval_result(eval_case("t", 0.5, runs=runs, without=[{"score": 0.4, "error": "e"}])))["t"]
        self.assertEqual(evalrun.clean_scores(entry), [1.0])                  # без счёта и булев score — не оценки
        self.assertEqual(evalrun.clean_scores(entry, turn_cap_ok=True), [1.0, 0.0])
        self.assertEqual((evalrun.error_runs(entry), evalrun.error_runs(entry, turn_cap_ok=True)), (2, 1))
        self.assertEqual(evalrun.clean_scores(entry, "without"), [])
        self.assertEqual(evalrun.error_runs(entry, "without"), 1)
        self.assertEqual(len(evalrun.clean_runs(entry)), 3)

    # --- снимок подписки: что разбирается из трейса и сохраняется между ночами ---

    def snapshot_of(self, *infos):
        path = os.path.join(self.repo.root, "stub", "plan.json.n")
        if os.path.exists(path):
            os.remove(path)
        res, _ = self.run_stub([{"result": eval_result(eval_case("q", 1.0, runs=[
            {"score": 1.0, "error": None, "trace": list(infos)}]))}])
        return res.snapshot

    def test_snapshot_carries_windows_status_and_reset_times(self):
        info = {"status": "allowed", "isUsingOverage": False,
                "unifiedWindows": {"five_hour": {"utilization": 0.4, "resetsAt": 1900000000},
                                   "seven_day": {"utilization": 0.55}},
                "resetsAt": 1800000000, "rateLimitType": "seven_day"}
        self.assertEqual(self.snapshot_of(info), {
            "status": "allowed", "overage": False,
            "windows": {"five_hour": {"utilization": 0.4, "resets_at": 1900000000.0},
                        "seven_day": {"utilization": 0.55, "resets_at": 1800000000.0}}})

    def test_snapshot_without_rate_limit_events_has_no_windows(self):
        self.assertEqual(self.snapshot_of(), {"status": "", "overage": False, "windows": {}})

    def test_snapshot_keeps_the_highest_utilization_and_latest_reset_of_the_call(self):
        low = {"status": "allowed", "unifiedWindows": {"five_hour": {"utilization": 0.3, "resetsAt": 2000000000}}}
        high = {"status": "allowed", "unifiedWindows": {"five_hour": {"utilization": 0.6, "resetsAt": 1900000000}}}
        self.assertEqual(self.snapshot_of(low, high)["windows"], {"five_hour": {"utilization": 0.6,
                                                                             "resets_at": 2000000000.0}})

    def test_snapshot_status_is_the_limit_status_when_there_was_one(self):
        rejected = dict(OK, status="rejected", isUsingOverage=True)
        snap = self.snapshot_of(OK, rejected)
        self.assertEqual((snap["status"], snap["overage"]), ("rejected", True))
        with contextlib.redirect_stderr(io.StringIO()):     # текст статуса уходит в журнал, не в снимок
            self.assertEqual(self.snapshot_of(dict(OK, status="SENTINEL tail words"))["status"], "не указан")

    def test_reset_time_formats(self):
        for raw, want in ((1900000000, 1900000000.0), (1900000000.5, 1900000000.5), (1900000000000, 1900000000.0),
                          ("2030-03-17T17:46:40Z", 1900000000.0), ("2030-03-17T17:46:40", 1900000000.0),
                          ("2030-03-17T19:46:40+02:00", 1900000000.0)):
            self.assertEqual(evalrun._reset_time(raw), want, raw)
        for junk in (None, True, False, 0, -5, float("nan"), float("inf"), "soon", "", [1900000000], {"at": 1}):
            self.assertIsNone(evalrun._reset_time(junk), junk)

    def test_window_reset_aliases_and_foreign_top_level_reset(self):
        for key in ("resetsAt", "resets_at", "resetAt", "reset_at"):
            info = {"status": "allowed", "unifiedWindows": {"seven_day": {"utilization": 0.5, key: 1900000000}}}
            self.assertEqual(self.snapshot_of(info)["windows"]["seven_day"]["resets_at"], 1900000000.0, key)
        # сброс верхнего уровня относится к окну rateLimitType; чужому окну он не приписывается
        info = {"status": "allowed", "resetsAt": 1900000000, "rateLimitType": "five_hour",
                "unifiedWindows": {"seven_day": {"utilization": 0.5}}}
        self.assertNotIn("resets_at", self.snapshot_of(info)["windows"]["seven_day"])

    def usage_path(self):
        return os.path.join(self.repo.root, "state", evalrun.USAGE_FILE)

    def result_with(self, windows, status="allowed", overage=False):
        return evalrun.RunResult(data={}, returncode=0, snapshot={"status": status, "overage": overage,
                                                                    "windows": windows})

    def stored(self):
        with open(self.usage_path(), encoding="utf-8") as fh:
            return json.load(fh)

    def test_save_usage_writes_the_snapshot_atomically_and_creates_the_state_dir(self):
        state = os.path.join(self.repo.root, "state")
        evalrun.save_usage(state, self.result_with({"five_hour": {"utilization": 0.4, "resets_at": 1900000000.0}}),
                           now=1700000000.0)
        self.assertEqual(self.stored(), {"status": "allowed", "overage": False,
                                         "five_hour": {"utilization": 0.4, "resets_at": 1900000000.0, "at": 1700000000.0}})
        self.assertEqual(os.listdir(state), [evalrun.USAGE_FILE])               # временный файл не остался

    def test_save_usage_replaces_the_window_it_saw_and_keeps_the_other(self):
        state = os.path.join(self.repo.root, "state")
        evalrun.save_usage(state, self.result_with({"five_hour": {"utilization": 0.9, "resets_at": 1900000000.0},
                                                    "seven_day": {"utilization": 0.5}}), now=1700000000.0)
        evalrun.save_usage(state, self.result_with({"five_hour": {"utilization": 0.1}}), now=1700005000.0)
        data = self.stored()
        self.assertEqual(data["five_hour"], {"utilization": 0.1, "at": 1700005000.0})    # прежний сброс не тянется
        self.assertEqual(data["seven_day"], {"utilization": 0.5, "at": 1700000000.0})

    def test_save_usage_skips_empty_snapshots_and_missing_state_dir(self):
        state = os.path.join(self.repo.root, "state")
        evalrun.save_usage(state, self.result_with({}))
        self.assertFalse(os.path.exists(state))
        evalrun.save_usage("", self.result_with({"five_hour": {"utilization": 0.4}}))
        evalrun.save_usage(state, evalrun.RunResult(data={}, returncode=0))
        self.assertFalse(os.path.exists(state))

    def test_save_usage_replaces_a_corrupt_file(self):
        state = os.path.join(self.repo.root, "state")
        os.makedirs(state)
        with open(self.usage_path(), "w") as fh:
            fh.write("{not json")
        evalrun.save_usage(state, self.result_with({"seven_day": {"utilization": 0.7}}), now=1700000000.0)
        self.assertEqual(self.stored()["seven_day"], {"utilization": 0.7, "at": 1700000000.0})
        with open(self.usage_path(), "w") as fh:
            json.dump(["not", "a", "dict"], fh)
        evalrun.save_usage(state, self.result_with({"seven_day": {"utilization": 0.2}}), now=1700000000.0)
        self.assertEqual(self.stored()["seven_day"]["utilization"], 0.2)

    def test_save_usage_failure_is_a_log_line_not_an_exception(self):
        blocker = os.path.join(self.repo.root, "state")
        with open(blocker, "w") as fh:
            fh.write("x")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            evalrun.save_usage(blocker, self.result_with({"five_hour": {"utilization": 0.4}}))
        self.assertEqual(len(err.getvalue().strip().splitlines()), 1)
        self.assertIn("[evalrun]", err.getvalue())
        state = os.path.join(self.repo.root, "state2")
        os.makedirs(state)
        with mock.patch.object(evalrun.json, "dump", side_effect=OSError("disk full")), \
                contextlib.redirect_stderr(io.StringIO()):
            evalrun.save_usage(state, self.result_with({"five_hour": {"utilization": 0.4}}))
        self.assertEqual(os.listdir(state), [])                                 # временный файл убран

    # --- остановка по сохранённому снимку: порог из прошлого прогона, пока окно не сбросилось ---

    NOW = 1700000000.0
    WEEK = "недельный лимит занят на 85% — запас для дневной работы"

    def put_usage(self, data):
        os.makedirs(os.path.dirname(self.usage_path()), exist_ok=True)
        with open(self.usage_path(), "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def stored_stop(self, env=None):
        err = io.StringIO()
        with mock.patch.dict(os.environ, env or {}), contextlib.redirect_stderr(err):
            reason = evalrun.stored_stop(os.path.join(self.repo.root, "state"), now=self.NOW)
        return reason, err.getvalue()

    def test_stored_week_over_the_stop_with_a_future_reset_stops(self):
        self.put_usage({"seven_day": {"utilization": 0.85, "resets_at": self.NOW + 3600, "at": self.NOW - 60}})
        reason, err = self.stored_stop()
        self.assertEqual(reason, self.WEEK)                          # тот же текст, что у остановки по порогу
        self.assertEqual(len(err.strip().splitlines()), 1)
        self.assertIn("[evalrun]", err)

    def test_stored_window_that_has_reset_does_not_stop(self):
        self.put_usage({"seven_day": {"utilization": 0.85, "resets_at": self.NOW - 1, "at": self.NOW - 3600},
                        "five_hour": {"utilization": 0.99, "resets_at": self.NOW, "at": self.NOW - 3600}})
        self.assertEqual(self.stored_stop(), ("", ""))

    def test_stored_window_with_unknown_reset_stops_while_the_snapshot_is_young(self):
        hour, day = 3600, 86400
        for window, age, stops in (("five_hour", 5 * hour - 1, True), ("five_hour", 5 * hour, False),
                                   ("seven_day", 7 * day - 1, True), ("seven_day", 7 * day, False)):
            with self.subTest(window=window, age=age):
                self.put_usage({window: {"utilization": 0.99, "at": self.NOW - age}})
                self.assertEqual(bool(self.stored_stop()[0]), stops)

    def test_stored_snapshot_uses_the_same_thresholds_and_overrides_as_a_call(self):
        self.put_usage({"seven_day": {"utilization": 0.85, "resets_at": self.NOW + 60, "at": self.NOW},
                        "five_hour": {"utilization": 0.9, "resets_at": self.NOW + 60, "at": self.NOW}})
        self.assertIn("5 часов", self.stored_stop()[0])              # 0.9 ≥ 0.9, окно 5 часов первым, как в _verdict
        self.put_usage({"seven_day": {"utilization": 0.79, "resets_at": self.NOW + 60, "at": self.NOW}})
        self.assertEqual(self.stored_stop()[0], "")
        self.put_usage({"seven_day": {"utilization": 0.85, "resets_at": self.NOW + 60, "at": self.NOW}})
        self.assertEqual(self.stored_stop({"PLUGIN_TEST_L2_SEVEN_DAY_STOP": "1.0"}), ("", ""))   # волна: без порога
        self.assertEqual(self.stored_stop({"PLUGIN_TEST_L2_SEVEN_DAY_STOP": "0.85"})[0], self.WEEK)
        self.assertEqual(self.stored_stop({"PLUGIN_TEST_L2_SEVEN_DAY_STOP": "0.9"}), ("", ""))

    def test_stored_five_hour_over_but_reset_week_over_reports_the_week(self):
        self.put_usage({"five_hour": {"utilization": 0.95, "resets_at": self.NOW - 5, "at": self.NOW - 600},
                        "seven_day": {"utilization": 0.85, "resets_at": self.NOW + 5, "at": self.NOW - 600}})
        self.assertEqual(self.stored_stop()[0], self.WEEK)

    def test_missing_corrupt_and_malformed_snapshots_never_stop(self):
        self.assertEqual(self.stored_stop(), ("", ""))                                # файла нет
        self.assertEqual(evalrun.stored_stop("", now=self.NOW), "")                   # история не ведётся
        for raw in ("{not json", "[]", "null", "5", ""):
            with self.subTest(raw=raw):
                os.makedirs(os.path.dirname(self.usage_path()), exist_ok=True)
                with open(self.usage_path(), "w") as fh:
                    fh.write(raw)
                self.assertEqual(self.stored_stop(), ("", ""))
        for window in ({"utilization": "high", "at": self.NOW}, {"utilization": True, "at": self.NOW},
                       {"utilization": float("nan"), "at": self.NOW}, {"utilization": 0.99, "at": "yesterday"},
                       {"utilization": 0.99}, {"utilization": 0.99, "resets_at": "soon"}, "0.99", None, 5):
            with self.subTest(window=window):
                self.put_usage({"seven_day": window, "five_hour": window})
                self.assertEqual(self.stored_stop(), ("", ""))


if __name__ == "__main__":
    unittest.main()
