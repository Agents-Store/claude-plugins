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
