import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, run_check  # noqa: E402

from plugin_test.checks import REGISTRY, api_paths  # noqa: E402
from plugin_test.model import FAIL, INFRA  # noqa: E402

try:
    import yaml  # noqa: F401
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False

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

SPEC_REL = "plugins/a-ops/references/openapi.json"


class ApiPathsTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)

    def make(self, text, spec=json.dumps(SPEC), name="openapi.json"):
        self.repo.plugin("a-ops", files={"skills/s/SKILL.md": text, "references/" + name: spec})
        self.repo.tests("a-ops", {"plugin-test.toml": MANIFEST.replace("openapi.json", name)})

    def check(self, *recipes, **kw):
        """Recipes are the lines of one bash block, starting at file line 3."""
        self.make("# Skill\n```bash\n%s\n```\n" % "\n".join(recipes), **kw)
        return run_check(api_paths, self.repo.root, "a-ops")

    def test_registered(self):
        self.assertIs(REGISTRY["api-paths"], api_paths.run)

    def test_method_of(self):
        self.assertEqual(api_paths.method_of(["curl", "-XPOST", "u"]), "POST")
        self.assertEqual(api_paths.method_of(["curl", "--data-raw=x", "u"]), "POST")
        self.assertEqual(api_paths.method_of(["curl", "-G", "-d", "q=1", "u"]), "GET")
        self.assertEqual(api_paths.method_of(["curl", "-I", "u"]), "HEAD")
        self.assertEqual(api_paths.method_of(["curl", "u"]), "GET")

    def test_method_of_clusters_upload_and_unknown(self):
        self.assertEqual(api_paths.method_of(["curl", "-sXPOST", "u"]), "POST")
        self.assertEqual(api_paths.method_of(["curl", "-sSX", "DELETE", "u"]), "DELETE")
        self.assertEqual(api_paths.method_of(["curl", "-X", "patch", "u"]), "PATCH")
        self.assertEqual(api_paths.method_of(["curl", "-T", "f", "u"]), "PUT")
        self.assertEqual(api_paths.method_of(["curl", "--upload-file=f", "u"]), "PUT")
        self.assertEqual(api_paths.method_of(["curl", "-X", "$METHOD", "u"]), "")
        self.assertEqual(api_paths.method_of(["curl", "--request", "${M}", "u"]), "")

    def test_url_path_skips_option_values(self):
        base = {"API": "", "SITE": ""}
        self.assertEqual(api_paths.url_path(["curl", "-d", '{"l":"${SITE}/x"}', "${API}/issue"], base),
                         ("API", "/issue"))
        self.assertEqual(api_paths.url_path(["curl", "-sSo", "/dev/null", "${API}/search"], base), ("API", "/search"))
        self.assertEqual(api_paths.url_path(["curl", "--url=${API}/issue", "-H", "X: ${SITE}"], base),
                         ("API", "/issue"))
        self.assertEqual(api_paths.url_path(["curl", "--url", "${API}/issue", "${SITE}/other"], base),
                         ("API", "/issue"))
        self.assertEqual(api_paths.url_path(["curl", "-d", "${SITE}/x", "https://example.com"], base), (None, None))

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
        self.assertEqual([(f.level, f.file) for f in found], [(FAIL, SPEC_REL)])

    def test_flag_values_are_not_urls(self):
        self.assertEqual(self.check(
            """curl -s -X POST -d '{"link":"${SITE}/browse/X-1"}' "${API}/issue\"""",
            'curl -s -H "Referer: ${SITE}/x" "${API}/search"',
            'curl -s -e "${SITE}/ref" -u "$USER:$PASS" -o /dev/null "${API}/search"',
            'curl -sSo /dev/null "${API}/search"',
            'curl -s --url "${API}/search" -d q=1',
            'curl -s -d "${SITE}/x" https://example.com/elsewhere'), [])

    def test_real_urls_still_fail_next_to_flags(self):
        found = self.check("""curl -s -H "X: 1" -d '{"a":"${SITE}/ok"}' "${API}/issues\"""")
        self.assertEqual([(f.line, f.level) for f in found], [(3, FAIL)])
        self.assertIn("/issues", found[0].message)

    def test_unknown_method_is_silent_and_clusters_are_read(self):
        self.assertEqual(self.check(
            'curl -s -X "$METHOD" "${API}/issue"',
            'curl -sX POST "${API}/issue" -d x=1',
            'curl -sSX POST "${API}/issue"',
            'curl -sXPUT "${API}/issue/1" -d x=1',
            'curl -T f "${API}/issue/1"',
            'curl --upload-file f "${API}/issue/1"'), [])

    def test_cluster_method_is_still_checked(self):
        found = self.check('curl -sX DELETE "${API}/issue"')
        self.assertEqual([(f.line, f.level) for f in found], [(3, FAIL)])
        self.assertIn("DELETE", found[0].message)
        self.assertIn("POST", found[0].fix)

    def test_malformed_specs_are_findings_with_the_spec_path(self):
        for spec in ['{"paths": []}', '{"paths": {"/a": {"get": {}}}, "servers": 5}', "[]", "null", '{"paths": 5}',
                     '{"paths": {"/a": {"get": {}}}, "servers": {"url": "x"}}']:
            with self.subTest(spec=spec):
                found = self.check('curl -s "${API}/issue"', spec=spec)
                self.assertEqual([(f.level, f.file) for f in found], [(FAIL, SPEC_REL)])
                self.assertTrue(found[0].message.startswith("спецификация не читается: "))

    def test_odd_but_valid_server_entries_are_skipped(self):
        spec = json.dumps({"servers": [None, 5, {"url": None}, {"url": 7}, {"url": "https://h/api/v2"}],
                           "paths": {"/issue": {"post": {}}}})
        self.assertEqual(self.check('curl -s -X POST "${API}/issue"', 'curl -s -X POST "${SITE}/api/v2/issue"',
                                    spec=spec), [])

    @unittest.skipUnless(HAVE_YAML, "PyYAML not installed")
    def test_broken_and_odd_yaml_specs_are_findings(self):
        rel = "plugins/a-ops/references/openapi.yaml"
        for spec in ["paths: [unclosed", "paths:\n  200:\n    get: {}\n", "paths:\n  /a: x\n  - y\n"]:
            with self.subTest(spec=spec):
                found = self.check('curl -s "${API}/issue"', spec=spec, name="openapi.yaml")
                self.assertEqual([(f.level, f.file) for f in found], [(FAIL, rel)])
                self.assertTrue(found[0].message.startswith("спецификация не читается: "))

    @unittest.skipUnless(HAVE_YAML, "PyYAML not installed")
    def test_yaml_error_names_its_class(self):
        found = self.check('curl -s "${API}/issue"', spec="paths: [unclosed", name="openapi.yaml")
        self.assertIn("ParserError", found[0].message)
        self.assertNotIn("\n", found[0].message)

    @unittest.skipUnless(HAVE_YAML, "PyYAML not installed")
    def test_good_yaml_spec(self):
        spec = "paths:\n  /issue:\n    post: {}\n"
        self.assertEqual(self.check('curl -s -X POST "${API}/issue"', spec=spec, name="openapi.yaml"), [])

    def test_missing_pyyaml_is_infra_not_fail(self):
        with mock.patch.dict(sys.modules, {"yaml": None}):
            found = self.check('curl -s "${API}/issue"', spec="paths: {}\n", name="openapi.yaml")
        self.assertEqual([(f.level, f.file) for f in found], [(INFRA, "plugins/a-ops/references/openapi.yaml")])
        self.assertIn("PyYAML", found[0].message)

    def test_missing_spec_file_is_a_finding_without_absolute_path(self):
        self.make(GOOD)
        os.remove(os.path.join(self.repo.root, SPEC_REL))
        found = run_check(api_paths, self.repo.root, "a-ops")
        self.assertEqual([(f.level, f.file) for f in found], [(FAIL, SPEC_REL)])
        self.assertNotIn(self.repo.root, found[0].message)


if __name__ == "__main__":
    unittest.main()
