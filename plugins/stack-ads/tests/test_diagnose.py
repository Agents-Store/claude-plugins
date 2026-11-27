"""launch diagnose: a read-only audit of why an approved, switched-on plan shows nothing."""
import contextlib
import datetime
import io
import json
import unittest
from unittest import mock

import helpers  # first: it puts the toolkit on the import path
import ads  # noqa: E402
import test_launch  # noqa: E402
from adskit import diagnose, google, launch, meta, tiktok
from adskit.core import append_jsonl

UTC = datetime.timezone.utc


def ago(hours):
    return (datetime.datetime.now(UTC) - datetime.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")


def meta_time(hours_from_now):
    """Meta writes times as 2026-11-26T10:00:00+0200."""
    moment = datetime.datetime.now(UTC) + datetime.timedelta(hours=hours_from_now)
    return moment.astimezone(datetime.timezone(datetime.timedelta(hours=2))).strftime("%Y-%m-%dT%H:%M:%S%z")


def record(ws, plan, entities, activated=None, paused=None):
    """Write what launch apply and launch activate would have left in the ledger."""
    ledger = launch.ledger_file(ws.ctx)
    for index, step in enumerate(plan["steps"]):
        append_jsonl(ledger, {"ts": ago(50), "event": "step", "plan": plan["name"], "platform": plan["platform"],
                              "step": step["id"], "do": step["do"], "ok": True, "result": {},
                              "entities": entities if index == 0 else []})
    if activated is not None:
        append_jsonl(ledger, {"ts": ago(activated), "event": "activate", "plan": plan["name"], "platform": plan["platform"]})
    if paused is not None:
        append_jsonl(ledger, {"ts": ago(paused), "event": "pause", "plan": plan["name"], "platform": plan["platform"]})


def states(findings, check=None, level=None):
    return [(f["level"], f["check"], f["state"]) for f in findings
            if (check is None or f["check"] == check) and (level is None or f["level"] == level)]


def one(findings, check, level=None):
    found = [f for f in findings if f["check"] == check and (level is None or f["level"] == level)]
    assert len(found) == 1, "%s: %r" % (check, found)
    return found[0]


def text_of(findings):
    return json.dumps(findings)


def read_only(testcase, calls, allowed=("GET",)):
    bad = [(method, url) for method, url, _ in calls if method not in allowed]
    testcase.assertEqual(bad, [])


# ── Meta ─────────────────────────────────────────────────────────────────

def meta_world(**over):
    world = {
        "account": {"name": "Example Brand Ads", "account_status": 1, "disable_reason": 0, "currency": "USD",
                    "amount_spent": "1200", "spend_cap": "0",
                    "funding_source_details": {"id": "555", "type": 1, "display_string": "Visa ending 0000"}},
        "ads_volume": {"data": [{"ads_running_or_in_review_count": 1}]},
        "campaign": {"id": "c-1", "name": "Example campaign", "status": "ACTIVE", "effective_status": "ACTIVE"},
        "adset": {"id": "s-1", "name": "Example set", "status": "ACTIVE", "effective_status": "ACTIVE",
                  "start_time": meta_time(-30), "daily_budget": "500", "budget_remaining": "500"},
        "ad": {"id": "a-1", "name": "Example ad", "status": "ACTIVE", "effective_status": "ACTIVE"},
        "creative": {"id": "cr-1", "name": "Example creative", "status": "ACTIVE"},
        "estimate": {"data": [{"estimate_mau_lower_bound": 49000000, "estimate_mau_upper_bound": 57600000,
                               "estimate_ready": True}]},
        "insights": {"data": []},
        "by_platform": {"data": []},
        "fail": {},
    }
    world.update(over)
    return world


def meta_handler(world):
    def handler(method, url, kwargs):
        tail = url.rstrip("/").split("/")
        last, before = tail[-1], tail[-2] if len(tail) > 1 else ""
        if world["fail"].get(last):
            return helpers.http_error(400, {"error": {"code": 100, "message": "Tried accessing nonexisting field"}})
        if last == "act_111222333":
            return world["account"]
        if last == "ads_volume":
            return world["ads_volume"]
        if last == "delivery_estimate":
            return world["estimate"]
        if last == "insights":
            return world["by_platform"] if "publisher_platform" in str((kwargs.get("params") or {}).get("breakdowns")) \
                else world["insights"]
        return {"c-1": world["campaign"], "s-1": world["adset"], "a-1": world["ad"], "cr-1": world["creative"]}[last]

    return handler


META_ENTITIES = [{"platform": "meta", "type": "campaign", "id": "c-1"}, {"platform": "meta", "type": "adset", "id": "s-1"},
                 {"platform": "meta", "type": "creative", "id": "cr-1"}, {"platform": "meta", "type": "ad", "id": "a-1"}]


class MetaDiagnose(unittest.TestCase):
    def run_meta(self, world=None, activated=8, paused=None):
        world = world or meta_world()
        with helpers.Workspace() as ws:
            plan = test_launch.meta_plan(ws)
            path = ws.write_plan(plan)
            record(ws, plan, META_ENTITIES, activated=activated, paused=paused)
            http = helpers.FakeHttp(meta_handler(world))
            with mock.patch.object(meta, "request", http):
                findings = diagnose.diagnose(ws.ctx, path)
        self.http = http
        return findings

    def test_approved_and_on_with_no_impressions_after_eight_hours_fails_with_next_steps(self):
        findings = self.run_meta(activated=8)
        alarm = one(findings, "delivery")
        self.assertEqual(alarm["state"], "fail")
        self.assertIn("8", alarm["detail"])
        self.assertIn("Delivery column", alarm["next"])
        self.assertIn("48", alarm["next"])
        self.assertIn("Facebook", alarm["next"])
        self.assertIn("Instagram", alarm["next"])
        # nothing else is wrong: every object read back as fine
        self.assertEqual([f for f in findings if f["state"] == "fail" and f["check"] != "delivery"], [])
        for key in ("level", "object", "check", "state", "detail", "next"):
            self.assertIn(key, alarm)

    def test_the_same_picture_two_hours_after_activation_only_warns_too_early(self):
        alarm = one(self.run_meta(activated=2), "delivery")
        self.assertEqual(alarm["state"], "warn")
        self.assertIn("too early", alarm["detail"])

    def test_impressions_clear_the_alarm_and_are_split_by_platform(self):
        world = meta_world(insights={"data": [{"impressions": "420", "spend": "1.50"}]},
                           by_platform={"data": [{"publisher_platform": "facebook", "impressions": "400"},
                                                 {"publisher_platform": "instagram", "impressions": "20"}]})
        findings = self.run_meta(world)
        delivery = one(findings, "delivery")
        self.assertEqual(delivery["state"], "ok")
        self.assertIn("420", delivery["detail"])
        self.assertIn("facebook 400", delivery["detail"])
        self.assertEqual([f for f in findings if f["state"] == "fail"], [])

    def test_a_disapproved_ad_names_the_reasons_from_its_review_feedback(self):
        world = meta_world(ad={"id": "a-1", "name": "Example ad", "status": "ACTIVE", "effective_status": "DISAPPROVED",
                               "ad_review_feedback": {"global": {"Personal attributes": "The ad asserts a personal attribute"}}})
        findings = self.run_meta(world)
        status = one(findings, "status", "ad")
        self.assertEqual(status["state"], "fail")
        self.assertIn("DISAPPROVED", status["detail"])
        review = one(findings, "review", "ad")
        self.assertEqual(review["state"], "fail")
        self.assertIn("Personal attributes", review["detail"])
        self.assertTrue(review["next"])
        self.assertEqual(one(findings, "delivery")["state"], "fail")

    def test_an_ad_with_issues_shows_issues_info(self):
        world = meta_world(adset={"id": "s-1", "name": "Example set", "status": "ACTIVE", "effective_status": "WITH_ISSUES",
                                  "start_time": meta_time(-30), "daily_budget": "500", "budget_remaining": "500",
                                  "issues_info": [{"level": "AD_SET", "error_code": 1487851,
                                                   "error_summary": "Audience too small",
                                                   "error_message": "Widen the targeting"}]})
        findings = self.run_meta(world)
        issues = one(findings, "issues", "adset")
        self.assertEqual(issues["state"], "warn")
        self.assertIn("Audience too small", issues["detail"])
        self.assertIn("Widen the targeting", issues["detail"])

    def test_recommendations_and_failed_delivery_checks_are_reported_when_present(self):
        world = meta_world(adset={"id": "s-1", "name": "Example set", "status": "ACTIVE", "effective_status": "ACTIVE",
                                  "start_time": meta_time(-30), "daily_budget": "500", "budget_remaining": "500",
                                  "failed_delivery_checks": [{"summary": "Targeting", "description": "No eligible audience",
                                                              "check_name": "TARGETING"}],
                                  "recommendations": [{"title": "Raise the budget", "message": "Low budget", "importance": "HIGH"}]})
        findings = self.run_meta(world)
        self.assertEqual(one(findings, "delivery checks", "adset")["state"], "fail")
        self.assertIn("No eligible audience", one(findings, "delivery checks", "adset")["detail"])
        self.assertIn("Raise the budget", one(findings, "recommendations", "adset")["detail"])

    def test_a_schedule_that_has_not_started_is_named_with_its_start(self):
        world = meta_world(adset={"id": "s-1", "name": "Example set", "status": "ACTIVE", "effective_status": "ACTIVE",
                                  "start_time": meta_time(20), "daily_budget": "500", "budget_remaining": "500"})
        findings = self.run_meta(world)
        schedule = one(findings, "schedule", "adset")
        self.assertEqual(schedule["state"], "fail")
        self.assertIn("not started", schedule["detail"])
        self.assertIn("20", schedule["detail"] + schedule["next"])
        # the schedule is the reason, so the audit does not call it the unexplained alarm
        self.assertIn("schedule", one(findings, "delivery")["detail"].lower() + one(findings, "delivery")["next"].lower())

    def test_an_ended_schedule_fails(self):
        world = meta_world(adset={"id": "s-1", "name": "Example set", "status": "ACTIVE", "effective_status": "ACTIVE",
                                  "start_time": meta_time(-90), "end_time": meta_time(-3), "daily_budget": "500",
                                  "budget_remaining": "500"})
        self.assertIn("ended", one(self.run_meta(world), "schedule", "adset")["detail"])

    def test_a_paused_parent_is_reported_on_the_parent_and_the_child(self):
        world = meta_world(campaign={"id": "c-1", "name": "Example campaign", "status": "PAUSED", "effective_status": "PAUSED"},
                           adset={"id": "s-1", "name": "Example set", "status": "ACTIVE",
                                  "effective_status": "CAMPAIGN_PAUSED", "start_time": meta_time(-30),
                                  "daily_budget": "500", "budget_remaining": "500"},
                           ad={"id": "a-1", "name": "Example ad", "status": "ACTIVE", "effective_status": "CAMPAIGN_PAUSED"})
        findings = self.run_meta(world)
        self.assertEqual(one(findings, "status", "campaign")["state"], "fail")
        self.assertIn("paused", one(findings, "status", "ad")["detail"].lower())
        self.assertEqual(one(findings, "status", "ad")["state"], "fail")

    def test_a_spend_cap_that_is_reached_fails(self):
        world = meta_world(account=dict(meta_world()["account"], spend_cap="5000", amount_spent="5000"))
        cap = one(self.run_meta(world), "spend cap", "account")
        self.assertEqual(cap["state"], "fail")
        self.assertIn("spend cap", cap["detail"])

    def test_a_spend_cap_that_is_near_warns_and_none_is_fine(self):
        near = meta_world(account=dict(meta_world()["account"], spend_cap="5000", amount_spent="4700"))
        self.assertEqual(one(self.run_meta(near), "spend cap", "account")["state"], "warn")
        self.assertEqual(one(self.run_meta(), "spend cap", "account")["state"], "ok")

    def test_an_account_without_a_funding_source_fails(self):
        account = {k: v for k, v in meta_world()["account"].items() if k != "funding_source_details"}
        funding = one(self.run_meta(meta_world(account=account)), "funding", "account")
        self.assertEqual(funding["state"], "fail")
        self.assertIn("payment", funding["detail"])

    def test_a_disabled_account_fails_with_the_reason(self):
        account = dict(meta_world()["account"], account_status=2, disable_reason=1)
        status = one(self.run_meta(meta_world(account=account)), "status", "account")
        self.assertEqual(status["state"], "fail")
        self.assertIn("disabled", status["detail"])
        self.assertIn("disable_reason 1", status["detail"])

    def test_the_account_count_of_running_ads_is_checked_against_the_active_ad(self):
        world = meta_world(ads_volume={"data": [{"ads_running_or_in_review_count": 0}]})
        volume = one(self.run_meta(world), "ads running", "account")
        self.assertEqual(volume["state"], "warn")
        self.assertIn("0", volume["detail"])
        self.assertEqual(one(self.run_meta(), "ads running", "account")["state"], "ok")

    def test_an_audience_of_zero_fails(self):
        world = meta_world(estimate={"data": [{"estimate_mau_lower_bound": 0, "estimate_mau_upper_bound": 0,
                                               "estimate_ready": True}]})
        audience = one(self.run_meta(world), "audience", "adset")
        self.assertEqual(audience["state"], "fail")

    def test_a_normal_audience_is_ok(self):
        audience = one(self.run_meta(), "audience", "adset")
        self.assertEqual(audience["state"], "ok")
        self.assertIn("49", audience["detail"])

    def test_a_used_up_daily_budget_warns(self):
        world = meta_world(adset={"id": "s-1", "name": "Example set", "status": "ACTIVE", "effective_status": "ACTIVE",
                                  "start_time": meta_time(-30), "daily_budget": "500", "budget_remaining": "0"})
        self.assertEqual(one(self.run_meta(world), "budget", "adset")["state"], "warn")

    def test_a_creative_that_is_not_active_is_reported(self):
        world = meta_world(creative={"id": "cr-1", "name": "Example creative", "status": "DELETED"})
        self.assertEqual(one(self.run_meta(world), "status", "creative")["state"], "fail")

    def test_a_read_that_fails_becomes_a_warning_and_the_rest_goes_on(self):
        findings = self.run_meta(meta_world(fail={"ads_volume": True, "delivery_estimate": True}))
        volume = one(findings, "ads running", "account")
        self.assertEqual(volume["state"], "warn")
        self.assertIn("nonexisting field", volume["detail"])
        self.assertEqual(one(findings, "audience", "adset")["state"], "warn")
        self.assertEqual(one(findings, "status", "ad")["state"], "ok")

    def test_a_plan_that_was_never_activated_says_so_and_asks_for_no_insights(self):
        with helpers.Workspace() as ws:
            plan = test_launch.meta_plan(ws)
            path = ws.write_plan(plan)
            record(ws, plan, META_ENTITIES)
            http = helpers.FakeHttp(meta_handler(meta_world(
                campaign={"id": "c-1", "name": "Example campaign", "status": "PAUSED", "effective_status": "PAUSED"})))
            with mock.patch.object(meta, "request", http):
                findings = diagnose.diagnose(ws.ctx, path)
        self.assertEqual(one(findings, "activation", "plan")["state"], "warn")
        self.assertEqual(http.sent("insights"), [])
        self.assertEqual([f for f in findings if f["check"] == "delivery"], [])

    def test_a_pause_after_the_activation_is_not_counted_as_running(self):
        findings = self.run_meta(activated=30, paused=2)
        self.assertIn("paused", one(findings, "activation", "plan")["detail"])
        self.assertEqual([f for f in findings if f["check"] == "delivery"], [])

    def test_the_hours_run_from_the_activation_after_the_last_pause(self):
        with helpers.Workspace() as ws:
            plan = test_launch.meta_plan(ws)
            record(ws, plan, META_ENTITIES, activated=70, paused=60)
            append_jsonl(launch.ledger_file(ws.ctx), {"ts": ago(5), "event": "activate", "plan": plan["name"], "platform": "meta"})
            info = diagnose.activation(ws.ctx, plan["name"])
        self.assertAlmostEqual(info["hours"], 5, delta=0.05)

    def test_insights_start_at_the_activation_date(self):
        self.run_meta(activated=8)
        sent = self.http.sent("c-1/insights")
        self.assertTrue(sent)
        window = json.loads(sent[0][2]["params"]["time_range"])
        since = (datetime.datetime.now(UTC) - datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
        self.assertEqual(window["since"], since)

    def test_only_reads_are_sent(self):
        self.run_meta()
        self.assertGreaterEqual(len(self.http.calls), 8)
        read_only(self, self.http.calls)


# ── Google ───────────────────────────────────────────────────────────────

CAMPAIGN = "customers/1234567890/campaigns/22"


def google_world(**over):
    world = {
        "billing": [{"billingSetup": {"status": "APPROVED"}}],
        "budget": [{"accountBudget": {"status": "APPROVED"}}],
        "customer": [{"customer": {"status": "ENABLED", "currencyCode": "EUR"}}],
        "campaign": [{"campaign": {"name": "Example search", "status": "ENABLED", "primaryStatus": "ELIGIBLE",
                                   "primaryStatusReasons": [], "servingStatus": "SERVING",
                                   "startDate": "2020-01-01", "endDate": "2037-12-30"},
                      "campaignBudget": {"amountMicros": "10000000"}}],
        "ads": [{"adGroupAd": {"status": "ENABLED", "ad": {"id": "301", "name": "Example ad"},
                               "policySummary": {"approvalStatus": "APPROVED", "reviewStatus": "REVIEWED"},
                               "primaryStatus": "ELIGIBLE", "primaryStatusReasons": []},
                 "adGroup": {"name": "Example group"}}],
        "metrics": [{"metrics": {"impressions": "0", "clicks": "0", "costMicros": "0"}}],
    }
    world.update(over)
    return world


def google_handler(world, seen=None):
    def handler(method, url, kwargs):
        if "oauth2.googleapis.com" in url:
            return {"access_token": "access-example"}
        query = kwargs["json_body"]["query"]
        if seen is not None:
            seen.append(query)
        for marker, key in (("FROM billing_setup", "billing"), ("FROM account_budget", "budget"),
                            ("FROM customer", "customer"), ("FROM ad_group_ad", "ads")):
            if marker in query:
                return {"results": world[key]}
        if "metrics.impressions" in query:
            return {"results": world["metrics"]}
        if "FROM campaign" in query:
            return {"results": world["campaign"]}
        raise AssertionError(query)

    return handler


GOOGLE_ENTITIES = [{"platform": "google", "type": "campaignBudgets", "id": "customers/1234567890/campaignBudgets/11"},
                   {"platform": "google", "type": "campaigns", "id": CAMPAIGN}]


class GoogleDiagnose(unittest.TestCase):
    def run_google(self, world=None, activated=8):
        world = world or google_world()
        self.queries = []
        with helpers.Workspace() as ws:
            ws.ctx.config["project"]["currency"] = "EUR"
            plan = dict(test_launch.GoogleLaunch.PLAN)
            path = ws.write_plan(plan)
            record(ws, plan, GOOGLE_ENTITIES, activated=activated)
            http = helpers.FakeHttp(google_handler(world, self.queries))
            with mock.patch.object(google, "request", http), mock.patch.dict(google._TOKENS, {}, clear=True):
                findings = diagnose.diagnose(ws.ctx, path)
        self.http = http
        return findings

    def with_campaign(self, **fields):
        campaign = dict(google_world()["campaign"][0]["campaign"], **fields)
        return google_world(campaign=[{"campaign": campaign, "campaignBudget": {"amountMicros": "10000000"}}])

    def test_a_learning_campaign_maps_the_reason_to_a_sentence_and_a_next_step(self):
        world = self.with_campaign(primaryStatus="LEARNING", primaryStatusReasons=["BIDDING_STRATEGY_LEARNING"])
        status = one(self.run_google(world), "primary status", "campaign")
        self.assertEqual(status["state"], "warn")
        self.assertIn("learning", status["detail"].lower())
        self.assertIn("BIDDING_STRATEGY_LEARNING", status["detail"])
        self.assertTrue(status["next"])

    def test_known_reasons_each_get_their_own_sentence(self):
        for reason in ("BUDGET_CONSTRAINED", "MOST_ADS_UNDER_REVIEW", "HAS_ADS_DISAPPROVED"):
            world = self.with_campaign(primaryStatus="LIMITED", primaryStatusReasons=[reason])
            status = one(self.run_google(world), "primary status", "campaign")
            self.assertNotEqual(status["detail"], reason)
            self.assertIn(reason, status["detail"])
            self.assertTrue(status["next"], reason)

    def test_an_unknown_reason_is_shown_as_it_comes(self):
        world = self.with_campaign(primaryStatus="NOT_ELIGIBLE", primaryStatusReasons=["SOMETHING_NEW_FROM_GOOGLE"])
        status = one(self.run_google(world), "primary status", "campaign")
        self.assertEqual(status["state"], "fail")
        self.assertIn("SOMETHING_NEW_FROM_GOOGLE", status["detail"])

    def test_a_paused_campaign_fails(self):
        world = self.with_campaign(status="PAUSED", primaryStatus="PAUSED", primaryStatusReasons=["CAMPAIGN_PAUSED"])
        self.assertEqual(one(self.run_google(world), "status", "campaign")["state"], "fail")

    def test_a_campaign_that_starts_later_fails_on_the_schedule(self):
        later = (datetime.datetime.now(UTC) + datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        schedule = one(self.run_google(self.with_campaign(startDate=later)), "schedule", "campaign")
        self.assertEqual(schedule["state"], "fail")
        self.assertIn(later, schedule["detail"])

    def test_a_disapproved_ad_names_its_policy_topic(self):
        ad = dict(google_world()["ads"][0])
        ad["adGroupAd"] = dict(ad["adGroupAd"], policySummary={
            "approvalStatus": "DISAPPROVED", "reviewStatus": "REVIEWED",
            "policyTopicEntries": [{"topic": "TRADEMARKS_IN_AD_TEXT", "type": "PROHIBITED"}]})
        review = one(self.run_google(google_world(ads=[ad])), "review", "ad")
        self.assertEqual(review["state"], "fail")
        self.assertIn("TRADEMARKS_IN_AD_TEXT", review["detail"])

    def test_an_ad_under_review_warns(self):
        ad = dict(google_world()["ads"][0])
        ad["adGroupAd"] = dict(ad["adGroupAd"], policySummary={"approvalStatus": "UNDER_REVIEW", "reviewStatus": "UNDER_REVIEW"})
        self.assertEqual(one(self.run_google(google_world(ads=[ad])), "review", "ad")["state"], "warn")

    def test_a_billing_setup_that_is_not_approved_fails(self):
        world = google_world(billing=[{"billingSetup": {"status": "PENDING"}}])
        billing = one(self.run_google(world), "billing", "account")
        self.assertEqual(billing["state"], "fail")
        self.assertIn("PENDING", billing["detail"])

    def test_an_account_without_any_billing_setup_fails(self):
        self.assertEqual(one(self.run_google(google_world(billing=[])), "billing", "account")["state"], "fail")

    def test_an_account_budget_that_is_not_approved_warns_and_none_is_fine(self):
        ended = google_world(budget=[{"accountBudget": {"status": "ENDED"}}])
        self.assertEqual(one(self.run_google(ended), "account budget", "account")["state"], "warn")
        self.assertEqual(one(self.run_google(google_world(budget=[])), "account budget", "account")["state"], "ok")

    def test_an_ad_that_google_made_itself_is_normal(self):
        extra = {"adGroupAd": {"status": "ENABLED", "ad": {"id": "302", "name": "auto-generated video ad"},
                               "policySummary": {"approvalStatus": "APPROVED", "reviewStatus": "REVIEWED"},
                               "primaryStatus": "ELIGIBLE", "primaryStatusReasons": []}, "adGroup": {"name": "Example group"}}
        world = google_world(ads=google_world()["ads"] + [extra])
        findings = self.run_google(world)
        self.assertEqual(len([f for f in findings if f["level"] == "ad" and f["check"] == "review"]), 2)
        self.assertEqual([f for f in findings if f["level"] == "ad" and f["state"] != "ok"], [])

    def test_no_impressions_after_eight_hours_with_everything_approved_fails(self):
        alarm = one(self.run_google(), "delivery")
        self.assertEqual(alarm["state"], "fail")
        self.assertTrue(alarm["next"])

    def test_the_same_two_hours_after_activation_warns(self):
        alarm = one(self.run_google(activated=2), "delivery")
        self.assertEqual(alarm["state"], "warn")
        self.assertIn("too early", alarm["detail"])

    def test_impressions_are_summed_and_clear_the_alarm(self):
        world = google_world(metrics=[{"metrics": {"impressions": "1200", "clicks": "30", "costMicros": "4500000"}}])
        delivery = one(self.run_google(world), "delivery")
        self.assertEqual(delivery["state"], "ok")
        self.assertIn("1200", delivery["detail"])

    def test_metrics_use_explicit_dates_from_the_activation_to_today(self):
        self.run_google(activated=8)
        query = next(q for q in self.queries if "metrics.impressions" in q)
        today = datetime.datetime.now(UTC).strftime("%Y-%m-%d")
        since = (datetime.datetime.now(UTC) - datetime.timedelta(hours=8)).strftime("%Y-%m-%d")
        self.assertIn("BETWEEN '%s' AND '%s'" % (since, today), query)
        self.assertNotIn("LAST_7_DAYS", query)

    def test_only_search_requests_are_sent(self):
        self.run_google()
        self.assertTrue(self.queries)
        for method, url, _ in self.http.calls:
            self.assertTrue(url.endswith("googleAds:search") or "oauth2.googleapis.com" in url, url)


# ── TikTok ───────────────────────────────────────────────────────────────

TIKTOK_PLAN = {"name": "tt-diagnose", "platform": "tiktok", "budget": {"daily": 30, "currency": "USD"}, "steps": [
    {"id": "campaign", "do": "tiktok.post", "with": {"path": "campaign/create/", "body": {
        "campaign_name": "T", "objective_type": "TRAFFIC", "budget_mode": "BUDGET_MODE_DAY", "budget": 30,
        "operation_status": "DISABLE"}}}]}
TIKTOK_ENTITIES = [{"platform": "tiktok", "type": "campaign", "id": "900", "smart_plus": False},
                   {"platform": "tiktok", "type": "adgroup", "id": "901", "smart_plus": False},
                   {"platform": "tiktok", "type": "ad", "id": "902", "smart_plus": False}]


def tiktok_world(**over):
    world = {
        "advertiser": {"list": [{"name": "Example Advertiser", "status": "STATUS_ENABLE", "balance": 120.5, "currency": "USD"}]},
        "campaign": {"list": [{"campaign_id": "900", "campaign_name": "Example campaign", "operation_status": "ENABLE",
                               "secondary_status": "CAMPAIGN_STATUS_ENABLE"}]},
        "adgroup": {"list": [{"adgroup_id": "901", "adgroup_name": "Example group", "operation_status": "ENABLE",
                              "secondary_status": "ADGROUP_STATUS_DELIVERY_OK"}]},
        "ad": {"list": [{"ad_id": "902", "ad_name": "Example ad", "operation_status": "ENABLE",
                         "secondary_status": "AD_STATUS_DELIVERY_OK"}]},
        "review": {"list": []},
        "report": {"list": [{"dimensions": {"campaign_id": "900"}, "metrics": {"impressions": "0", "spend": "0.00"}}],
                   "page_info": {"total_page": 1}},
    }
    world.update(over)
    return world


def tiktok_handler(world):
    def handler(method, url, kwargs):
        route = url.split("v1.3/")[1]
        key = {"advertiser/info/": "advertiser", "campaign/get/": "campaign", "adgroup/get/": "adgroup", "ad/get/": "ad",
               "ad/review_info/": "review", "report/integrated/get/": "report"}[route]
        return {"code": 0, "data": world[key]}

    return handler


class TikTokDiagnose(unittest.TestCase):
    def run_tiktok(self, world=None, activated=8):
        with helpers.Workspace() as ws:
            path = ws.write_plan(TIKTOK_PLAN)
            record(ws, TIKTOK_PLAN, TIKTOK_ENTITIES, activated=activated)
            http = helpers.FakeHttp(tiktok_handler(world or tiktok_world()))
            with mock.patch.object(tiktok, "request", http):
                findings = diagnose.diagnose(ws.ctx, path)
        self.http = http
        return findings

    def with_ad(self, **fields):
        ad = dict(tiktok_world()["ad"]["list"][0], **fields)
        return {"list": [ad]}

    def test_a_review_that_denied_the_ad_shows_the_reasons(self):
        world = tiktok_world(ad=self.with_ad(secondary_status="AD_STATUS_AUDIT_DENY"),
                             review={"list": [{"ad_id": "902", "reject_reason": ["Misleading claim in the video"]}]})
        findings = self.run_tiktok(world)
        status = one(findings, "status", "ad")
        self.assertEqual(status["state"], "fail")
        self.assertIn("AUDIT_DENY", status["detail"])
        review = one(findings, "review", "ad")
        self.assertIn("Misleading claim", review["detail"])
        self.assertTrue(review["next"])

    def test_an_ad_in_review_warns_and_reads_no_reasons(self):
        findings = self.run_tiktok(tiktok_world(ad=self.with_ad(secondary_status="AD_STATUS_AUDIT")))
        self.assertEqual(one(findings, "status", "ad")["state"], "warn")
        self.assertEqual(self.http.sent("review_info"), [])

    def test_an_ad_group_that_has_not_started_fails(self):
        group = {"list": [dict(tiktok_world()["adgroup"]["list"][0], secondary_status="ADGROUP_STATUS_NOT_START")]}
        status = one(self.run_tiktok(tiktok_world(adgroup=group)), "status", "adgroup")
        self.assertEqual(status["state"], "fail")
        self.assertIn("NOT_START", status["detail"])

    def test_a_campaign_over_its_budget_fails(self):
        campaign = {"list": [dict(tiktok_world()["campaign"]["list"][0], secondary_status="CAMPAIGN_STATUS_BUDGET_EXCEED")]}
        self.assertEqual(one(self.run_tiktok(tiktok_world(campaign=campaign)), "status", "campaign")["state"], "fail")

    def test_a_disabled_ad_fails(self):
        ad = self.with_ad(operation_status="DISABLE", secondary_status="AD_STATUS_DISABLE")
        self.assertEqual(one(self.run_tiktok(tiktok_world(ad=ad)), "status", "ad")["state"], "fail")

    def test_an_advertiser_without_balance_fails(self):
        advertiser = {"list": [{"name": "Example Advertiser", "status": "STATUS_ENABLE", "balance": 0, "currency": "USD"}]}
        balance = one(self.run_tiktok(tiktok_world(advertiser=advertiser)), "balance", "account")
        self.assertEqual(balance["state"], "fail")

    def test_an_advertiser_that_is_not_enabled_fails(self):
        advertiser = {"list": [{"name": "Example Advertiser", "status": "STATUS_LIMIT", "balance": 50, "currency": "USD"}]}
        self.assertEqual(one(self.run_tiktok(tiktok_world(advertiser=advertiser)), "status", "account")["state"], "fail")

    def test_no_impressions_after_eight_hours_fails_and_two_hours_warns(self):
        self.assertEqual(one(self.run_tiktok(activated=8), "delivery")["state"], "fail")
        self.assertEqual(one(self.run_tiktok(activated=2), "delivery")["state"], "warn")

    def test_impressions_in_the_report_clear_the_alarm(self):
        report = {"list": [{"dimensions": {"campaign_id": "900"}, "metrics": {"impressions": "5300", "spend": "7.10"}}],
                  "page_info": {"total_page": 1}}
        delivery = one(self.run_tiktok(tiktok_world(report=report)), "delivery")
        self.assertEqual(delivery["state"], "ok")
        self.assertIn("5300", delivery["detail"])

    def test_only_reads_are_sent(self):
        self.run_tiktok()
        self.assertGreaterEqual(len(self.http.calls), 5)
        read_only(self, self.http.calls)


# ── the command ──────────────────────────────────────────────────────────

class Command(unittest.TestCase):
    def run_command(self, *flags):
        out, err = io.StringIO(), io.StringIO()
        with helpers.Workspace() as ws:
            plan = test_launch.meta_plan(ws)
            path = ws.write_plan(plan)
            record(ws, plan, META_ENTITIES, activated=8)
            http = helpers.FakeHttp(meta_handler(meta_world()))
            with mock.patch.object(meta, "request", http), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = ads.main(["--dir", str(ws.project / "ads"), "launch", "diagnose", "--file", path, *flags])
        read_only(self, http.calls)
        return code, out.getvalue(), err.getvalue()

    def test_the_table_ends_with_one_verdict_line(self):
        code, out, err = self.run_command()
        self.assertEqual((code, err), (0, ""))
        lines = out.rstrip("\n").split("\n")
        self.assertTrue(lines[-1].startswith("verdict:"), lines[-1])
        self.assertEqual(len([l for l in lines if l.startswith("verdict:")]), 1)
        self.assertIn("FAIL", lines[-1])
        self.assertIn("Delivery column", out)

    def test_json_prints_the_findings_list(self):
        code, out, _ = self.run_command("--json")
        self.assertEqual(code, 0)
        rows = json.loads(out)
        self.assertTrue(rows)
        self.assertTrue(all(set(r) == {"level", "object", "check", "state", "detail", "next"} for r in rows))
        self.assertTrue(all(r["state"] in ("ok", "warn", "fail") for r in rows))

    def test_the_verdict_names_a_clean_plan(self):
        findings = [{"level": "ad", "object": "ad 1", "check": "status", "state": "ok", "detail": "ACTIVE", "next": ""}]
        self.assertIn("OK", diagnose.verdict(findings))
        findings.append(dict(findings[0], state="warn", check="x", next="look"))
        self.assertIn("WARN", diagnose.verdict(findings))

    def test_the_command_has_no_yes_flag(self):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            ads.build_parser().parse_args(["launch", "diagnose", "--file", "x.json", "--yes"])


if __name__ == "__main__":
    unittest.main()
