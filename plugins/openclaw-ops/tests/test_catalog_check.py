"""catalog-check — the battery and the findings catalog share one id space.

Upstream lint ids changed shape: a core check is ``core/doctor/<check>`` and a plugin's
check is ``<plugin>/<check>``, where they used to be flat dotted names. They are carried
through verbatim like the older families, so the checker has to recognise them as
pass-through by shape — a catalog row for every plugin that will ever ship a check could
not be written — and it must still insist that an id of OURS has a row.
"""

import importlib.util
import io
import os
import unittest
from contextlib import redirect_stdout

import _support

_PATH = os.path.join(_support.PLUGIN_ROOT, "scripts", "catalog-check.py")
_spec = importlib.util.spec_from_file_location("catalog_check", _PATH)
catalog_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(catalog_check)


class PassThroughShapeTest(unittest.TestCase):

    def test_the_new_upstream_id_shapes_are_pass_through(self):
        for fid in ("core/doctor/gateway-config", "core/doctor/lint-inspection",
                    "memory-core/managed-local-embedding-setup", "some-plugin/some-check"):
            with self.subTest(fid=fid):
                self.assertTrue(catalog_check.is_passthrough(fid))

    def test_the_older_upstream_families_still_are(self):
        for fid in ("fs.permissions", "gateway.auth", "tools.exec.mode", "plugins.load",
                    "security.exposure.metrics"):
            with self.subTest(fid=fid):
                self.assertTrue(catalog_check.is_passthrough(fid))

    def test_an_id_of_ours_is_never_pass_through(self):
        for fid in ("fleet.lint.run-failed", "fleet.lint.unclassified", "fleet.config.empty"):
            with self.subTest(fid=fid):
                self.assertFalse(catalog_check.is_passthrough(fid))


class CatalogCoversBatteryTest(unittest.TestCase):

    def test_every_id_the_battery_emits_has_a_row_or_is_pass_through(self):
        out = io.StringIO()
        with redirect_stdout(out):
            code = catalog_check.main([])
        self.assertEqual(code, 0, out.getvalue())

    def test_a_failed_lint_run_has_its_own_catalogued_id(self):
        pairs, _dynamic = catalog_check.emissions(catalog_check.BATTERY)
        rows = catalog_check.catalog_rows(catalog_check.CATALOG)
        self.assertIn(("fleet.lint.run-failed", "high"), pairs)
        self.assertEqual(rows["fleet.lint.run-failed"], "high")


if __name__ == "__main__":
    unittest.main()
