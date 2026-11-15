import unittest
from unittest import mock

import helpers
from adskit import creative
from adskit.core import Refused

# Model ids below are fixtures of what the providers listed on one day.
# <!-- example-only -->
OPENAI_IDS = ["gpt-image-2", "gpt-image-2-2026-04-21", "gpt-image-2.5-flare", "gpt-image-2.6-flare", "gpt-image-2.6-sunburst",
              "chatgpt-image-latest", "gpt-4o-mini-tts", "tts-1", "gpt-6-luna", "gpt-realtime-2", "gpt-transcribe"]
GEMINI_IDS = ["gemini-nano-banana-2.1", "gemini-3-pro-image", "gemini-3.1-flash-lite-image", "gemini-3-pro-image-preview",
              "gemini-omni-1.1-flash", "gemini-omni-1.2-flash", "gemini-omni-flash-preview", "gemini-3.8-flash-tts",
              "gemini-3.8-flash-lite-tts", "lyria-3.5", "lyria-3-clip-preview", "lyria-realtime-exp", "gemini-3.5-flash",
              "gemini-3.8-flash", "gemini-4-carbon", "gemini-3.8-live", "gemini-embedding-001"]
EXPECTED = {("openai", "image"): "gpt-image-2.6-flare", ("openai", "speech"): "gpt-4o-mini-tts",
            ("gemini", "image"): "gemini-nano-banana-2.1", ("gemini", "video"): "gemini-omni-1.2-flash",
            ("gemini", "speech"): "gemini-3.8-flash-tts", ("gemini", "music"): "lyria-3.5",
            ("gemini", "analysis"): "gemini-3.8-flash"}
# <!-- /example-only -->


def provider_http(method, url, kwargs):
    if "api.openai.com" in url:
        return {"data": [{"id": i} for i in OPENAI_IDS]}
    if "generativelanguage" in url:
        return {"models": [{"name": "models/" + i, "displayName": i} for i in GEMINI_IDS]}
    if "openapi.json" in url:
        return {"components": {"schemas": {"DemoInput": {"required": ["prompt"], "properties": {
            "prompt": {"type": "string"}, "num_images": {"type": "integer", "default": 1},
            "aspect_ratio": {"anyOf": [{"enum": ["auto", "1:1", "9:16", "16:9"]}, {"type": "null"}], "default": "auto"},
            "duration": {"type": "string", "enum": ["5", "10"]}, "image_url": {"type": "string"}}}}}}
    raise AssertionError("unexpected call %s" % url)


class FileNames(unittest.TestCase):
    def test_a_given_name_is_kept_and_nothing_is_overwritten(self):
        with helpers.Workspace() as ws:
            folder = ws.project / "ads" / "creatives"
            first = creative.target_path(folder, "hero", ".png", named=True)
            self.assertEqual(first.name, "hero.png")
            first.write_bytes(b"x")
            second = creative.target_path(folder, "hero", ".png", named=True)
            self.assertEqual(second.name, "hero-2.png")
            second.write_bytes(b"x")
            self.assertEqual(creative.target_path(folder, "hero", ".png", named=True).name, "hero-3.png")

    def test_without_a_name_the_file_carries_a_timestamp(self):
        with helpers.Workspace() as ws:
            name = creative.target_path(ws.project / "ads" / "creatives", "red-shoe", ".png").name
            self.assertRegex(name, r"^red-shoe-\d{8}-\d{6}\.png$")

    def test_image_command_uses_the_given_name(self):
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 32

        def handler(method, url, kwargs):
            if method == "GET":
                return provider_http(method, url, kwargs)
            import base64
            return {"data": [{"b64_json": base64.b64encode(png).decode()}, {"b64_json": base64.b64encode(png).decode()}],
                    "output_format": "png"}

        with helpers.Workspace() as ws, mock.patch.object(creative, "request", helpers.FakeHttp(handler)):
            ws.ctx.env.update({"OPENAI_API_KEY": "openai-example"})
            out = creative.image(ws.ctx, "a red shoe", provider="openai", n=2, name="shoe-1x1")
            names = [f["file"].rsplit("/", 1)[-1] for f in out["files"]]
            self.assertEqual(names, ["shoe-1x1.png", "shoe-1x1-2.png"])
            again = creative.image(ws.ctx, "a red shoe", provider="openai", n=1, name="shoe-1x1")
            self.assertTrue(again["files"][0]["file"].endswith("shoe-1x1-3.png"))


class Discovery(unittest.TestCase):
    def test_dated_snapshots_and_previews_are_left_out(self):
        with helpers.Workspace() as ws, mock.patch.object(creative, "request", helpers.FakeHttp(provider_http)):
            ws.ctx.env.update({"OPENAI_API_KEY": "openai-example", "GEMINI_API_KEY": "gemini-example"})
            openai_ids = [r["id"] for r in creative.list_models(ws.ctx, "openai")]
            gemini_ids = [r["id"] for r in creative.list_models(ws.ctx, "gemini")]
        self.assertFalse([i for i in openai_ids if i[-10:-6].isdigit()])
        self.assertFalse([i for i in openai_ids + gemini_ids if "preview" in i or "realtime" in i or "live" in i])
        self.assertNotIn("gemini-embedding-001", gemini_ids)

    def test_pick_prefers_the_newest_general_model(self):
        with helpers.Workspace() as ws, mock.patch.object(creative, "request", helpers.FakeHttp(provider_http)):
            ws.ctx.env.update({"OPENAI_API_KEY": "openai-example", "GEMINI_API_KEY": "gemini-example"})
            for (provider, kind), wanted in EXPECTED.items():
                self.assertEqual(creative.pick(ws.ctx, provider, kind), wanted, (provider, kind))
            with self.assertRaises(Refused):
                creative.pick(ws.ctx, "openai", "analysis")
            with self.assertRaises(Refused):
                creative.pick(ws.ctx, "openai", "video")

    def test_explicit_provider_does_not_replace_the_saved_default(self):
        with helpers.Workspace() as ws, mock.patch.object(creative, "request", helpers.FakeHttp(provider_http)):
            ws.ctx.env.update({"OPENAI_API_KEY": "openai-example", "GEMINI_API_KEY": "gemini-example"})
            creative.pick(ws.ctx, "gemini", "image", save=True)
            self.assertEqual(creative.resolve_model(ws.ctx, "image", "openai"), EXPECTED[("openai", "image")])
            self.assertEqual(ws.ctx.config["models"]["image"]["provider"], "gemini")
            self.assertEqual(creative.default_provider(ws.ctx, "image"), "gemini")

    def test_default_provider_follows_the_keys_present(self):
        with helpers.Workspace() as ws:
            ws.ctx.env["FAL_KEY"] = "fal-example"
            self.assertEqual(creative.default_provider(ws.ctx, "video"), "fal")
            with self.assertRaises(Refused):
                creative.default_provider(ws.ctx, "video", "openai")


class Mapping(unittest.TestCase):
    def test_openai_sizes_are_multiples_of_16_with_the_right_ratio(self):
        for aspect, size in creative.OPENAI_SIZE.items():
            width, height = (int(x) for x in size.split("x"))
            self.assertEqual((width % 16, height % 16), (0, 0), size)
            self.assertAlmostEqual(width / height, creative.ratio_of(aspect), delta=0.02)
            self.assertTrue(655360 <= width * height <= 8294400)

    def test_nearest_aspect(self):
        self.assertEqual(creative.nearest_aspect("1.91:1", creative.GEMINI_ASPECTS), "16:9")
        self.assertEqual(creative.nearest_aspect("4:5", creative.GEMINI_ASPECTS), "4:5")
        self.assertEqual(creative.aspect_from_size("1080x1350")[0], "4:5")
        self.assertEqual(creative.aspect_from_size("1200x628")[0], "1.91:1")

    def test_fal_payloads_follow_the_model_schema(self):
        with helpers.Workspace() as ws, mock.patch.object(creative, "request", helpers.FakeHttp(provider_http)):
            image = creative._fal_image_payload(ws.ctx, "demo/model", "a bottle", "4:5", None, 2, None)
            self.assertEqual(image, {"prompt": "a bottle", "aspect_ratio": "1:1", "num_images": 2})
            video = creative._fal_video_payload(ws.ctx, "demo/model", "a clip", "9:16", 8, "720p", "frame.png")
            self.assertEqual(video, {"prompt": "a clip", "aspect_ratio": "9:16", "duration": "10",
                                     "image_url": {"@upload": "frame.png"}})

    def test_result_urls_are_found_at_any_depth(self):
        result = {"images": [{"url": "https://example.com/a.png", "content_type": "image/png"}],
                  "video": {"url": "https://example.com/v.mp4"}, "seed": 1, "note": {"url": "not-a-link"}}
        self.assertEqual(creative._urls(result, []), [("https://example.com/a.png", "image/png"), ("https://example.com/v.mp4", "")])

    def test_gemini_parts_come_from_model_output_only(self):
        data = {"steps": [{"type": "thought", "content": [{"type": "text", "text": "hidden"}]},
                          {"type": "model_output", "content": [{"type": "text", "text": "shown"}, {"type": "image", "data": "QQ=="}]}]}
        self.assertEqual([p["text"] for p in creative._gemini_parts(data, "text")], ["shown"])
        self.assertEqual(creative._gemini_media(None, data, "image", ".png"), [(b"A", ".png")])


class Commands(unittest.TestCase):
    def test_image_rejects_unknown_aspect_and_unsupported_options(self):
        with helpers.Workspace() as ws:
            ws.ctx.env["GEMINI_API_KEY"] = "gemini-example"
            with self.assertRaises(Refused):
                creative.image(ws.ctx, "x", aspect="7:3")
            with self.assertRaises(Refused):
                creative.image(ws.ctx, "x", provider="gemini", model="any", transparent=True)

    def test_gemini_video_limits(self):
        with helpers.Workspace() as ws:
            ws.ctx.env["GEMINI_API_KEY"] = "gemini-example"
            with self.assertRaises(Refused):
                creative.video(ws.ctx, "x", provider="gemini", model="any", seconds=40)
            with self.assertRaises(Refused):
                creative.video(ws.ctx, "x", provider="gemini", model="any", aspect="1:1")

    def test_generated_files_are_recorded_in_the_manifest(self):
        def http(method, url, kwargs):
            return {"steps": [{"type": "model_output", "content": [{"type": "image", "mime_type": "image/jpeg", "data": "QUJD"}]}]}

        with helpers.Workspace() as ws, mock.patch.object(creative, "request", helpers.FakeHttp(http)):
            ws.ctx.env["GEMINI_API_KEY"] = "gemini-example"
            out = creative.image(ws.ctx, "a bottle on a bench", provider="gemini", model="any-model", aspect="9:16", n=2)
            self.assertEqual(len(out["files"]), 2)
            rows = (ws.ctx.ws / "creatives" / "manifest.jsonl").read_text().splitlines()
            self.assertEqual(len(rows), 2)
            self.assertIn('"aspect": "9:16"', rows[0])
            self.assertNotIn("gemini-example", "".join(rows))


if __name__ == "__main__":
    unittest.main()
