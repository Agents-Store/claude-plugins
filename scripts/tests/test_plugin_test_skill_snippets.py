import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, run_check  # noqa: E402

from plugin_test.checks import REGISTRY, skill_snippets  # noqa: E402
from plugin_test.model import FAIL, INFRA  # noqa: E402

GOOD = '''# Good
```json
{"a": [1, 2]}
```
```jsonc
{"a": 1, // comment
}
```
```yaml
a: 1
---
b: <value>
```
```bash
curl -s "$ROOT/x" -H "Authorization: Bearer <token>" | jq . > <out-file>.json
cat <<EOF > f.txt
<not a placeholder>
EOF
diff <(sort a) <(sort b)
```
```console
$ echo "unterminated
```
<!-- plugin-test: skip -->

```json
{ "deliberately": incomplete
```
'''

BROKEN = '''# Broken
```json
{
  "a": 1,
}
```
```yaml
a: [1, 2
```
```bash
if true; then
  echo x
```
'''


class SkillSnippetsTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)

    def test_registered(self):
        self.assertIs(REGISTRY["skill-snippets"], skill_snippets.run)

    def test_placeholder_regex(self):
        self.assertEqual(skill_snippets.RE_PLACEHOLDER.sub("P", "a <b c> <<EOF <(x) < f"), "a P <<EOF <(x) < f")

    def test_good(self):
        self.repo.plugin("good-dev", files={"skills/s/SKILL.md": GOOD})
        self.assertEqual(run_check(skill_snippets, self.repo.root, "good-dev"), [])

    def test_broken_lines(self):
        self.repo.plugin("bad-dev", files={"skills/s/SKILL.md": BROKEN})
        found = run_check(skill_snippets, self.repo.root, "bad-dev")
        self.assertEqual([(f.line, f.level) for f in found], [(5, FAIL), (8, FAIL), (13, FAIL)])
        self.assertIn("json", found[0].message)
        self.assertIn("bash -n", found[2].message)

    def test_yaml_missing_is_one_infra(self):
        self.repo.plugin("y-dev", files={"a.md": "```yaml\na: 1\n```\n", "b.md": "```yml\nb: 2\n```\n"})
        with mock.patch.object(skill_snippets, "yaml", None):
            found = run_check(skill_snippets, self.repo.root, "y-dev")
        self.assertEqual([f.level for f in found], [INFRA])


if __name__ == "__main__":
    unittest.main()
