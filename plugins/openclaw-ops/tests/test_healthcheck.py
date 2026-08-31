"""healthcheck — the severity vocabulary at the one place foreign words enter it.

Every finding this plugin emits carries one of four severities, and every other
place that meets an unknown one raises. The lint check is the single door an
upstream word comes through, and it used to end in `else "info"` — a chain that
turned a spelling nobody had mapped into the quietest class in the report. These
tests pin the translation and pin the refusal.
"""

import unittest

import _support                                  # noqa: F401  (path bootstrap)
import healthcheck


class UpstreamSeverityTest(unittest.TestCase):

    def test_the_mapped_spellings_land_in_the_one_vocabulary(self):
        for word, expected in (("critical", "critical"), ("FATAL", "critical"),
                               ("error", "high"), ("warning", "warn"),
                               ("warn", "warn"), ("info", "info")):
            with self.subTest(word=word):
                self.assertEqual(healthcheck.upstream_severity(word), expected)

    def test_every_translation_target_is_a_severity_this_plugin_declares(self):
        for value in healthcheck.UPSTREAM_SEVERITIES.values():
            self.assertIn(value, healthcheck.SEVERITIES)

    def test_an_unmapped_word_raises_instead_of_becoming_info(self):
        for word in ("blocker", "sev1", "notice", ""):
            with self.subTest(word=word):
                with self.assertRaisesRegex(ValueError, "unknown upstream severity"):
                    healthcheck.upstream_severity(word)

    def test_the_message_names_the_finding_it_came_from(self):
        with self.assertRaisesRegex(ValueError, "fs.permissions"):
            healthcheck.upstream_severity("blocker", "doctor --lint finding 'fs.permissions'")

    def test_a_missing_severity_is_not_quietly_ranked(self):
        with self.assertRaises(ValueError):
            healthcheck.upstream_severity(None)


if __name__ == "__main__":
    unittest.main()
