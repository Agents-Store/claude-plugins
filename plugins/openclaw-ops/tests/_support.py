"""Shared bootstrap for the openclaw-ops test suite.

Level 2 of the verification ladder: dry fixtures, no server. Nothing in this
suite talks to a Docker daemon, a gateway, or the network — every input comes
from ``fixtures/`` and every output goes to a temporary directory.

The scripts are not an installed package; the commands run them as files. The
tests import them the same way, by putting ``scripts/`` and ``scripts/lib/`` on
the path, so a test exercises exactly the module a command would load.
"""

import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(TESTS_DIR)
FIXTURES = os.path.join(PLUGIN_ROOT, "fixtures")

for _entry in (os.path.join(PLUGIN_ROOT, "scripts", "lib"),
               os.path.join(PLUGIN_ROOT, "scripts")):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)


def fixture_path(*parts):
    """Absolute path of a fixture, so a test never depends on the working directory."""
    return os.path.join(FIXTURES, *parts)


def load_json(*parts):
    with open(fixture_path(*parts), "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_text(*parts):
    with open(fixture_path(*parts), "r", encoding="utf-8") as fh:
        return fh.read()
