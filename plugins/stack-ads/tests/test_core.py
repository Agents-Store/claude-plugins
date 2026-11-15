import json
import os
import unittest
from unittest import mock

import helpers
from adskit import core, workspace
from adskit.core import Context, MissingKey, Refused


class EnvFiles(unittest.TestCase):
    def test_parse_handles_quotes_comments_and_export(self):
        text = "# note\nA=1\nexport B='two words'\nC=\"x\"\nD=plain # trailing\nE=\n  F = spaced\n"
        self.assertEqual(core.parse_env_text(text), {"A": "1", "B": "two words", "C": "x", "D": "plain", "E": "", "F": "spaced"})

    def test_workspace_env_beats_project_env_and_shell_beats_both(self):
        with helpers.Workspace() as ws:
            (ws.project / ".env").write_text("META_PAGE_ID=from-project\nGSC_SITE_URL=sc-domain:example.com\n")
            ctx = Context(ws.project / "ads")
            self.assertEqual(ctx.key("META_PAGE_ID"), "444555666")
            self.assertEqual(ctx.key("GSC_SITE_URL"), "sc-domain:example.com")
            with mock.patch.dict(os.environ, {"META_PAGE_ID": "from-shell"}):
                self.assertEqual(Context(ws.project / "ads").key("META_PAGE_ID"), "from-shell")

    def test_missing_key_explains_where_to_get_it(self):
        with helpers.Workspace() as ws:
            with self.assertRaises(MissingKey) as caught:
                ws.ctx.key("FAL_KEY")
            self.assertIn("fal.ai", caught.exception.hint)
            self.assertEqual(caught.exception.code, core.EXIT_MISSING_KEY)

    def test_set_env_value_replaces_in_place_and_redacts(self):
        with helpers.Workspace() as ws:
            core.set_env_value(ws.ctx.ws, "META_PAGE_ID", "replaced-value-1")
            core.set_env_value(ws.ctx.ws, "NEW_SECRET_TOKEN", "brand-new-value-2")
            values = core.parse_env_text((ws.ctx.ws / ".env").read_text())
            self.assertEqual(values["META_PAGE_ID"], "replaced-value-1")
            self.assertEqual(values["NEW_SECRET_TOKEN"], "brand-new-value-2")
            self.assertEqual(core.redact("x brand-new-value-2 y"), "x *** y")

    def test_loaded_keys_are_masked_in_output(self):
        with helpers.Workspace():
            self.assertNotIn("meta-token-example", core.redact("token=meta-token-example"))


class Helpers(unittest.TestCase):
    def test_join_url(self):
        self.assertEqual(core.join_url("https://example.com/v1/", "a", "/b/", "c"), "https://example.com/v1/a/b/c")

    def test_multipart_carries_fields_and_files(self):
        ctype, body = core.multipart({"name": "x"}, [("source", "a.mp4", b"DATA", "video/mp4")])
        self.assertTrue(ctype.startswith("multipart/form-data; boundary="))
        self.assertIn(b'name="name"\r\n\r\nx', body)
        self.assertIn(b'filename="a.mp4"\r\nContent-Type: video/mp4\r\n\r\nDATA', body)

    def test_csv_flattens_nested_rows(self):
        text = core.to_csv([{"campaign": {"name": "A"}, "metrics": {"clicks": "3"}}, {"campaign": {"name": "B"}, "tags": [1, 2]}])
        self.assertEqual(text.splitlines()[0], "campaign.name,metrics.clicks,tags")
        self.assertIn("B,,\"[1, 2]\"", text)

    def test_load_json_arg(self):
        with helpers.Workspace() as ws:
            path = ws.project / "body.json"
            path.write_text('{"a": 1}')
            self.assertEqual(core.load_json_arg("@%s" % path), {"a": 1})
            self.assertEqual(core.load_json_arg('{"b": 2}'), {"b": 2})
            with self.assertRaises(Refused):
                core.load_json_arg("{broken")

    def test_parse_pairs(self):
        self.assertEqual(core.parse_pairs(["a=1", "b=x=y"]), {"a": "1", "b": "x=y"})
        with self.assertRaises(Refused):
            core.parse_pairs(["novalue"])

    def test_request_retries_reads_but_never_writes(self):
        import urllib.error
        attempts = []

        def failing(req, timeout=0):
            attempts.append(req.get_method())
            raise urllib.error.HTTPError(req.full_url, 503, "busy", {}, None)

        with mock.patch("urllib.request.urlopen", failing), mock.patch("time.sleep"):
            with self.assertRaises(core.HttpError):
                core.request("POST", "https://example.com/x", json_body={})
            self.assertEqual(attempts, ["POST"])
            with self.assertRaises(core.HttpError):
                core.request("GET", "https://example.com/x")
            self.assertEqual(attempts, ["POST", "GET", "GET", "GET"])


class WorkspaceSetup(unittest.TestCase):
    def test_init_creates_layout_and_copies_toolkit(self):
        with helpers.Workspace() as ws:
            root = ws.project / "ads"
            for name in ("config.json", ".env", ".gitignore", "README.md", "tools/ads.py", "tools/adskit/core.py",
                         "tools/assets/env.example", "tools/VERSION", "research/raw", "creatives", "launch", "plan", "reports"):
                self.assertTrue((root / name).exists(), name)
            self.assertIn(".env", (root / ".gitignore").read_text().split())
            self.assertTrue(list((root / "tools" / "guides").glob("keys-*.md")))

    def test_init_keeps_existing_keys_and_config(self):
        with helpers.Workspace() as ws:
            root = ws.project / "ads"
            (root / "config.json").write_text(json.dumps({"guardrails": {"max_daily_budget": 7}}))
            workspace.init(root)
            self.assertEqual(Context(root).config["guardrails"]["max_daily_budget"], 7)
            self.assertIn("META_ACCESS_TOKEN=meta-token-example", (root / ".env").read_text())

    def test_update_needs_an_existing_workspace(self):
        with helpers.Workspace() as ws:
            with self.assertRaises(Refused):
                workspace.init(ws.project / "elsewhere", update=True)

    def test_sync_claude_merges_known_keys_only(self):
        with helpers.Workspace() as ws:
            settings = ws.project / ".claude" / "settings.local.json"
            settings.parent.mkdir()
            settings.write_text(json.dumps({"permissions": {"allow": ["Read"]}, "env": {"KEEP": "1"}}))
            (ws.ctx.ws / ".env").write_text("APIFY_TOKEN=apify-example\nUNRELATED=x\nFAL_KEY=\n")
            with mock.patch.object(workspace, "git_ignored", return_value=True):
                out = workspace.sync_claude(Context(ws.ctx.ws))
            data = json.loads(settings.read_text())
            self.assertEqual(data["env"], {"KEEP": "1", "APIFY_TOKEN": "apify-example"})
            self.assertEqual(data["permissions"], {"allow": ["Read"]})
            self.assertEqual(out["variables_written"], ["APIFY_TOKEN"])

    def test_sync_claude_refuses_a_file_git_would_commit(self):
        with helpers.Workspace() as ws:
            with mock.patch.object(workspace, "git_ignored", return_value=False):
                with self.assertRaises(Refused):
                    workspace.sync_claude(ws.ctx)


if __name__ == "__main__":
    unittest.main()
