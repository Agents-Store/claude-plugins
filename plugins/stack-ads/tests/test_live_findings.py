"""What the first runs against the live services showed (2026-11-22 and 2026-11-23)."""
import contextlib
import io
import time
import unittest
import urllib.parse
from unittest import mock

import helpers  # first: it puts the toolkit on the import path
import ads  # noqa: E402
import test_launch  # noqa: E402
from adskit import google, launch, meta, recon
from adskit.core import AdsError, Refused


class ApifyCost(unittest.TestCase):
    """Apify fills usageTotalUsd a moment after a run ends; the charged events are there at once."""

    RUN = {"id": "run1", "status": "SUCCEEDED", "defaultDatasetId": "ds1", "usageTotalUsd": 0,
           "chargedEventCounts": {"apify-default-dataset-item": 3, "ecommerce-enrichment": 0},
           "pricingInfo": {"pricingModel": "PAY_PER_EVENT", "pricingPerEvent": {"actorChargeEvents": {
               "apify-default-dataset-item": {"eventPriceUsd": 0.005},
               "ecommerce-enrichment": {"eventPriceUsd": 0.0032}}}}}

    def cost_of(self, run):
        def handler(method, url, kwargs):
            if "datasets" in url:
                return [{"n": 1}, {"n": 2}, {"n": 3}]
            return {"data": run}

        with helpers.Workspace() as ws, mock.patch.object(recon, "request", helpers.FakeHttp(handler)):
            ws.ctx.env["APIFY_TOKEN"] = "apify-token-example"
            done = recon.apify_run(ws.ctx, "apify/facebook-ads-scraper", {"startUrls": []}, max_usd=0.05, max_items=3)
        self.assertEqual(len(done["items"]), 3)
        return done["usage_usd"]

    def test_the_cost_comes_from_the_charged_events_while_usage_is_still_zero(self):
        self.assertAlmostEqual(self.cost_of(self.RUN), 0.015)

    def test_the_larger_of_usage_and_charged_events_is_reported(self):
        self.assertAlmostEqual(self.cost_of(dict(self.RUN, usageTotalUsd=0.04)), 0.04)

    def test_a_run_billed_by_usage_reports_its_usage(self):
        by_usage = {k: v for k, v in self.RUN.items() if k not in ("chargedEventCounts", "pricingInfo")}
        self.assertAlmostEqual(self.cost_of(dict(by_usage, usageTotalUsd=0.2)), 0.2)


class GoogleLogin(unittest.TestCase):
    def test_the_consent_link_lets_the_user_pick_the_google_login(self):
        # the login that owns the ad account is often not the one the browser is signed in with
        with helpers.Workspace() as ws:
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(google.login_url(ws.ctx)).query)
        self.assertEqual(query["prompt"], ["select_account consent"])


class GoogleRefusals(unittest.TestCase):
    """Two answers of the Google Ads API that need a next step, not only the error text."""

    def refused(self, code_key, code, message):
        payload = {"error": {"code": 403, "status": "PERMISSION_DENIED", "message": "The caller does not have permission",
                             "details": [{"errors": [{"errorCode": {code_key: code}, "message": message}]}]}}

        def handler(method, url, kwargs):
            if "oauth2.googleapis.com" in url:
                return {"access_token": "access-example"}
            return helpers.http_error(403, payload)

        with helpers.Workspace() as ws, mock.patch.object(google, "request", helpers.FakeHttp(handler)):
            with self.assertRaises(AdsError) as caught:
                google._ads_call(ws.ctx, "GET", "https://googleads.googleapis.com/v26/customers:listAccessibleCustomers")
        return caught.exception

    def test_a_login_without_an_ads_account_is_told_which_login_to_use(self):
        error = self.refused("authenticationError", "NOT_ADS_USER",
                             "The Google account that generated the OAuth access tokens is not associated with any Ads accounts.")
        self.assertIn("ads.google.com", error.hint)
        self.assertIn("google login", error.hint)

    def test_keyword_planner_on_explorer_access_is_told_to_apply_for_basic(self):
        error = self.refused("authorizationError", "DEVELOPER_TOKEN_NOT_APPROVED",
                             "This method is not allowed for use with explorer access. Please apply for basic or standard access.")
        self.assertIn("Basic", error.hint)

    def test_the_test_access_hint_is_kept(self):
        error = self.refused("authorizationError", "CLOUD_PROJECT_NOT_APPROVED_FOR_PRODUCTION",
                             "The Google Cloud project is only approved for use with test accounts.")
        self.assertIn("Explorer", error.hint)


class MetaRollbackCleanup(unittest.TestCase):
    """launch rollback --remove deleted campaign, ad set and ad, and left the creative and the uploaded image (2026-11-23)."""

    def run_plan(self, image_created, remove=True):
        base = test_launch.meta_handler()

        def handler(method, url, kwargs):
            if method == "GET" and url.rstrip("/").endswith("adimages"):
                if image_created is None:
                    return helpers.http_error(500, {"error": {"code": 1, "message": "An unknown error occurred"}})
                return {"data": [{"hash": "hash-1", "created_time": image_created}]}
            return base(method, url, kwargs)

        with helpers.Workspace() as ws:
            path = ws.write_plan(test_launch.meta_plan(ws))
            http = helpers.FakeHttp(handler)
            with mock.patch.object(meta, "request", http):
                test_launch.planned(ws, path)
                launch.apply(ws.ctx, path, yes=True)
                rows = launch.status(ws.ctx, path)
                http.calls.clear()
                text = launch.rollback(ws.ctx, path, remove=remove, yes=True)
            left = launch.entities(ws.ctx, "meta-traffic")
        calls = [(c[0], c[1].rstrip("/").rsplit("/", 1)[-1], (c[2].get("params") or {}).get("hash")) for c in http.calls
                 if c[0] in ("DELETE", "POST")]
        return calls, text, left, rows

    def test_remove_deletes_the_creative_and_an_image_the_plan_uploaded(self):
        now = time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime())
        calls, text, left, _ = self.run_plan(now)
        self.assertEqual(calls, [("DELETE", "a-1", None), ("DELETE", "s-1", None), ("DELETE", "c-1", None),
                                 ("DELETE", "cr-1", None), ("DELETE", "adimages", "hash-1")])
        self.assertEqual(left, [])

    def test_an_image_that_was_in_the_library_before_is_kept(self):
        # Meta keeps one image per hash: uploading a file the library already held returns that image
        calls, text, left, _ = self.run_plan("2025-02-07T01:03:10+0200")
        self.assertEqual([c[1] for c in calls], ["a-1", "s-1", "c-1", "cr-1"])
        self.assertIn("hash-1", text)
        self.assertIn("before", text)

    def test_an_image_whose_age_cannot_be_read_is_kept(self):
        calls, text, left, _ = self.run_plan(None)
        self.assertNotIn("adimages", [c[1] for c in calls])
        self.assertIn("hash-1", text)

    def test_pausing_leaves_the_creative_and_the_image_alone(self):
        now = time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime())
        calls, _, left, _ = self.run_plan(now, remove=False)
        self.assertEqual([c[:2] for c in calls], [("POST", "a-1"), ("POST", "s-1"), ("POST", "c-1")])
        self.assertEqual(sorted(item["type"] for item in left), ["ad", "adset", "campaign", "creative", "image"])

    def test_status_lists_the_image_without_reading_it_as_an_object(self):
        now = time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime())
        _, _, _, rows = self.run_plan(now)
        image = [row for row in rows if row["type"] == "image"]
        self.assertEqual([row["id"] for row in image], ["hash-1"])
        self.assertNotIn("error", image[0])


class MetaDelete(unittest.TestCase):
    """An image is deleted from the library by its hash, a parameter; meta delete took no parameters (2026-11-23)."""

    def test_the_command_takes_parameters(self):
        args = ads.build_parser().parse_args(["meta", "delete", "{account}/adimages", "-p", "hash=h1", "--yes"])
        self.assertEqual((args.path, args.param, args.yes), ("{account}/adimages", ["hash=h1"], True))

    def test_the_parameters_are_sent_and_shown_in_the_dry_run(self):
        with helpers.Workspace() as ws:
            http = helpers.FakeHttp(lambda method, url, kwargs: {"success": True})
            with mock.patch.object(meta, "request", http):
                dry = meta.delete(ws.ctx, "{account}/adimages", {"hash": "h1"})
                self.assertEqual(http.calls, [])
                meta.delete(ws.ctx, "{account}/adimages", {"hash": "h1"}, yes=True)
        self.assertEqual(dry["params"], {"hash": "h1"})
        method, url, kwargs = http.calls[0]
        self.assertEqual((method, url.rsplit("/", 2)[-2:]), ("DELETE", ["act_111222333", "adimages"]))
        self.assertEqual(kwargs["params"]["hash"], "h1")

    def test_a_method_parameter_is_refused(self):
        with helpers.Workspace() as ws:
            with self.assertRaises(Refused):
                meta.delete(ws.ctx, "{account}/adimages", {"method": "post", "hash": "h1"}, yes=True)


class CurrencyPerPlatform(unittest.TestCase):
    """The Google account bills in EUR and the Meta account in USD: one project currency failed one of them (2026-11-23)."""

    def meta_plan_text(self, config):
        with helpers.Workspace() as ws:
            ws.ctx.config["project"].update(config.get("project", {}))
            ws.ctx.config["guardrails"].update(config.get("guardrails", {}))
            path = ws.write_plan(test_launch.meta_plan(ws))
            with mock.patch.object(meta, "request", helpers.FakeHttp(test_launch.meta_handler())):
                return launch.plan(ws.ctx, path)

    def test_a_platform_currency_wins_over_the_project_currency(self):
        text, problems = self.meta_plan_text({"project": {"currency": "EUR", "currencies": {"meta": "USD"}}})
        self.assertEqual(problems, [])

    def test_without_an_entry_for_the_platform_the_project_currency_still_applies(self):
        text, problems = self.meta_plan_text({"project": {"currency": "EUR", "currencies": {"google": "EUR"}}})
        self.assertTrue(any("USD" in p and "EUR" in p for p in problems), problems)

    def test_a_ceiling_per_platform(self):
        text, problems = self.meta_plan_text({"guardrails": {"max_daily_budget": {"meta": 10, "google": 500}}})
        self.assertTrue(any("ceiling of 10" in p for p in problems), problems)
        text, problems = self.meta_plan_text({"guardrails": {"max_daily_budget": {"meta": 30, "google": 5}}})
        self.assertEqual(problems, [])

    def test_a_ceiling_map_without_the_platform_is_no_permission(self):
        text, problems = self.meta_plan_text({"guardrails": {"max_daily_budget": {"google": 50}}})
        self.assertTrue(any("none for meta" in p for p in problems), problems)

    def test_single_calls_read_amounts_in_the_platform_currency(self):
        # JPY has no minor unit: 3000 is 3000 yen, not 30
        with helpers.Workspace() as ws:
            ws.ctx.config["project"]["currencies"] = {"meta": "JPY"}
            ws.ctx.config["guardrails"]["max_daily_budget"] = {"meta": 2000}
            with self.assertRaises(Refused) as caught:
                meta.post(ws.ctx, "{account}/adsets", {"name": "Set", "campaign_id": "1", "daily_budget": 3000,
                                                       "status": "PAUSED"}, yes=False, preview=True)
        self.assertIn("ceiling of 2000", caught.exception.message)


if __name__ == "__main__":
    unittest.main()
