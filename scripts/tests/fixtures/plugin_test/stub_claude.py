#!/usr/bin/env python3
"""Заглушка `claude` для тестов L2: `auth status` и `plugin eval` по плану.

STUB_PLAN — JSON-массив шагов, по одному на вызов `plugin eval` (последний повторяется):
  {"exit": 0, "stdout": "", "stderr": "", "sleep": 0, "result": <aggregate-result.json> | null}
У прогона в result ключ "trace": [rate_limit_info, …] — заглушка создаёт <tmp>/claude-eval-*/out/trace.jsonl
с этими событиями и подставляет tracePath, как настоящий CLI с --keep-temp.
STUB_AUTH — что печатать на `auth status --json` ("SLEEP" — зависнуть). STUB_LOG — журнал вызовов:
argv, имена переменных окружения и, для `plugin eval`, файлы дерева --eval-dir.
"""
import json
import os
import sys
import tempfile
import time

DEFAULT_AUTH = '{"loggedIn": true, "authMethod": "claude.ai", "subscriptionType": "max"}'


def log(entry):
    path = os.environ.get("STUB_LOG")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")


def materialize_traces(result):
    for case in result.get("cases", []):
        for arm in ("with", "without"):
            for run in (case.get("arms") or {}).get(arm) or []:
                infos = run.pop("trace", None)
                if infos is None:
                    continue
                tmp = tempfile.mkdtemp(prefix="claude-eval-")
                os.makedirs(os.path.join(tmp, "out"))
                trace = os.path.join(tmp, "out", "trace.jsonl")
                with open(trace, "w", encoding="utf-8") as fh:
                    fh.write(json.dumps({"type": "system", "subtype": "init"}) + "\n")
                    for info in infos:
                        fh.write(json.dumps({"type": "rate_limit_event", "rate_limit_info": info}) + "\n")
                run["tracePath"] = trace


def main(argv):
    entry = {"argv": argv, "env": sorted(k for k in os.environ if not k.startswith("STUB_"))}
    if argv[:2] == ["plugin", "eval"] and "--eval-dir" in argv:
        root = os.path.join(argv[2], argv[argv.index("--eval-dir") + 1])
        entry["files"] = sorted(os.path.relpath(os.path.join(d, f), root)
                                for d, _, names in os.walk(root) for f in names)
    log(entry)
    if argv[:2] == ["auth", "status"]:
        auth = os.environ.get("STUB_AUTH", DEFAULT_AUTH)
        if auth == "SLEEP":
            time.sleep(30)
        print(auth)
        return 0
    if argv[:2] != ["plugin", "eval"]:
        print("stub: unknown command", file=sys.stderr)
        return 64
    plan_path = os.environ["STUB_PLAN"]
    with open(plan_path, encoding="utf-8") as fh:
        plan = json.load(fh)
    counter = plan_path + ".n"
    n = 0
    if os.path.exists(counter):
        with open(counter) as fh:
            n = int(fh.read())
    with open(counter, "w") as fh:
        fh.write(str(n + 1))
    step = plan[min(n, len(plan) - 1)]
    if step.get("sleep"):
        time.sleep(step["sleep"])
    result = step.get("result")
    if result is not None:
        materialize_traces(result)
        out_dir = argv[argv.index("--output-dir") + 1]
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "aggregate-result.json"), "w", encoding="utf-8") as fh:
            json.dump(result, fh)
    sys.stdout.write(step.get("stdout", ""))
    sys.stderr.write(step.get("stderr", ""))
    return step.get("exit", 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
