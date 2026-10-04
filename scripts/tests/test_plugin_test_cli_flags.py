import os
import stat
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test_fixtures import Repo, run_check  # noqa: E402

from plugin_test import cli_snapshot, shell, snapshots  # noqa: E402
from plugin_test.checks import REGISTRY, cli_flags  # noqa: E402
from plugin_test.model import FAIL, INFO, SKIPPED, WARN  # noqa: E402

FAKE_CLI = r'''#!/bin/sh
case "$*" in
  "--version") echo "fake version 1.2.3" ;;
  "--help") printf 'Usage:\n  fake [command]\n\nAvailable Commands:\n  login       Log in\n  secrets     Manage secrets\n\nFlags:\n      --domain string   API\n  -h, --help            help\n' ;;
  "secrets --help") printf 'Available Commands:\n  get   Get\n  set   Set\n\nFlags:\n      --env string   env\n      --plain        plain\n' ;;
  "secrets set --help") printf 'Flags:\n      --env string   env\n      --type string  type\n' ;;
  *) printf 'Flags:\n      --method string  m\n' ;;
esac
'''

COBRA_CLI = r'''#!/bin/sh
case "$*" in
  "--version") echo "cobra 2.0.0" ;;
  "--help") printf 'Available Commands:\n  login          Log in\n  dynamic-secrets Manage dynamic secrets\n  secrets        Manage secrets\n\nFlags:\n      --domain string   API\n' ;;
  "secrets --help") printf 'Available Commands:\n  get                  Get\n  generate-example-env Generate an example env\n\nFlags:\n      --env string   env\n' ;;
  *) printf 'Flags:\n      --method string  m\n' ;;
esac
'''

COBRA_HELP = (
    "Available Commands:\n"
    "  login                Log in\n"
    "  generate-example-env Generate an example env\n"
    "  secrets              Manage secrets\n"
    "\nFlags:\n"
    "      --domain string   API\n"
)

SNAPSHOT = {"tool": "fake", "version": "1.2.3", "global": ["--domain", "--help"], "subcommands": ["login", "secrets"],
            "commands": {"secrets": ["--env", "--plain"], "secrets set": ["--env", "--type"]},
            "children": {"secrets": ["get", "set"]}}

GOOD = '''# Skill
```bash
fake secrets set FOO=bar --env prod
fake --domain https://example.com secrets
fake login --anything
fake secrets get NAME --not-snapshotted-child-flag
sudo fake secrets --plain | tee out
echo "$(fake secrets --env x)"
fake --help
other-tool --whatever
```
'''

BROKEN = '''# Skill
```bash
fake secretz list
fake secrets set --nope
fake secrets --plain --typo=1
```
'''

MANIFEST = '[cli.fake]\nversion = "1.2.3"\ncommands = ["secrets", "secrets set"]\n'


class ShellTest(unittest.TestCase):
    def test_logical_lines(self):
        body = '# c\na \\\n  b\n\nX=$(curl -d "{\n  \\"k\\": 1\n}")\nlast'
        self.assertEqual([off for off, _ in shell.logical_lines(body)], [1, 4, 7])

    def test_commands_and_prefix(self):
        self.assertEqual(shell.commands("a x && b --y | c; d &"), [["a", "x"], ["b", "--y"], ["c"], ["d"]])
        self.assertEqual(shell.commands('echo "$(fake secrets get X --plain)"'),
                         [["echo"], ["fake", "secrets", "get", "X", "--plain"]])
        self.assertEqual(shell.commands('K=$(curl -s "$U/x")')[0][:2], ["curl", "-s"])
        self.assertEqual(shell.strip_prefix(["sudo", "env", "A=1", "fake", "x"]), ["fake", "x"])
        self.assertEqual(shell.commands('echo "unterminated'), [])


class CliSnapshotTest(unittest.TestCase):
    def test_build_with_fake_binary(self):
        repo = Repo()
        self.addCleanup(repo.cleanup)
        path = repo.write("bin/fake", FAKE_CLI)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        with mock.patch.dict(os.environ, {"PATH": os.path.dirname(path) + os.pathsep + os.environ["PATH"]}):
            data = cli_snapshot.build("fake", ["secrets", "secrets set"])
        self.assertEqual(data, SNAPSHOT)

    def test_missing_binary(self):
        with self.assertRaises(FileNotFoundError):
            cli_snapshot.build("definitely-not-installed-cli", [])

    def test_cobra_alignment_keeps_the_longest_command(self):
        # cobra pads to the longest name plus ONE space: that name must not be dropped
        self.assertEqual(cli_snapshot.parse_subcommands(COBRA_HELP), ["generate-example-env", "login", "secrets"])
        repo = Repo()
        self.addCleanup(repo.cleanup)
        path = repo.write("bin/cobra", COBRA_CLI)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        with mock.patch.dict(os.environ, {"PATH": os.path.dirname(path) + os.pathsep + os.environ["PATH"]}):
            data = cli_snapshot.build("cobra", ["secrets"])
        self.assertEqual(data["subcommands"], ["dynamic-secrets", "login", "secrets"])
        self.assertEqual(data["children"], {"secrets": ["generate-example-env", "get"]})


class CliFlagsTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)

    def make(self, text, snapshot=SNAPSHOT, manifest=MANIFEST):
        self.repo.plugin("c-dev", files={"skills/s/SKILL.md": text})
        files = {"plugin-test.toml": manifest}
        if snapshot is not None:
            files["snapshots/cli/fake.json"] = snapshot
        self.repo.tests("c-dev", files)

    def test_registered(self):
        self.assertIs(REGISTRY["cli-flags"], cli_flags.run)

    def test_good(self):
        self.make(GOOD)
        self.assertEqual(run_check(cli_flags, self.repo.root, "c-dev"), [])

    def test_broken(self):
        self.make(BROKEN)
        found = run_check(cli_flags, self.repo.root, "c-dev")
        self.assertEqual([(f.line, f.level) for f in found], [(3, FAIL), (4, FAIL), (5, FAIL)])
        self.assertIn("secretz", found[0].message)
        self.assertIn("--nope", found[1].message)
        self.assertIn("--typo", found[2].message)

    def test_flag_before_the_subcommand_is_ambiguous_and_silent(self):
        self.make("# S\n```bash\nfake --domain https://x secrets --plain\n"
                  "fake secrets --env prod set K --type t\n```\n")
        self.assertEqual(run_check(cli_flags, self.repo.root, "c-dev"), [])

    def test_unknown_flag_still_found_with_flag_first(self):
        self.make("# S\n```bash\nfake --domain https://x --nope\nfake secrets --env prod --nope\n```\n")
        found = run_check(cli_flags, self.repo.root, "c-dev")
        self.assertEqual([(f.line, f.level) for f in found], [(3, FAIL), (4, FAIL)])

    def test_bad_snapshot_is_one_finding(self):
        rel = "tests/plugins/c-dev/snapshots/cli/fake.json"
        shapes = ["{nope", [], {"commands": {"secrets": 5}}, {"commands": {"secrets": [1]}},
                  {"commands": {}, "subcommands": 5}, {"commands": {}, "global": [1]},
                  {"commands": {}, "children": []}, {"commands": {}, "children": {"secrets": "get"}}]
        for shape in shapes:
            with self.subTest(shape=shape):
                self.make(GOOD, snapshot=shape)
                found = run_check(cli_flags, self.repo.root, "c-dev")
                self.assertEqual([(f.level, f.file) for f in found], [(FAIL, rel)])

    def test_no_snapshot_and_no_manifest(self):
        self.make(BROKEN, snapshot=None)
        self.assertEqual([f.level for f in run_check(cli_flags, self.repo.root, "c-dev")], [SKIPPED])
        self.make(BROKEN, snapshot=None, manifest="")
        self.assertEqual(run_check(cli_flags, self.repo.root, "c-dev"), [])

    def test_update_snapshots(self):
        path = self.repo.write("bin/fake", FAKE_CLI)
        os.chmod(path, os.stat(path).st_mode | stat.S_IEXEC)
        self.make(GOOD, snapshot=None, manifest=MANIFEST.replace("1.2.3", "9.9.9"))
        with mock.patch.dict(os.environ, {"PATH": os.path.dirname(path) + os.pathsep + os.environ["PATH"]}):
            found = run_check(cli_flags, self.repo.root, "c-dev", update_snapshots=True)
        self.assertEqual(sorted(f.level for f in found), [INFO, WARN])
        written = snapshots.load_cli(os.path.join(self.repo.root, "tests/plugins/c-dev/snapshots/cli/fake.json"))
        self.assertEqual(written, SNAPSHOT)


if __name__ == "__main__":
    unittest.main()
