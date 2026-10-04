"""Командная строка runner-а — разбор аргументов, выбор плагинов, вывод."""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

from . import discover, envfile, report
from .model import CHECK_IDS, CI, SERVER, Context
from .runner import run_plugin

DEFAULT_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parse_args(argv):
    ap = argparse.ArgumentParser(prog="plugin_test.py",
                                 description="L1 «Контракт»: текст плагина против снимков реальности.")
    ap.add_argument("--repo", default=DEFAULT_REPO, help="корень репозитория плагинов")
    ap.add_argument("--with-repo", action="append", default=[],
                    help="ещё репозиторий, где искать плагины по имени (соседний находится сам)")
    ap.add_argument("--plugin", action="append", default=[], help="имя или каталог плагина; можно повторять")
    ap.add_argument("--changed", metavar="BASE_REF", help="только изменённые с BASE_REF и зависимые от них")
    ap.add_argument("--check", action="append", default=[], choices=CHECK_IDS)
    ap.add_argument("--mode", choices=(CI, SERVER), default=CI)
    ap.add_argument("--env-file", help="значения ${VAR} для режима server (не печатаются)")
    ap.add_argument("--json", metavar="OUT", help="записать JSON-отчёт")
    ap.add_argument("--strict", action="store_true", help="warn проверок со статусом blocking — провал")
    ap.add_argument("--update-snapshots", action="store_true", help="перезаписать снимки вместо сравнения")
    ap.add_argument("--verbose", action="store_true", help="печатать и skipped / info")
    return ap.parse_args(argv)


def main(argv=None):
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        # argparse выходит с 2 при ошибке использования; 2 здесь — «только warn/infra», CI считает его зелёным
        return 1 if exc.code == 2 else (exc.code or 0)
    repo = os.path.abspath(args.repo)
    plugins = discover.discover(repo)
    if not plugins:
        print("plugin-test: в %s нет плагинов" % os.path.join(repo, "plugins"), file=sys.stderr)
        return 1
    selected, unknown = discover.select(plugins, args.plugin)
    if unknown:
        print("plugin-test: нет плагина %s" % ", ".join(unknown), file=sys.stderr)
        return 1

    notes = []
    if args.changed:
        try:
            changed = discover.changed(repo, args.changed, plugins)
            selected = [p for p in selected if p in changed]
        except discover.ChangedError as exc:
            notes.append("WARN --changed: %s — проверяю все выбранные плагины" % exc)

    env = {}
    if args.env_file:
        try:
            env = envfile.load(args.env_file)
        except (OSError, UnicodeDecodeError) as exc:
            reason = (exc.strerror or str(exc)) if isinstance(exc, OSError) else "не UTF-8"
            print("plugin-test: env-файл не читается: %s" % reason, file=sys.stderr)
            return 1

    repos = [repo, *(os.path.abspath(r) for r in args.with_repo), *discover.sibling_repos(repo)]
    ctx = Context(mode=args.mode, repo=repo, catalog=discover.build_catalog(repos),
                  env=env if args.mode == SERVER else {}, update_snapshots=args.update_snapshots)
    checks = args.check or list(CHECK_IDS)
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    findings, suppressed = [], 0
    for plugin in selected:
        got, skipped = run_plugin(plugin, ctx, checks)
        findings.extend(got)
        suppressed += skipped

    redactor = report.Redactor(env, repo=repo)
    findings = [redactor.finding(f) for f in report.apply_status(findings, args.strict)]
    for note in notes:
        print(redactor.text(note))
    print(report.render_text(findings, len(selected), verbose=args.verbose))
    if args.json:
        data = report.build(findings, mode=args.mode, repo=repo, plugins=[p.name for p in selected],
                            started=started, suppressed=suppressed)
        os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
    return report.exit_code(findings)
