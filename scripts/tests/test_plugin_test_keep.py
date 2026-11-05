"""PLUGIN_TEST_L2_KEEP: ответы модели и вердикты судьи сохраняются локально для триажа и больше нигде не видны."""
import contextlib
import io
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import eval_case, eval_result  # noqa: E402
import test_plugin_test_behavior as tb  # noqa: E402  (модулем: имя BehaviorTest в этом модуле подхватил бы unittest)
from test_plugin_test_behavior import NO, QUALITY, REJECTED, T, YES, behavior  # noqa: E402

from plugin_test import keep  # noqa: E402
from plugin_test.model import L2_BELOW  # noqa: E402

SECRET = "-".join(["sk", "ant", "api03", "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"])    # собирается в рантайме: не секрет в дереве
BEARER = "Authorization: Bearer abcdef0123456789abcdef0123456789"
ANSWER = "Use the endpoint /v1/things and pass the id."
VOTES = "judge votes: FAIL FAIL PASS"
CRITERION = "says how to call it"


def assistant(text=None, skill=None):
    content = []
    if text is not None:
        content.append({"type": "text", "text": text})
    if skill is not None:
        content.append({"type": "tool_use", "name": "Skill", "id": "t1", "input": {"skill": skill, "args": SECRET}})
    return {"type": "assistant", "message": {"content": content}}


def noise():
    """События трейса, которых в файлах быть не должно: окружение, заголовки, тела запросов, вызовы инструментов."""
    return [{"type": "system", "subtype": "init", "env": {"ANTHROPIC_API_KEY": SECRET},
             "headers": {"authorization": BEARER}, "request_body": {"token": SECRET}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "content": "tool says " + SECRET}]}}]


def run(score, answer=ANSWER, skill=None, graders=None, error=None, final=True):
    events = noise() + [assistant(answer, skill)]
    if final:
        events.append({"type": "result", "subtype": "success", "result": answer})
    r = {"score": score, "error": error, "events": events}
    if graders is not None:
        r["graders"] = graders
    return r


def llm(passed, explanation=VOTES, name="e1", votes=(False, False, True), evidence="do not copy " + SECRET):
    return {"name": name, "passed": passed, "weight": 1, "explanation": explanation, "withOnly": False, "scored": True,
            "judgeVotes": list(votes), "evidence": evidence}


def fired(passed, name="fired", explanation="Skill called 1x (expected 1..\u221e)"):
    return {"name": name, "passed": passed, "weight": 1, "withOnly": True, "scored": False, "explanation": explanation}


def with_graders(case, prompt="how to do it"):
    case["promptMarkdown"] = prompt
    case["graders"] = [{"name": "e1", "type": "llm", "weight": 1,
                        "graderMarkdown": "PASS if the response satisfies this requirement: " + CRITERION},
                       {"name": "fired", "type": "tool_used", "weight": 1}]
    return case


class KeepTest(unittest.TestCase):
    add_plugin = tb.BehaviorTest.add_plugin
    ctx = tb.BehaviorTest.ctx
    check = tb.BehaviorTest.check
    hist = tb.BehaviorTest.hist

    def setUp(self):
        tb.BehaviorTest.setUp(self)
        self.keep = os.path.join(self.repo.root, "kept")

    def tearDown(self):
        self.repo.cleanup()

    def kept(self, case, plugin="b-dev"):
        with open(os.path.join(self.keep, plugin, case + ".json"), encoding="utf-8") as fh:
            return json.load(fh)

    def files(self, plugin="b-dev"):
        path = os.path.join(self.keep, plugin)
        return sorted(os.listdir(path)) if os.path.isdir(path) else []

    def go(self, plan, keep_dir=True, extra=None, **kw):
        env = dict(extra or {})
        if keep_dir:
            env[keep.KEEP_VAR] = self.keep
        err = io.StringIO()
        with mock.patch.dict(os.environ, env), contextlib.redirect_stderr(err), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            res = self.check(plan, **kw)
        return res, err.getvalue(), out.getvalue()

    def quality_plan(self):
        case = with_graders(eval_case(
            "q-web-1", 0.5, delta=0.1,
            runs=[run(0.0, graders=[llm(False), fired(True)], skill="web"),
                  run(1.0, answer="second answer", graders=[llm(True, "judge votes: PASS", votes=(True,))])],
            without=[run(0.0, answer="bare answer", graders=[llm(False, "judge votes: FAIL", votes=(False,))])]))
        return [{"result": eval_result(case)}]

    def all_text(self):
        out = []
        for d, _, names in os.walk(self.keep):
            for n in names:
                with open(os.path.join(d, n), encoding="utf-8") as fh:
                    out.append(fh.read())
        return "\n".join(out)

    def test_quality_case_file_has_both_arms_answers_graders_and_reasons(self):
        self.add_plugin(queries=(), quality=QUALITY)
        (got, evals, _, _), err, out = self.go(self.quality_plan())
        self.assertEqual(self.files(), ["q-web-1.json"])
        data = self.kept("q-web-1")
        self.assertEqual((data["plugin"], data["case"], data["tree"], data["prompt"]),
                         ("b-dev", "q-web-1", "quality", "how to do it"))
        self.assertEqual(data["calls"]["качество"], {"score": 0.5, "delta": 0.1})
        runs = data["runs"]
        self.assertEqual([(r["arm"], r["index"]) for r in runs], [("with", 0), ("with", 1), ("without", 0)])
        first = runs[0]
        self.assertEqual((first["answer"], first["score"], first["error"], first["call"]), (ANSWER, 0.0, None, "качество"))
        self.assertEqual((first["skill_fired"], first["skills_called"]), (True, ["web"]))
        judge, tool = first["graders"]
        self.assertEqual((judge["name"], judge["type"], judge["passed"], judge["explanation"], judge["judge_votes"]),
                         ("e1", "llm", False, VOTES, [False, False, True]))
        self.assertEqual(judge["criterion"], "PASS if the response satisfies this requirement: " + CRITERION)
        self.assertEqual((tool["name"], tool["type"], tool["passed"], tool["with_only"], tool["scored"]),
                         ("fired", "tool_used", True, True, False))
        self.assertEqual(tool["explanation"], "Skill called 1x (expected 1..\u221e)")     # фиксированная форма CLI
        self.assertEqual((first["answer_source"], first["skipped_paid_graders"]), ("trace", False))
        self.assertEqual((runs[1]["answer"], runs[1]["graders"][0]["explanation"]), ("second answer", "judge votes: PASS"))
        self.assertEqual((runs[2]["answer"], runs[2]["skill_fired"]), ("bare answer", False))
        self.assertEqual(err.count("ответы сохранены"), 1)
        self.assertIn("[behavior] b-dev: ответы сохранены в %s\n" % os.path.join(self.keep, "b-dev"), err)
        self.assertEqual(out, "")

    def test_trigger_cases_are_kept_for_every_case(self):
        self.add_plugin()
        plan = [{"result": eval_result(
            eval_case(T(YES), 1.0, runs=[run(1.0, answer="fired it", skill="b-dev:web", graders=[fired(True)],
                                              error="exit 1: Reached maximum number of turns (1)")]),
            eval_case(T(NO), 1.0, runs=[run(1.0, answer="no skill", graders=[fired(True)])]))}]
        (got, _, _, _), err, _ = self.go(plan)
        self.assertEqual(got, [])
        self.assertEqual(self.files(), sorted([T(YES) + ".json", T(NO) + ".json"]))
        yes, no = self.kept(T(YES)), self.kept(T(NO))
        self.assertEqual((yes["tree"], yes["runs"][0]["skill_fired"], yes["runs"][0]["skills_called"]),
                         ("trigger", True, ["b-dev:web"]))
        self.assertEqual(yes["runs"][0]["error"], "exit 1: Reached maximum number of turns (1)")
        self.assertEqual((no["runs"][0]["skill_fired"], no["runs"][0]["skills_called"], no["runs"][0]["answer"]),
                         (False, [], "no skill"))

    def test_rerun_adds_runs_to_the_same_case_file(self):
        self.add_plugin(queries=((YES, True),))
        first = eval_result(eval_case(T(YES), 0.0, runs=[run(0.0, answer="miss one")]))
        rerun = eval_result(eval_case(T(YES), 0.0, runs=[run(0.0, answer="miss two"), run(0.0, answer="miss three")]))
        (got, _, _, _), _, _ = self.go([{"result": first}, {"result": rerun}])
        runs = self.kept(T(YES))["runs"]
        self.assertEqual([(r["call"], r["index"], r["answer"]) for r in runs],
                         [("срабатывание", 0, "miss one"), ("повтор срабатывания", 0, "miss two"),
                          ("повтор срабатывания", 1, "miss three")])

    def test_second_invocation_overwrites_the_files(self):
        self.add_plugin(queries=((YES, True),))
        plan = lambda text: [{"result": eval_result(eval_case(T(YES), 1.0, runs=[run(1.0, answer=text)]))}]  # noqa: E731
        self.go(plan("old"))
        self.go(plan("new"))
        runs = self.kept(T(YES))["runs"]
        self.assertEqual([r["answer"] for r in runs], ["new"])
        self.assertEqual(self.files(), [T(YES) + ".json"])      # временных файлов не осталось

    def test_unset_writes_nothing(self):
        self.add_plugin(queries=(), quality=QUALITY)
        (got, _, _, _), err, out = self.go(self.quality_plan(), keep_dir=False)
        self.assertFalse(os.path.exists(self.keep))
        self.assertNotIn("ответы сохранены", err)
        self.assertEqual(out, "")

    def test_empty_value_is_unset(self):
        self.add_plugin(queries=(), quality=QUALITY)
        (_, _, calls, _), err, _ = self.go(self.quality_plan(), keep_dir=False, extra={keep.KEEP_VAR: "  "})
        self.assertNotIn("ответы сохранены", err)

    def test_findings_and_history_are_identical_with_and_without(self):
        self.add_plugin(queries=((YES, True), (NO, False)), quality=QUALITY)
        fail_first = eval_result(eval_case(T(YES), 0.0, runs=[run(0.0)]), eval_case(T(NO), 1.0, runs=[run(1.0)]))
        rerun = eval_result(eval_case(T(YES), 0.0, runs=[run(0.0), run(0.0)]))
        plan = [{"result": fail_first}, {"result": rerun}] + self.quality_plan()

        def rows():
            return [{k: v for k, v in r.items() if k != "date"} for r in self.hist()]

        with_keep, _, _ = self.go(plan)
        got_with, hist_with = with_keep[0], rows()
        os.remove(os.path.join(self.state, "l2-history.jsonl"))
        without, _, _ = self.go(plan, keep_dir=False)
        self.assertEqual([f.to_dict() if hasattr(f, "to_dict") else f for f in got_with],
                         [f.to_dict() if hasattr(f, "to_dict") else f for f in without[0]])
        self.assertTrue(got_with)
        self.assertEqual(hist_with, rows())

    def test_nothing_from_kept_files_reaches_findings_history_or_stdout(self):
        self.add_plugin(queries=(), quality=QUALITY)
        case = with_graders(eval_case("q-web-1", 0.0, delta=-0.5, runs=[
            run(0.0, answer="SENTINEL_ANSWER", graders=[llm(False, "SENTINEL_EXPLANATION")])]))
        (got, _, _, _), err, out = self.go([{"result": eval_result(case)}])
        self.assertTrue(got)
        blob = json.dumps([f.message + f.fix + f.file for f in got]) + json.dumps(self.hist()) + out
        self.assertNotIn("SENTINEL", blob)
        self.assertNotIn("SENTINEL", err)
        self.assertIn("SENTINEL_ANSWER", self.all_text())

    def test_secret_shaped_strings_outside_the_answer_never_reach_the_files(self):
        self.add_plugin(queries=(), quality=QUALITY)
        case = with_graders(eval_case("q-web-1", 0.5, runs=[
            run(0.5, graders=[llm(False), fired(True, explanation="tool_used Skill input " + SECRET)], skill="web",
                error="API Error " + SECRET)]))
        self.go([{"result": eval_result(case)}])
        text = self.all_text()
        self.assertNotIn(SECRET, text)
        self.assertNotIn("abcdef0123456789abcdef0123456789", text)
        self.assertNotIn("do not copy", text)           # evidence судьи не копируется
        self.assertNotIn("tool_used Skill input", text)  # пояснение tool_used-грейдера иной формы несёт кусок вызова
        self.assertNotIn("tool says", text)
        self.assertNotIn("ANTHROPIC_API_KEY", text)
        self.assertIn(ANSWER, text)

    def test_secret_shaped_strings_in_the_answer_are_masked(self):
        self.add_plugin(queries=(), quality=QUALITY)
        answer = "Call it like this:\nexport API_TOKEN=%s\n%s\nthen retry" % (SECRET, BEARER)
        case = with_graders(eval_case("q-web-1", 0.5, runs=[run(0.5, answer=answer, graders=[
            llm(False, "judge saw api_key=" + "x" * 40)])]))
        self.go([{"result": eval_result(case)}])
        text = self.all_text()
        for needle in (SECRET, "abcdef0123456789abcdef0123456789", "x" * 40):
            self.assertNotIn(needle, text)
        data = self.kept("q-web-1")["runs"][0]
        self.assertIn("Call it like this:", data["answer"])
        self.assertIn("then retry", data["answer"])

    def test_answer_falls_back_to_the_last_assistant_text_without_a_result_event(self):
        self.add_plugin(queries=(), quality=QUALITY)
        case = with_graders(eval_case("q-web-1", 0.5, runs=[
            {"score": 0.5, "error": None,
             "events": noise() + [assistant("first thought"), assistant(skill="web"), assistant("last words")]}]))
        self.go([{"result": eval_result(case)}])
        self.assertEqual(self.kept("q-web-1")["runs"][0]["answer"], "last words")

    def test_run_without_a_trace_keeps_scores_and_verdicts_only(self):
        self.add_plugin(queries=(), quality=QUALITY)
        case = with_graders(eval_case("q-web-1", 0.5, runs=[{"score": 0.5, "error": None, "graders": [llm(False, evidence="")]}]))
        self.go([{"result": eval_result(case)}])
        r = self.kept("q-web-1")["runs"][0]
        self.assertEqual((r["answer"], r["answer_source"], r["skill_fired"], r["skills_called"], r["score"]),
                         (None, None, None, None, 0.5))
        self.assertEqual(r["graders"][0]["explanation"], VOTES)

    def test_answer_comes_from_the_judge_evidence_when_the_trace_is_missing(self):
        self.add_plugin(queries=(), quality=QUALITY)
        case = with_graders(eval_case("q-web-1", 0.5, runs=[
            {"score": 0.5, "error": None, "graders": [llm(False, evidence="what the judge saw")]}]))
        self.go([{"result": eval_result(case)}])
        r = self.kept("q-web-1")["runs"][0]
        self.assertEqual((r["answer"], r["answer_source"]), ("what the judge saw", "judge_evidence"))

    def test_the_trace_answer_wins_over_the_judge_evidence(self):
        self.add_plugin(queries=(), quality=QUALITY)
        case = with_graders(eval_case("q-web-1", 0.5, runs=[run(0.5, graders=[llm(False, evidence="from judge")])]))
        self.go([{"result": eval_result(case)}])
        r = self.kept("q-web-1")["runs"][0]
        self.assertEqual((r["answer"], r["answer_source"]), (ANSWER, "trace"))

    def test_invalid_limit_call_is_kept_too(self):
        self.add_plugin(queries=(), quality=QUALITY)
        limited = run(0.0, answer="cut off by the limit")
        limited["trace"] = [REJECTED]
        case = with_graders(eval_case("q-web-1", 0.0, runs=[limited]))
        (got, _, _, ctx), _, _ = self.go([{"result": eval_result(case)}])
        self.assertTrue(ctx.l2_stop)
        self.assertEqual(self.kept("q-web-1")["runs"][0]["answer"], "cut off by the limit")

    def test_an_unwritable_directory_is_one_stderr_note_and_the_run_goes_on(self):
        self.add_plugin(queries=(), quality=QUALITY)
        blocker = os.path.join(self.repo.root, "blocker")
        with open(blocker, "w") as fh:
            fh.write("a file, not a directory")
        env = {keep.KEEP_VAR: os.path.join(blocker, "inside")}
        (got, _, _, _), err, _ = self.go(self.quality_plan(), keep_dir=False, extra=env)
        self.assertEqual(err.count("ответы не сохранены"), 1)
        self.assertNotIn("ответы сохранены в", err)
        self.assertEqual([f.message.split(":")[0] for f in got], [L2_BELOW])    # вердикт кейса не потерян

    def test_a_failing_atomic_write_leaves_no_temp_file(self):
        self.add_plugin(queries=(), quality=QUALITY)
        with mock.patch.object(keep.os, "replace", side_effect=PermissionError(13, "Permission denied")):
            (got, _, _, _), err, _ = self.go(self.quality_plan())
        self.assertEqual(err.count("ответы не сохранены"), 1)
        self.assertEqual(self.files(), [])
        self.assertTrue(got)

    def test_works_with_skill_filter_and_quick_mode(self):
        self.add_plugin(queries=(), quality=QUALITY)
        case = with_graders(eval_case("q-web-1", 0.5, runs=[run(0.5, graders=[llm(False)])]))
        extra = {behavior.SKILLS_VAR: "web", behavior.QUICK_VAR: "1"}
        (got, evals, _, _), err, _ = self.go([{"result": eval_result(case)}], extra=extra)
        self.assertEqual(self.kept("q-web-1")["runs"][0]["answer"], ANSWER)
        self.assertEqual([r["arm"] for r in self.kept("q-web-1")["runs"]], ["with"])
        self.assertIn("ответы сохранены", err)

    def test_case_name_with_unsafe_characters_gets_a_safe_distinct_file_name(self):
        a, b = keep._file_name("n-a/b"), keep._file_name("n-a_b")
        self.assertNotEqual(a, b)
        self.assertRegex(a, r"^[A-Za-z0-9_.-]+$")
        self.assertEqual(keep._file_name("q-web-1"), "q-web-1.json")
        self.assertRegex(keep._file_name("../.."), r"^[A-Za-z0-9_.-]+$")
        self.assertFalse(keep._file_name("../..").startswith("."))


if __name__ == "__main__":
    unittest.main()
