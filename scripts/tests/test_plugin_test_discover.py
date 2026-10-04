import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo  # noqa: E402

from plugin_test import discover  # noqa: E402
from plugin_test.model import FAIL, WARN, Finding  # noqa: E402


class FindingTest(unittest.TestCase):
    def test_replace_and_dict(self):
        f = Finding("p", "skill-links", FAIL, "msg", "plugins/p/a.md", 3, "fix")
        g = f.replace(level=WARN, original=FAIL)
        self.assertEqual(g.level, WARN)
        self.assertEqual(f.level, FAIL)
        self.assertEqual(g.to_dict()["original"], FAIL)


class DiscoverTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)

    def test_finds_plugins_sorted_with_deps(self):
        self.repo.plugin("b-dev", deps=["a-dev", {"name": "c-dev", "version": "^1"}])
        self.repo.plugin("a-dev")
        os.makedirs(os.path.join(self.repo.root, "plugins", "not-a-plugin"))
        found = discover.discover(self.repo.root)
        self.assertEqual([p.dirname for p in found], ["a-dev", "b-dev"])
        self.assertEqual(found[1].dependencies, ("a-dev", "c-dev"))
        self.assertEqual(found[0].tests_dir, os.path.join(self.repo.root, "tests", "plugins", "a-dev"))

    def test_name_falls_back_to_dirname_on_broken_json(self):
        self.repo.write("plugins/x-dev/.claude-plugin/plugin.json", "{not json")
        self.assertEqual(discover.discover(self.repo.root)[0].name, "x-dev")

    def test_select_by_name_or_dir(self):
        self.repo.plugin("dir-dev", plugin_json={"name": "named-dev"})
        plugins = discover.discover(self.repo.root)
        picked, unknown = discover.select(plugins, ["named-dev", "dir-dev", "ghost"])
        self.assertEqual([p.dirname for p in picked], ["dir-dev"])
        self.assertEqual(unknown, ["ghost"])

    def test_components(self):
        self.repo.plugin("a-dev", files={
            "skills/one/SKILL.md": "x", "skills/no-skill-md/notes.md": "x",
            "commands/run.md": "x", "agents/helper.md": "x"})
        p = discover.discover(self.repo.root)[0]
        self.assertEqual(discover.components(p), {"one", "run", "helper"})

    def test_catalog_spans_repos_and_prefers_first(self):
        other = Repo()
        self.addCleanup(other.cleanup)
        self.repo.plugin("a-dev", files={"skills/mine/SKILL.md": "x"})
        other.plugin("a-dev", files={"skills/theirs/SKILL.md": "x"})
        other.plugin("b-ops", files={"skills/s/SKILL.md": "x"})
        cat = discover.build_catalog([self.repo.root, other.root])
        self.assertEqual(cat.components("a-dev"), {"mine"})
        self.assertEqual(cat.components("b-ops"), {"s"})
        self.assertEqual(cat.components("ghost"), set())

    def test_sibling_repos(self):
        parent = Repo()
        self.addCleanup(parent.cleanup)
        for name in ("claude-public-plugins", "claude-plugins-private"):
            os.makedirs(os.path.join(parent.root, name, "plugins"))
        public = os.path.join(parent.root, "claude-public-plugins")
        self.assertEqual(discover.sibling_repos(public),
                         [os.path.join(parent.root, "claude-plugins-private")])


class ChangedTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.repo.init_git()
        self.repo.plugin("base-dev", files={"skills/s/SKILL.md": "v1"})
        self.repo.plugin("mid-dev", deps=["base-dev"])
        self.repo.plugin("top-dev", deps=["mid-dev"])
        self.repo.plugin("lone-ops")
        self.base = self.repo.commit_all("base")

    def names(self):
        plugins = discover.discover(self.repo.root)
        return [p.name for p in discover.changed(self.repo.root, self.base, plugins)]

    def test_reverse_dependencies_to_fixpoint(self):
        self.repo.write("plugins/base-dev/skills/s/SKILL.md", "v2")
        self.repo.commit_all("change")
        self.assertEqual(self.names(), ["base-dev", "mid-dev", "top-dev"])

    def test_tests_dir_change_selects_plugin(self):
        self.repo.write("tests/plugins/lone-ops/plugin-test.toml", "")
        self.repo.commit_all("tests")
        self.assertEqual(self.names(), ["lone-ops"])

    def test_runner_change_selects_all(self):
        self.repo.write("scripts/plugin_test/model.py", "# x")
        self.repo.commit_all("runner")
        self.assertEqual(len(self.names()), 4)

    def test_changed_deleted_and_outside(self):
        self.repo.git("rm", "-rq", "plugins/lone-ops")
        self.repo.write("README.md", "outside plugins")
        self.repo.write("plugins/renamed-dev/.claude-plugin/plugin.json", '{"name": "renamed-dev"}')
        self.repo.commit_all("delete, outside, new")
        self.assertEqual(self.names(), ["renamed-dev"])

    def test_non_ascii_path_selects_plugin(self):
        self.repo.write("plugins/lone-ops/skills/s/привет.md", "x")
        self.repo.commit_all("non-ascii name")
        self.assertEqual(self.names(), ["lone-ops"])

    def test_bad_base_raises(self):
        plugins = discover.discover(self.repo.root)
        with self.assertRaises(discover.ChangedError):
            discover.changed(self.repo.root, "0" * 40, plugins)


if __name__ == "__main__":
    unittest.main()
