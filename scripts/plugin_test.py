#!/usr/bin/env python3
"""L1 «Контракт»: текст плагина против снимков реальности.

  python3 scripts/plugin_test.py                          # все плагины, режим ci
  python3 scripts/plugin_test.py --plugin plane-ops       # один плагин
  python3 scripts/plugin_test.py --changed origin/main --strict
  python3 scripts/plugin_test.py --mode server --env-file <workspace>/.env --update-snapshots
  python3 scripts/plugin_test.py --repo <workspace>/claude-plugins-private --mode server --env-file …

Коды выхода — как у publication gate: 0 чисто, 1 есть fail, 2 только warn/infra.
Как писать манифест и фикстуры: tests/README.md.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plugin_test.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
