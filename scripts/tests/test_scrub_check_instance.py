"""instance-name: the words of a plugin's own skill and component names are not deployment names."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import scrub_check  # noqa: E402


def flagged(line):
    return [hit for hit, _ in scrub_check.check_instance(line, None)]


class InstanceNameTest(unittest.TestCase):
    def test_openclaw_plugin_dev_skill_names_pass(self):
        # openclaw-plugin-dev: its own skills were read as deployments and blocked the refresh (2026-11-27)
        for skill in ("openclaw-channel-dev", "openclaw-registration-api", "openclaw-examples",
                      "openclaw-testing-distribution"):
            self.assertEqual(flagged("- `%s` — see the skill" % skill), [], skill)

    def test_mcp_client_name_bridge_passes(self):
        self.assertEqual(flagged('client = new Client({ name: "openclaw-bridge", version: "1.0.0" });'), [])

    def test_real_looking_instance_still_fails(self):
        name = "openclaw" + "-zephyr"      # split, or the gate flags this file itself
        self.assertEqual(flagged("restart %s after the update" % name), [name])


if __name__ == "__main__":
    unittest.main()
