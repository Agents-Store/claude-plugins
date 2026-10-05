import json
import os
import re
import shutil
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plugin_test_fixtures  # noqa: E402,F401  (sys.path для plugin_test)

from plugin_test import evalgen  # noqa: E402
from plugin_test.evalsrc import QualityCase, TriggerQuery  # noqa: E402

RE_DOC = re.compile(r"\A---\n(.*?)\n---\n\n(.*)\Z", re.S)


def parse(path):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = RE_DOC.match(text)
    assert m, text
    return yaml.safe_load(m.group(1)), m.group(2)


def tree(root):
    out = {}
    for d, _, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            with open(p, "rb") as fh:
                out[os.path.relpath(p, root)] = fh.read()
    return out


class EvalgenTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="evalgen-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.copy = os.path.join(self.tmp, "copy")
        os.makedirs(self.copy)

    def test_names(self):
        self.assertEqual(evalgen.quality_name("alpha", "3"), "q-alpha-3")
        self.assertEqual(evalgen.trigger_name("s", "hello"), "t-s-aaf4c61d")
        self.assertEqual(evalgen.trigger_name("s", "hello"), evalgen.trigger_name("s", "hello"))
        self.assertEqual(evalgen.native_name("smoke"), "n-smoke")

    def test_input_match_is_exact(self):
        pat = re.compile(evalgen.input_match("p-dev", "api-reference"))
        self.assertTrue(pat.search('{"skill":"p-dev:api-reference"}'))
        self.assertTrue(pat.search('{"skill": "api-reference"}'))
        self.assertFalse(pat.search('{"skill":"p-dev:api"}'))
        self.assertFalse(pat.search('{"skill":"other:api-reference"}'))
        short = re.compile(evalgen.input_match("p-dev", "api"))
        self.assertFalse(short.search('{"skill":"p-dev:api-reference"}'))
        self.assertFalse(short.search('{"skill":"other:api"}'))
        self.assertTrue(short.search('{"skill":"p-dev:api"}'))
        dotted = re.compile(evalgen.input_match("a.b", "x"))
        self.assertFalse(dotted.search('{"skill":"aXb:x"}'))

    def test_trigger_tree(self):
        queries = [TriggerQuery("web", "grab https://example.com", True), TriggerQuery("web", "parse my html", False)]
        cases = evalgen.write_triggers(self.copy, evalgen.TRIGGER_DIR, "p-dev", queries)
        self.assertEqual(set(cases), {evalgen.trigger_name("web", q.query) for q in queries})
        root = os.path.join(self.copy, evalgen.TRIGGER_DIR)
        self.assertFalse(os.path.exists(os.path.join(root, "mocks")))
        pos = os.path.join(root, evalgen.trigger_name("web", queries[0].query))
        front, body = parse(os.path.join(pos, "prompt.md"))
        self.assertEqual(front, {"tags": ["trigger", "skill:web"], "runs": 1, "max_turns": 1, "allowed_tools": ["Skill"]})
        self.assertEqual(body, "grab https://example.com\n")
        g, gbody = parse(os.path.join(pos, "graders", "fired.md"))
        self.assertEqual((g["type"], g["tool"], g["min"], g["arm"]), ("tool_used", "Skill", 1, "both"))
        self.assertNotIn("max", g)
        self.assertEqual(g["input_match"], evalgen.input_match("p-dev", "web"))
        self.assertEqual(gbody, "")
        neg = os.path.join(root, evalgen.trigger_name("web", queries[1].query))
        g2, _ = parse(os.path.join(neg, "graders", "fired.md"))
        self.assertEqual((g2["min"], g2["max"], g2["arm"]), (0, 0, "both"))

    def test_trigger_only_subset(self):
        queries = [TriggerQuery("web", "a", True), TriggerQuery("web", "b", False)]
        keep = evalgen.trigger_name("web", "b")
        cases = evalgen.write_triggers(self.copy, evalgen.RERUN_DIR, "p-dev", queries, only={keep})
        self.assertEqual(list(cases), [keep])
        self.assertEqual(os.listdir(os.path.join(self.copy, evalgen.RERUN_DIR)), [keep])

    def test_prompt_with_quotes_and_dashes_roundtrips(self):
        query = 'он сказал "привет" \\ и ушёл\n---\nname: evil\n--- конец: да'
        evalgen.write_triggers(self.copy, evalgen.TRIGGER_DIR, "p-dev", [TriggerQuery("web", query, True)])
        path = os.path.join(self.copy, evalgen.TRIGGER_DIR, evalgen.trigger_name("web", query), "prompt.md")
        front, body = parse(path)
        self.assertEqual(front["tags"], ["trigger", "skill:web"])
        self.assertEqual(body, query + "\n")

    def test_quality_tree_invocable(self):
        cases = [QualityCase("web", "1", "how to scrape", ("uses map", "uses scrape"), "x", False),
                 QualityCase("web", "2", "compare", (), "the expected outcome", False)]
        meta = evalgen.write_quality(self.copy, "p-dev", cases, {"web": True}, {})
        self.assertEqual(meta, {"q-web-1": {"kind": "quality", "skill": "web", "id": "1"},
                                "q-web-2": {"kind": "quality", "skill": "web", "id": "2"}})
        root = os.path.join(self.copy, evalgen.QUALITY_DIR)
        front, body = parse(os.path.join(root, "q-web-1", "prompt.md"))
        self.assertEqual(front, {"tags": ["quality", "skill:web"], "runs": 3,
                                 "allowed_tools": ["Read", "Grep", "Glob", "Skill"]})
        self.assertEqual(body, "how to scrape\n")
        graders = sorted(os.listdir(os.path.join(root, "q-web-1", "graders")))
        self.assertEqual(graders, ["e1.md", "e2.md", "fired.md"])
        e1, rubric = parse(os.path.join(root, "q-web-1", "graders", "e1.md"))
        self.assertEqual(e1, {"type": "llm"})
        self.assertIn("uses map", rubric)
        fired, _ = parse(os.path.join(root, "q-web-1", "graders", "fired.md"))
        self.assertEqual((fired["type"], fired["arm"]), ("tool_used", "with-only"))
        exp, rubric2 = parse(os.path.join(root, "q-web-2", "graders", "expected.md"))
        self.assertEqual(exp, {"type": "llm"})
        self.assertIn("the expected outcome", rubric2)

    def test_quality_dmi_skill_is_slash_invoked(self):
        cases = [QualityCase("ref", "1", "show endpoints", ("lists endpoints",), "", False)]
        evalgen.write_quality(self.copy, "p-dev", cases, {"ref": False}, {})
        root = os.path.join(self.copy, evalgen.QUALITY_DIR, "q-ref-1")
        _, body = parse(os.path.join(root, "prompt.md"))
        self.assertEqual(body, "/p-dev:ref show endpoints\n")
        self.assertEqual(sorted(os.listdir(os.path.join(root, "graders"))), ["e1.md"])

    def test_quality_skips_cases_with_files(self):
        cases = [QualityCase("web", "1", "p", ("c",), "", True)]
        self.assertEqual(evalgen.write_quality(self.copy, "p-dev", cases, {"web": True}, {}), {})

    def test_mocks_from_snapshots(self):
        snap = os.path.join(self.tmp, "fc.tools.json")
        data = {"tools": [{"name": "scrape", "description": "d", "inputSchema": {"type": "object"}},
                          {"name": "map", "description": "d", "inputSchema": {"type": "object"}}]}
        with open(snap, "w") as fh:
            json.dump(data, fh)
        broken = os.path.join(self.tmp, "bad.tools.json")
        with open(broken, "w") as fh:
            fh.write("{")
        evalgen.write_quality(self.copy, "p-dev", [QualityCase("web", "1", "p", ("c",), "", False)],
                              {"web": True}, {"firecrawl": snap, "bad": broken, "gone": os.path.join(self.tmp, "x.json")})
        mocks = os.path.join(self.copy, evalgen.QUALITY_DIR, "mocks")
        self.assertEqual(os.listdir(mocks), ["firecrawl"])
        with open(os.path.join(mocks, "firecrawl", "_tools.json")) as fh:
            self.assertEqual(json.load(fh), data)
        front, body = parse(os.path.join(mocks, "firecrawl", "_server.md"))
        self.assertEqual(front, {"type": "agent", "tools": ["map", "scrape"]})
        self.assertIn('"firecrawl"', body)

    def test_native_cases_copied_with_prefix_and_mocks_override(self):
        native = os.path.join(self.tmp, "native")
        os.makedirs(os.path.join(native, "smoke", "graders"))
        os.makedirs(os.path.join(native, "mocks", "firecrawl"))
        with open(os.path.join(native, "smoke", "prompt.md"), "w") as fh:
            fh.write("---\nruns: 1\n---\n\nhi\n")
        with open(os.path.join(native, "smoke", "graders", "g.md"), "w") as fh:
            fh.write("---\ntype: llm\n---\n\nPASS if hi.\n")
        with open(os.path.join(native, "mocks", "firecrawl", "scrape.md"), "w") as fh:
            fh.write("fixed answer\n")
        meta = evalgen.write_quality(self.copy, "p-dev", [], {}, {}, native_root=native, native_names=("smoke",))
        self.assertEqual(meta, {"n-smoke": {"kind": "native", "skill": "", "id": "smoke"}})
        root = os.path.join(self.copy, evalgen.QUALITY_DIR)
        self.assertTrue(os.path.isfile(os.path.join(root, "n-smoke", "graders", "g.md")))
        with open(os.path.join(root, "mocks", "firecrawl", "scrape.md")) as fh:
            self.assertEqual(fh.read(), "fixed answer\n")

    def test_deterministic(self):
        q = [TriggerQuery("web", "a", True), TriggerQuery("web", "b", False)]
        c = [QualityCase("web", "1", "p", ("c1", "c2"), "e", False)]
        roots = []
        for name in ("one", "two"):
            copy = os.path.join(self.tmp, name)
            os.makedirs(copy)
            evalgen.write_triggers(copy, evalgen.TRIGGER_DIR, "p-dev", q)
            evalgen.write_quality(copy, "p-dev", c, {"web": True}, {})
            roots.append(tree(copy))
        self.assertEqual(roots[0], roots[1])

    def test_copy_plugin_skips_git_and_generated(self):
        src = os.path.join(self.tmp, "src")
        for rel in ("skills/a/SKILL.md", ".git/HEAD", "evals-trigger/x/prompt.md", ".claude-plugin/plugin.json"):
            os.makedirs(os.path.dirname(os.path.join(src, rel)), exist_ok=True)
            with open(os.path.join(src, rel), "w") as fh:
                fh.write("x")
        dest = evalgen.copy_plugin(src, os.path.join(self.tmp, "dest"))
        self.assertEqual(sorted(tree(dest)), [os.path.join(".claude-plugin", "plugin.json"),
                                              os.path.join("skills", "a", "SKILL.md")])


if __name__ == "__main__":
    unittest.main()
