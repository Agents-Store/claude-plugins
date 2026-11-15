"""The documentation is part of the product: every command it shows must exist, every plan must pass the guards."""
import contextlib
import io
import json
import re
import shlex
import unittest

import helpers
import ads
from adskit import __version__, guards, keys, launch
from adskit.core import DEFAULT_CONFIG, parse_env_text

PLUGIN = helpers.PLUGIN
RE_COMMAND = re.compile(r"python3 ads/tools/ads\.py[ \t]+([^\n`]+)")
RE_FENCE = re.compile(r"```(\w*)\n(.*?)```", re.S)
SYNTAX_MARKS = ("<group>", "<command>", "...", "[--", "|", "…")


def markdown_files():
    return sorted(p for p in PLUGIN.rglob("*.md") if "node_modules" not in p.parts)


def shown_commands():
    for path in markdown_files():
        text = path.read_text(encoding="utf-8").replace("\\\n", " ")
        for number, line in enumerate(text.split("\n"), 1):
            for match in RE_COMMAND.finditer(line):
                yield path.relative_to(PLUGIN), number, match.group(1).strip()


def tokens_of(command):
    """Cut a documented command at the first shell operator and turn placeholders into plain words."""
    command = re.split(r"\s(?:\|\||&&|[|;>])\s|\s#\s|\s>\s?|\s2>", " " + command + " ")[0]
    command = re.sub(r"<([A-Za-z][^<>]*)>", lambda m: re.sub(r"\W+", "_", m.group(1)), command)
    command = command.replace("$(", "(").strip().rstrip(".,:;)")
    try:
        return shlex.split(command)
    except ValueError:
        return None


class Commands(unittest.TestCase):
    def test_every_documented_command_parses(self):
        parser = ads.build_parser()
        failures, checked = [], 0
        for path, number, command in shown_commands():
            if any(mark in command for mark in SYNTAX_MARKS[:4]) or command.startswith(("<", "[")):
                continue
            tokens = tokens_of(command)
            if not tokens:
                failures.append("%s:%d cannot be read as a shell command: %s" % (path, number, command))
                continue
            checked += 1
            sink = io.StringIO()
            try:
                with contextlib.redirect_stderr(sink), contextlib.redirect_stdout(sink):
                    parser.parse_args(tokens)
            except SystemExit as exit_:
                if exit_.code not in (0, None):
                    reason = sink.getvalue().strip().splitlines()[-1] if sink.getvalue().strip() else "rejected"
                    failures.append("%s:%d %s\n    -> %s" % (path, number, command, reason))
        self.assertGreater(checked, 40)
        self.assertEqual(failures, [], "\n" + "\n".join(failures))

    def test_toolkit_reference_lists_every_command(self):
        text = (PLUGIN / "skills/init-project/references/toolkit.md").read_text(encoding="utf-8")
        parser = ads.build_parser()
        groups = next(a for a in parser._actions if a.dest == "group").choices
        missing = []
        for group, sub in groups.items():
            nested = [a for a in sub._actions if a.dest == "command"]
            names = ["%s %s" % (group, n) for n in nested[0].choices] if nested else [group]
            missing.extend(n for n in names if "`%s" % n not in text)
        self.assertEqual(missing, [])


class Plans(unittest.TestCase):
    def test_every_complete_plan_in_the_docs_passes_the_guards(self):
        found = 0
        for path in markdown_files():
            for language, body in RE_FENCE.findall(path.read_text(encoding="utf-8")):
                if language != "json" or '"steps"' not in body or '"platform"' not in body:
                    continue
                found += 1
                with helpers.Workspace() as ws:
                    plan = json.loads(body)
                    doc = launch.load_plan(ws.write_plan(plan))
                    for step in doc["steps"]:
                        args = step["with"]      # judged as launch plan does: a plan step only creates
                        if step["do"] == "google.mutate":
                            guards.google_mutate(args, DEFAULT_CONFIG, plan=set())
                        elif step["do"] == "meta.post":
                            guards.meta_request("POST", args["path"], args.get("params") or {}, DEFAULT_CONFIG, plan=True)
                        elif step["do"] == "tiktok.post":
                            guards.tiktok_request(args["path"], args.get("body") or {}, DEFAULT_CONFIG, plan=True)
                    if plan.get("budget", {}).get("daily") is not None:
                        self.assertLessEqual(plan["budget"]["daily"], DEFAULT_CONFIG["guardrails"]["max_daily_budget"], path.name)
                    # what the steps carry equals what the plan declares, in the currency the plan names
                    ws.ctx.config["project"]["currency"] = plan.get("budget", {}).get("currency", "USD")
                    self.assertEqual(launch.budget_check(ws.ctx, doc)[1], [], path.name)
                    self.assertNotRegex(body, r"customers/\d{6,}", "%s: write {customer}, not an account id" % path.name)
                    self.assertNotRegex(body, r"act_\d{5,}", "%s: write {account}, not an account id" % path.name)
        self.assertGreaterEqual(found, 3)


    @staticmethod
    def commented_json(block):
        """A jsonc sample without its comments."""
        lines = [line for line in block.split("\n") if not line.strip().startswith("//")]
        return re.sub(r"\s+//[^\n]*", "", "\n".join(lines))

    def test_partial_sample_bodies_pass_the_plan_rules(self):
        """The Performance Max, Demand Gen and Smart+ samples are fragments: they must pass the same rules as whole plans."""
        google = (PLUGIN / "skills/launch-campaign/references/google-ads.md").read_text(encoding="utf-8")
        bodies = [self.commented_json(block) for block in re.findall(r"```jsonc\n(.*?)```", google, re.S)]
        bodies = [json.loads(text) for text in bodies if text.strip().startswith("[")]
        self.assertGreaterEqual(len(bodies), 2)
        for operations in bodies:
            body = guards.google_canonical({"mutateOperations": operations})
            self.assertFalse(guards.google_mutate(body, DEFAULT_CONFIG, plan=set())["activates"])
            plan = {"name": "sample", "platform": "google", "steps": [{"id": "create", "do": "google.mutate", "with": body}]}
            self.assertEqual(launch.uncapped(plan), [])
        tiktok = (PLUGIN / "skills/launch-campaign/references/tiktok-ads.md").read_text(encoding="utf-8")
        block = re.search(r"```jsonc\n(\"steps\": \[.*?)```", tiktok, re.S).group(1)
        steps = json.loads("{" + self.commented_json(block) + "}")["steps"]
        self.assertGreaterEqual(len(steps), 3)
        for step in steps:
            if step["do"] == "tiktok.post":
                guards.tiktok_request(step["with"]["path"], step["with"].get("body") or {}, DEFAULT_CONFIG, plan=True)
        self.assertEqual(launch.uncapped({"name": "sample", "platform": "tiktok", "steps": steps}), [])


class Frontmatter(unittest.TestCase):
    """Ten of the eleven generated targets get SKILL.md as written, and their agents read the frontmatter with a
    strict YAML parser. Claude Code is lenient, so nothing else catches a value that only it can read."""

    FILES = sorted(PLUGIN.glob("skills/*/SKILL.md")) + sorted(PLUGIN.glob("agents/*.md"))

    @staticmethod
    def block(path):
        match = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
        return match.group(1) if match else None

    def test_plain_values_carry_nothing_a_strict_yaml_parser_trips_over(self):
        self.assertGreater(len(self.FILES), 10)
        problems = []
        for path in self.FILES:
            block = self.block(path)
            self.assertIsNotNone(block, "%s has no frontmatter" % path.name)
            for line in block.split("\n"):
                pair = re.match(r"([A-Za-z][\w-]*):[ \t]+(.*)$", line)        # a top-level "key: value" line
                if not pair or pair.group(2)[:1] in "\"'|>[{":                # quoted, block and flow values are safe
                    continue
                value = pair.group(2)
                if ": " in value or " #" in value or value.endswith(":") or value[:1] in "@`*&!%?-":
                    problems.append("%s: %s holds ': ', ' #' or a leading special character: reword or quote it"
                                    % (path.relative_to(PLUGIN), pair.group(1)))
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_frontmatter_parses_with_a_real_yaml_parser_when_one_is_installed(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("PyYAML is not installed; the rule above covers the known hazards")
        for path in self.FILES:
            data = yaml.safe_load(self.block(path))
            self.assertIsInstance(data.get("description"), str, path.name)
            self.assertEqual(data.get("name"), path.parent.name if path.name == "SKILL.md" else path.stem, path.name)


class Parity(unittest.TestCase):
    def test_env_templates_are_identical_and_match_the_key_registry(self):
        inner = (PLUGIN / "skills/init-project/scripts/assets/env.example").read_bytes()
        self.assertEqual(inner, (PLUGIN / "templates/.env.example").read_bytes())
        declared = list(parse_env_text(inner.decode("utf-8")))
        self.assertEqual(sorted(declared), sorted(keys.all_keys()))
        self.assertEqual([v for v in parse_env_text(inner.decode("utf-8")).values() if v], [], "the template carries no values")

    def test_claude_md_template_copies_are_identical(self):
        self.assertEqual((PLUGIN / "templates/CLAUDE.md.template").read_bytes(),
                         (PLUGIN / "skills/init-project/scripts/assets/claude-md.template").read_bytes())

    def test_toolkit_version_matches_the_manifest(self):
        manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], __version__)

    def test_mcp_config_uses_only_declared_variables(self):
        text = (PLUGIN / ".mcp.json").read_text(encoding="utf-8")
        used = set(re.findall(r"\$\{([A-Z0-9_]+)", text))
        self.assertTrue(used)
        self.assertEqual(used - set(keys.all_keys()), set())
        for name, server in json.loads(text)["mcpServers"].items():
            if "url" in server:
                self.assertEqual(server.get("type"), "http", name)

    def test_every_key_guide_exists(self):
        for service in keys.SERVICES:
            self.assertTrue((PLUGIN / "skills/init-project/references" / service["guide"]).is_file(), service["guide"])


if __name__ == "__main__":
    unittest.main()
