import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, run_check  # noqa: E402

from plugin_test.checks import REGISTRY, api_paths  # noqa: E402
from plugin_test.model import FAIL  # noqa: E402

SPEC = {"openapi": "3.0.1", "servers": [{"url": "https://{site}/api/v2"}], "paths": {
    "/issue": {"post": {}},
    "/issue/{key}": {"get": {}, "put": {}, "delete": {}},
    "/issue/{key}/comment": {"get": {}, "post": {}},
    "/search": {"get": {}, "post": {}},
}}

GOOD = '''# Skill
```bash
API="${SITE}/api/v2"
curl -s "${AUTH[@]}" -X POST "${API}/issue" -d '{"a": 1}'
curl -s "$API/issue/PROJ-1?fields=summary"
curl -s -X DELETE "${API}/issue/${KEY}"
curl -s --request=PUT "${API}/issue/$KEY" --json '{}'
KEY=$(curl -s -d "{
  \\"q\\": 1
}" "${API}/issue" | jq -r .key)
curl -s "${SITE}/api/v2/search"
curl -s https://example.com/not/checked
```
'''

BROKEN = '''# Skill
```bash
curl -s "${API}/issues"
curl -s -X PATCH "${API}/issue/X"
curl -s -X DELETE "${API}/search"
curl -s "${SITE}/rest/api/2/search"
```
'''

MANIFEST = '[api]\nspec = "references/openapi.json"\nbase_vars = { API = "", SITE = "" }\n'


class ApiPathsTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)

    def make(self, text, spec=json.dumps(SPEC)):
        self.repo.plugin("a-ops", files={"skills/s/SKILL.md": text, "references/openapi.json": spec})
        self.repo.tests("a-ops", {"plugin-test.toml": MANIFEST})

    def test_registered(self):
        self.assertIs(REGISTRY["api-paths"], api_paths.run)

    def test_method_of(self):
        self.assertEqual(api_paths.method_of(["curl", "-XPOST", "u"]), "POST")
        self.assertEqual(api_paths.method_of(["curl", "--data-raw=x", "u"]), "POST")
        self.assertEqual(api_paths.method_of(["curl", "-G", "-d", "q=1", "u"]), "GET")
        self.assertEqual(api_paths.method_of(["curl", "-I", "u"]), "HEAD")
        self.assertEqual(api_paths.method_of(["curl", "u"]), "GET")

    def test_good(self):
        self.make(GOOD)
        self.assertEqual(run_check(api_paths, self.repo.root, "a-ops"), [])

    def test_broken(self):
        self.make(BROKEN)
        found = run_check(api_paths, self.repo.root, "a-ops")
        self.assertEqual([(f.line, f.level) for f in found], [(3, FAIL), (4, FAIL), (5, FAIL), (6, FAIL)])
        self.assertIn("/issues", found[0].message)
        self.assertIn("PATCH", found[1].message)
        self.assertIn("DELETE", found[1].fix)

    def test_bad_spec(self):
        self.make(GOOD, spec="{nope")
        found = run_check(api_paths, self.repo.root, "a-ops")
        self.assertEqual([(f.level, f.file) for f in found], [(FAIL, "plugins/a-ops/references/openapi.json")])


if __name__ == "__main__":
    unittest.main()
