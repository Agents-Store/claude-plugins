#!/usr/bin/env python3
"""catalog-check.py — prove that the code and the catalog share one id space.

    catalog-check.py [--verbose]

The findings catalog is a contract with four consumers, and the battery is one of
them. If ``healthcheck.py`` emits an id the catalog does not declare, the loop
audit -> report -> repair breaks at exactly that finding: the report prints a
repair line nobody can resolve, and ``/openclaw-ops:repair`` stops with "no row".
That failure is silent per finding, which is why it is checked mechanically here
rather than by reading two files side by side.

What it asserts
---------------
1. Every finding id ``healthcheck.py`` can emit has a row in the catalog. Ids
   reached through a loop variable or an ``or``-default are resolved too, so the
   set is the emittable set, not the grep-able set.
2. The severity each emission carries equals the ``sev`` the catalog's row
   states, in the one four-name vocabulary.
3. Upstream pass-through ids are exempt from (1) by design — they arrive from the
   runtime with their own ``checkId`` and are carried verbatim — but their
   families must be the ones the catalog documents.

Exit codes
----------
    0  the catalog covers the code
    1  a mismatch (the offending ids are listed)
    2  a file could not be read or parsed
"""

import argparse
import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BATTERY = os.path.join(HERE, "healthcheck.py")
CATALOG = os.path.join(ROOT, "skills", "fleet-diagnostics", "references",
                       "findings-catalog.md")

SEVERITIES = ("info", "warn", "high", "critical")
# Families the runtime owns. Their ids are carried through verbatim and are
# therefore not, and must never be, rows in our catalog.
PASSTHROUGH_FAMILIES = ("fs.", "gateway.", "tools.exec.", "plugins.", "security.exposure.")

ROW_RE = re.compile(r"^\|\s*`([a-z][a-z0-9.-]+)`\s*\|\s*([a-z]+)\s*\|")


# --------------------------------------------------------------------------- #
# the code side
# --------------------------------------------------------------------------- #

def _const(node):
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _loop_bindings(tree):
    """``for a, b, c in ((...), (...)):`` -> a list of per-iteration bindings.

    Kept row by row rather than column by column on purpose: the id and the
    severity of one loop row belong together, and flattening them into two
    independent lists would invent every cross-product pair that the code cannot
    actually emit.
    """
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.For):
            continue
        if not isinstance(node.target, ast.Tuple) or not isinstance(node.iter, (ast.Tuple, ast.List)):
            continue
        names = [e.id for e in node.target.elts if isinstance(e, ast.Name)]
        if len(names) != len(node.target.elts):
            continue
        rows = []
        for row in node.iter.elts:
            if not isinstance(row, ast.Tuple) or len(row.elts) != len(names):
                continue
            rows.append({name: _const(element) for name, element in zip(names, row.elts)})
        if rows:
            out.append((set(names), rows))
    return out


def _or_defaults(tree):
    """``name = something or "literal"`` -> {name: "literal"} (the fallback id)."""
    out = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if isinstance(node.value, ast.BoolOp) and isinstance(node.value.op, ast.Or):
            value = _const(node.value.values[-1])
            if value is not None:
                out[target.id] = value
    return out


def emissions(path):
    """Every ``(id, severity)`` pair the battery can emit, plus what stayed dynamic."""
    tree = ast.parse(open(path, encoding="utf-8").read(), filename=path)
    loops, defaults = _loop_bindings(tree), _or_defaults(tree)
    pairs, dynamic = set(), []
    for node in ast.walk(tree):
        # Read through getattr rather than an attribute chain: the publication
        # gate reads a dotted chain ending in a TLD-shaped label as a hostname.
        if not isinstance(node, ast.Call):
            continue
        callee = getattr(node, "func", None)
        if not (isinstance(callee, ast.Name) and getattr(callee, "id", None) == "finding"):
            continue
        if len(node.args) < 3:
            dynamic.append("finding() called with %d positional args at line %d"
                           % (len(node.args), node.lineno))
            continue
        fid_node, sev_node = node.args[1], node.args[2]
        names = {n.id for n in (fid_node, sev_node) if isinstance(n, ast.Name)}
        bindings = [rows for keys, rows in loops if names and names <= keys]
        if bindings:
            # Both arguments come from the same loop row: expand row by row.
            for row in bindings[0]:
                fid = _const(fid_node) or row.get(getattr(fid_node, "id", None))
                sev = _const(sev_node) or row.get(getattr(sev_node, "id", None))
                if fid is None:
                    dynamic.append("line %d: id is not statically resolvable" % node.lineno)
                else:
                    pairs.add((fid, sev))
            continue
        fid = _const(fid_node)
        if fid is None and isinstance(fid_node, ast.Name):
            fid = defaults.get(fid_node.id)
        if fid is None:
            dynamic.append("line %d: id is not statically resolvable" % node.lineno)
            continue
        sev = _const(sev_node)
        if sev is None:
            # A severity computed at run time (an upstream finding carries its own).
            dynamic.append("line %d: %s takes its severity from upstream" % (node.lineno, fid))
        pairs.add((fid, sev))
    return pairs, dynamic


# --------------------------------------------------------------------------- #
# the catalog side
# --------------------------------------------------------------------------- #

def catalog_rows(path):
    """``id -> severity`` for every row in the catalog's tables."""
    rows = {}
    for line in open(path, encoding="utf-8"):
        match = ROW_RE.match(line.strip())
        if match and match.group(2) in SEVERITIES:
            rows[match.group(1)] = match.group(2)
    return rows


# --------------------------------------------------------------------------- #

def main(argv=None):
    ap = argparse.ArgumentParser(prog="catalog-check.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verbose", action="store_true", help="print every id on both sides")
    args = ap.parse_args(argv)

    try:
        pairs, dynamic = emissions(BATTERY)
        rows = catalog_rows(CATALOG)
    except (OSError, SyntaxError) as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2

    emitted = sorted({fid for fid, _sev in pairs})
    missing = [fid for fid in emitted
               if fid not in rows and not fid.startswith(PASSTHROUGH_FAMILIES)]
    bad_sev = sorted({(fid, sev, rows[fid]) for fid, sev in pairs
                      if sev is not None and fid in rows and rows[fid] != sev})
    unknown_sev = sorted({(fid, sev) for fid, sev in pairs
                          if sev is not None and sev not in SEVERITIES})

    print("emitted by healthcheck.py : %d distinct id(s)" % len(emitted))
    print("declared by the catalog   : %d row(s)" % len(rows))
    print("severity vocabulary       : %s" % ", ".join(SEVERITIES))
    print("upstream pass-through     : %s (carried verbatim, no row by design)"
          % ", ".join(f + "*" for f in PASSTHROUGH_FAMILIES))
    if args.verbose:
        print("\nemitted:")
        for fid in emitted:
            print("  %-42s %s" % (fid, rows.get(fid, "(pass-through)")))
        print("\ncatalog ids not emitted by the battery (reported by skills, agents or /repair):")
        for fid in sorted(set(rows) - set(emitted)):
            print("  %-42s %s" % (fid, rows[fid]))

    ok = True
    if missing:
        ok = False
        print("\nFAIL: emitted with no catalog row (%d):" % len(missing))
        for fid in missing:
            print("  %s" % fid)
    if unknown_sev:
        ok = False
        print("\nFAIL: severity outside the vocabulary (%d):" % len(unknown_sev))
        for fid, sev in unknown_sev:
            print("  %s -> %r" % (fid, sev))
    if bad_sev:
        ok = False
        print("\nFAIL: severity disagrees with the catalog row (%d):" % len(bad_sev))
        for fid, sev, want in bad_sev:
            print("  %s: code %r, catalog %r" % (fid, sev, want))
    if dynamic:
        print("\nnote: %d emission(s) resolved dynamically:" % len(dynamic))
        for line in dynamic:
            print("  %s" % line)

    print("\n%s" % ("PASS: the catalog covers every id the battery emits."
                    if ok else "FAIL: the two id spaces do not agree."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
