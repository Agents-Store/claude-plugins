"""redact — nothing the plugin prints may carry a value.

Everything printed lands in the session transcript on disk and in the model
context, and there is no after-the-fact edit. So the property under test is
absolute rather than statistical: for every value the fixture declares to be a
credential, that exact string must not survive anywhere in the output.

The fixture holds invented values in real key shapes. Shapes are what the rules
match on, so a fixture of harmless-looking strings would test nothing.
"""

import json
import os
import re
import tempfile
import unittest

import _support                                  # noqa: F401  (path bootstrap)
import redact


ENV_LINE = re.compile(r"^\s*(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=(?P<val>.*)$")


def env_pairs():
    """``name -> raw value`` straight from the fixture, quotes stripped."""
    pairs = {}
    for line in _support.load_text("env-with-keys.env").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = ENV_LINE.match(line)
        if not m:
            continue
        val = m.group("val").strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        pairs[m.group("name")] = val
    return pairs


class ScrubStreamTest(unittest.TestCase):
    """Input carrying keys, output carrying none of their values."""

    def setUp(self):
        self.text = _support.load_text("env-with-keys.env")
        self.pairs = env_pairs()
        self.described = {e["name"]: e for e in
                          redact.read_env_file(_support.fixture_path("env-with-keys.env"))}
        self.result = redact.scrub_stream(self.text)

    def test_the_fixture_actually_contains_credential_shapes(self):
        classified = [n for n, e in self.described.items()
                      if e["klass"] not in ("unclassified", None) and e["status"] == "present"]
        self.assertGreaterEqual(len(classified), 10, "the fixture stopped exercising the rules")

    def test_no_classified_value_survives_anywhere_in_the_output(self):
        for name, entry in self.described.items():
            if entry["klass"] in ("unclassified", None) or entry["status"] != "present":
                continue
            with self.subTest(key=name):
                self.assertNotIn(self.pairs[name], self.result.text)

    def test_each_removal_is_replaced_by_a_fingerprinted_marker(self):
        self.assertGreater(self.result.count, 0)
        self.assertIn("[REDACTED:", self.result.text)
        self.assertIn("fp:", self.result.text)

    def test_the_human_is_told_how_much_was_removed(self):
        marker = self.result.marker()
        self.assertIn(str(self.result.count), marker)
        self.assertTrue(marker.startswith("[scrubbed:"))

    def test_key_names_survive_so_delivery_can_still_be_reasoned_about(self):
        for name in ("ANTHROPIC_API_KEY", "GATEWAY_BEARER_TOKEN", "AWS_ACCESS_KEY_ID"):
            self.assertIn(name, self.result.text)

    def test_metadata_that_is_not_a_secret_is_left_alone(self):
        self.assertIn("OPENCLAW_INSTANCE_LABEL=alpha", self.result.text)
        self.assertIn("OPENCLAW_LOG_LEVEL=info", self.result.text)

    def test_a_second_pass_does_not_redact_the_placeholders_again(self):
        once = redact.scrub(self.text)
        self.assertEqual(redact.scrub(once), once)

    def test_an_empty_value_is_reported_as_empty_not_as_a_fingerprint(self):
        self.assertEqual(self.described["EMPTY_API_KEY"]["status"], "empty")
        self.assertIsNone(self.described["EMPTY_API_KEY"]["fp"])

    def test_redact_argv_scrubs_a_command_line(self):
        argv = ["openclaw", "--token", self.pairs["ANTHROPIC_API_KEY"]]
        self.assertNotIn(self.pairs["ANTHROPIC_API_KEY"], " ".join(redact.redact_argv(argv)))


class FingerprintTest(unittest.TestCase):
    """A fingerprint answers every operational question and none of an attacker's."""

    def test_the_same_value_always_fingerprints_the_same(self):
        self.assertEqual(redact.fp("a-shared-value"), redact.fp("a-shared-value"))

    def test_two_values_fingerprint_differently(self):
        self.assertNotEqual(redact.fp("value-one"), redact.fp("value-two"))

    def test_the_fingerprint_does_not_contain_the_value(self):
        secret = env_pairs()["ANTHROPIC_API_KEY"]
        self.assertNotIn(secret, redact.fp(secret))

    def test_the_shape_is_a_short_prefixed_digest(self):
        value = redact.fp("anything")
        self.assertTrue(value.startswith("fp:"))
        self.assertEqual(len(value), len("fp:") + 8)

    def test_absence_is_reported_as_absence(self):
        self.assertIsNone(redact.fp(None))
        self.assertIsNone(redact.fp(""))

    def test_a_file_is_fingerprinted_without_returning_its_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            same_a = os.path.join(tmp, "a")
            same_b = os.path.join(tmp, "b")
            other = os.path.join(tmp, "c")
            for path, body in ((same_a, "identical"), (same_b, "identical"), (other, "different")):
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(body)
            self.assertEqual(redact.fp_of_file(same_a), redact.fp_of_file(same_b))
            self.assertNotEqual(redact.fp_of_file(same_a), redact.fp_of_file(other))
            self.assertIsNone(redact.fp_of_file(os.path.join(tmp, "absent")))


class EnvFileReaderTest(unittest.TestCase):
    """The env audit's safe half: names, presence, size bucket — never a value."""

    def setUp(self):
        self.entries = redact.read_env_file(_support.fixture_path("env-with-keys.env"))
        self.pairs = env_pairs()

    def test_every_name_is_reported(self):
        self.assertEqual(sorted(e["name"] for e in self.entries), sorted(self.pairs))

    def test_no_value_appears_in_the_returned_structure(self):
        blob = json.dumps(self.entries)
        for name, value in self.pairs.items():
            if not value or name.startswith("OPENCLAW_"):
                continue
            with self.subTest(key=name):
                self.assertNotIn(value, blob)

    def test_env_names_is_names_only(self):
        names = redact.env_names(_support.fixture_path("env-with-keys.env"))
        self.assertIn("ANTHROPIC_API_KEY", names)
        self.assertNotIn(self.pairs["ANTHROPIC_API_KEY"], names)

    def test_a_missing_file_is_reported_rather_than_raising(self):
        entries = redact.read_env_file(_support.fixture_path("no-such-file.env"))
        self.assertEqual(entries[0]["status"], "unreadable")

    def test_the_key_class_is_named_without_the_value(self):
        by_name = {e["name"]: e for e in self.entries}
        self.assertEqual(by_name["ANTHROPIC_API_KEY"]["klass"], "anthropic-key")
        self.assertEqual(by_name["AWS_ACCESS_KEY_ID"]["klass"], "aws-access-key-id")
        self.assertEqual(by_name["DATABASE_PASSWORD"]["klass"], "opaque-secret")


class StructureOnlyTest(unittest.TestCase):
    """Auth profiles are described by shape, expiry and fingerprint — never printed."""

    def setUp(self):
        self.doc = _support.load_json("auth-profiles.json")
        self.reduced = redact.structure_only(self.doc)
        self.blob = json.dumps(self.reduced)

    def test_no_token_value_survives(self):
        for profile in self.doc["profiles"]:
            for key in ("apiKey", "token", "accessToken", "refreshToken"):
                value = profile.get(key)
                if value:
                    with self.subTest(profile=profile["id"], key=key):
                        self.assertNotIn(value, self.blob)

    def test_the_metadata_an_operator_needs_survives_verbatim(self):
        modes = [p["mode"] for p in self.reduced["profiles"]]
        self.assertEqual(modes, ["oauth", "api_key", "token"])
        self.assertEqual(self.reduced["profiles"][0]["expiresAt"], "2026-07-09T11:20:00Z")

    def test_an_identity_collapses_to_a_comparison_key(self):
        email = self.reduced["profiles"][0]["email"]
        self.assertTrue(email.startswith("fp:"))
        self.assertNotIn("operator@example.com", self.blob)

    def test_an_empty_token_is_visible_as_empty(self):
        access = self.reduced["profiles"][0]["accessToken"]
        self.assertFalse(access["present"])
        self.assertEqual(access["len_bucket"], "empty")

    def test_a_present_token_keeps_its_class_and_size_bucket(self):
        api_key = self.reduced["profiles"][1]["apiKey"]
        self.assertTrue(api_key["present"])
        self.assertEqual(api_key["klass"], "anthropic-key")
        self.assertTrue(api_key["fp"].startswith("fp:"))


class ConfigStructureTest(unittest.TestCase):
    """A config can be described well enough to diagnose without printing it."""

    def setUp(self):
        self.doc = _support.load_json("openclaw-config-legacy-refs.json")
        self.reduced = redact.structure_only(self.doc)
        self.blob = json.dumps(self.reduced)

    def test_the_model_chain_stays_readable_so_drift_can_be_seen(self):
        defaults = self.reduced["agents"]["defaults"]
        self.assertEqual(defaults["model"]["primary"], "demo-cli/demo-large")
        self.assertEqual(
            self.reduced["agents"]["defaults"]["models"]["acme/demo-small"]["agentRuntime"]["id"],
            "demo-cli")

    def test_operational_metadata_survives_verbatim(self):
        self.assertEqual(self.reduced["gateway"]["port"], self.doc["gateway"]["port"])
        self.assertTrue(self.reduced["memory"]["enabled"])

    def test_the_gateway_credential_is_described_rather_than_quoted(self):
        token = self.reduced["gateway"]["auth"]["token"]
        self.assertNotIn(self.doc["gateway"]["auth"]["token"], self.blob)
        self.assertTrue(token["present"])
        self.assertTrue(token["fp"].startswith("fp:"))


class FlatPlaceholderTest(unittest.TestCase):
    """One secret, one placeholder — never a placeholder inside a placeholder.

    A later rule must not read the text an earlier rule wrote. The key-value rule
    matches on the word "token", which the placeholder `[REDACTED:bot-token:…]`
    contains, so the second pass used to redact the first one's own label and
    produce `[REDACTED:bot-token:[REDACTED:kv:fp:…]]` — the nesting hides which
    rule fired and buries the fingerprint the operator reads.
    """

    NESTED = re.compile(r"\[REDACTED:[^\]]*\[REDACTED")

    def scrubbed(self, text):
        result = redact.scrub_stream(text)
        self.assertNotRegex(result.text, self.NESTED)
        return result

    def test_a_bot_token_under_an_api_key_header_is_wrapped_once(self):
        result = self.scrubbed("x-api-key: 1234567890:AA%s" % ("b" * 34))
        self.assertEqual(result.by_rule, {"bot-token": 1})
        self.assertEqual(result.text.count("[REDACTED"), 1)

    def test_every_rule_survives_a_line_that_carries_several_secrets(self):
        # Assembled from parts on purpose: a literal of this shape in the file is
        # itself what the publication scrub refuses to ship, fixture or not.
        slack = "xox" + "b-1234567890-" + "d" * 12
        result = self.scrubbed("client_secret: gsk_%s and SLACK_TOKEN=%s" % ("c" * 24, slack))
        self.assertEqual(result.count, 2)
        self.assertEqual(sorted(result.by_rule), ["groq-key", "slack-token"])

    def test_scrubbing_a_scrubbed_line_changes_nothing(self):
        once = redact.scrub("Authorization: Bearer sk-ant-api03-%s" % ("A" * 24))
        self.assertEqual(redact.scrub(once), once)


if __name__ == "__main__":
    unittest.main()
