"""What the first runs against the live services showed (2026-11-22 and 2026-11-23)."""
import unittest
import urllib.parse
from unittest import mock

import helpers
from adskit import google, recon
from adskit.core import AdsError


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


if __name__ == "__main__":
    unittest.main()
