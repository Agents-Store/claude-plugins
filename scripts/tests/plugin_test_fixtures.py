"""Временные репозитории плагинов для тестов runner-а plugin_test.

У каждой проверки — «хороший» и «сломанный» плагин; строить их кодом в самом
тесте нагляднее, чем держать десятки файлов-фикстур: правило и пример, который
его нарушает, видны на одном экране. Постоянные фикстуры (MCP-заглушка) лежат в
fixtures/plugin_test/.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(TESTS_DIR)
FIXTURES = os.path.join(TESTS_DIR, "fixtures", "plugin_test")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

GIT_ENV = {
    "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "fixture@example.com",
    "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "fixture@example.com",
}


class Repo:
    """plugins/<p>/… и tests/plugins/<p>/… во временном каталоге."""

    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="plugin-test-")

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write(self, rel, content):
        path = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return path

    def plugin(self, name, files=None, deps=None, mcp=None, plugin_json=None):
        meta = dict(plugin_json or {"name": name, "version": "1.0.0", "description": "fixture"})
        if deps is not None:
            meta["dependencies"] = deps
        self.write("plugins/%s/.claude-plugin/plugin.json" % name, json.dumps(meta))
        if mcp is not None:
            self.write("plugins/%s/.mcp.json" % name, json.dumps({"mcpServers": mcp}))
        for rel, content in (files or {}).items():
            self.write("plugins/%s/%s" % (name, rel), content)
        return os.path.join(self.root, "plugins", name)

    def tests(self, name, files):
        for rel, content in files.items():
            if not isinstance(content, str):
                content = json.dumps(content, indent=2)
            self.write("tests/plugins/%s/%s" % (name, rel), content)

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", self.root, *args], check=True, capture_output=True,
            text=True, env={**os.environ, **GIT_ENV}).stdout

    def init_git(self):
        self.git("init", "-q", "-b", "main")

    def commit_all(self, msg="x"):
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", msg)
        return self.git("rev-parse", "HEAD").strip()


def context(repo_root, mode="ci", env=None, extra_repos=(), update_snapshots=False):
    from plugin_test import discover
    from plugin_test.model import Context
    return Context(mode=mode, repo=repo_root,
                   catalog=discover.build_catalog([repo_root, *extra_repos]),
                   env=dict(env or {}), update_snapshots=update_snapshots)


def load_plugin(repo_root, dirname):
    from plugin_test import discover
    return next(p for p in discover.discover(repo_root) if p.dirname == dirname)


def run_check(module, repo_root, dirname, mode="ci", env=None,
              update_snapshots=False, extra_repos=()):
    from plugin_test import manifest
    plugin = load_plugin(repo_root, dirname)
    loaded, _ = manifest.load(plugin)
    ctx = context(repo_root, mode, env, extra_repos, update_snapshots)
    return module.run(plugin, ctx, loaded)
