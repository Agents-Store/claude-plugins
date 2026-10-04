import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, run_check  # noqa: E402

from plugin_test import markdown  # noqa: E402
from plugin_test.checks import REGISTRY, skill_links  # noqa: E402
from plugin_test.model import FAIL, WARN  # noqa: E402

GOOD = """# Skill
See [the guide](references/guide.md#setup), ![diagram](assets/d.png) and [dir](references/).
[ref]: references/guide.md
External: [docs](https://example.com/x), [anchor](#top), [mail](mailto:a@example.com).
Placeholder: [file](<your-file>.md), [var](${ROOT}/x.md).
Pointers: `other-dev:helper-skill`, `other-dev:run`, `superpowers:brainstorming`, `node:lts`.
Inline code is not a link: `[x](missing.md)`.

```markdown
[in a fence](missing.md)
```
"""

BROKEN = """# Skill
Broken [link](references/nope.md) on line 2.
Outside [shared](../../../../shared.md).
Absolute [path](/x.md).
Pointer `other-dev:no-such-skill`.
Unknown `ghost-ops:thing`.
"""


class MarkdownTest(unittest.TestCase):
    def test_blocks_and_skip_marker(self):
        text = "a\n<!-- plugin-test: skip -->\n\n```json\n{bad\n```\n~~~~bash title=x\necho ok\n~~~~\n```\nopen"
        bs = markdown.blocks(text)
        self.assertEqual([(b.info, b.line, b.skip) for b in bs], [("json", 5, True), ("bash", 8, False), ("", 11, False)])
        self.assertEqual(bs[0].body, "{bad")
        self.assertEqual(bs[2].body, "open")

    def test_links_skip_fences_and_inline_code(self):
        text = "[a](x.md) `[b](y.md)`\n```\n[c](z.md)\n```\n[d]: w.md"
        self.assertEqual(list(markdown.links(text)), [("x.md", 1), ("w.md", 5)])

    def test_iter_markdown_skips(self):
        repo = Repo()
        self.addCleanup(repo.cleanup)
        base = repo.plugin("p-dev", files={"README.md": "", "CHANGELOG.md": "", "LEARNINGS.md": "",
                                           "node_modules/x/README.md": "", "skills/s/SKILL.md": ""})
        got = [os.path.relpath(p, base) for p in markdown.iter_markdown(base)]
        self.assertEqual(got, ["README.md", os.path.join("skills", "s", "SKILL.md")])


class SkillLinksTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.repo.plugin("other-dev", files={"skills/helper-skill/SKILL.md": "x", "commands/run.md": "x"})

    def test_registered(self):
        self.assertIs(REGISTRY["skill-links"], skill_links.run)

    def test_good(self):
        self.repo.plugin("good-dev", files={"skills/s/SKILL.md": GOOD, "skills/s/references/guide.md": "g",
                                            "skills/s/assets/d.png": "png"})
        self.assertEqual(run_check(skill_links, self.repo.root, "good-dev"), [])

    def test_broken(self):
        self.repo.plugin("bad-dev", files={"skills/s/SKILL.md": BROKEN})
        self.repo.write("shared.md", "outside every plugin")
        found = run_check(skill_links, self.repo.root, "bad-dev")
        got = sorted((f.line, f.level) for f in found)
        self.assertEqual(got, [(2, FAIL), (3, FAIL), (4, FAIL), (5, FAIL), (6, WARN)])
        self.assertTrue(all(f.file == "plugins/bad-dev/skills/s/SKILL.md" for f in found))
        self.assertIn("за пределы", next(f for f in found if f.line == 3).message)
        self.assertIn("helper-skill", next(f for f in found if f.line == 5).fix)

    def test_pointer_into_other_repo(self):
        other = Repo()
        self.addCleanup(other.cleanup)
        other.plugin("private-ops", files={"skills/secret-skill/SKILL.md": "x"})
        self.repo.plugin("p-dev", files={"README.md": "`private-ops:secret-skill`"})
        self.assertEqual(run_check(skill_links, self.repo.root, "p-dev", extra_repos=[other.root]), [])


if __name__ == "__main__":
    unittest.main()
