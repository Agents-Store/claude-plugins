import json
import unittest
from unittest import mock

import helpers
from adskit import google, launch, meta, tiktok
from adskit.core import AdsError, Refused, read_jsonl

BLOCKS = ("TARGET", "PRECHECK", "CHANGE", "BACKUP", "IMPACT", "VALIDATE", "ROLLBACK", "APPLY")


def meta_plan(ws):
    image = ws.project / "ads" / "creatives" / "hero.png"
    image.write_bytes(b"\x89PNG fake")
    return {
        "name": "meta-traffic", "platform": "meta", "objective": "Traffic to the landing page",
        "budget": {"daily": 20, "currency": "USD"}, "landing_url": "https://example.com/",
        "steps": [
            {"id": "image", "do": "meta.upload_image", "with": {"file": str(image)}},
            {"id": "campaign", "do": "meta.post", "with": {"path": "{account}/campaigns", "params": {
                "name": "Traffic", "objective": "OUTCOME_TRAFFIC", "status": "PAUSED", "special_ad_categories": []}}},
            {"id": "adset", "do": "meta.post", "with": {"path": "{account}/adsets", "params": {
                "name": "Set", "campaign_id": "{{campaign.id}}", "daily_budget": 2000, "status": "PAUSED",
                "targeting": {"geo_locations": {"countries": ["DE"]}}}}},
            {"id": "creative", "do": "meta.post", "with": {"path": "{account}/adcreatives", "params": {
                "name": "Creative", "object_story_spec": {"page_id": "{page}", "link_data": {
                    "image_hash": "{{image.hash}}", "link": "https://example.com/", "message": "Hello"}}}}},
            {"id": "ad", "do": "meta.post", "with": {"path": "{account}/ads", "params": {
                "name": "Ad", "adset_id": "{{adset.id}}", "creative": {"creative_id": "{{creative.id}}"}, "status": "PAUSED"}}},
        ],
    }


def meta_handler(fail_once=None):
    state = {"failed": False}

    def handler(method, url, kwargs):
        data = kwargs.get("data") or {}
        if method == "GET":
            return {"id": "1", "name": "Tester", "account_status": 1, "currency": "USD"}
        if method == "DELETE":
            return {"success": True}
        edge = url.rstrip("/").split("/")[-1]
        if isinstance(data, dict) and "execution_options" in data:
            return {"success": True}
        if fail_once == edge and not state["failed"]:
            state["failed"] = True
            return helpers.http_error(400, {"error": {"code": 100, "error_subcode": 1815946, "message": "Invalid parameter"}})
        if edge == "adimages":
            return {"images": {"hero.png": {"hash": "hash-1", "url": "https://example.com/i.png"}}}
        ids = {"campaigns": "c-1", "adsets": "s-1", "adcreatives": "cr-1", "ads": "a-1"}
        return {"id": ids[edge]} if edge in ids else {"success": True}

    return handler


def real_posts(http, fragment):
    """POST calls that really write: the dry run's validate_only calls are left out."""
    return [c for c in http.calls if c[0] == "POST" and fragment in c[1]
            and not (isinstance(c[2].get("data"), dict) and "execution_options" in c[2]["data"])]


def planned(ws, path):
    """A clean dry run, which launch apply demands."""
    text, problems = launch.plan(ws.ctx, path)
    assert problems == [], problems
    return text


class PlanFile(unittest.TestCase):
    def test_rejects_bad_plans(self):
        with helpers.Workspace() as ws:
            for plan in ({"name": "x", "platform": "meta"},
                         {"name": "x", "platform": "other", "steps": [{"id": "a", "do": "meta.post"}]},
                         {"name": "x", "platform": "meta", "steps": [{"id": "a", "do": "google.mutate"}]},
                         {"name": "x", "platform": "meta", "steps": [{"id": "a", "do": "meta.post"}, {"id": "a", "do": "meta.post"}]}):
                with self.assertRaises(Refused):
                    launch.load_plan(ws.write_plan(dict(plan, name="bad")) if plan.get("name") else ws.write_plan(plan))

    def test_resolve_references_and_base64(self):
        with helpers.Workspace() as ws:
            logo = ws.project / "logo.bin"
            logo.write_bytes(b"abc")
            results = {"up": {"hash": "h1"}, "g": {"results": ["customers/1/campaigns/9"]}}
            value = {"a": "{{up.hash}}", "b": "x-{{ g.results.0 }}", "c": {"@base64": str(logo)}, "d": [1, "{{up.hash}}"]}
            self.assertEqual(launch.resolve(value, results),
                             {"a": "h1", "b": "x-customers/1/campaigns/9", "c": "YWJj", "d": [1, "h1"]})
            with self.assertRaises(launch.Unresolved):
                launch.resolve("{{later.id}}", results)
            with self.assertRaises(Refused):
                launch.resolve("{{up.missing}}", results)

    def test_whole_value_reference_keeps_its_type(self):
        self.assertEqual(launch.resolve("{{s.ids}}", {"s": {"ids": [1, 2]}}), [1, 2])


class MetaLaunch(unittest.TestCase):
    def test_dry_run_prints_eight_blocks_and_sends_no_write(self):
        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            http = helpers.FakeHttp(meta_handler())
            with mock.patch.object(meta, "request", http):
                text, problems = launch.plan(ws.ctx, path)
            self.assertEqual(problems, [])
            positions = [text.index("\n%s\n" % b if b != "TARGET" else "TARGET\n") for b in BLOCKS]
            self.assertEqual(positions, sorted(positions))
            self.assertIn("launch rollback --file", text)
            writes = [c for c in http.calls if c[0] != "GET" and "execution_options" not in (c[2].get("data") or {})]
            self.assertEqual(writes, [])
            self.assertIn("validated by Meta", text)
            self.assertIn("needs {{campaign.id}}", text)
            self.assertTrue((ws.ctx.ws / "launch" / "meta-traffic.dry-run.txt").is_file())

    def test_dry_run_reports_guard_violations(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            plan["steps"][1]["with"]["params"]["status"] = "ACTIVE"
            plan["steps"][2]["with"]["params"]["daily_budget"] = 900000
            with mock.patch.object(meta, "request", helpers.FakeHttp(meta_handler())):
                text, problems = launch.plan(ws.ctx, ws.write_plan(plan))
            joined = " | ".join(problems)
            self.assertIn("campaigns would be created with status 'ACTIVE'", joined)
            self.assertIn("add up to 9000", joined)
            self.assertIn("declares 20", joined)
            self.assertIn("blocked", text)

    def test_plan_budget_is_the_sum_of_what_the_steps_carry(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            second = json.loads(json.dumps(plan["steps"][2]))
            second["id"], second["with"]["params"]["daily_budget"] = "adset2", 4000
            plan["steps"].insert(3, second)
            self.assertEqual(launch.plan_budgets(ws.ctx, plan), (60.0, 0.0))
            with mock.patch.object(meta, "request", helpers.FakeHttp(meta_handler())):
                text, problems = launch.plan(ws.ctx, ws.write_plan(plan))
            # each ad set is under the ceiling of 50, the plan as a whole is not
            self.assertTrue(any("add up to 60" in p and "ceiling of 50" in p for p in problems), problems)
            self.assertTrue(any("declares 20" in p for p in problems), problems)
            plan["budget"]["daily"] = 60
            ws.ctx.config["guardrails"]["max_daily_budget"] = 100
            with mock.patch.object(meta, "request", helpers.FakeHttp(meta_handler())):
                text, problems = launch.plan(ws.ctx, ws.write_plan(plan))
            self.assertEqual(problems, [])
            self.assertIn("up to 60 USD per day", text)

    def test_a_campaign_budget_caps_the_ad_sets_below_it(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            plan["steps"][1]["with"]["params"]["daily_budget"] = 3000
            self.assertEqual(launch.plan_budgets(ws.ctx, plan), (30.0, 0.0))

    def test_lifetime_budgets_are_off_until_the_owner_sets_a_ceiling(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            params = plan["steps"][2]["with"]["params"]
            del params["daily_budget"]
            params["lifetime_budget"] = 30000
            plan["budget"] = {"total": 300, "currency": "USD"}
            with mock.patch.object(meta, "request", helpers.FakeHttp(meta_handler())):
                text, problems = launch.plan(ws.ctx, ws.write_plan(plan))
            self.assertTrue(any("lifetime" in p and "switched off" in p for p in problems), problems)
            ws.ctx.config["guardrails"]["max_total_budget"] = 500
            with mock.patch.object(meta, "request", helpers.FakeHttp(meta_handler())):
                text, problems = launch.plan(ws.ctx, ws.write_plan(plan))
            self.assertEqual(problems, [])
            self.assertIn("300 USD in total", text)
            plan["budget"] = {"daily": 20, "currency": "USD"}
            with mock.patch.object(meta, "request", helpers.FakeHttp(meta_handler())):
                text, problems = launch.plan(ws.ctx, ws.write_plan(plan))
            self.assertTrue(any("declares no" in p and "total" in p for p in problems), problems)

    def test_apply_needs_yes(self):
        with helpers.Workspace() as ws:
            with self.assertRaises(Refused):
                launch.apply(ws.ctx, ws.write_plan(meta_plan(ws)))

    def test_apply_demands_a_clean_dry_run_of_the_same_content(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            path = ws.write_plan(plan)
            http = helpers.FakeHttp(meta_handler())
            with mock.patch.object(meta, "request", http):
                with self.assertRaises(Refused) as never_planned:
                    launch.apply(ws.ctx, path, yes=True)
                self.assertIn("launch plan", never_planned.exception.hint)
                planned(ws, path)
                plan["steps"][2]["with"]["params"]["targeting"] = {"geo_locations": {"countries": ["DE", "AT"]}}
                ws.write_plan(plan)
                with self.assertRaises(Refused) as changed:
                    launch.apply(ws.ctx, path, yes=True)
                self.assertIn("changed", changed.exception.message)
                self.assertEqual(real_posts(http, "act_111222333"), [])
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
            self.assertEqual(len(launch.entities(ws.ctx, "meta-traffic")), 4)

    def test_a_dry_run_with_problems_does_not_unlock_apply(self):
        with helpers.Workspace() as ws:
            plan = meta_plan(ws)
            plan["steps"][1]["with"]["params"]["status"] = "ACTIVE"
            path = ws.write_plan(plan)
            with mock.patch.object(meta, "request", helpers.FakeHttp(meta_handler())):
                launch.plan(ws.ctx, path)
                with self.assertRaises(Refused):
                    launch.apply(ws.ctx, path, yes=True)

    def test_apply_creates_everything_and_fills_references(self):
        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            http = helpers.FakeHttp(meta_handler())
            with mock.patch.object(meta, "request", http):
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
            adset = real_posts(http, "act_111222333/adsets")[0][2]["data"]
            self.assertEqual(adset["campaign_id"], "c-1")
            creative = real_posts(http, "adcreatives")[0][2]["data"]
            spec = json.loads(creative["object_story_spec"])
            self.assertEqual(spec["page_id"], "444555666")
            self.assertEqual(spec["link_data"]["image_hash"], "hash-1")
            ad = [c for c in real_posts(http, "") if c[1].endswith("/ads")][0][2]["data"]
            self.assertEqual(json.loads(ad["creative"]), {"creative_id": "cr-1"})
            kinds = [(e["type"], e["id"]) for e in launch.entities(ws.ctx, "meta-traffic")]
            self.assertEqual(kinds, [("campaign", "c-1"), ("adset", "s-1"), ("creative", "cr-1"), ("ad", "a-1")])

    def test_second_apply_is_a_no_op(self):
        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            with mock.patch.object(meta, "request", helpers.FakeHttp(meta_handler())):
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
            again = helpers.FakeHttp(meta_handler())
            with mock.patch.object(meta, "request", again):
                log = launch.apply(ws.ctx, path, yes=True)
            self.assertEqual(again.calls, [])
            self.assertEqual(log.count("skip"), 5)

    def test_failed_step_stops_and_a_rerun_resumes(self):
        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            http = helpers.FakeHttp(meta_handler(fail_once="adsets"))
            with mock.patch.object(meta, "request", http):
                planned(ws, path)
                with self.assertRaises(AdsError) as caught:
                    launch.apply(ws.ctx, path, yes=True)
                self.assertIn("adset", caught.exception.message)
                self.assertIn("launch rollback", caught.exception.hint)
                self.assertIn("launch plan", caught.exception.hint)
                self.assertNotIn("may have created", caught.exception.hint)
                self.assertEqual([c for c in real_posts(http, "") if c[1].endswith("/ads")], [])
                launch.apply(ws.ctx, path, yes=True)
            self.assertEqual(len(real_posts(http, "act_111222333/campaigns")), 1)
            entries = [e for e in read_jsonl(launch.ledger_file(ws.ctx)) if e.get("event") == "step"]
            self.assertEqual([e["ok"] for e in entries if e["step"] == "adset"], [False, True])
            self.assertEqual([e.get("uncertain") for e in entries if e["step"] == "adset"], [False, None])
            self.assertNotIn("meta-token-example", (launch.ledger_file(ws.ctx)).read_text())

    def test_a_write_without_a_clear_answer_is_marked_uncertain(self):
        def handler(method, url, kwargs):
            data = kwargs.get("data") or {}
            if method == "POST" and url.endswith("/adsets") and "execution_options" not in data:
                return helpers.http_error(503, {"error": {"code": 2, "message": "Service temporarily unavailable"}})
            return meta_handler()(method, url, kwargs)

        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            with mock.patch.object(meta, "request", helpers.FakeHttp(handler)):
                planned(ws, path)
                with self.assertRaises(AdsError) as caught:
                    launch.apply(ws.ctx, path, yes=True)
            self.assertIn("may have created", caught.exception.hint)
            entry = [e for e in read_jsonl(launch.ledger_file(ws.ctx)) if e.get("step") == "adset"][-1]
            self.assertEqual((entry["ok"], entry["uncertain"]), (False, True))

    def test_activate_then_pause_then_remove(self):
        with helpers.Workspace() as ws:
            path = ws.write_plan(meta_plan(ws))
            http = helpers.FakeHttp(meta_handler())
            with mock.patch.object(meta, "request", http):
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
                http.calls.clear()
                self.assertIn("nothing changed", launch.activate(ws.ctx, path))
                self.assertEqual([c for c in http.calls if c[0] == "POST" and "execution_options" not in c[2]["data"]], [])
                http.calls.clear()
                launch.activate(ws.ctx, path, yes=True)
                order = [(c[1].rsplit("/", 1)[-1], c[2]["data"]["status"]) for c in http.calls if c[0] == "POST"]
                self.assertEqual(order, [("c-1", "ACTIVE"), ("s-1", "ACTIVE"), ("a-1", "ACTIVE")])
                http.calls.clear()
                launch.rollback(ws.ctx, path, yes=True)
                order = [(c[1].rsplit("/", 1)[-1], c[2]["data"]["status"]) for c in http.calls if c[0] == "POST"]
                self.assertEqual(order, [("a-1", "PAUSED"), ("s-1", "PAUSED"), ("c-1", "PAUSED")])
                self.assertEqual(len(launch.entities(ws.ctx, "meta-traffic")), 4)
                http.calls.clear()
                launch.rollback(ws.ctx, path, remove=True, yes=True)
                self.assertEqual([c[0] for c in http.calls], ["DELETE", "DELETE", "DELETE"])
            self.assertEqual(launch.entities(ws.ctx, "meta-traffic"), [])


class GoogleLaunch(unittest.TestCase):
    PLAN = {"name": "g-search", "platform": "google", "budget": {"daily": 10, "currency": "EUR"}, "steps": [
        {"id": "create", "do": "google.mutate", "with": {"mutateOperations": [
            {"campaignBudgetOperation": {"create": {"resourceName": "customers/{customer}/campaignBudgets/-1",
                                                    "amountMicros": "10000000"}}},
            {"campaignOperation": {"create": {"resourceName": "customers/{customer}/campaigns/-2", "status": "PAUSED",
                                              "campaignBudget": "customers/{customer}/campaignBudgets/-1"}}}]}}]}

    @staticmethod
    def handler(method, url, kwargs):
        if "oauth2.googleapis.com" in url:
            return {"access_token": "access-example"}
        if url.endswith("listAccessibleCustomers"):
            return {"resourceNames": ["customers/1234567890"]}
        if url.endswith("googleAds:search"):
            return {"results": [{"customer": {"id": "1234567890", "currencyCode": "EUR", "status": "ENABLED"}}]}
        body = kwargs["json_body"]
        if body.get("validateOnly"):
            return {}
        return {"mutateOperationResponses": [{"campaignBudgetResult": {"resourceName": "customers/1234567890/campaignBudgets/11"}},
                                             {"campaignResult": {"resourceName": "customers/1234567890/campaigns/22"}}]}

    def test_plan_validates_and_apply_records_resource_names(self):
        with helpers.Workspace() as ws:
            ws.ctx.config["project"]["currency"] = "EUR"
            path = ws.write_plan(self.PLAN)
            http = helpers.FakeHttp(self.handler)
            with mock.patch.object(google, "request", http), mock.patch.dict(google._TOKENS, {}, clear=True):
                text, problems = launch.plan(ws.ctx, path)
                self.assertEqual(problems, [])
                self.assertIn("validated by Google Ads", text)
                validate = [c for c in http.calls if c[1].endswith("googleAds:mutate")]
                self.assertTrue(all(c[2]["json_body"]["validateOnly"] for c in validate))
                self.assertIn("customers/1234567890/campaigns/-2", json.dumps(validate[0][2]["json_body"]))
                self.assertEqual(validate[0][2]["headers"]["Authorization"], "Bearer access-example")
                launch.apply(ws.ctx, path, yes=True)
                launch.activate(ws.ctx, path, yes=True)
            names = [e["id"] for e in launch.entities(ws.ctx, "g-search")]
            self.assertEqual(names, ["customers/1234567890/campaignBudgets/11", "customers/1234567890/campaigns/22"])
            enable = http.calls[-1][2]["json_body"]
            self.assertFalse(enable["validateOnly"])
            self.assertEqual(enable["mutateOperations"], [{"campaignOperation": {
                "update": {"resourceName": "customers/1234567890/campaigns/22", "status": "ENABLED"}, "updateMask": "status"}}])

    def test_single_mutate_fills_the_customer_placeholder(self):
        body = {"mutateOperations": [{"campaignCriterionOperation": {"create": {
            "campaign": "customers/{customer}/campaigns/22", "negative": True,
            "keyword": {"text": "vorlage", "matchType": "PHRASE"}}}}]}
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(self.handler)
            with mock.patch.object(google, "request", http), mock.patch.dict(google._TOKENS, {}, clear=True):
                out = google.mutate(ws.ctx, body)
            sent = http.calls[-1][2]["json_body"]
            self.assertTrue(out["validated_only"] and sent["validateOnly"])
            self.assertEqual(sent["mutateOperations"][0]["campaignCriterionOperation"]["create"]["campaign"],
                             "customers/1234567890/campaigns/22")

    def test_call_fills_the_customer_placeholder_and_reads_without_yes(self):
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(self.handler)
            with mock.patch.object(google, "request", http), mock.patch.dict(google._TOKENS, {}, clear=True):
                google.call(ws.ctx, "POST", "customers/{customer}:generateKeywordForecastMetrics",
                            {"customer": "customers/{customer}"})
                sent = http.calls[-1]
                self.assertTrue(sent[1].endswith("customers/1234567890:generateKeywordForecastMetrics"))
                self.assertEqual(sent[2]["json_body"], {"customer": "customers/1234567890"})
                dry = google.call(ws.ctx, "POST", "customers/{customer}:uploadClickConversions", {"conversions": []})
                self.assertTrue(dry["dry_run"])
                self.assertEqual(dry["would_send"]["path"], "customers/1234567890:uploadClickConversions")
                self.assertEqual(http.calls[-1], sent)

    def test_validation_errors_name_the_field(self):
        failure = helpers.http_error(400, {"error": {"code": 400, "status": "INVALID_ARGUMENT", "details": [{"errors": [{
            "errorCode": {"campaignError": "DUPLICATE_CAMPAIGN_NAME"}, "message": "Name is in use.",
            "location": {"fieldPathElements": [{"fieldName": "mutate_operations", "index": 1}, {"fieldName": "create"},
                                               {"fieldName": "name"}]}}]}]}})

        def handler(method, url, kwargs):
            if url.endswith("googleAds:mutate"):
                return failure
            return self.handler(method, url, kwargs)

        with helpers.Workspace() as ws:
            ws.ctx.config["project"]["currency"] = "EUR"
            with mock.patch.object(google, "request", helpers.FakeHttp(handler)), mock.patch.dict(google._TOKENS, {}, clear=True):
                text, problems = launch.plan(ws.ctx, ws.write_plan(self.PLAN))
            self.assertEqual(len(problems), 1)
            self.assertIn("mutate_operations[1].create.name", text)
            self.assertIn("DUPLICATE_CAMPAIGN_NAME", text)


class TikTokLaunch(unittest.TestCase):
    def test_apply_and_activate(self):
        plan = {"name": "tt-traffic", "platform": "tiktok", "budget": {"daily": 30, "currency": "USD"}, "steps": [
            {"id": "campaign", "do": "tiktok.post", "with": {"path": "campaign/create/", "body": {
                "campaign_name": "T", "objective_type": "TRAFFIC", "budget_mode": "BUDGET_MODE_DAY", "budget": 30,
                "operation_status": "DISABLE"}}},
            {"id": "adgroup", "do": "tiktok.post", "with": {"path": "adgroup/create/", "body": {
                "campaign_id": "{{campaign.campaign_id}}", "adgroup_name": "G", "budget_mode": "BUDGET_MODE_DAY",
                "budget": 30, "operation_status": "DISABLE"}}},
            {"id": "ad", "do": "tiktok.post", "with": {"path": "ad/create/", "body": {
                "adgroup_id": "{{adgroup.adgroup_id}}", "creatives": [{"ad_name": "A", "operation_status": "DISABLE"}]}}}]}

        def handler(method, url, kwargs):
            if method == "GET":
                return {"code": 0, "data": {"list": [{"name": "Adv", "currency": "USD", "status": "STATUS_ENABLE"}]}}
            if url.endswith("campaign/create/"):
                return {"code": 0, "data": {"campaign_id": "900"}}
            if url.endswith("adgroup/create/"):
                return {"code": 0, "data": {"adgroup_id": "901"}}
            if url.endswith("ad/create/"):
                return {"code": 0, "data": {"ad_ids": ["902"]}}
            return {"code": 0, "data": {}}

        with helpers.Workspace() as ws:
            path = ws.write_plan(plan)
            http = helpers.FakeHttp(handler)
            with mock.patch.object(tiktok, "request", http):
                text, problems = launch.plan(ws.ctx, path)
                self.assertEqual(problems, [])
                self.assertEqual([c for c in http.calls if c[0] == "POST"], [])
                launch.apply(ws.ctx, path, yes=True)
                group = http.sent("adgroup/create/")[0][2]["json_body"]
                self.assertEqual((group["campaign_id"], group["advertiser_id"]), ("900", "777888999"))
                self.assertEqual(http.sent("campaign/create/")[0][2]["headers"]["Access-Token"], "tiktok-token-example")
                http.calls.clear()
                launch.activate(ws.ctx, path, yes=True)
                sent = [(c[1].split("v1.3/")[1], c[2]["json_body"]["operation_status"]) for c in http.calls]
                self.assertEqual(sent, [("campaign/status/update/", "ENABLE"), ("adgroup/status/update/", "ENABLE"),
                                        ("ad/status/update/", "ENABLE")])
                self.assertEqual(http.sent("ad/status/update/")[0][2]["json_body"]["ad_ids"], ["902"])
                http.calls.clear()
                launch.rollback(ws.ctx, path, yes=True)
            sent = [(c[1].split("v1.3/")[1], c[2]["json_body"]["operation_status"]) for c in http.calls]
            self.assertEqual(sent, [("ad/status/update/", "DISABLE"), ("adgroup/status/update/", "DISABLE"),
                                    ("campaign/status/update/", "DISABLE")])

    def test_smart_plus_is_switched_through_its_own_endpoints(self):
        plan = {"name": "tt-smart", "platform": "tiktok", "budget": {"daily": 30, "currency": "USD"}, "steps": [
            {"id": "campaign", "do": "tiktok.post", "with": {"path": "smart_plus/campaign/create/", "body": {
                "request_id": "1001", "campaign_name": "S", "objective_type": "WEB_CONVERSIONS", "budget": 30,
                "operation_status": "DISABLE"}}},
            {"id": "adgroup", "do": "tiktok.post", "with": {"path": "smart_plus/adgroup/create/", "body": {
                "request_id": "1002", "campaign_id": "{{campaign.campaign_id}}", "operation_status": "DISABLE"}}},
            {"id": "ad", "do": "tiktok.post", "with": {"path": "smart_plus/ad/create/", "body": {
                "adgroup_id": "{{adgroup.adgroup_id}}", "operation_status": "DISABLE"}}}]}
        created = {"smart_plus/campaign/create/": {"campaign_id": "910"}, "smart_plus/adgroup/create/": {"adgroup_id": "911"},
                   "smart_plus/ad/create/": {"smart_plus_ad_id": "912"}}

        def handler(method, url, kwargs):
            if method == "GET":
                return {"code": 0, "data": {"list": [{"name": "Adv", "currency": "USD", "status": "STATUS_ENABLE"}]}}
            return {"code": 0, "data": created.get(url.split("v1.3/")[1], {})}

        with helpers.Workspace() as ws:
            path = ws.write_plan(plan)
            http = helpers.FakeHttp(handler)
            with mock.patch.object(tiktok, "request", http):
                planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
                http.calls.clear()
                launch.activate(ws.ctx, path, yes=True)
                bodies = [(c[1].split("v1.3/")[1], {k: v for k, v in c[2]["json_body"].items() if k != "advertiser_id"})
                          for c in http.calls]
                self.assertEqual(bodies, [
                    ("smart_plus/campaign/status/update/", {"campaign_ids": ["910"], "operation_status": "ENABLE"}),
                    ("smart_plus/adgroup/status/update/", {"adgroup_ids": ["911"], "operation_status": "ENABLE"}),
                    ("smart_plus/ad/status/update/", {"smart_plus_ad_ids": ["912"], "operation_status": "ENABLE"})])
                http.calls.clear()
                launch.rollback(ws.ctx, path, remove=True, yes=True)
            sent = [(c[1].split("v1.3/")[1], c[2]["json_body"]["operation_status"]) for c in http.calls]
            self.assertEqual(sent, [("smart_plus/ad/status/update/", "DELETE"), ("smart_plus/adgroup/status/update/", "DELETE"),
                                    ("smart_plus/campaign/status/update/", "DELETE")])

    def test_status_change_refused_for_one_object_is_an_error(self):
        # TikTok answers code 0 and names the objects it did not change in error_list.
        def handler(method, url, kwargs):
            return {"code": 0, "data": {"adgroup_list": [], "error_list": [
                {"adgroup_id": "901", "error_message": "Adgroup does not exist."}]}}

        with helpers.Workspace() as ws:
            with mock.patch.object(tiktok, "request", helpers.FakeHttp(handler)):
                with self.assertRaises(AdsError) as caught:
                    tiktok.set_status(ws.ctx, "adgroup", ["901"], "DISABLE", yes=True)
            self.assertIn("Adgroup does not exist", caught.exception.message)

    def test_status_changes_go_in_batches_of_twenty(self):
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(lambda m, u, k: {"code": 0, "data": {}})
            with mock.patch.object(tiktok, "request", http):
                tiktok.set_status(ws.ctx, "ad", [str(n) for n in range(45)], "DISABLE", yes=True)
            self.assertEqual([len(c[2]["json_body"]["ad_ids"]) for c in http.calls], [20, 20, 5])

    def test_error_code_on_http_200_is_an_error(self):
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(lambda m, u, k: {"code": 40002, "message": "bad field", "request_id": "r-1"})
            with mock.patch.object(tiktok, "request", http):
                with self.assertRaises(AdsError) as caught:
                    tiktok.get(ws.ctx, "campaign/get/")
            self.assertIn("40002", caught.exception.message)
            self.assertIn("r-1", caught.exception.message)


if __name__ == "__main__":
    unittest.main()
