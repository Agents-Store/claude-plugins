import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, load_plugin  # noqa: E402

from plugin_test import envfile, manifest  # noqa: E402
from plugin_test.model import FAIL, WARN  # noqa: E402

FULL = '''
[mcp.dataforseo]
start = "ci"
env = { DATAFORSEO_USERNAME = "dummy", DATAFORSEO_PASSWORD = "dummy" }

[mcp.nocodb]
snapshot = "names"

[cli.infisical]
version = "0.43.138"
commands = ["login", "secrets set"]

[[api]]
spec = "skills/api/references/jira.json"
base_vars = { JIRA = "/rest/api/3", JIRA_ROOT = "" }

[[api]]
spec = "skills/api/references/conf.json"
base_vars = ["CONF"]

[[unit]]
name = "suite"
run = "python3 -m unittest"
cwd = "plugins/demo-dev"
needs = ["python3"]
timeout = 30

[budget]
always_on_tokens = 5000

[skip]
"skill-snippets" = ["skills/legacy/*"]
'''


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.repo.plugin("demo-dev")

    def load(self, text=None):
        if text is not None:
            self.repo.tests("demo-dev", {"plugin-test.toml": text})
        return manifest.load(load_plugin(self.repo.root, "demo-dev"))

    def test_absent_manifest_is_empty(self):
        m, findings = self.load()
        self.assertEqual(findings, [])
        self.assertEqual(m.mcp_spec("x").start, "server")
        self.assertEqual(m.always_on_tokens, manifest.DEFAULT_ALWAYS_ON)

    def test_full_manifest(self):
        m, findings = self.load(FULL)
        self.assertEqual(findings, [])
        self.assertEqual(m.mcp_spec("dataforseo").start, "ci")
        self.assertEqual(m.mcp_spec("dataforseo").env["DATAFORSEO_USERNAME"], "dummy")
        self.assertEqual((m.mcp_spec("dataforseo").snapshot, m.mcp_spec("nocodb").snapshot), ("full", "names"))
        self.assertEqual(m.cli["infisical"].bin, "infisical")
        self.assertEqual(m.cli["infisical"].commands, ["login", "secrets set"])
        self.assertEqual(m.api[0].base_vars, {"JIRA": "/rest/api/3", "JIRA_ROOT": ""})
        self.assertEqual(m.api[1].base_vars, {"CONF": ""})
        self.assertEqual((m.unit[0].cwd, m.unit[0].timeout, m.unit[0].needs), ("plugins/demo-dev", 30, ["python3"]))
        self.assertEqual(m.skip["skill-snippets"], ["skills/legacy/*"])
        self.assertEqual(m.always_on_tokens, 5000)

    def test_single_api_table_is_accepted(self):
        m, findings = self.load('[api]\nspec = "a.json"\nbase_vars = ["X"]\n')
        self.assertEqual(findings, [])
        self.assertEqual(m.api[0].spec, "a.json")

    def test_malformed_toml_is_a_finding(self):
        m, findings = self.load("[mcp.x\nstart = ")
        self.assertEqual(len(findings), 1)
        self.assertEqual((findings[0].check, findings[0].level), ("manifest", FAIL))
        self.assertEqual(findings[0].file, "tests/plugins/demo-dev/plugin-test.toml")
        self.assertEqual(m.mcp, {})

    def test_bad_values_are_findings(self):
        m, findings = self.load('extra = 1\n[mcp.x]\nstart = "always"\n[skip]\n"nope" = ["a"]\n'
                                '[[unit]]\nname = "no run"\n[[unit]]\nrun = "x"\ntimeout = "slow"\n')
        levels = sorted((f.level, f.message.split()[0]) for f in findings)
        self.assertIn(FAIL, [lvl for lvl, _ in levels])
        self.assertIn(WARN, [lvl for lvl, _ in levels])
        self.assertEqual(len(findings), 5)
        self.assertEqual(m.mcp_spec("x").start, "server")
        self.assertEqual(m.unit, [])

    def test_wrong_section_types_are_findings_not_tracebacks(self):
        m, findings = self.load('mcp = 1\ncli = "x"\nskip = 1\napi = 5\nunit = 3\nbudget = 2\n')
        self.assertEqual(len(findings), 6)
        for f in findings:
            self.assertEqual((f.check, f.level), ("manifest", FAIL))
            self.assertEqual(f.file, "tests/plugins/demo-dev/plugin-test.toml")
        for key in ("mcp", "cli", "skip", "api", "unit", "budget"):
            self.assertEqual(sum("[%s]" % key in f.message for f in findings), 1, key)
        self.assertEqual((m.mcp, m.cli, m.api, m.unit, m.skip), ({}, {}, [], [], {}))
        self.assertEqual(m.always_on_tokens, manifest.DEFAULT_ALWAYS_ON)

    def test_falsy_wrong_section_types_are_findings(self):
        m, findings = self.load('mcp = 0\nskip = false\nbudget = ""\nunit = {}\n')
        self.assertEqual([f.level for f in findings], [FAIL] * 4)
        self.assertEqual(m.always_on_tokens, manifest.DEFAULT_ALWAYS_ON)

    def test_bool_is_not_an_integer(self):
        m, findings = self.load('[[unit]]\nrun = "x"\ntimeout = true\n[budget]\nalways_on_tokens = true\n')
        self.assertEqual([(f.check, f.level) for f in findings], [("manifest", FAIL)] * 2)
        self.assertEqual(m.unit, [])
        self.assertEqual(m.always_on_tokens, manifest.DEFAULT_ALWAYS_ON)

    def test_not_utf8_is_a_finding(self):
        self.repo.tests("demo-dev", {"plugin-test.toml": ""})
        path = manifest.path_of(load_plugin(self.repo.root, "demo-dev"))
        with open(path, "wb") as fh:
            fh.write(b'[mcp.x]\nstart = "\xff"\n')
        m, findings = manifest.load(load_plugin(self.repo.root, "demo-dev"))
        self.assertEqual([(f.check, f.level) for f in findings], [("manifest", FAIL)])
        self.assertEqual(m.mcp, {})

    def test_huge_integer_is_a_finding(self):
        m, findings = self.load("[budget]\nalways_on_tokens = %s\n" % ("9" * 5000))
        self.assertEqual([(f.check, f.level, f.file) for f in findings],
                         [("manifest", FAIL, "tests/plugins/demo-dev/plugin-test.toml")])
        self.assertEqual(m.always_on_tokens, manifest.DEFAULT_ALWAYS_ON)

    def test_deep_nesting_is_a_finding(self):
        m, findings = self.load("x = %s1%s\n" % ("[" * 100000, "]" * 100000))
        self.assertEqual([(f.check, f.level) for f in findings], [("manifest", FAIL)])
        self.assertEqual(m.mcp, {})

    def test_unreadable_file_is_a_finding_without_the_absolute_path(self):
        self.load("")
        plugin = load_plugin(self.repo.root, "demo-dev")
        denied = PermissionError(13, "Permission denied", manifest.path_of(plugin))
        with mock.patch("plugin_test.manifest.open", side_effect=denied, create=True):
            m, findings = manifest.load(plugin)
        self.assertEqual([(f.check, f.level, f.file) for f in findings],
                         [("manifest", FAIL, "tests/plugins/demo-dev/plugin-test.toml")])
        self.assertNotIn(self.repo.root, findings[0].message)
        self.assertEqual(m.mcp, {})


class EnvFileTest(unittest.TestCase):
    def test_parse(self):
        env = envfile.parse('# c\nA=1\nexport B="two words"\nC=\'q\'\nD=v # note\nbad line\n=x\n'
                            'E="v" # c\nF=\'w\'  # d\n')
        self.assertEqual(env, {"A": "1", "B": "two words", "C": "q", "D": "v", "E": "v", "F": "w"})

    def test_expand(self):
        self.assertEqual(envfile.expand("${A}/x/${B:-dflt}/${C}", {"A": "a"}), ("a/x/dflt/", ["C"]))
        self.assertEqual(envfile.expand("${E:-d}", {"E": ""}), ("d", []))

    def test_expand_obj(self):
        obj, missing = envfile.expand_obj({"args": ["--k", "${K}"], "env": {"U": "${U}"}, "n": 1}, {"K": "kk"})
        self.assertEqual(obj, {"args": ["--k", "kk"], "env": {"U": ""}, "n": 1})
        self.assertEqual(missing, ["U"])


if __name__ == "__main__":
    unittest.main()
