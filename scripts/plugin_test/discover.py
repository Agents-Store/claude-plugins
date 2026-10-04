"""Плагины репозитория, их компоненты и изменённый набор для --changed."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field

# Изменение любого пути с этим префиксом перепроверяет все плагины (spec §4.1).
ALL_PLUGINS_TRIGGERS = ("scripts/plugin_test", ".github/workflows/plugin-test.yml")
REPO_NAMES = ("claude-public-plugins", "claude-plugins-private")


class ChangedError(RuntimeError):
    """git не посчитал diff: нет базового коммита, shallow clone, не репозиторий."""


@dataclass(frozen=True)
class Plugin:
    name: str
    dirname: str
    repo: str
    dependencies: tuple = ()

    @property
    def dir(self) -> str:
        return os.path.join(self.repo, "plugins", self.dirname)

    @property
    def tests_dir(self) -> str:
        return os.path.join(self.repo, "tests", "plugins", self.dirname)

    def rel(self, path: str) -> str:
        return os.path.relpath(path, self.repo)


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _dependencies(raw) -> tuple:
    out = []
    for item in raw if isinstance(raw, list) else ():
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and isinstance(item.get("name"), str):
            out.append(item["name"])
    return tuple(out)


def discover(repo: str) -> list:
    """Каталоги plugins/* с .claude-plugin/plugin.json, по алфавиту."""
    repo = os.path.abspath(repo)
    root = os.path.join(repo, "plugins")
    if not os.path.isdir(root):
        return []
    plugins = []
    for dirname in sorted(os.listdir(root)):
        meta_path = os.path.join(root, dirname, ".claude-plugin", "plugin.json")
        if not os.path.isfile(meta_path):
            continue
        meta = _read_json(meta_path)
        meta = meta if isinstance(meta, dict) else {}
        name = meta.get("name") if isinstance(meta.get("name"), str) else dirname
        plugins.append(Plugin(name=name, dirname=dirname, repo=repo,
                              dependencies=_dependencies(meta.get("dependencies"))))
    return plugins


def select(plugins, wanted):
    """--plugin по имени из plugin.json или по каталогу → (выбранные, неизвестные)."""
    if not wanted:
        return list(plugins), []
    index = {}
    for p in plugins:
        index.setdefault(p.name, p)
        index.setdefault(p.dirname, p)
    picked, unknown = [], []
    for w in wanted:
        p = index.get(w)
        if p is None:
            unknown.append(w)
        elif p not in picked:
            picked.append(p)
    return picked, unknown


def changed_paths(repo, base):
    # -z: пути через NUL и без кавычек — иначе git берёт в кавычки не-ASCII имена
    # (core.quotePath), и плагин с таким файлом молча не выбирается.
    try:
        out = subprocess.run(
            ["git", "-C", repo, "diff", "-z", "--name-only", "--relative", "%s...HEAD" % base],
            capture_output=True, check=True, timeout=60).stdout
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or b"").decode("utf-8", "replace").strip()
        raise ChangedError("git diff %s...HEAD: %s" % (base, stderr[:200])) from exc
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        raise ChangedError("git diff %s...HEAD: %s" % (base, exc)) from exc
    return [p for p in out.decode("utf-8", "surrogateescape").split("\0") if p]


def _plugin_dir_of(path):
    parts = path.split("/")
    if len(parts) >= 3 and parts[0] == "plugins":
        return parts[1]
    if len(parts) >= 4 and parts[0] == "tests" and parts[1] == "plugins":
        return parts[2]
    return None


def changed(repo, base, plugins):
    """Изменённые плагины плюс все, кто зависит от них (до неподвижной точки)."""
    paths = changed_paths(repo, base)
    if any(p.startswith(t) for p in paths for t in ALL_PLUGINS_TRIGGERS):
        return list(plugins)
    by_dir = {p.dirname: p for p in plugins}
    names = {by_dir[d].name for d in map(_plugin_dir_of, paths) if d in by_dir}
    grew = True
    while grew:
        grew = False
        for p in plugins:
            if p.name not in names and any(dep in names for dep in p.dependencies):
                names.add(p.name)
                grew = True
    return [p for p in plugins if p.name in names]


def components(plugin) -> set:
    """Имена skills (skills/<d>/SKILL.md), команд и агентов (*.md без расширения)."""
    out = set()
    skills = os.path.join(plugin.dir, "skills")
    if os.path.isdir(skills):
        for d in os.listdir(skills):
            if os.path.isfile(os.path.join(skills, d, "SKILL.md")):
                out.add(d)
    for sub in ("commands", "agents"):
        for _, _, files in os.walk(os.path.join(plugin.dir, sub)):
            out.update(f[:-3] for f in files if f.endswith(".md"))
    return out


@dataclass
class Catalog:
    """Плагины всех известных репозиториев по имени — для ссылок между плагинами."""
    plugins: dict
    _components: dict = field(default_factory=dict, repr=False)

    def components(self, name) -> set:
        if name not in self._components:
            p = self.plugins.get(name)
            self._components[name] = components(p) if p else set()
        return self._components[name]


def build_catalog(repos) -> Catalog:
    plugins = {}
    for repo in repos:
        for p in discover(repo):
            plugins.setdefault(p.name, p)
    return Catalog(plugins)


def sibling_repos(repo):
    """Соседние репозитории плагинов рядом с repo (public ↔ private)."""
    here = os.path.abspath(repo)
    parent = os.path.dirname(here)
    out = []
    for name in REPO_NAMES:
        path = os.path.join(parent, name)
        if path != here and os.path.isdir(os.path.join(path, "plugins")):
            out.append(path)
    return out
