#!/usr/bin/env python3
"""plugin_upstream.py — какие плагины пора обновить и почему, без модели.

  plugin_upstream.py queue --repo <repo> [--nightly-report <json>] [--today YYYY-MM-DD] --out <queue.json>

Очередь — JSON [{plugin, dir, priority, reasons}]. Код выхода 0 и при ошибках реестров: такой источник
получает повод source-error и плагин из-за него в очередь не встаёт. Формат [upstream] — tests/README.md.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_test import upstream  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(prog="plugin_upstream.py", description=__doc__.splitlines()[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("queue")
    q.add_argument("--repo", required=True)
    q.add_argument("--nightly-report", default="")
    q.add_argument("--today", default="")
    q.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    today = datetime.date.fromisoformat(args.today) if args.today else datetime.datetime.now(datetime.timezone.utc).date()
    drift = upstream.nightly_drift(args.nightly_report) if args.nightly_report else {}
    entries = upstream.queue(os.path.abspath(args.repo), upstream.default_fetch, today, drift)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    errors = sum(1 for e in entries for r in e["reasons"] if r["kind"] == "source-error")
    print("plugin_upstream: в очереди %d, ошибок источников у них %d" % (len(entries), errors), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
