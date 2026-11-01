#!/usr/bin/env python3
"""Ночная фаза L2: какие плагины гонять сегодня, и что перенести на завтра (spec очереди 2 §6.1).

select — имена по одному в строке; record — записать итог ночи, код 3 если L2 остановлен (порог подписки);
defer — отложить плагины без прогона (L2 уже остановлен на другом репозитории).
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plugin_test import l2plan  # noqa: E402

STOPPED = 3


def main(argv=None):
    ap = argparse.ArgumentParser(prog="plugin_test_l2plan.py", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("select", "record", "defer"):
        p = sub.add_parser(name)
        p.add_argument("--repo", required=True)
        p.add_argument("--state", required=True)
        if name == "select":
            p.add_argument("--weekday", type=int, default=datetime.datetime.now(datetime.timezone.utc).weekday())
        elif name == "record":
            p.add_argument("report")
        else:
            p.add_argument("names", nargs="+")
    args = ap.parse_args(argv)
    repo, state = os.path.abspath(args.repo), os.path.abspath(args.state)
    if args.cmd == "select":
        names, notes = l2plan.select(repo, state, args.weekday)
        for note in notes:
            print("plugin_test_l2plan: %s" % note, file=sys.stderr)
        for name in names:
            print(name)
        return 0
    if args.cmd == "defer":
        l2plan.defer(repo, state, args.names)
        return 0
    try:
        with open(args.report, encoding="utf-8") as fh:
            report = json.load(fh)
    except (OSError, ValueError) as exc:
        print("plugin_test_l2plan: отчёт не читается: %s" % exc, file=sys.stderr)
        return 1
    stop = l2plan.record(repo, state, report)
    if stop:
        print("L2 остановлен: %s" % stop)
        return STOPPED
    return 0


if __name__ == "__main__":
    sys.exit(main())
