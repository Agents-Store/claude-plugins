import unittest

import helpers  # noqa: F401  (sets the import path)
from adskit import guards
from adskit.core import DEFAULT_CONFIG, Refused


def google_body(status="PAUSED", micros="20000000"):
    return {"mutateOperations": [
        {"campaignBudgetOperation": {"create": {"resourceName": "customers/1/campaignBudgets/-1", "amountMicros": micros}}},
        {"campaignOperation": {"create": {"resourceName": "customers/1/campaigns/-2", "status": status}}},
    ]}


class GoogleGuard(unittest.TestCase):
    def test_paused_campaign_within_budget_passes(self):
        summary = guards.google_mutate(google_body(), DEFAULT_CONFIG)
        self.assertEqual(summary["daily_budgets"], [20.0])
        self.assertEqual(summary["creates"], ["campaignBudgetOperation", "campaignOperation"])

    def test_enabled_campaign_is_refused(self):
        with self.assertRaises(Refused):
            guards.google_mutate(google_body(status="ENABLED"), DEFAULT_CONFIG)

    def test_missing_status_is_refused(self):
        body = google_body()
        del body["mutateOperations"][1]["campaignOperation"]["create"]["status"]
        with self.assertRaises(Refused):
            guards.google_mutate(body, DEFAULT_CONFIG)

    def test_budget_above_ceiling_is_refused(self):
        with self.assertRaises(Refused):
            guards.google_mutate(google_body(micros="90000000"), DEFAULT_CONFIG)

    def test_lifetime_budget_is_off_until_a_ceiling_is_set(self):
        body = google_body()
        budget = body["mutateOperations"][0]["campaignBudgetOperation"]["create"]
        del budget["amountMicros"]
        budget["totalAmountMicros"] = "300000000"
        with self.assertRaises(Refused):
            guards.google_mutate(body, DEFAULT_CONFIG)
        allowed = {"guardrails": {"max_daily_budget": 50, "max_total_budget": 400}}
        self.assertEqual(guards.google_mutate(body, allowed)["total_budgets"], [300.0])

    def test_enabling_needs_activate(self):
        body = {"mutateOperations": [{"campaignOperation": {"update": {"resourceName": "customers/1/campaigns/5",
                                                                        "status": "ENABLED"}, "updateMask": "status"}}]}
        with self.assertRaises(Refused):
            guards.google_mutate(body, DEFAULT_CONFIG)
        self.assertTrue(guards.google_mutate(body, DEFAULT_CONFIG, activate=True)["activates"])

    def test_malformed_body_is_refused(self):
        for body in ({}, {"mutateOperations": []}, {"mutateOperations": [{"a": {}, "b": {}}]}):
            with self.assertRaises(Refused):
                guards.google_mutate(body, DEFAULT_CONFIG)


class MetaGuard(unittest.TestCase):
    def test_create_must_be_paused(self):
        for edge in ("campaigns", "adsets", "ads"):
            with self.assertRaises(Refused):
                guards.meta_request("POST", "act_1/%s" % edge, {"status": "ACTIVE"}, DEFAULT_CONFIG)
            with self.assertRaises(Refused):
                guards.meta_request("POST", "act_1/%s" % edge, {}, DEFAULT_CONFIG)
            self.assertEqual(guards.meta_request("POST", "act_1/%s" % edge, {"status": "PAUSED"}, DEFAULT_CONFIG)["creates"], edge)

    def test_budget_is_read_in_minor_units(self):
        ok = guards.meta_request("POST", "act_1/adsets", {"status": "PAUSED", "daily_budget": "2000"}, DEFAULT_CONFIG)
        self.assertEqual(ok["daily_budget"], 20.0)
        with self.assertRaises(Refused):
            guards.meta_request("POST", "act_1/adsets", {"status": "PAUSED", "daily_budget": "9000"}, DEFAULT_CONFIG)

    def test_zero_decimal_currency(self):
        config = dict(DEFAULT_CONFIG, project={"currency": "JPY"}, guardrails={"max_daily_budget": 5000})
        self.assertEqual(guards.meta_request("POST", "act_1/adsets", {"status": "PAUSED", "daily_budget": 3000}, config)["daily_budget"], 3000.0)

    def test_activation_needs_flag(self):
        with self.assertRaises(Refused):
            guards.meta_request("POST", "120000000001", {"status": "ACTIVE"}, DEFAULT_CONFIG)
        self.assertTrue(guards.meta_request("POST", "120000000001", {"status": "ACTIVE"}, DEFAULT_CONFIG, activate=True)["activates"])

    def test_other_writes_pass(self):
        self.assertIsNone(guards.meta_request("POST", "act_1/adcreatives", {"name": "c"}, DEFAULT_CONFIG)["creates"])

    def test_lifetime_budget_is_off_until_a_ceiling_is_set(self):
        params = {"status": "PAUSED", "lifetime_budget": 30000}
        with self.assertRaises(Refused) as off:
            guards.meta_request("POST", "act_1/adsets", params, DEFAULT_CONFIG)
        self.assertIn("max_total_budget", off.exception.hint)
        allowed = {"guardrails": {"max_daily_budget": 50, "max_total_budget": 400}, "project": {"currency": "EUR"}}
        self.assertEqual(guards.meta_request("POST", "act_1/adsets", params, allowed)["total_budget"], 300)
        with self.assertRaises(Refused):
            guards.meta_request("POST", "act_1/adsets", dict(params, lifetime_budget=50000), allowed)


class TikTokGuard(unittest.TestCase):
    def test_every_level_must_be_created_disabled(self):
        for route in ("campaign/create/", "adgroup/create", "smart_plus/campaign/create/", "smart_plus/adgroup/create/",
                      "smart_plus/ad/create/"):
            with self.assertRaises(Refused):
                guards.tiktok_request(route, {"budget": 30}, DEFAULT_CONFIG)
            with self.assertRaises(Refused):
                guards.tiktok_request(route, {"operation_status": "ENABLE"}, DEFAULT_CONFIG)
            self.assertIsNotNone(guards.tiktok_request(route, {"operation_status": "DISABLE"}, DEFAULT_CONFIG)["creates"])

    def test_every_ad_of_a_request_must_be_created_disabled(self):
        off = {"ad_name": "a", "operation_status": "DISABLE"}
        self.assertEqual(guards.tiktok_request("ad/create/", {"creatives": [off, dict(off)]}, DEFAULT_CONFIG)["creates"], "ad")
        for creatives in ([{"ad_name": "a"}], [off, {"ad_name": "b"}], [off, {"ad_name": "b", "operation_status": "ENABLE"}]):
            with self.assertRaises(Refused):
                guards.tiktok_request("ad/create/", {"creatives": creatives}, DEFAULT_CONFIG)
        # the manual ad/create/ reads the status on each creative: one at the top of the body covers nothing
        with self.assertRaises(Refused):
            guards.tiktok_request("ad/create/", {"operation_status": "DISABLE", "creatives": [{"ad_name": "a"}]}, DEFAULT_CONFIG)
        # Smart+ makes one ad per call and reads the status at the top
        self.assertEqual(guards.tiktok_request("smart_plus/ad/create/", {"operation_status": "DISABLE"}, DEFAULT_CONFIG)["creates"], "ad")

    def test_gmv_max_cannot_be_created_paused_so_it_needs_activate(self):
        body = {"store_id": "1", "budget": 30, "operation_status": "DISABLE"}
        with self.assertRaises(Refused):
            guards.tiktok_request("campaign/gmv_max/create/", body, DEFAULT_CONFIG)
        self.assertTrue(guards.tiktok_request("campaign/gmv_max/create/", body, DEFAULT_CONFIG, activate=True)["activates"])
        with self.assertRaises(Refused):
            guards.tiktok_request("campaign/gmv_max/create/", dict(body, budget=500), DEFAULT_CONFIG, activate=True)

    def test_daily_budget_ceiling(self):
        body = {"operation_status": "DISABLE", "budget_mode": "BUDGET_MODE_DAY", "budget": 500}
        with self.assertRaises(Refused):
            guards.tiktok_request("campaign/create/", body, DEFAULT_CONFIG)
        body["budget_mode"] = "BUDGET_MODE_INFINITE"
        self.assertIsNone(guards.tiktok_request("campaign/create/", body, DEFAULT_CONFIG)["daily_budget"])

    def test_lifetime_budget_is_off_until_a_ceiling_is_set(self):
        body = {"operation_status": "DISABLE", "budget_mode": "BUDGET_MODE_TOTAL", "budget": 500}
        with self.assertRaises(Refused):
            guards.tiktok_request("campaign/create/", body, DEFAULT_CONFIG)
        allowed = {"guardrails": {"max_daily_budget": 50, "max_total_budget": 600}}
        self.assertEqual(guards.tiktok_request("campaign/create/", body, allowed)["total_budget"], 500)
        with self.assertRaises(Refused):
            guards.tiktok_request("campaign/create/", dict(body, budget=700), allowed)

    def test_enable_needs_activate(self):
        body = {"campaign_ids": ["1"], "operation_status": "ENABLE"}
        with self.assertRaises(Refused):
            guards.tiktok_request("campaign/status/update/", body, DEFAULT_CONFIG)
        self.assertTrue(guards.tiktok_request("campaign/status/update/", body, DEFAULT_CONFIG, activate=True)["activates"])

    def test_reads_and_reports_pass(self):
        self.assertIsNone(guards.tiktok_request("report/task/create/", {"report_type": "BASIC"}, DEFAULT_CONFIG)["creates"])


if __name__ == "__main__":
    unittest.main()
