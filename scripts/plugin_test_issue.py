#!/usr/bin/env python3
"""Сводка отчёта plugin_test.py: markdown для CI и один постоянный issue на репозиторий.

  plugin_test_issue.py render REPORT.json                      # markdown в stdout
  plugin_test_issue.py sync --repo OWNER/NAME REPORT.json [--dry-run]

sync (spec §7.2): есть fail или infra — тело issue «Nightly plugin tests» с меткой
plugin-tests перезаписывается сводкой, закрытый issue открывается; всё чисто —
открытый issue закрывается комментарием с датой. Через `gh` под учёткой сервера.
Отчёт уже прошёл Redactor runner-а: значений env-файла в нём нет.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plugin_test.report import render_markdown  # noqa: E402

TITLE = "Nightly plugin tests"
LABEL = "plugin-tests"


def gh(args, input_text=None):
    proc = subprocess.run(["gh", *args], input=input_text, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError("gh %s: %s" % (" ".join(args[:2]), proc.stderr.strip()[:300]))
    return proc.stdout


def dry_run(args, input_text=None):
    if args[:2] == ["issue", "list"]:
        return gh(args)
    print("dry-run: gh %s%s" % (" ".join(args), " (тело: %d символов)" % len(input_text) if input_text else ""))
    return ""


def find_issue(repo, run):
    out = run(["issue", "list", "--repo", repo, "--label", LABEL, "--state", "all", "--limit", "100",
               "--json", "number,state,title"])
    issues = [i for i in json.loads(out or "[]") if i.get("title") == TITLE]
    return min(issues, key=lambda i: i["number"]) if issues else None


def sync(repo, report, run):
    summary = report.get("summary", {})
    problems = summary.get("fail", 0) or summary.get("infra", 0)
    found = find_issue(repo, run)
    actions = []
    if problems:
        body = render_markdown(report, title=TITLE)
        if found is None:
            run(["label", "create", LABEL, "--repo", repo, "--color", "B60205",
                 "--description", "Failures of the nightly L1 plugin tests", "--force"])
            run(["issue", "create", "--repo", repo, "--title", TITLE, "--label", LABEL, "--body-file", "-"], body)
            actions.append("created")
        else:
            number = str(found["number"])
            run(["issue", "edit", number, "--repo", repo, "--body-file", "-"], body)
            actions.append("updated")
            if str(found.get("state", "")).upper() == "CLOSED":
                run(["issue", "reopen", number, "--repo", repo])
                actions.append("reopened")
    elif found is not None and str(found.get("state", "")).upper() == "OPEN":
        number = str(found["number"])
        run(["issue", "comment", number, "--repo", repo, "--body",
             "Чистый прогон %s — закрываю." % report.get("started", "")])
        run(["issue", "close", number, "--repo", repo])
        actions.append("closed")
    return actions


def main(argv=None):
    ap = argparse.ArgumentParser(prog="plugin_test_issue.py", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    render = sub.add_parser("render")
    render.add_argument("report")
    syncp = sub.add_parser("sync")
    syncp.add_argument("--repo", required=True)
    syncp.add_argument("--dry-run", action="store_true")
    syncp.add_argument("report")
    args = ap.parse_args(argv)
    try:
        with open(args.report, encoding="utf-8") as fh:
            report = json.load(fh)
    except (OSError, ValueError) as exc:
        print("plugin_test_issue: отчёт не читается: %s" % exc, file=sys.stderr)
        return 1
    if args.cmd == "render":
        print(render_markdown(report))
        return 0
    try:
        actions = sync(args.repo, report, dry_run if args.dry_run else gh)
    except RuntimeError as exc:
        print("plugin_test_issue: %s" % exc, file=sys.stderr)
        return 1
    print("issue %s: %s" % (args.repo, ", ".join(actions) or "без изменений"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
