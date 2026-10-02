#!/usr/bin/env python3
"""Third gate pass: the official manifest validator over the covered plugins.

Exit 0 clean (or claude CLI absent — reported, not failed), 1 any plugin failed.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plugin_lint import plugins_for, rel  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(prog="validate_pass.py")
    ap.add_argument("targets", nargs="*")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("--strict", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--baseline", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--no-baseline", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if shutil.which("claude") is None:
        print(json.dumps({"skipped": True}) if args.format == "json"
              else "validate: claude CLI not on PATH — skipped")
        return 0
    results = []
    for plugin in plugins_for(args.targets or ["."]):
        proc = subprocess.run(["claude", "plugin", "validate", plugin, "--strict"],
                              capture_output=True, text=True)
        results.append({"plugin": rel(plugin), "exit": proc.returncode,
                        "output": (proc.stdout + proc.stderr).strip()})
    failed = [r for r in results if r["exit"] != 0]
    if args.format == "json":
        print(json.dumps({"fail": len(failed), "results": results}, indent=2))
    else:
        for r in failed:
            print("FAIL %s [validate]\n%s" % (r["plugin"], r["output"]))
        print("validate: %d plugins, %d failed" % (len(results), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
