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

    def test_input_match_with_alias_commands(self):
        pat = re.compile(evalgen.input_match("p-dev", "explain-code", ("explain", "walk.through")))
        for ok in ('{"skill":"p-dev:explain-code"}', '{"skill": "explain"}', '{"skill":"p-dev:explain"}',
                   '{"skill" : "p-dev:walk.through"}'):
            self.assertTrue(pat.search(ok), ok)
        for bad in ('{"skill":"other:explain"}', '{"skill":"p-dev:explain-more"}', '{"skill":"p-dev:walkXthrough"}',
                    '{"skill":"p-dev:code"}', '{"skill":"p-dev:explain:x"}', '{"skill":"xp-dev:explain"}'):
            self.assertFalse(pat.search(bad), bad)
        plain = re.compile(evalgen.input_match("p-dev", "explain-code"))
        self.assertTrue(plain.search('{"skill":"p-dev:explain-code"}'))
        self.assertFalse(plain.search('{"skill":"p-dev:explain"}'))     # без alias команда — не срабатывание
        self.assertEqual(evalgen.input_match("p-dev", "s"), evalgen.input_match("p-dev", "s", ()))

    def test_skill_routes(self):
        src = os.path.join(self.tmp, "routes")
        for skill in ("api", "api-reference", "deep-research", "lonely"):
            os.makedirs(os.path.join(src, "skills", skill))
            with open(os.path.join(src, "skills", skill, "SKILL.md"), "w") as fh:
                fh.write("x")
        os.makedirs(os.path.join(src, "skills", "no-skill-md"))
        commands = {
            "explain": "Read `${CLAUDE_PLUGIN_ROOT}/skills/api-reference/SKILL.md` first.\n",
            "review": "Use the p-dev:deep-research skill.\n",
            "zeta": "skills/api/ and also /p-dev:deep-research.\n",
            "alpha": "see skills/api-reference/references/x.md and `p-dev:api`.\n",
            "deep-research": "this command repeats skills/deep-research/ — its own namesake.\n",
            "longer": "only p-dev:api-reference, p-dev:deep-researcher and skills/api-reference-v2/.\n",
            "foreign": "other-dev:api, xp-dev:lonely, myskills/lonely/, skills/no-skill-md/ and skills/ghost/.\n",
            "plain": "no routing here at all\n",
        }
        os.makedirs(os.path.join(src, "commands"))
        for name, text in commands.items():
            with open(os.path.join(src, "commands", name + ".md"), "w", encoding="utf-8") as fh:
                fh.write(text)
        with open(os.path.join(src, "commands", "notes.txt"), "w") as fh:
            fh.write("skills/lonely/ p-dev:lonely\n")
        routes = evalgen.skill_routes(src, "p-dev")
        self.assertEqual(routes, {"api": ["alpha", "zeta"],
                                  "api-reference": ["alpha", "explain", "longer"],
                                  "deep-research": ["review", "zeta"]})
        self.assertEqual(evalgen.skill_routes(src, "p-dev"), routes)              # детерминировано
        self.assertEqual(list(routes), sorted(routes))

    def routes_plugin(self, skills, commands, name="routes2"):
        src = os.path.join(self.tmp, name)
        for skill in skills:
            os.makedirs(os.path.join(src, "skills", skill))
            with open(os.path.join(src, "skills", skill, "SKILL.md"), "w") as fh:
                fh.write("x")
        os.makedirs(os.path.join(src, "commands"))
        for command, text in commands.items():
            with open(os.path.join(src, "commands", command + ".md"), "w", encoding="utf-8") as fh:
                fh.write(text)
        return src

    def test_command_named_like_any_skill_is_never_an_alias(self):
        # {"skill":"p-dev:reconcile"} — одна и та же строка для skill и для команды: по ней не отличить, что сработало
        src = self.routes_plugin(
            ["planning", "reconcile", "intake", "setup"],
            {"planning": "Read skills/reconcile/SKILL.md.\n",
             "reconcile": "Read skills/intake/SKILL.md.\n",
             "intake": "Read skills/setup/SKILL.md.\n",
             "start": "Read skills/intake/SKILL.md and skills/setup/SKILL.md.\n"})
        self.assertEqual(evalgen.skill_routes(src, "p-dev"), {"intake": ["start"], "setup": ["start"]})

    def test_hub_command_is_not_an_alias(self):
        self.assertEqual(evalgen.MAX_ROUTES_PER_COMMAND, 2)
        skills = ["a", "b", "c", "d"]
        src = self.routes_plugin(skills, {
            "pair": "skills/a/ and skills/b/.\n",                        # 2 skill-ов — ещё alias
            "hub": "skills/a/, skills/b/ and p-dev:c — three skills.\n",   # 3 skill-а — хаб, не alias
            "wide": "skills/a/ skills/b/ skills/c/ skills/d/\n",
            "single": "skills/c/\n"})
        self.assertEqual(evalgen.skill_routes(src, "p-dev"), {"a": ["pair"], "b": ["pair"], "c": ["single"]})

    def test_hub_does_not_make_siblings_fire_negatives(self):
        src = self.routes_plugin(["a", "b", "c"], {"check": "skills/a/ skills/b/ skills/c/\n"})
        self.assertEqual(evalgen.skill_routes(src, "p-dev"), {})

    def test_skill_routes_without_commands_or_skills(self):
        src = os.path.join(self.tmp, "bare")
        os.makedirs(os.path.join(src, "skills", "a"))
        with open(os.path.join(src, "skills", "a", "SKILL.md"), "w") as fh:
            fh.write("x")
        self.assertEqual(evalgen.skill_routes(src, "p-dev"), {})
        self.assertEqual(evalgen.skill_routes(os.path.join(self.tmp, "absent"), "p-dev"), {})

    def test_trigger_graders_accept_routed_commands(self):
        queries = [TriggerQuery("web", "explain this", True), TriggerQuery("web", "unrelated", False),
                   TriggerQuery("other", "something", True)]
        evalgen.write_triggers(self.copy, evalgen.TRIGGER_DIR, "p-dev", queries, routes={"web": ["explain"]})
        root = os.path.join(self.copy, evalgen.TRIGGER_DIR)
        pos, _ = parse(os.path.join(root, evalgen.trigger_name("web", "explain this"), "graders", "fired.md"))
        neg, _ = parse(os.path.join(root, evalgen.trigger_name("web", "unrelated"), "graders", "fired.md"))
        none, _ = parse(os.path.join(root, evalgen.trigger_name("other", "something"), "graders", "fired.md"))
        self.assertEqual(pos["input_match"], evalgen.input_match("p-dev", "web", ("explain",)))
        self.assertEqual(neg["input_match"], pos["input_match"])
        self.assertEqual((pos["min"], "max" in pos), (1, False))
        self.assertEqual((neg["min"], neg["max"]), (0, 0))        # сработавшая команда — провал «не должен срабатывать»
        self.assertTrue(re.search(neg["input_match"], '{"skill":"p-dev:explain"}'))
        self.assertFalse(re.search(neg["input_match"], '{"skill":"other-dev:explain"}'))
        self.assertEqual(none["input_match"], evalgen.input_match("p-dev", "other"))     # у другого skill alias нет

    def test_routes_default_changes_nothing(self):
        q = [TriggerQuery("web", "a", True), TriggerQuery("web", "b", False)]
        c = [QualityCase("web", "1", "p", ("c",), "e", False)]
        roots = []
        for name, kw in (("one", {}), ("two", {"routes": None}), ("three", {"routes": {}})):
            copy = os.path.join(self.tmp, name)
            os.makedirs(copy)
            evalgen.write_triggers(copy, evalgen.TRIGGER_DIR, "p-dev", q, **kw)
            evalgen.write_quality(copy, "p-dev", c, {"web": True}, {}, **kw)
            roots.append(tree(copy))
        self.assertEqual(roots[0], roots[1])
        self.assertEqual(roots[0], roots[2])

    def test_quality_fired_indicator_accepts_routed_commands(self):
        cases = [QualityCase("web", "1", "how", ("c",), "", False), QualityCase("ref", "1", "show", ("c",), "", False)]
        evalgen.write_quality(self.copy, "p-dev", cases, {"web": True, "ref": False}, {},
                              routes={"web": ["explain"], "ref": ["status"]})
        root = os.path.join(self.copy, evalgen.QUALITY_DIR)
        fired, _ = parse(os.path.join(root, "q-web-1", "graders", "fired.md"))
        self.assertEqual(fired["input_match"], evalgen.input_match("p-dev", "web", ("explain",)))
        self.assertEqual(fired["arm"], "with-only")
        self.assertFalse(os.path.exists(os.path.join(root, "q-ref-1", "graders", "fired.md")))

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

    def make_plugin(self, manifest_text, name="src"):
        src = os.path.join(self.tmp, name)
        path = os.path.join(src, ".claude-plugin", "plugin.json")
        os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(manifest_text)
        os.makedirs(os.path.join(src, "skills", "a"))
        with open(os.path.join(src, "skills", "a", "SKILL.md"), "w") as fh:
            fh.write("x")
        return src

    def manifest_of(self, root):
        with open(os.path.join(root, ".claude-plugin", "plugin.json"), "rb") as fh:
            return fh.read()

    def test_copy_plugin_drops_dependencies_from_the_copy_only(self):
        original = json.dumps({"name": "p-dev", "version": "1.0.0", "dependencies": ["web-search-dev"],
                               "author": {"name": "Ж"}}, ensure_ascii=False)
        src = self.make_plugin(original)
        dest = evalgen.copy_plugin(src, os.path.join(self.tmp, "dest"))
        self.assertEqual(json.loads(self.manifest_of(dest)), {"name": "p-dev", "version": "1.0.0", "author": {"name": "Ж"}})
        self.assertEqual(self.manifest_of(src), original.encode("utf-8"))      # источник не тронут
        text = self.manifest_of(dest).decode("utf-8")
        self.assertIn('\n  "name"', text)                                      # indent=2
        self.assertIn("Ж", text)                                               # не \\u-эскейпы

    def test_copy_plugin_keeps_manifest_without_dependencies_byte_identical(self):
        odd = '{ "name":"p-dev",\r\n\t"version" : "1.0.0" }\r\n'
        src = self.make_plugin(odd)
        dest = evalgen.copy_plugin(src, os.path.join(self.tmp, "dest"))
        self.assertEqual(self.manifest_of(dest), odd.encode("utf-8"))

    def test_copy_plugin_leaves_unreadable_manifest_alone(self):
        for bad in ("{ not json", "[1, 2]", '"dependencies"', ""):
            with self.subTest(bad=bad):
                src = self.make_plugin(bad, name="bad")
                dest = evalgen.copy_plugin(src, os.path.join(self.tmp, "dest-bad"))
                self.assertEqual(self.manifest_of(dest), bad.encode("utf-8"))
                shutil.rmtree(src)
                shutil.rmtree(dest)

    def test_copy_plugin_does_not_write_through_a_manifest_symlink(self):
        real = os.path.join(self.tmp, "shared.json")
        original = json.dumps({"name": "p-dev", "dependencies": ["x"]})
        with open(real, "w", encoding="utf-8") as fh:
            fh.write(original)
        src = os.path.join(self.tmp, "linked")
        os.makedirs(os.path.join(src, ".claude-plugin"))
        os.symlink(real, os.path.join(src, ".claude-plugin", "plugin.json"))
        dest = evalgen.copy_plugin(src, os.path.join(self.tmp, "dest-link"))
        with open(real, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), original)
        self.assertFalse(os.path.islink(os.path.join(dest, ".claude-plugin", "plugin.json")))
        self.assertEqual(json.loads(self.manifest_of(dest)), {"name": "p-dev"})

    def test_copy_plugin_leaves_manifest_outside_the_copy_alone(self):
        outside = os.path.join(self.tmp, "outside")
        os.makedirs(outside)
        original = json.dumps({"name": "p-dev", "dependencies": ["x"]})
        with open(os.path.join(outside, "plugin.json"), "w", encoding="utf-8") as fh:
            fh.write(original)
        src = os.path.join(self.tmp, "dirlink")
        os.makedirs(src)
        os.symlink(outside, os.path.join(src, ".claude-plugin"))
        evalgen.copy_plugin(src, os.path.join(self.tmp, "dest-dirlink"))
        with open(os.path.join(outside, "plugin.json"), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), original)

    def agents_plugin(self, name="withagents", manifest=None):
        meta = manifest if manifest is not None else {"name": "p-dev", "version": "1.0.0", "agents": ["./agents/helper.md"],
                                                      "dependencies": ["web-search-dev"]}
        src = self.make_plugin(json.dumps(meta), name=name)
        os.makedirs(os.path.join(src, "agents"))
        with open(os.path.join(src, "agents", "helper.md"), "w") as fh:
            fh.write("---\nname: helper\n---\n")
        return src

    def test_copy_plugin_drop_agents_removes_dir_and_manifest_key_in_the_copy_only(self):
        src = self.agents_plugin()
        before = self.manifest_of(src)
        dest = evalgen.copy_plugin(src, os.path.join(self.tmp, "dest-na"), drop_agents=True)
        self.assertFalse(os.path.exists(os.path.join(dest, "agents")))
        self.assertEqual(json.loads(self.manifest_of(dest)), {"name": "p-dev", "version": "1.0.0"})
        self.assertTrue(os.path.isfile(os.path.join(dest, "skills", "a", "SKILL.md")))      # остальное на месте
        self.assertTrue(os.path.isfile(os.path.join(src, "agents", "helper.md")))          # источник не тронут
        self.assertEqual(self.manifest_of(src), before)

    def test_copy_plugin_keeps_agents_by_default(self):
        src = self.agents_plugin()
        dest = evalgen.copy_plugin(src, os.path.join(self.tmp, "dest-wa"))
        self.assertTrue(os.path.isfile(os.path.join(dest, "agents", "helper.md")))
        self.assertEqual(json.loads(self.manifest_of(dest)),
                         {"name": "p-dev", "version": "1.0.0", "agents": ["./agents/helper.md"]})   # dependencies — прежнее поведение

    def test_copy_plugin_drop_agents_without_manifest_key_keeps_manifest_byte_identical(self):
        odd = '{ "name":"p-dev",\r\n\t"version" : "1.0.0" }\r\n'
        src = self.agents_plugin(manifest=None)
        with open(os.path.join(src, ".claude-plugin", "plugin.json"), "w", newline="") as fh:
            fh.write(odd)
        dest = evalgen.copy_plugin(src, os.path.join(self.tmp, "dest-nk"), drop_agents=True)
        self.assertFalse(os.path.exists(os.path.join(dest, "agents")))
        self.assertEqual(self.manifest_of(dest), odd.encode("utf-8"))

    def test_copy_plugin_drop_agents_without_agents_dir_and_with_unreadable_manifest(self):
        src = self.make_plugin("{ not json", name="noagents")
        dest = evalgen.copy_plugin(src, os.path.join(self.tmp, "dest-bad2"), drop_agents=True)
        self.assertEqual(self.manifest_of(dest), b"{ not json")
        self.assertFalse(os.path.exists(os.path.join(dest, "agents")))

    def test_copy_plugin_drop_agents_removes_a_symlink_not_its_target(self):
        outside = os.path.join(self.tmp, "shared-agents")
        os.makedirs(outside)
        with open(os.path.join(outside, "x.md"), "w") as fh:
            fh.write("x")
        src = self.make_plugin(json.dumps({"name": "p-dev"}), name="linkagents")
        os.symlink(outside, os.path.join(src, "agents"))
        dest = evalgen.copy_plugin(src, os.path.join(self.tmp, "dest-la"), drop_agents=True)
        self.assertFalse(os.path.lexists(os.path.join(dest, "agents")))
        self.assertTrue(os.path.isfile(os.path.join(outside, "x.md")))
        self.assertTrue(os.path.islink(os.path.join(src, "agents")))

    def test_copy_plugin_drop_agents_does_not_write_through_a_manifest_symlink(self):
        real = os.path.join(self.tmp, "shared2.json")
        original = json.dumps({"name": "p-dev", "agents": ["./agents/helper.md"]})
        with open(real, "w", encoding="utf-8") as fh:
            fh.write(original)
        src = os.path.join(self.tmp, "linked2")
        os.makedirs(os.path.join(src, ".claude-plugin"))
        os.symlink(real, os.path.join(src, ".claude-plugin", "plugin.json"))
        dest = evalgen.copy_plugin(src, os.path.join(self.tmp, "dest-link2"), drop_agents=True)
        with open(real, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), original)
        self.assertEqual(json.loads(self.manifest_of(dest)), {"name": "p-dev"})

    def test_copy_plugin_without_manifest_is_fine(self):
        src = os.path.join(self.tmp, "nomanifest")
        os.makedirs(os.path.join(src, "skills", "a"))
        dest = evalgen.copy_plugin(src, os.path.join(self.tmp, "dest-nm"))
        self.assertTrue(os.path.isdir(os.path.join(dest, "skills", "a")))
        self.assertFalse(os.path.exists(os.path.join(dest, ".claude-plugin")))


if __name__ == "__main__":
    unittest.main()
