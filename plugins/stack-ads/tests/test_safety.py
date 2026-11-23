"""Regression tests for the ways the money rules were once defeated.

Each class holds one family: a request that hides what it does from the guard
rails, a budget the plan check did not count, a write whose outcome is unknown,
a plan that no longer matches the account.
"""
import contextlib
import http.client
import io
import json
import unittest
from unittest import mock

import helpers
import ads
from adskit import core, google, guards, launch, meta, tiktok
from adskit.core import DEFAULT_CONFIG, AdsError, Refused, read_jsonl
import test_launch
from test_launch import meta_handler, meta_plan, planned, real_posts

# Referred to through the module: a TestCase imported by name would be collected and run a second time here.
GOOGLE = test_launch.GoogleLaunch

NOT_NUMBERS = (float("nan"), "NaN", "nan", float("inf"), "-1", -5, "abc", True, [1])


def tiktok_handler(method, url, kwargs):
    if method == "GET":
        return {"code": 0, "data": {"list": [{"name": "Adv", "currency": "USD", "status": "STATUS_ENABLE"}]}}
    made = {"campaign/create/": {"campaign_id": "900"}, "adgroup/create/": {"adgroup_id": "901"},
            "ad/create/": {"ad_ids": ["902"]}}
    return {"code": 0, "data": made.get(url.split("v1.3/")[1], {})}


class HiddenRequests(unittest.TestCase):
    """What a request does must be readable from its parameters, never tucked into the path."""

    def test_a_meta_path_cannot_carry_parameters(self):
        for path in ("act_1/campaigns?status=ACTIVE&daily_budget=9999999", "act_1/campaigns#x", "act_1/campaigns status=ACTIVE",
                     "", "/", "act_1/../campaigns", "act_1/campaigns%3Fstatus=ACTIVE", "act_1//campaigns"):
            with self.assertRaises(Refused, msg=path):
                guards.meta_request("POST", path, {"name": "x", "status": "PAUSED"}, DEFAULT_CONFIG)

    def test_meta_refuses_calls_that_hold_other_calls(self):
        for params in ({"batch": "[]"}, {"adbatch": "[]"}, {"status": "PAUSED", "adset_spec": {"daily_budget": 999999}},
                       {"status": "PAUSED", "campaign_spec": {"name": "c"}}):
            with self.assertRaises(Refused, msg=str(params)):
                guards.meta_request("POST", "act_1/ads", params, DEFAULT_CONFIG)
        with self.assertRaises(Refused):
            guards.meta_request("POST", "act_1/async_batch_requests", {"name": "x"}, DEFAULT_CONFIG)

    def test_a_meta_copy_is_paused_unless_activation_is_asked_for(self):
        for params in ({}, {"status_option": "ACTIVE"}, {"status_option": "INHERITED_FROM_SOURCE"}):
            with self.assertRaises(Refused, msg=str(params)):
                guards.meta_request("POST", "120000000001/copies", params, DEFAULT_CONFIG)
        self.assertFalse(guards.meta_request("POST", "120000000001/copies", {"status_option": "PAUSED"}, DEFAULT_CONFIG)["activates"])
        self.assertTrue(guards.meta_request("POST", "120000000001/copies", {"status_option": "ACTIVE"}, DEFAULT_CONFIG,
                                            activate=True)["activates"])

    def test_a_smuggling_path_is_never_sent(self):
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(meta_handler())
            with mock.patch.object(meta, "request", http):
                for yes in (False, True):
                    with self.assertRaises(Refused):
                        meta.post(ws.ctx, "{account}/campaigns?status=ACTIVE&daily_budget=9999999",
                                  {"name": "x", "objective": "OUTCOME_TRAFFIC"}, yes=yes)
                with self.assertRaises(Refused):
                    meta.delete(ws.ctx, "120000000001?x=1", yes=True)
            self.assertEqual(http.calls, [])

    def test_a_tiktok_path_cannot_carry_parameters(self):
        body = {"operation_status": "ENABLE", "campaign_name": "x"}
        for path in ("campaign/create?x=1", "campaign/create/?x=1", "campaign/create#", "campaign/Create", "", "campaign//create"):
            with self.assertRaises(Refused, msg=path):
                guards.tiktok_request(path, body, DEFAULT_CONFIG, activate=True)
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(tiktok_handler)
            with mock.patch.object(tiktok, "request", http):
                with self.assertRaises(Refused):
                    tiktok.post(ws.ctx, "campaign/create?x=1", body, yes=True)
            self.assertEqual(http.calls, [])

    def test_tiktok_status_counts_only_where_the_platform_reads_it(self):
        nested = {"campaign_name": "x", "extra": {"operation_status": "DISABLE"}}
        for route in ("campaign/create/", "adgroup/create/", "smart_plus/ad/create/"):
            with self.assertRaises(Refused, msg=route):
                guards.tiktok_request(route, nested, DEFAULT_CONFIG)

    def test_tiktok_enable_needs_activate_on_every_route(self):
        for route, body in (("adgroup/update/", {"adgroup_id": "1", "operation_status": "ENABLE"}),
                            ("campaign/update/", {"campaign_id": "1", "operation_status": "ENABLE"}),
                            ("ad/update/", {"adgroup_id": "1", "creatives": [{"ad_id": "2", "operation_status": "ENABLE"}]})):
            with self.assertRaises(Refused, msg=route):
                guards.tiktok_request(route, body, DEFAULT_CONFIG)
            self.assertTrue(guards.tiktok_request(route, body, DEFAULT_CONFIG, activate=True)["activates"])

    def test_tiktok_budget_lists_are_checked(self):
        body = {"budget": [{"adgroup_id": "1", "budget": 30}, {"adgroup_id": "2", "budget": 900}]}
        with self.assertRaises(Refused):
            guards.tiktok_request("adgroup/budget/update/", body, DEFAULT_CONFIG)
        body["budget"][1]["budget"] = 40
        self.assertEqual(guards.tiktok_request("adgroup/budget/update/", body, DEFAULT_CONFIG)["daily_budget"], 40.0)


class GoogleCall(unittest.TestCase):
    """google call is for reads and conversion uploads; everything that shapes a campaign goes through google mutate."""

    def test_reads_are_reads(self):
        for method, path in (("GET", "customers:listAccessibleCustomers"), ("POST", "googleAdsFields:search"),
                             ("POST", "customers/1/googleAds:searchStream"), ("POST", "customers/1:generateReachForecast"),
                             ("POST", "customers/1:generateKeywordForecastMetrics"), ("POST", "geoTargetConstants:suggest"),
                             ("POST", "customers/1:suggestKeywordThemes"), ("POST", ":listPlannableLocations")):
            self.assertEqual(guards.google_call(method, path), "read", path)

    def test_uploads_are_the_only_writes(self):
        for path in ("customers/1:uploadClickConversions", "customers/1:uploadConversionAdjustments",
                     "customers/1/offlineUserDataJobs:create", "customers/1/offlineUserDataJobs/9:addOperations",
                     "customers/1/offlineUserDataJobs/9:run"):
            self.assertEqual(guards.google_call("POST", path), "write", path)

    def test_anything_that_shapes_a_campaign_is_refused(self):
        for method, path in (("POST", "customers/1/campaigns:mutate"), ("POST", "customers/1/campaignBudgets:mutate"),
                             ("POST", "customers/1/adGroupAds:mutate"), ("POST", "customers/1/googleAds:mutate"),
                             ("POST", "customers/1/googleAds:mutate?x=1"), ("POST", "customers/1/campaigns:mutate#:search"),
                             ("POST", "customers/1/campaigns:mutate?x=:search"), ("POST", "customers/1/batchJobs:mutate"),
                             ("POST", "customers/1/batchJobs/7:addOperations"), ("POST", "customers/1/batchJobs/7:run"),
                             ("POST", "customers/1/recommendations:apply"), ("POST", "customers/1/experiments/3:promoteExperiment"),
                             ("POST", "customers/1/campaigns"), ("DELETE", "customers/1/campaigns/5"),
                             ("PATCH", "customers/1/campaigns/5"), ("POST", "customers/1 :search"), ("POST", "")):
            with self.assertRaises(Refused, msg="%s %s" % (method, path)):
                guards.google_call(method, path)

    def test_a_refused_path_is_refused_before_the_dry_run_and_never_sent(self):
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(GOOGLE.handler)
            with mock.patch.object(google, "request", http), mock.patch.dict(google._TOKENS, {}, clear=True):
                for yes in (False, True):
                    with self.assertRaises(Refused) as caught:
                        google.call(ws.ctx, "POST", "customers/{customer}/campaigns:mutate",
                                    {"operations": [{"create": {"status": "ENABLED"}}]}, yes=yes)
                    self.assertIn("google mutate", caught.exception.hint)
                dry = google.call(ws.ctx, "POST", "customers/{customer}:uploadClickConversions", {"conversions": []})
                self.assertTrue(dry["dry_run"])
            self.assertEqual(http.calls, [])


class Amounts(unittest.TestCase):
    """A budget that is not a plain non-negative number switches the comparisons off, so it is refused."""

    def test_guards_refuse_what_is_not_an_amount(self):
        for bad in NOT_NUMBERS:
            with self.assertRaises(Refused, msg=repr(bad)):
                guards.meta_request("POST", "act_1/adsets", {"status": "PAUSED", "daily_budget": bad}, DEFAULT_CONFIG)
            with self.assertRaises(Refused, msg=repr(bad)):
                guards.meta_request("POST", "act_1/adsets", {"status": "PAUSED", "lifetime_budget": bad}, DEFAULT_CONFIG)
            with self.assertRaises(Refused, msg=repr(bad)):
                guards.tiktok_request("campaign/create/", {"operation_status": "DISABLE", "budget": bad}, DEFAULT_CONFIG)
            with self.assertRaises(Refused, msg=repr(bad)):
                guards.google_mutate({"mutateOperations": [{"campaignBudgetOperation": {"create": {"amountMicros": bad}}}]},
                                     DEFAULT_CONFIG)

    def test_numbers_written_as_text_still_count(self):
        body = {"mutateOperations": [{"campaignBudgetOperation": {"create": {"amountMicros": "1.5e7"}}}]}
        self.assertEqual(guards.google_mutate(body, DEFAULT_CONFIG)["daily_budgets"], [15.0])

    def test_a_plan_with_such_a_budget_is_blocked_not_passed(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            plan["budget"]["daily"] = 1
            for number, value in enumerate((4900, 4900, "NaN")):
                extra = json.loads(json.dumps(plan["steps"][2]))
                extra["id"], extra["with"]["params"]["daily_budget"] = "more%d" % number, value
                plan["steps"].insert(3, extra)
            with mock.patch.object(meta, "request", helpers.FakeHttp(meta_handler())):
                text, problems = launch.plan(ws.ctx, ws.write_plan(plan))
            self.assertTrue(problems)
            self.assertIn("blocked", text)

    def test_a_negative_budget_cannot_offset_the_others(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            plan["budget"]["daily"] = 49
            plan["steps"][2]["with"]["params"]["daily_budget"] = 4900
            for number, value in enumerate((4900, 4900, 4900, -14700)):
                extra = json.loads(json.dumps(plan["steps"][2]))
                extra["id"], extra["with"]["params"]["daily_budget"] = "more%d" % number, value
                plan["steps"].insert(3, extra)
            with self.assertRaises(Refused):
                launch.budget_check(ws.ctx, plan)


class PlanBudgets(unittest.TestCase):
    """The plan total counts every campaign: a budget on one campaign does not hide the ad sets of another."""

    def test_meta_counts_ad_sets_of_a_campaign_without_its_own_budget(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            campaign, adset = plan["steps"][1], plan["steps"][2]
            campaign["with"]["params"]["daily_budget"] = 2000
            adset["with"]["params"]["daily_budget"] = 1000       # under the campaign that has a budget: not counted
            second = json.loads(json.dumps(campaign))
            second["id"] = "campaign2"
            del second["with"]["params"]["daily_budget"]
            plan["steps"].append(second)
            for number in range(5):
                extra = json.loads(json.dumps(adset))
                extra["id"] = "other%d" % number
                extra["with"]["params"].update({"campaign_id": "{{campaign2.id}}", "daily_budget": 4000})
                plan["steps"].append(extra)
            self.assertEqual(launch.plan_budgets(ws.ctx, plan), (220.0, 0.0))
            problems = launch.budget_check(ws.ctx, plan)[1]
            self.assertTrue(any("add up to 220" in p for p in problems), problems)

    def test_an_ad_set_under_a_campaign_outside_the_plan_counts(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            plan["steps"][1]["with"]["params"]["daily_budget"] = 2000
            extra = json.loads(json.dumps(plan["steps"][2]))
            extra["id"] = "foreign"
            extra["with"]["params"].update({"campaign_id": "120000000009", "daily_budget": 3000})
            plan["steps"].append(extra)
            self.assertEqual(launch.plan_budgets(ws.ctx, plan), (50.0, 0.0))

    def test_tiktok_counts_ad_groups_of_a_campaign_without_its_own_budget(self):
        def campaign(name, budget=None):
            body = {"campaign_name": name, "objective_type": "TRAFFIC", "operation_status": "DISABLE",
                    "budget_mode": "BUDGET_MODE_INFINITE"}
            if budget:
                body.update({"budget_mode": "BUDGET_MODE_DAY", "budget": budget})
            return {"id": name, "do": "tiktok.post", "with": {"path": "campaign/create/", "body": body}}

        def group(name, parent, budget):
            return {"id": name, "do": "tiktok.post", "with": {"path": "adgroup/create/", "body": {
                "campaign_id": "{{%s.campaign_id}}" % parent, "adgroup_name": name, "budget_mode": "BUDGET_MODE_DAY",
                "budget": budget, "operation_status": "DISABLE"}}}

        plan = {"name": "tt-two", "platform": "tiktok", "steps": [campaign("one", 20), group("capped", "one", 20),
                                                                     campaign("two")] + [group("g%d" % n, "two", 40) for n in range(5)]}
        with helpers.Workspace() as ws:
            self.assertEqual(launch.plan_budgets(ws.ctx, plan), (220.0, 0.0))

    def test_google_budget_updates_count(self):
        operations = [{"campaignBudgetOperation": {"create": {"resourceName": "customers/{customer}/campaignBudgets/-1",
                                                              "amountMicros": "10000000"}}}]
        operations += [{"campaignBudgetOperation": {"update": {"resourceName": "customers/{customer}/campaignBudgets/%d" % n,
                                                              "amountMicros": "49000000"}, "updateMask": "amount_micros"}}
                       for n in range(10)]
        plan = {"name": "g-raise", "platform": "google", "steps": [{"id": "m", "do": "google.mutate",
                                                                      "with": {"mutateOperations": operations}}]}
        with helpers.Workspace() as ws:
            self.assertEqual(launch.plan_budgets(ws.ctx, plan), (500.0, 0.0))

    def test_the_plan_currency_must_be_the_project_currency(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            plan["budget"]["currency"] = "EUR"
            problems = launch.budget_check(ws.ctx, plan)[1]
            self.assertTrue(any("EUR" in p and "USD" in p for p in problems), problems)

    def test_the_account_currency_must_be_the_project_currency(self):
        def handler(method, url, kwargs):
            if method == "GET":
                return {"id": "1", "name": "Tester", "account_status": 1, "currency": "JPY"}
            return meta_handler()(method, url, kwargs)

        with helpers.Workspace() as ws:
            with mock.patch.object(meta, "request", helpers.FakeHttp(handler)):
                text, problems = launch.plan(ws.ctx, ws.write_plan(meta_plan(ws)))
            self.assertTrue(any("JPY" in p and "USD" in p for p in problems), problems)


class GoogleDeliverables(unittest.TestCase):
    """Under a campaign that already exists, a new ad group or ad would serve at once: it is created paused."""

    @staticmethod
    def body(*operations):
        return {"mutateOperations": list(operations)}

    def test_new_objects_under_an_existing_parent_need_paused_or_activate(self):
        cases = (
            {"adGroupOperation": {"create": {"campaign": "customers/1/campaigns/123", "name": "g", "status": "ENABLED"}}},
            {"adGroupOperation": {"create": {"campaign": "customers/1/campaigns/123", "name": "g"}}},
            {"adGroupAdOperation": {"create": {"adGroup": "customers/1/adGroups/55", "status": "ENABLED", "ad": {}}}},
            {"assetGroupOperation": {"create": {"campaign": "customers/1/campaigns/123", "name": "a", "status": "ENABLED"}}},
            {"adGroupOperation": {"create": {"campaign": "customers/1/campaigns/-9", "name": "g", "status": "ENABLED"}}},
        )
        for operation in cases:
            with self.assertRaises(Refused, msg=str(operation)):
                guards.google_mutate(self.body(operation), DEFAULT_CONFIG)
            self.assertTrue(guards.google_mutate(self.body(operation), DEFAULT_CONFIG, activate=True)["activates"])
            kind = next(iter(operation))
            operation[kind]["create"]["status"] = "PAUSED"
            self.assertFalse(guards.google_mutate(self.body(operation), DEFAULT_CONFIG)["activates"])

    def test_children_of_a_campaign_created_paused_in_the_same_request_may_be_enabled(self):
        body = self.body(
            {"campaignBudgetOperation": {"create": {"resourceName": "customers/1/campaignBudgets/-1", "amountMicros": "10000000"}}},
            {"campaignOperation": {"create": {"resourceName": "customers/1/campaigns/-2", "status": "PAUSED"}}},
            {"adGroupOperation": {"create": {"resourceName": "customers/1/adGroups/-3", "campaign": "customers/1/campaigns/-2",
                                             "status": "ENABLED"}}},
            {"adGroupAdOperation": {"create": {"adGroup": "customers/1/adGroups/-3", "status": "ENABLED", "ad": {}}}},
            {"assetGroupOperation": {"create": {"campaign": "customers/1/campaigns/-2", "status": "ENABLED"}}})
        self.assertFalse(guards.google_mutate(body, DEFAULT_CONFIG)["activates"])

    def test_a_plan_switches_what_a_later_step_created_paused(self):
        plan = json.loads(json.dumps(GOOGLE.PLAN))
        plan["name"] = "g-two-steps"
        plan["steps"].append({"id": "extend", "do": "google.mutate", "with": {"mutateOperations": [
            {"adGroupOperation": {"create": {"resourceName": "customers/{customer}/adGroups/-1",
                                             "campaign": "{{create.results.1}}", "name": "new", "status": "PAUSED"}}},
            {"adGroupAdOperation": {"create": {"adGroup": "customers/{customer}/adGroups/-1", "status": "PAUSED", "ad": {}}}}]}})

        def handler(method, url, kwargs):
            body = kwargs.get("json_body") or {}
            if url.endswith("googleAds:mutate") and not body.get("validateOnly") and "adGroupOperation" in json.dumps(body) \
                    and "create" in json.dumps(body):
                return {"mutateOperationResponses": [{"adGroupResult": {"resourceName": "customers/1234567890/adGroups/77"}},
                                                     {"adGroupAdResult": {"resourceName": "customers/1234567890/adGroupAds/77~88"}}]}
            return GOOGLE.handler(method, url, kwargs)

        with helpers.Workspace() as ws:
            ws.ctx.config["project"]["currency"] = "EUR"
            path = ws.write_plan(plan)
            http = helpers.FakeHttp(handler)
            with mock.patch.object(google, "request", http), mock.patch.dict(google._TOKENS, {}, clear=True):
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
                group = [c for c in http.calls if c[1].endswith("googleAds:mutate") and not c[2]["json_body"]["validateOnly"]][-1]
                self.assertEqual(group[2]["json_body"]["mutateOperations"][0]["adGroupOperation"]["create"]["campaign"],
                                 "customers/1234567890/campaigns/22")
                http.calls.clear()
                launch.activate(ws.ctx, path, yes=True)
                enabled = [next(iter(op.values()))["update"] for c in http.calls if c[1].endswith("googleAds:mutate")
                           for op in c[2]["json_body"]["mutateOperations"]]
                self.assertEqual(enabled, [
                    {"resourceName": "customers/1234567890/campaigns/22", "status": "ENABLED"},
                    {"resourceName": "customers/1234567890/adGroups/77", "status": "ENABLED"},
                    {"resourceName": "customers/1234567890/adGroupAds/77~88", "status": "ENABLED"}])
                http.calls.clear()
                launch.rollback(ws.ctx, path, yes=True)
                paused = [next(iter(op.values()))["update"]["resourceName"] for c in http.calls
                          if c[1].endswith("googleAds:mutate") for op in c[2]["json_body"]["mutateOperations"]]
            self.assertEqual(paused, ["customers/1234567890/adGroupAds/77~88", "customers/1234567890/adGroups/77",
                                      "customers/1234567890/campaigns/22"])

    def test_partial_failure_has_no_place_in_a_plan(self):
        plan = json.loads(json.dumps(GOOGLE.PLAN))
        plan["steps"][0]["with"]["partialFailure"] = True
        with helpers.Workspace() as ws:
            with self.assertRaises(Refused):
                launch.load_plan(ws.write_plan(plan))

    def test_a_single_mutate_reports_a_partial_failure(self):
        def handler(method, url, kwargs):
            if url.endswith("googleAds:mutate"):
                return {"partialFailureError": {"code": 3, "message": "Multiple errors in 'details'."},
                        "mutateOperationResponses": [{}, {"campaignResult": {"resourceName": "customers/1234567890/campaigns/22"}}]}
            return GOOGLE.handler(method, url, kwargs)

        with helpers.Workspace() as ws:
            with mock.patch.object(google, "request", helpers.FakeHttp(handler)), mock.patch.dict(google._TOKENS, {}, clear=True):
                out = google.mutate(ws.ctx, GOOGLE.PLAN["steps"][0]["with"], yes=True, partial_failure=True)
            self.assertIn("Multiple errors", out["partial_failure"])


class UnknownOutcome(unittest.TestCase):
    """A write that ended without a clear answer is never sent again on its own."""

    @staticmethod
    def flaky(answer):
        """Fails the first real ad set create with `answer`, then behaves."""
        state = {"failed": False}
        normal = meta_handler()

        def handler(method, url, kwargs):
            data = kwargs.get("data") or {}
            real = method == "POST" and url.endswith("/adsets") and not (isinstance(data, dict) and "execution_options" in data)
            if real and not state["failed"]:
                state["failed"] = True
                if isinstance(answer, BaseException) and not isinstance(answer, Exception):
                    raise answer
                return answer
            return normal(method, url, kwargs)

        return handler

    def test_apply_refuses_to_resend_until_told_which_step(self):
        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            http = helpers.FakeHttp(self.flaky(helpers.http_error(503, {"error": {"code": 2, "message": "unavailable"}})))
            with mock.patch.object(meta, "request", http):
                planned(ws, path)
                with self.assertRaises(AdsError) as first:
                    launch.apply(ws.ctx, path, yes=True)
                self.assertIn("--resend adset", first.exception.hint)
                self.assertEqual(list(launch.uncertain_steps(ws.ctx, "meta-traffic")), ["adset"])
                with self.assertRaises(Refused) as again:
                    launch.apply(ws.ctx, path, yes=True)
                self.assertIn("adset", again.exception.message)
                self.assertIn("--resend adset", again.exception.hint)
                self.assertEqual(len(real_posts(http, "act_111222333/adsets")), 1)
                text, problems = launch.plan(ws.ctx, path)
                self.assertEqual(problems, [])
                self.assertIn("without a clear answer", text)
                with self.assertRaises(Refused):
                    launch.apply(ws.ctx, path, yes=True, resend=["campaign"])
                launch.apply(ws.ctx, path, yes=True, resend=["adset"])
            self.assertEqual(len(real_posts(http, "act_111222333/adsets")), 2)
            self.assertEqual(len(launch.entities(ws.ctx, "meta-traffic")), 5)
            self.assertEqual(launch.uncertain_steps(ws.ctx, "meta-traffic"), {})
            events = [e["event"] for e in read_jsonl(launch.ledger_file(ws.ctx)) if e.get("step") == "adset"]
            self.assertEqual(events, ["sending", "step", "resend", "sending", "step"])

    def test_an_interrupted_send_counts_as_unknown(self):
        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            http = helpers.FakeHttp(self.flaky(KeyboardInterrupt()))
            with mock.patch.object(meta, "request", http):
                planned(ws, path)
                with self.assertRaises(KeyboardInterrupt):
                    launch.apply(ws.ctx, path, yes=True)
                self.assertEqual(list(launch.uncertain_steps(ws.ctx, "meta-traffic")), ["adset"])
                with self.assertRaises(Refused):
                    launch.apply(ws.ctx, path, yes=True)

    def test_an_error_the_toolkit_does_not_know_is_recorded_as_unknown(self):
        for answer in (http.client.IncompleteRead(b""), BrokenPipeError(), helpers.Reply(b"<html>ok</html>")):
            with helpers.Workspace() as ws:
                path = ws.write_plan(meta_plan(ws))
                fake = helpers.FakeHttp(self.flaky(answer))
                with mock.patch.object(meta, "request", fake):
                    planned(ws, path)
                    with self.assertRaises(AdsError) as caught:
                        launch.apply(ws.ctx, path, yes=True)
                self.assertIn("may have created", caught.exception.hint, repr(answer))
                entry = [e for e in read_jsonl(launch.ledger_file(ws.ctx)) if e.get("step") == "adset"][-1]
                self.assertEqual((entry["event"], entry["ok"], entry["uncertain"]), ("step", False, True), repr(answer))

    def test_a_reply_that_is_not_json_is_marked_unknown(self):
        with self.assertRaises(AdsError) as caught:
            core.Response(200, {}, b"<html>ok</html>", "https://graph.facebook.com/v27.0/act_1/adsets").json()
        self.assertTrue(launch._ambiguous(caught.exception))

    def test_a_definite_refusal_can_be_retried_without_resend(self):
        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            with mock.patch.object(meta, "request", helpers.FakeHttp(meta_handler(fail_once="adsets"))):
                planned(ws, path)
                with self.assertRaises(AdsError):
                    launch.apply(ws.ctx, path, yes=True)
                self.assertEqual(launch.uncertain_steps(ws.ctx, "meta-traffic"), {})
                launch.apply(ws.ctx, path, yes=True)
            self.assertEqual(len(launch.entities(ws.ctx, "meta-traffic")), 5)


class PlanAndAccount(unittest.TestCase):
    """What the plan file says and what the account holds may not drift apart unnoticed."""

    def test_a_step_that_was_applied_cannot_be_edited(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            path = ws.write_plan(plan)
            http = helpers.FakeHttp(meta_handler(fail_once="ads"))
            with mock.patch.object(meta, "request", http):
                planned(ws, path)
                with self.assertRaises(AdsError):
                    launch.apply(ws.ctx, path, yes=True)
                plan["steps"][2]["with"]["params"]["daily_budget"] = 500
                plan["budget"]["daily"] = 5
                ws.write_plan(plan)
                text, problems = launch.plan(ws.ctx, path)
                self.assertTrue(any("adset" in p and "changed after it was applied" in p for p in problems), problems)
                with self.assertRaises(Refused):
                    launch.apply(ws.ctx, path, yes=True)

    def test_the_dry_run_covers_account_currency_and_files(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            path = ws.write_plan(plan)
            image = ws.project / "ads" / "creatives" / "hero.png"
            with mock.patch.object(meta, "request", helpers.FakeHttp(meta_handler())):
                planned(ws, path)
                before = launch.fingerprint(ws.ctx, launch.load_plan(path))

                ws.ctx.env["META_AD_ACCOUNT_ID"] = "999000111"
                with self.assertRaises(Refused) as account:
                    launch.apply(ws.ctx, path, yes=True)
                self.assertIn("changed", account.exception.message)
                ws.ctx.env["META_AD_ACCOUNT_ID"] = helpers.FAKE_ENV["META_AD_ACCOUNT_ID"]

                image.write_bytes(b"\x89PNG another picture")
                with self.assertRaises(Refused):
                    launch.apply(ws.ctx, path, yes=True)
                image.write_bytes(b"\x89PNG fake")

                ws.ctx.config["project"]["currency"] = "JPY"
                with self.assertRaises(Refused):
                    launch.apply(ws.ctx, path, yes=True)
                ws.ctx.config["project"]["currency"] = "USD"

                self.assertEqual(launch.fingerprint(ws.ctx, launch.load_plan(path)), before)
                launch.apply(ws.ctx, path, yes=True)
            self.assertNotIn("111222333", launch.ledger_file(ws.ctx).read_text().replace("act_111222333", ""))

    def test_a_removed_plan_needs_a_new_dry_run(self):
        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            http = helpers.FakeHttp(meta_handler())
            with mock.patch.object(meta, "request", http):
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
                launch.rollback(ws.ctx, path, remove=True, yes=True)
                with self.assertRaises(Refused) as caught:
                    launch.apply(ws.ctx, path, yes=True)
                self.assertIn("dry run", caught.exception.message)
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
            self.assertEqual(len(real_posts(http, "act_111222333/campaigns")), 2)

    def test_activation_needs_the_whole_plan_applied(self):
        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            http = helpers.FakeHttp(meta_handler(fail_once="ads"))
            with mock.patch.object(meta, "request", http):
                planned(ws, path)
                with self.assertRaises(AdsError):
                    launch.apply(ws.ctx, path, yes=True)
                http.calls.clear()
                with self.assertRaises(Refused) as caught:
                    launch.activate(ws.ctx, path, yes=True)
                self.assertIn("not fully applied", caught.exception.message)
                self.assertEqual(http.calls, [])

    def test_the_activation_preview_states_the_budget(self):
        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            http = helpers.FakeHttp(meta_handler())
            with mock.patch.object(meta, "request", http):
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
                http.calls.clear()
                text = launch.activate(ws.ctx, path)
            self.assertIn("up to 20 USD per day", text)
            self.assertIn("nothing changed", text)
            self.assertEqual([c for c in http.calls if c[0] != "GET"], [])

    def test_an_applied_step_without_its_hash_counts_as_changed(self):
        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            with mock.patch.object(meta, "request", helpers.FakeHttp(meta_handler())):
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
                ledger = launch.ledger_file(ws.ctx)
                rows = [json.loads(line) for line in ledger.read_text().splitlines()]
                for row in rows:
                    row.pop("sha256", None) if row.get("event") == "step" else None
                ledger.write_text("".join(json.dumps(row) + "\n" for row in rows))
                with self.assertRaises(Refused):
                    launch.activate(ws.ctx, path, yes=True)

    def test_a_plan_name_is_a_plain_file_name(self):
        with helpers.Workspace() as ws:
            for name in ("../escape", "a/b", "with space", ".hidden", "x" * 90):
                plan = dict(meta_plan(ws), name=name)
                target = ws.project / "plan.json"
                target.write_text(json.dumps(plan), encoding="utf-8")
                with self.assertRaises(Refused, msg=name):
                    launch.load_plan(str(target))
            self.assertFalse((ws.project / "ads" / "escape.dry-run.txt").exists())


class Rollback(unittest.TestCase):
    """Pausing and removing go on past an object that fails, and a second run finishes the job."""

    @staticmethod
    def handler(broken):
        normal = meta_handler()

        def handler(method, url, kwargs):
            target = url.rstrip("/").split("/")[-1]
            if target in broken and method in broken[target]:
                answer = broken[target][method]
                if answer.get("once"):
                    del broken[target][method]
                return helpers.http_error(answer["status"], {"error": answer["error"]})
            return normal(method, url, kwargs)

        return handler

    def launched(self, ws, http):
        path = ws.write_plan(meta_plan(ws))
        planned(ws, path)
        launch.apply(ws.ctx, path, yes=True)
        http.calls.clear()
        return path

    def test_remove_goes_on_after_a_failure_and_a_second_run_finishes(self):
        broken = {"s-1": {"DELETE": {"status": 500, "error": {"code": 2, "message": "temporary"}, "once": True}}}
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(self.handler(broken))
            with mock.patch.object(meta, "request", http):
                path = self.launched(ws, http)
                with self.assertRaises(AdsError) as caught:
                    launch.rollback(ws.ctx, path, remove=True, yes=True)
                self.assertIn("s-1", caught.exception.message)
                self.assertEqual([c[1].rsplit("/", 1)[-1] for c in http.calls if c[0] == "DELETE"], ["a-1", "s-1", "c-1"])
                # the creative and the image wait: an ad set that is still there leaves them for the next run
                self.assertEqual([(e["type"], e["id"]) for e in launch.entities(ws.ctx, "meta-traffic")],
                                 [("image", "hash-1"), ("adset", "s-1"), ("creative", "cr-1")])
                with self.assertRaises(Refused):
                    launch.apply(ws.ctx, path, yes=True)
                http.calls.clear()
                launch.rollback(ws.ctx, path, remove=True, yes=True)
                self.assertEqual([c[1].rsplit("/", 1)[-1] for c in http.calls if c[0] == "DELETE"], ["s-1", "cr-1"])
            self.assertEqual(launch.entities(ws.ctx, "meta-traffic"), [])

    def test_an_object_the_platform_no_longer_has_does_not_stop_the_rest(self):
        gone = {"status": 400, "error": {"code": 100, "error_subcode": 33, "message": "Object with ID 'a-1' does not exist"}}
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(self.handler({"a-1": {"POST": dict(gone), "DELETE": dict(gone)}}))
            with mock.patch.object(meta, "request", http):
                path = self.launched(ws, http)
                text = launch.rollback(ws.ctx, path, yes=True)
                self.assertIn("no longer exists", text)
                paused = [c[1].rsplit("/", 1)[-1] for c in http.calls if c[0] == "POST"]
                self.assertEqual(paused, ["a-1", "s-1", "c-1"])
                launch.rollback(ws.ctx, path, remove=True, yes=True)
            self.assertEqual(launch.entities(ws.ctx, "meta-traffic"), [])

    def test_pause_goes_on_after_a_failure_and_reports_it(self):
        broken = {"a-1": {"POST": {"status": 500, "error": {"code": 2, "message": "temporary"}}}}
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(self.handler(broken))
            with mock.patch.object(meta, "request", http):
                path = self.launched(ws, http)
                with self.assertRaises(AdsError) as caught:
                    launch.rollback(ws.ctx, path, yes=True)
            self.assertIn("a-1", caught.exception.message)
            self.assertEqual([c[1].rsplit("/", 1)[-1] for c in http.calls if c[0] == "POST"], ["a-1", "s-1", "c-1"])

    def test_activation_stops_at_the_first_failure(self):
        broken = {"s-1": {"POST": {"status": 400, "error": {"code": 100, "message": "bad"}}}}
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(self.handler(broken))
            with mock.patch.object(meta, "request", http):
                path = self.launched(ws, http)
                with self.assertRaises(AdsError):
                    launch.activate(ws.ctx, path, yes=True)
            self.assertEqual([c[1].rsplit("/", 1)[-1] for c in http.calls if c[0] == "POST"], ["c-1", "s-1"])

    def test_tiktok_keeps_what_was_removed_when_one_object_is_refused(self):
        plan = {"name": "tt-traffic", "platform": "tiktok", "budget": {"daily": 30, "currency": "USD"}, "steps": [
            {"id": "campaign", "do": "tiktok.post", "with": {"path": "campaign/create/", "body": {
                "campaign_name": "T", "budget_mode": "BUDGET_MODE_DAY", "budget": 30, "operation_status": "DISABLE"}}},
            {"id": "adgroup", "do": "tiktok.post", "with": {"path": "adgroup/create/", "body": {
                "campaign_id": "{{campaign.campaign_id}}", "adgroup_name": "G", "operation_status": "DISABLE"}}},
            {"id": "ad", "do": "tiktok.post", "with": {"path": "ad/create/", "body": {
                "adgroup_id": "{{adgroup.adgroup_id}}", "creatives": [{"ad_name": "A", "operation_status": "DISABLE"}]}}}]}
        state = {"refuse": True}

        def handler(method, url, kwargs):
            if url.endswith("adgroup/status/update/") and state["refuse"]:
                return {"code": 0, "data": {"error_list": [{"adgroup_id": "901", "error_message": "busy"}]}}
            return tiktok_handler(method, url, kwargs)

        with helpers.Workspace() as ws:
            path = ws.write_plan(plan)
            http = helpers.FakeHttp(handler)
            with mock.patch.object(tiktok, "request", http):
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
                with self.assertRaises(AdsError):
                    launch.rollback(ws.ctx, path, remove=True, yes=True)
                self.assertEqual([e["id"] for e in launch.entities(ws.ctx, "tt-traffic")], ["901"])
                state["refuse"] = False
                launch.rollback(ws.ctx, path, remove=True, yes=True)
            self.assertEqual(launch.entities(ws.ctx, "tt-traffic"), [])


class Preview(unittest.TestCase):
    """A single command that would switch delivery on can be shown without --yes; sending it needs --activate too."""

    ENABLE = {"mutateOperations": [{"campaignOperation": {"update": {"resourceName": "customers/{customer}/campaigns/5",
                                                                      "status": "ENABLED"}, "updateMask": "status"}}]}

    def test_google(self):
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(GOOGLE.handler)
            with mock.patch.object(google, "request", http), mock.patch.dict(google._TOKENS, {}, clear=True):
                out = google.mutate(ws.ctx, self.ENABLE, preview=True)
                self.assertIn("--activate", out["note"])
                self.assertTrue(http.calls[-1][2]["json_body"]["validateOnly"])
                sent = len(http.calls)
                with self.assertRaises(Refused):
                    google.mutate(ws.ctx, self.ENABLE, yes=True, preview=True)
                with self.assertRaises(Refused):
                    google.mutate(ws.ctx, self.ENABLE)
                self.assertEqual(len(http.calls), sent)

    def test_meta_and_tiktok(self):
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(meta_handler())
            with mock.patch.object(meta, "request", http), mock.patch.object(tiktok, "request", http):
                out = meta.post(ws.ctx, "120000000001", {"status": "ACTIVE"}, preview=True)
                self.assertTrue(out["dry_run"])
                self.assertIn("--activate", out["note"])
                with self.assertRaises(Refused):
                    meta.post(ws.ctx, "120000000001", {"status": "ACTIVE"}, yes=True, preview=True)
                body = {"campaign_ids": ["1"], "operation_status": "ENABLE"}
                out = tiktok.post(ws.ctx, "campaign/status/update/", body, preview=True)
                self.assertIn("--activate", out["note"])
                with self.assertRaises(Refused):
                    tiktok.post(ws.ctx, "campaign/status/update/", body, yes=True, preview=True)
                out = tiktok.post(ws.ctx, "campaign/gmv_max/create/", {"store_id": "1", "budget": 30}, preview=True)
                self.assertIn("--activate", out["note"])
            self.assertEqual(http.calls, [])

    def test_a_plan_step_gets_no_such_leniency(self):
        plan = {"name": "g-on", "platform": "google", "steps": [{"id": "m", "do": "google.mutate", "with": self.ENABLE}]}
        with helpers.Workspace() as ws:
            with mock.patch.object(google, "request", helpers.FakeHttp(GOOGLE.handler)), \
                    mock.patch.dict(google._TOKENS, {}, clear=True):
                text, problems = launch.plan(ws.ctx, ws.write_plan(plan))
            self.assertTrue(any("only creates" in p or "switches" in p for p in problems), problems)


class EquivalentSpellings(unittest.TestCase):
    """Google reads snake_case field names and numeric enum values like the camelCase and named ones: so do the rules."""

    def test_snake_case_bodies_are_judged_like_camel_case(self):
        over = {"mutate_operations": [{"campaign_budget_operation": {"create": {"amount_micros": "999000000"}}}]}
        with self.assertRaises(Refused):
            guards.google_mutate(guards.google_canonical(over), DEFAULT_CONFIG)
        live = {"mutate_operations": [{"campaign_operation": {"create": {"status": "ENABLED"}}}]}
        with self.assertRaises(Refused):
            guards.google_mutate(guards.google_canonical(live), DEFAULT_CONFIG)
        total = {"mutate_operations": [{"campaign_budget_operation": {"create": {"total_amount_micros": "999000000"}}}]}
        with self.assertRaises(Refused):
            guards.google_mutate(guards.google_canonical(total), DEFAULT_CONFIG)
        self.assertEqual(guards.google_canonical({"a_b": [{"c_d_e": 1, "@base64": "x_y.png"}], "fooBar": {"x_y": "kept_value"}}),
                         {"aB": [{"cDE": 1, "@base64": "x_y.png"}], "fooBar": {"xY": "kept_value"}})

    def test_a_status_must_be_written_as_its_name(self):
        for status in (2, "2", "enabled", "Enabled", None, "UNKNOWN"):
            body = {"mutateOperations": [{"campaignOperation": {"update": {"resourceName": "customers/1/campaigns/2",
                                                                            "status": status}, "updateMask": "status"}}]}
            with self.assertRaises(Refused, msg=repr(status)):
                guards.google_mutate(body, DEFAULT_CONFIG)
            self.assertTrue(guards.google_mutate(body, DEFAULT_CONFIG, activate=True)["activates"])
        for status in (3, "paused", None):
            body = {"mutateOperations": [{"campaignOperation": {"create": {"status": status}}}]}
            with self.assertRaises(Refused, msg=repr(status)):
                guards.google_mutate(body, DEFAULT_CONFIG, activate=True)
        paused = {"mutateOperations": [{"adGroupOperation": {"update": {"resourceName": "customers/1/adGroups/2",
                                                                         "status": "PAUSED"}, "updateMask": "status"}}]}
        self.assertFalse(guards.google_mutate(paused, DEFAULT_CONFIG)["activates"])

    def test_the_toolkit_sends_what_it_judged(self):
        body = {"mutate_operations": [{"campaign_criterion_operation": {"create": {
            "campaign": "customers/{customer}/campaigns/22", "negative": True, "keyword": {"text": "x", "match_type": "PHRASE"}}}}],
            "validate_only": False}
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(GOOGLE.handler)
            with mock.patch.object(google, "request", http), mock.patch.dict(google._TOKENS, {}, clear=True):
                google.mutate(ws.ctx, body)
            sent = http.calls[-1][2]["json_body"]
            self.assertTrue(sent["validateOnly"])
            self.assertNotIn("validate_only", sent)
            self.assertIn("campaignCriterionOperation", sent["mutateOperations"][0])
            self.assertEqual(sent["mutateOperations"][0]["campaignCriterionOperation"]["create"]["keyword"]["matchType"], "PHRASE")

    def test_a_snake_case_plan_is_read_like_any_other(self):
        plan = {"name": "g-snake", "platform": "google", "budget": {"daily": 10, "currency": "EUR"}, "steps": [
            {"id": "create", "do": "google.mutate", "with": {"mutate_operations": [
                {"campaign_budget_operation": {"create": {"resource_name": "customers/{customer}/campaignBudgets/-1",
                                                          "amount_micros": "10000000"}}},
                {"campaign_operation": {"create": {"resource_name": "customers/{customer}/campaigns/-2", "status": "PAUSED",
                                                   "campaign_budget": "customers/{customer}/campaignBudgets/-1"}}}]}}]}
        with helpers.Workspace() as ws:
            ws.ctx.config["project"]["currency"] = "EUR"
            path = ws.write_plan(plan)
            self.assertEqual(launch.plan_budgets(ws.ctx, launch.load_plan(path)), (10.0, 0.0))
            with mock.patch.object(google, "request", helpers.FakeHttp(GOOGLE.handler)), \
                    mock.patch.dict(google._TOKENS, {}, clear=True):
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
            self.assertEqual([e["type"] for e in launch.entities(ws.ctx, "g-snake")], ["campaignBudgets", "campaigns"])


class MethodOverride(unittest.TestCase):
    """The Graph API lets a parameter named method turn a GET into a write: no call carries one."""

    def test_reads_cannot_carry_a_method_or_a_query_in_the_path(self):
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(meta_handler())
            with mock.patch.object(meta, "request", http):
                for call in (lambda: meta.get(ws.ctx, "120000000001", {"method": "DELETE"}),
                             lambda: meta.get(ws.ctx, "120000000001", {"METHOD": "post"}),
                             lambda: meta.get(ws.ctx, "act_1/campaigns?method=post&status=ACTIVE&name=x"),
                             lambda: meta.get_all(ws.ctx, "{account}/campaigns?method=post"),
                             lambda: meta.insights(ws.ctx, obj="120000000001?method=delete#"),
                             lambda: meta.insights(ws.ctx, extra={"method": "delete"}),
                             lambda: meta.search(ws.ctx, "adinterest", "x", {"method": "post"}),
                             lambda: meta.post(ws.ctx, "{account}/campaigns", {"status": "PAUSED", "method": "delete"}, yes=True)):
                    with self.assertRaises(Refused):
                        call()
            self.assertEqual(http.calls, [])

    def test_a_tiktok_read_path_is_plain_too(self):
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(tiktok_handler)
            with mock.patch.object(tiktok, "request", http):
                with self.assertRaises(Refused):
                    tiktok.get(ws.ctx, "campaign/get?x=1")
            self.assertEqual(http.calls, [])


class OtherAccounts(unittest.TestCase):
    """A write goes to the account in ads/.env, the one the dry run looked at, and to no other."""

    def test_meta_refuses_another_ad_account_in_the_path(self):
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(meta_handler())
            with mock.patch.object(meta, "request", http):
                with self.assertRaises(Refused):
                    meta.post(ws.ctx, "act_999888777/campaigns", {"name": "x", "status": "PAUSED"}, yes=True)
                with self.assertRaises(Refused):
                    meta.post(ws.ctx, "act_999888777/campaigns", {"name": "x", "status": "PAUSED"})
                meta.post(ws.ctx, "act_111222333/campaigns", {"name": "x", "status": "PAUSED"})
            self.assertEqual([c for c in http.calls if "999888777" in c[1]], [])

    def test_tiktok_refuses_another_advertiser_in_the_body(self):
        body = {"advertiser_id": "555000111", "campaign_name": "x", "operation_status": "DISABLE"}
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(tiktok_handler)
            with mock.patch.object(tiktok, "request", http):
                for yes in (False, True):
                    with self.assertRaises(Refused):
                        tiktok.post(ws.ctx, "campaign/create/", body, yes=yes)
                tiktok.post(ws.ctx, "campaign/create/", dict(body, advertiser_id="777888999"), yes=True)
            self.assertEqual(len(http.calls), 1)


class Uncapped(unittest.TestCase):
    """A campaign the plan creates must be limited by a budget the plan carries, or it could spend without a cap."""

    def test_tiktok_campaign_and_ad_group_without_a_budget(self):
        plan = {"name": "tt-open", "platform": "tiktok", "steps": [
            {"id": "campaign", "do": "tiktok.post", "with": {"path": "campaign/create/", "body": {
                "campaign_name": "T", "budget_mode": "BUDGET_MODE_INFINITE", "operation_status": "DISABLE"}}},
            {"id": "adgroup", "do": "tiktok.post", "with": {"path": "adgroup/create/", "body": {
                "campaign_id": "{{campaign.campaign_id}}", "adgroup_name": "G", "budget_mode": "BUDGET_MODE_INFINITE",
                "budget": 999999, "operation_status": "DISABLE"}}}]}
        with helpers.Workspace() as ws:
            problems = launch.budget_check(ws.ctx, plan)[1]
            self.assertTrue(any("adgroup" in p and "no budget" in p for p in problems), problems)
            plan["steps"][1]["with"]["body"].update({"budget_mode": "BUDGET_MODE_DAY", "budget": 30})
            plan["budget"] = {"daily": 30, "currency": "USD"}
            self.assertEqual(launch.budget_check(ws.ctx, plan)[1], [])

    def test_meta_ad_set_without_a_budget_under_a_campaign_without_one(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            del plan["steps"][2]["with"]["params"]["daily_budget"]
            del plan["budget"]
            problems = launch.budget_check(ws.ctx, plan)[1]
            self.assertTrue(any("adset" in p and "no budget" in p for p in problems), problems)
            plan["steps"][1]["with"]["params"]["daily_budget"] = 2000
            plan["budget"] = {"daily": 20, "currency": "USD"}
            self.assertEqual(launch.budget_check(ws.ctx, plan)[1], [])

    def test_google_campaign_on_a_budget_the_plan_does_not_create(self):
        def plan(budget):
            operations = [{"campaignOperation": {"create": {"resourceName": "customers/{customer}/campaigns/-2",
                                                            "status": "PAUSED", "campaignBudget": budget}}}]
            return {"name": "g-open", "platform": "google", "steps": [{"id": "m", "do": "google.mutate",
                                                                         "with": {"mutateOperations": operations}}]}
        with helpers.Workspace() as ws:
            for budget in ("customers/{customer}/campaignBudgets/777", "customers/{customer}/campaignBudgets/-9", None):
                problems = launch.budget_check(ws.ctx, plan(budget))[1]
                self.assertTrue(any("budget" in p and "does not create" in p for p in problems), (budget, problems))
            self.assertEqual(launch.budget_check(ws.ctx, plan("{{earlier.results.0}}"))[1], [])

    def test_a_ceiling_that_is_not_set_refuses_instead_of_allowing(self):
        for value in (0, None, "", -5, "abc"):
            config = {"guardrails": {"max_daily_budget": value}, "project": {"currency": "USD"}}
            with self.assertRaises(Refused, msg=repr(value)):
                guards.meta_request("POST", "act_1/adsets", {"status": "PAUSED", "daily_budget": 2000}, config)
            with self.assertRaises(Refused, msg=repr(value)):
                guards.tiktok_request("campaign/create/", {"operation_status": "DISABLE", "budget": 30}, config)
            with self.assertRaises(Refused, msg=repr(value)):
                guards.google_mutate({"mutateOperations": [{"campaignBudgetOperation": {"create": {"amountMicros": "1000000"}}}]},
                                     config)
            with helpers.Workspace() as ws:
                ws.ctx.config["guardrails"]["max_daily_budget"] = value
                self.assertTrue(launch.budget_check(ws.ctx, meta_plan(ws))[1], repr(value))


class PlansOnlyCreate(unittest.TestCase):
    """The dry run promises that nothing existing is modified: a plan that would is refused."""

    def google(self, *operations):
        return {"mutateOperations": list(operations)}

    def test_google_updates_and_removals_have_no_place_in_a_plan(self):
        update = {"campaignBudgetOperation": {"update": {"resourceName": "customers/1/campaignBudgets/7",
                                                         "amountMicros": "30000000"}, "updateMask": "amount_micros"}}
        remove = {"campaignOperation": {"remove": "customers/1/campaigns/7"}}
        for operation in (update, remove):
            with self.assertRaises(Refused, msg=str(operation)):
                guards.google_mutate(self.google(operation), DEFAULT_CONFIG, plan=set())
            guards.google_mutate(self.google(operation), DEFAULT_CONFIG)        # a single command may

    def test_google_additions_to_an_existing_campaign_have_no_place_in_a_plan(self):
        keyword = {"adGroupCriterionOperation": {"create": {"adGroup": "customers/1/adGroups/55",
                                                            "keyword": {"text": "x", "matchType": "EXACT"}}}}
        negative = {"campaignCriterionOperation": {"create": {"campaign": "customers/1/campaigns/22", "negative": True,
                                                              "keyword": {"text": "x", "matchType": "PHRASE"}}}}
        for operation in (keyword, negative):
            with self.assertRaises(Refused, msg=str(operation)):
                guards.google_mutate(self.google(operation), DEFAULT_CONFIG, plan=set())
            guards.google_mutate(self.google(operation), DEFAULT_CONFIG)
        # what an earlier step of the same plan created is the plan's own
        guards.google_mutate(self.google(keyword), DEFAULT_CONFIG, plan={"customers/1/adGroups/55"})
        later = {"adGroupCriterionOperation": {"create": {"adGroup": "{{create.results.3}}",
                                                          "keyword": {"text": "x", "matchType": "EXACT"}}}}
        guards.google_mutate(self.google(later), DEFAULT_CONFIG, plan=set())

    def test_meta_and_tiktok_plan_steps_only_create(self):
        for path in ("120000000001", "120000000001/copies", "{pixel}/events", "{account}/campaigns/extra"):
            with self.assertRaises(Refused, msg=path):
                guards.meta_request("POST", path, {"daily_budget": 1000, "status_option": "PAUSED"}, DEFAULT_CONFIG, plan=True)
        guards.meta_request("POST", "120000000001", {"daily_budget": 1000}, DEFAULT_CONFIG)
        for route in ("campaign/update/", "adgroup/budget/update/", "campaign/status/update/", "tt_video/authorize/"):
            with self.assertRaises(Refused, msg=route):
                guards.tiktok_request(route, {"campaign_id": "1", "operation_status": "DISABLE"}, DEFAULT_CONFIG, plan=True)
        guards.tiktok_request("creative/portfolio/create/", {"creative_portfolio_type": "CTA"}, DEFAULT_CONFIG, plan=True)

    def test_a_plan_with_an_update_is_blocked_at_the_dry_run(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            plan["steps"].append({"id": "raise", "do": "meta.post", "with": {"path": "120000000001",
                                                                                "params": {"daily_budget": 4000}}})
            plan["budget"]["daily"] = 60
            ws.ctx.config["guardrails"]["max_daily_budget"] = 100
            with mock.patch.object(meta, "request", helpers.FakeHttp(meta_handler())):
                text, problems = launch.plan(ws.ctx, ws.write_plan(plan))
            self.assertTrue(any("raise" in p and "only creates" in p for p in problems), problems)

    def test_rules_that_act_later_need_the_spend_approval(self):
        rule = {"name": "r", "execution_spec": {"execution_type": "UNPAUSE"}}
        with self.assertRaises(Refused):
            guards.meta_request("POST", "act_1/adrules_library", rule, DEFAULT_CONFIG)
        self.assertTrue(guards.meta_request("POST", "act_1/adrules_library", rule, DEFAULT_CONFIG, activate=True)["activates"])
        with self.assertRaises(Refused):
            guards.tiktok_request("optimizer/rule/create/", {"rules": []}, DEFAULT_CONFIG)
        self.assertTrue(guards.tiktok_request("optimizer/rule/create/", {"rules": []}, DEFAULT_CONFIG, activate=True)["activates"])


class OwnCampaignsOnly(unittest.TestCase):
    """What a plan creates hangs under campaigns the plan creates: nothing joins a campaign, and a budget, from elsewhere."""

    def test_meta_ad_set_and_ad_must_hang_under_the_plan(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            plan["steps"][2]["with"]["params"]["campaign_id"] = "23850000000"
            problems = launch.budget_check(ws.ctx, plan)[1]
            self.assertTrue(any("adset" in p and "does not create" in p for p in problems), problems)
            plan = meta_plan(ws)
            plan["steps"][4]["with"]["params"]["adset_id"] = "23850000001"
            problems = launch.budget_check(ws.ctx, plan)[1]
            self.assertTrue(any("ad " in p and "does not create" in p for p in problems), problems)
            self.assertEqual(launch.budget_check(ws.ctx, meta_plan(ws))[1], [])

    def test_tiktok_ad_group_and_ad_must_hang_under_the_plan(self):
        def plan(campaign_ref, adgroup_ref):
            return {"name": "tt", "platform": "tiktok", "budget": {"daily": 30, "currency": "USD"}, "steps": [
                {"id": "campaign", "do": "tiktok.post", "with": {"path": "campaign/create/", "body": {
                    "campaign_name": "T", "budget_mode": "BUDGET_MODE_DAY", "budget": 30, "operation_status": "DISABLE"}}},
                {"id": "adgroup", "do": "tiktok.post", "with": {"path": "adgroup/create/", "body": {
                    "campaign_id": campaign_ref, "adgroup_name": "G", "operation_status": "DISABLE"}}},
                {"id": "ad", "do": "tiktok.post", "with": {"path": "ad/create/", "body": {
                    "adgroup_id": adgroup_ref, "creatives": [{"ad_name": "A", "operation_status": "DISABLE"}]}}}]}
        with helpers.Workspace() as ws:
            self.assertEqual(launch.budget_check(ws.ctx, plan("{{campaign.campaign_id}}", "{{adgroup.adgroup_id}}"))[1], [])
            problems = launch.budget_check(ws.ctx, plan("1700000000", "{{adgroup.adgroup_id}}"))[1]
            self.assertTrue(any("adgroup" in p and "does not create" in p for p in problems), problems)
            problems = launch.budget_check(ws.ctx, plan("{{campaign.campaign_id}}", "1700000001"))[1]
            self.assertTrue(any("ad " in p and "does not create" in p for p in problems), problems)

    def test_google_plan_adds_nothing_to_a_campaign_it_did_not_create(self):
        for operation in (
                {"adGroupOperation": {"create": {"campaign": "customers/1/campaigns/123", "name": "g", "status": "PAUSED"}}},
                {"assetGroupOperation": {"create": {"campaign": "customers/1/campaigns/123", "name": "a", "status": "PAUSED"}}},
                {"adGroupAdOperation": {"create": {"adGroup": "customers/1/adGroups/55", "status": "PAUSED", "ad": {}}}}):
            with self.assertRaises(Refused, msg=str(operation)):
                guards.google_mutate({"mutateOperations": [operation]}, DEFAULT_CONFIG, plan=set())
            guards.google_mutate({"mutateOperations": [operation]}, DEFAULT_CONFIG)          # a single command may, paused

    def test_a_plan_creates_campaign_parts_and_nothing_else(self):
        for kind in ("conversionActionOperation", "customerNegativeCriterionOperation", "biddingStrategyOperation",
                     "customerOperation", "sharedSetOperation"):
            with self.assertRaises(Refused, msg=kind):
                guards.google_mutate({"mutateOperations": [{kind: {"create": {"name": "x"}}}]}, DEFAULT_CONFIG, plan=set())
            guards.google_mutate({"mutateOperations": [{kind: {"create": {"name": "x"}}}]}, DEFAULT_CONFIG)
        for edge in ("customaudiences", "assigned_users", "adspixels", "insights", "adlabels"):
            with self.assertRaises(Refused, msg=edge):
                guards.meta_request("POST", "{account}/%s" % edge, {"name": "x"}, DEFAULT_CONFIG, plan=True)
            guards.meta_request("POST", "{account}/%s" % edge, {"name": "x"}, DEFAULT_CONFIG)
        for route in ("pixel/create/", "bc/asset/create/", "dmp/custom_audience/create/"):
            with self.assertRaises(Refused, msg=route):
                guards.tiktok_request(route, {"name": "x"}, DEFAULT_CONFIG, plan=True)
            guards.tiktok_request(route, {"name": "x"}, DEFAULT_CONFIG)

    def test_a_budget_of_zero_in_any_spelling_is_no_budget(self):
        for zero in (0, "0", "0.0", "00", " 0 ", "0e0", 0.0):
            plan = {"name": "tt-zero", "platform": "tiktok", "steps": [
                {"id": "campaign", "do": "tiktok.post", "with": {"path": "campaign/create/", "body": {
                    "campaign_name": "T", "budget_mode": "BUDGET_MODE_DAY", "budget": zero, "operation_status": "DISABLE"}}},
                {"id": "adgroup", "do": "tiktok.post", "with": {"path": "adgroup/create/", "body": {
                    "campaign_id": "{{campaign.campaign_id}}", "adgroup_name": "G", "budget_mode": "BUDGET_MODE_INFINITE",
                    "operation_status": "DISABLE"}}}]}
            with helpers.Workspace() as ws:
                problems = launch.budget_check(ws.ctx, plan)[1]
                self.assertTrue(any("no budget" in p for p in problems), (zero, problems))
                meta = meta_plan(ws)
                meta["steps"][1]["with"]["params"]["daily_budget"] = zero
                del meta["steps"][2]["with"]["params"]["daily_budget"]
                del meta["budget"]
                self.assertTrue(any("no budget" in p for p in launch.budget_check(ws.ctx, meta)[1]), zero)

    def test_pointing_a_campaign_at_another_budget_needs_the_spend_approval(self):
        body = {"mutateOperations": [{"campaignOperation": {"update": {
            "resourceName": "customers/1/campaigns/5", "campaignBudget": "customers/1/campaignBudgets/999"},
            "updateMask": "campaign_budget"}}]}
        with self.assertRaises(Refused):
            guards.google_mutate(body, DEFAULT_CONFIG)
        self.assertTrue(guards.google_mutate(body, DEFAULT_CONFIG, activate=True)["activates"])

    def test_the_guard_reads_snake_case_on_its_own(self):
        with self.assertRaises(Refused):
            guards.google_mutate({"mutate_operations": [{"campaign_operation": {"create": {"status": "ENABLED"}}}]}, DEFAULT_CONFIG)

    def test_method_in_any_disguise_is_refused(self):
        for key in ("_method", "__method", "Method ", "%6dethod", "http_method", "X-HTTP-Method-Override"):
            with self.assertRaises(Refused, msg=key):
                guards.meta_read("120000000001", {key: "DELETE"})


class LedgerAndPlan(unittest.TestCase):
    """What the ledger holds and what the plan lists stay the same set of steps."""

    def test_a_renamed_applied_step_is_not_applied_a_second_time(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            path = ws.write_plan(plan)
            http = helpers.FakeHttp(meta_handler())
            with mock.patch.object(meta, "request", http):
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
                plan["steps"][-1]["id"] = "ad_v2"
                ws.write_plan(plan)
                text, problems = launch.plan(ws.ctx, path)
                self.assertTrue(any("ad" in p and "no longer in the plan" in p for p in problems), problems)
                with self.assertRaises(Refused):
                    launch.apply(ws.ctx, path, yes=True)
                with self.assertRaises(Refused) as caught:
                    launch.activate(ws.ctx, path, yes=True)
                self.assertIn("no longer in the plan", caught.exception.message)
                self.assertEqual(len([c for c in real_posts(http, "") if c[1].endswith("/ads")]), 1)
                launch.rollback(ws.ctx, path, yes=True)         # stopping still reaches everything that was created

    def test_removal_does_not_forget_an_unknown_outcome(self):
        state = {"failed": False}
        normal = meta_handler()

        def handler(method, url, kwargs):       # the image is applied, then the campaign create gets no clear answer
            data = kwargs.get("data") or {}
            real = method == "POST" and url.endswith("/campaigns") and not (isinstance(data, dict) and "execution_options" in data)
            if real and not state["failed"]:
                state["failed"] = True
                return helpers.http_error(503, {"error": {"code": 2, "message": "unavailable"}})
            return normal(method, url, kwargs)

        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            http = helpers.FakeHttp(handler)
            with mock.patch.object(meta, "request", http):
                planned(ws, path)
                with self.assertRaises(AdsError):
                    launch.apply(ws.ctx, path, yes=True)
                self.assertEqual(list(launch.uncertain_steps(ws.ctx, "meta-traffic")), ["campaign"])
                text = launch.rollback(ws.ctx, path, remove=True, yes=True)
                self.assertIn("campaign", text)
                self.assertIn("without a clear answer", text)
                self.assertEqual(list(launch.uncertain_steps(ws.ctx, "meta-traffic")), ["campaign"])
                planned(ws, path)
                with self.assertRaises(Refused) as caught:
                    launch.apply(ws.ctx, path, yes=True)
                self.assertIn("--resend campaign", caught.exception.hint)
                launch.apply(ws.ctx, path, yes=True, resend=["campaign"])
            self.assertEqual(len(launch.entities(ws.ctx, "meta-traffic")), 5)

    def test_activation_checks_the_budget_again(self):
        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            http = helpers.FakeHttp(meta_handler())
            with mock.patch.object(meta, "request", http):
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
                http.calls.clear()
                ws.ctx.config["guardrails"]["max_daily_budget"] = 5
                with self.assertRaises(Refused):
                    launch.activate(ws.ctx, path, yes=True)
                ws.ctx.config["guardrails"]["max_daily_budget"] = 50
                ws.ctx.config["project"]["currency"] = "JPY"
                with self.assertRaises(Refused):
                    launch.activate(ws.ctx, path, yes=True)
            self.assertEqual(http.calls, [])

    def test_a_refresh_token_that_fails_is_not_an_unknown_outcome(self):
        def handler(method, url, kwargs):
            if "oauth2.googleapis.com" in url and state["apply"]:
                return helpers.http_error(400, {"error": "invalid_grant"})
            return GOOGLE.handler(method, url, kwargs)

        state = {"apply": False}
        with helpers.Workspace() as ws:
            ws.ctx.config["project"]["currency"] = "EUR"
            path = ws.write_plan(GOOGLE.PLAN)
            with mock.patch.object(google, "request", helpers.FakeHttp(handler)), mock.patch.dict(google._TOKENS, {}, clear=True):
                planned(ws, path)
                google._TOKENS.clear()
                state["apply"] = True
                with self.assertRaises(AdsError) as caught:
                    launch.apply(ws.ctx, path, yes=True)
            self.assertNotIn("may have created", caught.exception.hint)
            self.assertEqual(launch.uncertain_steps(ws.ctx, "g-search"), {})


class CommandLine(unittest.TestCase):
    def test_flags_cannot_be_abbreviated(self):
        parser = ads.build_parser()
        for argv in (["launch", "apply", "--file", "p.json", "--y"], ["launch", "activate", "--file", "p.json", "--ye"],
                     ["google", "mutate", "--file", "ops.json", "--yes", "--act"],
                     ["launch", "rollback", "--file", "p.json", "--rem", "--yes"]):
            with self.assertRaises(SystemExit, msg=" ".join(argv)), contextlib.redirect_stderr(io.StringIO()):
                parser.parse_args(argv)
        self.assertTrue(parser.parse_args(["launch", "apply", "--file", "p.json", "--yes", "--resend", "adset"]).yes)


if __name__ == "__main__":
    unittest.main()
