import json
import subprocess
import sys
import unittest

import helpers

GUARD = helpers.PLUGIN / "hooks" / "guard.py"
sys.path.insert(0, str(GUARD.parent))
import guard  # noqa: E402


def decide(tool, tool_input=None):
    """Run the hook the way Claude Code does: the event on stdin, the verdict on stdout."""
    event = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tool_input or {}}
    done = subprocess.run([sys.executable, "-B", str(GUARD)], input=json.dumps(event), capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)["hookSpecificOutput"] if done.stdout.strip() else None


class BashCommands(unittest.TestCase):
    ASK = [
        # the toolkit
        "python3 ads/tools/ads.py launch apply --file ads/launch/x.plan.json --yes",
        "cd project && python3 ads/tools/ads.py meta post {account}/campaigns -p status=PAUSED --yes",
        "python3 ads/tools/ads.py google mutate --file ops.json --yes --activate",
        "python3 ads/tools/ads.py launch apply \\\n  --file ads/launch/x.json \\\n  --yes",
        "python3 ads/tools/ads.py meta post '{account}/campaigns' -p 'name=a&b' -p status=PAUSED --yes",
        "ADS_DIR=ads python3 ./ads/tools/ads.py tiktok post campaign/create/ --data @c.json --yes",
        "bash -c 'python3 ads/tools/ads.py launch apply --file x.json --yes'",
        "echo start; python3 ads/tools/ads.py launch rollback --file x.json --remove --yes",
        # curl, in the shapes people really type
        "curl -X POST https://graph.facebook.com/v27.0/act_1/campaigns -F name=x",
        "curl -s https://googleads.googleapis.com/v26/customers/1/googleAds:mutate -d @body.json",
        "curl -X POST datamanager.googleapis.com/v1/events:ingest -d @events.json",
        "python3 ads/tools/ads.py google upload-conversions --file c.csv --action 555 --yes",
        "curl -H 'Access-Token: x' -X POST https://business-api.tiktok.com/open_api/v1.3/campaign/create/ -d '{}'",
        "curl -X POST \\\n  https://graph.facebook.com/v27.0/act_1/campaigns \\\n  -d name=x",
        "curl --request POST https://graph.facebook.com/v27.0/act_1/campaigns",
        "curl -s -d@payload https://graph.facebook.com/v27.0/act_1/adsets",
        "curl -d'a=b' https://graph.facebook.com/v27.0/act_1/adsets",
        "curl --json @b.json https://business-api.tiktok.com/open_api/v1.3/campaign/create/",
        "curl -T clip.mp4 https://graph.facebook.com/v27.0/act_1/advideos",
        "curl -XDELETE https://graph.facebook.com/v27.0/123",
        # other clients and inline code
        "wget --post-data='name=x' https://graph.facebook.com/v27.0/act_1/campaigns",
        "http POST https://graph.facebook.com/v27.0/act_1/campaigns name=x",
        "python3 -c \"import requests; requests.post('https://graph.facebook.com/v27.0/act_1/campaigns', data={})\"",
        "node -e \"fetch('https://business-api.tiktok.com/open_api/v1.3/campaign/create/', {method: 'POST'})\"",
        # the Meta command-line tool
        "meta -o json ads campaign create --name Q4",
        "meta ads campaign update 123 --status ACTIVE",
        # a shortened flag, which an older copy of the toolkit still reads as --yes
        "python3 ads/tools/ads.py launch apply --file p.json --y",
        "python3 ads/tools/ads.py launch activate --file p.json --ye",
        "python3 ads/tools/ads.py --dir ads launch rollback --file p.json --rem --yes",
        # curl with its short options packed together
        "curl -sd 'status=ACTIVE' https://graph.facebook.com/v27.0/123",
        "curl -sSd x=1 https://graph.facebook.com/v27.0/123",
        "curl -sSX POST \"https://graph.facebook.com/v27.0/123?status=ACTIVE\"",
        "curl -sX POST https://graph.facebook.com/v27.0/123",
        "curl -sSfT clip.mp4 https://graph.facebook.com/v27.0/act_1/advideos",
        # a client behind a wrapper and its options
        "timeout 30 curl -s -d status=ACTIVE https://graph.facebook.com/v27.0/123",
        "sudo -u bob curl -d a=b https://graph.facebook.com/v27.0/123",
        "nice -n 5 curl -d a=b https://graph.facebook.com/v27.0/123",
        "env -i curl -d a=b https://graph.facebook.com/v27.0/123",
        "echo 123 | xargs -I{} curl -d a=b https://graph.facebook.com/v27.0/{}",
        "docker exec box curl -d a=b https://graph.facebook.com/v27.0/123",
        "sudo -u bob bash -c 'curl -d a=b https://graph.facebook.com/v27.0/123'",
        "for id in 1 2; do curl -d status=PAUSED \"https://graph.facebook.com/v27.0/$id\"; done",
        # the address in a variable, the write in another command
        "URL=https://graph.facebook.com/v27.0/act_1/campaigns; curl -X POST \"$URL\" -d status=ACTIVE",
        "export URL=https://business-api.tiktok.com/open_api/v1.3/campaign/create/ && curl \"$URL\" -d '{}'",
        # a script on stdin: the address on one line, the call on another
        "python3 - <<'EOF'\nimport requests\nurl = 'https://graph.facebook.com/v27.0/act_1/campaigns'\nrequests.post(url, data={'name': 'x'})\nEOF",
        # inline code that sends a body without naming a method
        "python3 -c \"import urllib.request as u; u.urlopen(u.Request('https://graph.facebook.com/v27.0/123', data=b'status=ACTIVE'))\"",
        # command substitution
        "echo `curl -d a=b https://graph.facebook.com/v27.0/123`",
        "echo \"$(curl -d a=b https://graph.facebook.com/v27.0/123)\"",
        # other clients
        "http https://graph.facebook.com/v27.0/123 < body.json",
        "wget --method POST https://graph.facebook.com/v27.0/123",
        "wget --method=DELETE https://graph.facebook.com/v27.0/123",
        # a parameter that turns a Graph API read into a write
        "curl -G https://graph.facebook.com/v27.0/123 -d method=delete",
        "curl -s 'https://graph.facebook.com/v27.0/act_1/campaigns?method=post&name=x&status=ACTIVE'",
        "python3 ads/tools/ads.py meta get 120000000001 -p method=DELETE",
        "python3 ads/tools/ads.py meta get 'act_1/campaigns?method=post&status=ACTIVE'",
        # inline code that sends a body without any telling word
        "python3 -c 'import urllib.request as u; u.urlopen(\"https://graph.facebook.com/v27.0/act_1/campaigns\", b\"name=x&status=ACTIVE\")'",
        "ruby -rnet/http -e 'Net::HTTP.post_form(URI(\"https://graph.facebook.com/v27.0/act_1/campaigns\"), {})'",
        "python3 - <<'EOF'\nimport urllib.request as u\nu.urlopen('https://graph.facebook.com/v27.0/act_1/campaigns', b'name=x')\nEOF",
        "python3 -c \"import os, urllib.request as u; t = os.environ.get('T'); u.urlopen('https://graph.facebook.com/v27.0/act_1/campaigns', b'name=x&access_token=' + t.encode())\"",
        "python3 -c \"import requests, os; requests.get('https://graph.facebook.com/v27.0/me'); requests.request('POST', 'https://graph.facebook.com/v27.0/act_1/campaigns')\"",
        # the same override, encoded, spaced or with a leading underscore
        "curl 'https://graph.facebook.com/v27.0/123?method=%44ELETE'",
        "curl 'https://graph.facebook.com/v27.0/123?%6dethod=delete'",
        "curl -G https://graph.facebook.com/v27.0/123 -d 'method = delete'",
        "curl 'https://graph.facebook.com/v27.0/123?_method=delete'",
        "python3 ads/tools/ads.py meta get 120000000001 -p _method=DELETE",
        # the upload host of the Graph API
        "curl -F source=@clip.mp4 https://graph-video.facebook.com/v27.0/act_1/advideos",
        # a Google write that only looks like a read
        "curl -X POST 'https://googleads.googleapis.com/v26/customers/1/campaigns:mutate?x=:search' -d '{}'",
        "curl -X POST 'https://googleads.googleapis.com/v26/customers/1/campaigns:mutate#:search' -d '{}'",
    ]
    SILENT = [
        "python3 ads/tools/ads.py launch plan --file ads/launch/x.plan.json",
        "python3 ads/tools/ads.py meta insights --preset last_7d",
        "python3 ads/tools/ads.py image --prompt 'yes we can --yes' --aspect 1:1",
        "python3 ads/tools/ads.py google mutate --file ops.json",
        "curl -s https://graph.facebook.com/v27.0/me",
        "curl -sG https://graph.facebook.com/v27.0/act_1/insights --data-urlencode 'fields=spend'",
        "curl -X POST https://googleads.googleapis.com/v26/customers/1/googleAds:search -d '{\"query\": \"SELECT campaign.id FROM campaign\"}'",
        "curl -X POST https://example.com/api/items -d name=x",
        "wget https://graph.facebook.com/v27.0/me",
        "meta -o json ads campaign list",
        "git commit -m 'meta ads: create dashboard' --yes",
        "grep -r 'meta ads create' docs/",
        "cat docs/meta-ads-update-notes.md",
        "echo meta tags for ads: update",
        "git commit -m 'update ads plan' --yes",
        "ls -la",
        # reads behind wrappers, in variables, next to an unrelated write
        "timeout 30 curl -s https://graph.facebook.com/v27.0/me",
        "URL=https://graph.facebook.com/v27.0/me; curl -s \"$URL\"",
        "URL=https://graph.facebook.com/v27.0/act_1/insights; curl -sG \"$URL\" --data-urlencode fields=spend",
        "curl -s https://graph.facebook.com/v27.0/me; curl -X POST https://example.com/hook -d ok=1",
        "curl -s https://graph.facebook.com/v27.0/me | jq -r .name",
        "bash -c \"curl -sG https://graph.facebook.com/v27.0/act_1/insights --data-urlencode fields=spend\"",
        "curl -sH 'Accept: application/json' https://graph.facebook.com/v27.0/me",
        "curl -so data.json https://graph.facebook.com/v27.0/act_1/insights",
        "wget --method GET https://graph.facebook.com/v27.0/me",
        "http https://graph.facebook.com/v27.0/me fields==id",
        "grep -rn graph.facebook.com skills/ | grep POST",
        "curl -X POST https://googleads.googleapis.com/v26/customers/1:generateKeywordIdeas -d '{}'",
        "python3 -c \"import os, requests; print(requests.get('https://graph.facebook.com/v27.0/me', params={'access_token': os.environ.get('T')}).json())\"",
        # the toolkit shown without --yes, also when the call would switch delivery on
        "python3 ads/tools/ads.py google mutate --file ops.json --activate",
        "python3 ads/tools/ads.py launch activate --file ads/launch/x.plan.json",
        "python3 ads/tools/ads.py launch apply --file ads/launch/yes.json",
    ]

    def test_writes_ask_for_confirmation(self):
        for command in self.ASK:
            reason = guard.bash_reason(command)
            self.assertIsNotNone(reason, command)
            self.assertTrue(reason.startswith("stack-ads:"), command)

    def test_reads_and_unrelated_commands_pass_silently(self):
        for command in self.SILENT:
            self.assertIsNone(guard.bash_reason(command), command)

    def test_spend_is_named(self):
        for command in ("python3 ads/tools/ads.py launch activate --file x --yes",
                        "python3 ads/tools/ads.py google mutate --file ops.json --yes --activate",
                        "python3 ads/tools/ads.py tiktok post campaign/gmv_max/create/ --data @g.json --yes --activate",
                        "meta ads campaign update 123 --status ACTIVE"):
            self.assertIn("spend", guard.bash_reason(command), command)

    def test_removal_is_named(self):
        self.assertIn("delete", guard.bash_reason("python3 ads/tools/ads.py launch rollback --file x.json --remove --yes"))
        self.assertIn("delete", guard.bash_reason("python3 ads/tools/ads.py --dir ads launch rollback --file x.json --rem --yes"))
        self.assertIn("pauses", guard.bash_reason("python3 ads/tools/ads.py launch rollback --file x.json --yes"))

    def test_a_shortened_activate_is_still_spend(self):
        for command in ("python3 ads/tools/ads.py launch activate --file p.json --ye",
                        "python3 ads/tools/ads.py google mutate --file ops.json --yes --act",
                        "python3 ads/tools/ads.py --dir ads launch activate --file p.json --yes"):
            self.assertIn("spend", guard.bash_reason(command), command)

    def test_unbalanced_quotes_still_get_a_verdict(self):
        self.assertIsNotNone(guard.bash_reason("python3 ads/tools/ads.py launch apply --file \"x.json --yes"))
        self.assertIsNone(guard.bash_reason("echo \"unfinished"))


class McpTools(unittest.TestCase):
    PREFIX = "mcp__plugin_stack-ads_"

    def test_writes_ask(self):
        for tool in ("meta-ads__ads_create_campaign", "meta-ads__ads_activate_entity", "meta-ads__ads_update_entity",
                     "meta-ads__ads_boost_ig_post", "meta-ads__enable_campaign", "meta-ads__pause_campaign",
                     "meta-ads__publish_ad", "meta-ads__duplicate_campaign", "meta-ads__get_or_create_audience",
                     "tiktok-ads__campaign_create", "tiktok-ads__adgroup_status_update", "tiktok-ads__file_video_ad_upload",
                     "tiktok-ads__smart_plus_ad_create", "tiktok-ads__campaign_gmv_max_create",
                     "google-ads__assets_create_asset", "google-ads__assets_upload_video_asset",
                     "google-ads__labels_manage_labels"):
            self.assertIsNotNone(guard.mcp_reason(self.PREFIX + tool), tool)

    def test_a_tool_the_guard_does_not_know_asks(self):
        self.assertIsNotNone(guard.mcp_reason(self.PREFIX + "tiktok-ads__something_new"))

    def test_a_name_that_joins_a_read_with_another_action_asks(self):
        for tool in ("meta-ads__search_and_replace_creatives", "meta-ads__get_and_toggle_campaign",
                     "tiktok-ads__list_then_cancel", "google-ads__find_and_fix", "meta-ads__get_or_refresh_token",
                     "meta-ads__get_campaign_optimize", "tiktok-ads__query_budget_fix", "meta-ads__ads_get_and_scale"):
            self.assertIsNotNone(guard.mcp_reason(self.PREFIX + tool), tool)

    def test_reads_pass(self):
        for tool in ("meta-ads__ads_get_ad_accounts", "meta-ads__ads_library_search", "meta-ads__ads_get_errors",
                     "meta-ads__fetch_ad_status", "meta-ads__query_budget_usage", "meta-ads__describe_budget",
                     "tiktok-ads__campaign_get", "tiktok-ads__report_integrated_get", "tiktok-ads__identity_get",
                     "tiktok-ads__ad_audience_size_estimate", "tiktok-ads__creative_cta_recommend_get",
                     "tiktok-ads__file_name_check", "google-ads__search_search",
                     "google-ads__customers_list_accessible_customers", "google-ads__metadata_get_resource_metadata"):
            self.assertIsNone(guard.mcp_reason(self.PREFIX + tool), tool)

    def test_spend_and_platform_are_named(self):
        for tool in ("meta-ads__ads_activate_entity", "meta-ads__ads_update_entity", "tiktok-ads__campaign_status_update"):
            self.assertIn("spend", guard.mcp_reason(self.PREFIX + tool), tool)
        self.assertIn("Google Ads", guard.mcp_reason(self.PREFIX + "google-ads__assets_create_asset"))
        self.assertIn("TikTok", guard.mcp_reason(self.PREFIX + "tiktok-ads__campaign_create"))
        self.assertIn("Meta", guard.mcp_reason(self.PREFIX + "meta-ads__ads_create_campaign"))

    def test_other_servers_are_not_judged(self):
        self.assertIsNone(guard.mcp_reason(self.PREFIX + "firecrawl__firecrawl_scrape"))
        self.assertIsNone(guard.mcp_reason(self.PREFIX + "dataforseo__api_request"))


class LiveNames(unittest.TestCase):
    """Tool names the live TikTok and Meta servers listed on 2026-11-22 (tests/fixtures/mcp-live-names.json)."""

    PREFIX = "mcp__plugin_stack-ads_"
    DISPATCHER = PREFIX + "tiktok-ads__tool_execute"

    @classmethod
    def setUpClass(cls):
        path = helpers.PLUGIN / "tests" / "fixtures" / "mcp-live-names.json"
        cls.live = json.loads(path.read_text(encoding="utf-8"))

    def asked(self, server, names):
        return sorted(name for name in names if guard.mcp_reason("%s%s__%s" % (self.PREFIX, server, name)))

    def test_smart_plus_is_a_product_name_not_two_actions(self):
        for tool in ("smart_plus_campaign_get", "smart_plus_adgroup_get", "smart_plus_ad_get",
                     "smart_plus_ad_review_info_get", "smart_plus_material_review_info_get"):
            self.assertIsNone(guard.mcp_reason(self.PREFIX + "tiktok-ads__" + tool), tool)

    def test_smart_plus_writes_still_ask(self):
        for tool in ("smart_plus_campaign_create", "smart_plus_adgroup_create", "smart_plus_ad_create",
                     "smart_plus_campaign_update", "smart_plus_ad_update", "smart_plus_ad_appeal"):
            self.assertIsNotNone(guard.mcp_reason(self.PREFIX + "tiktok-ads__" + tool), tool)
        for tool in ("smart_plus_campaign_status_update", "smart_plus_adgroup_budget_update"):
            self.assertIn("spend", guard.mcp_reason(self.PREFIX + "tiktok-ads__" + tool), tool)

    def test_a_set_of_products_or_events_is_a_thing_not_an_action(self):
        for tool in ("tiktok-ads__catalog_set_get", "tiktok-ads__catalog_set_product_get",
                     "tiktok-ads__ctm_message_event_set_get",
                     "meta-ads__ads_catalog_get_product_feed_upload_sessions"):
            self.assertIsNone(guard.mcp_reason(self.PREFIX + tool), tool)

    def test_writes_on_those_things_still_ask(self):
        for tool in ("tiktok-ads__catalog_set_create", "tiktok-ads__catalog_set_update", "tiktok-ads__catalog_set_delete",
                     "meta-ads__ads_catalog_create_product_set", "meta-ads__ads_catalog_update_product_set",
                     "meta-ads__ads_catalog_product_set_delete",
                     "meta-ads__ads_catalog_create_product_feed_upload_session",
                     "meta-ads__ads_permission_set_asset_permissions"):
            self.assertIsNotNone(guard.mcp_reason(self.PREFIX + tool), tool)

    def test_a_get_that_changes_something_asks(self):
        # the live server names two writes like reads: one stops a split test, one stores an edited image
        for tool in ("split_test_end_get", "creative_image_edit_get"):
            self.assertIsNotNone(guard.mcp_reason(self.PREFIX + "tiktok-ads__" + tool), tool)
            self.assertIsNotNone(decide(self.DISPATCHER, {"tool_name": tool, "params": {}}), tool)

    def test_the_dispatcher_passes_a_read(self):
        for tool in ("campaign_get", "adgroup_get", "ad_get", "tool_region_get", "bc_asset_get", "report_task_check"):
            self.assertIsNone(decide(self.DISPATCHER, {"tool_name": tool, "params": {"advertiser_id": "1"}}), tool)

    def test_the_dispatcher_asks_for_a_write_and_names_it(self):
        for tool in ("campaign_create", "adgroup_create", "ad_create", "file_video_ad_upload",
                     "bc_asset_advertiser_assign", "advertiser_update", "bc_transfer", "term_confirm"):
            verdict = decide(self.DISPATCHER, {"tool_name": tool, "params": {}})
            self.assertIsNotNone(verdict, tool)
            self.assertEqual(verdict["permissionDecision"], "ask")
            self.assertIn(tool, verdict["permissionDecisionReason"])

    def test_the_dispatcher_warns_when_delivery_can_change(self):
        for tool in ("campaign_status_update", "adgroup_status_update", "ad_status_update", "adgroup_budget_update"):
            verdict = decide(self.DISPATCHER, {"tool_name": tool, "params": {"operation_status": "ENABLE"}})
            self.assertIn("spend", verdict["permissionDecisionReason"], tool)

    def test_the_dispatcher_asks_when_the_tool_is_not_a_plain_name(self):
        for tool_input in ({}, {"params": {}}, {"tool_name": ""}, {"tool_name": None}, {"tool_name": ["campaign_get"]},
                           {"tool_name": "campaign_get;campaign_create"}, {"tool_name": "Campaign_Get"},
                           {"tool_name": "tool_execute"}, {"tool_name": "campaign get"}):
            self.assertIsNotNone(decide(self.DISPATCHER, tool_input), tool_input)

    def test_only_the_tiktok_server_has_a_dispatcher(self):
        for server in ("meta-ads", "google-ads"):
            tool = "%s%s__tool_execute" % (self.PREFIX, server)
            self.assertIsNotNone(decide(tool, {"tool_name": "campaign_get", "params": {}}), server)

    def test_the_verdict_on_every_live_name_is_the_reviewed_one(self):
        # A rule change that frees or adds a name fails here: review the name, then update the list in the fixture.
        for key, server in (("tiktok_core", "tiktok-ads"), ("tiktok_dispatcher", "tiktok-ads"), ("meta", "meta-ads")):
            self.assertEqual(self.asked(server, self.live[key]), self.live[key + "_ask"], key)

    def test_every_live_tool_behind_the_dispatcher_is_judged_like_the_tool_itself(self):
        for tool in self.live["tiktok_dispatcher"]:
            direct = guard.mcp_reason(self.PREFIX + "tiktok-ads__" + tool)
            through = guard.mcp_reason(self.DISPATCHER, {"tool_name": tool, "params": {}})
            self.assertEqual(direct is None, through is None, tool)


class HookProcess(unittest.TestCase):
    def test_answers_ask_as_json(self):
        out = decide("Bash", {"command": "python3 ads/tools/ads.py launch apply --file x.json --yes"})
        self.assertEqual(out["permissionDecision"], "ask")
        self.assertEqual(out["hookEventName"], "PreToolUse")
        out = decide("mcp__plugin_stack-ads_meta-ads__ads_create_campaign")
        self.assertEqual(out["permissionDecision"], "ask")

    def test_other_tools_pass(self):
        self.assertIsNone(decide("Write", {"file_path": "x"}))
        self.assertIsNone(decide("Bash", {"command": "ls"}))

    def test_bad_input_passes_with_a_warning(self):
        done = subprocess.run([sys.executable, "-B", str(GUARD)], input="not json", capture_output=True, text=True)
        self.assertEqual((done.returncode, done.stdout), (0, ""))
        self.assertIn("stack-ads", done.stderr)


if __name__ == "__main__":
    unittest.main()
