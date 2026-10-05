import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plugin_test_fixtures  # noqa: E402,F401

from plugin_test import history  # noqa: E402


class HistoryTest(unittest.TestCase):
    def setUp(self):
        self.state = tempfile.mkdtemp(prefix="hist-test-")
        self.addCleanup(shutil.rmtree, self.state, True)

    def test_missing_file_and_empty_state(self):
        self.assertEqual(history.scores(self.state, "r", "p"), {})
        self.assertEqual(history.scores("", "r", "p"), {})
        history.append("", [{"case": "x"}])          # без каталога — ничего не пишет и не падает

    def test_append_and_filter(self):
        history.append(os.path.join(self.state, "sub"), [
            {"repo": "r", "plugin": "p", "case": "q-a-1", "score": 1.0, "ok": True},
            {"repo": "r", "plugin": "p", "case": "q-a-1", "score": 0.5, "ok": True},
            {"repo": "r", "plugin": "p", "case": "q-a-1", "score": 0.0, "ok": False},
            {"repo": "r", "plugin": "other", "case": "q-a-1", "score": 0.1, "ok": True},
            {"repo": "x", "plugin": "p", "case": "q-a-1", "score": 0.2, "ok": True},
        ])
        with open(os.path.join(self.state, "sub", history.FILE), "a") as fh:
            fh.write("not json\n[1,2]\n")
        self.assertEqual(history.scores(os.path.join(self.state, "sub"), "r", "p"), {"q-a-1": [1.0, 0.5]})

    def test_scores_per_model(self):
        history.append(self.state, [
            {"repo": "r", "plugin": "p", "case": "q-a-1", "score": 1.0, "ok": True, "model": "m-new"},
            {"repo": "r", "plugin": "p", "case": "q-a-1", "score": 0.4, "ok": True, "model": "m-old"},
            {"repo": "r", "plugin": "p", "case": "q-a-1", "score": 0.6, "ok": True},
            {"repo": "r", "plugin": "p", "case": "q-a-2", "score": 0.9, "ok": True, "model": "m-new"},
        ])
        self.assertEqual(history.scores(self.state, "r", "p", model="m-new"), {"q-a-1": [1.0], "q-a-2": [0.9]})
        self.assertEqual(history.scores(self.state, "r", "p", model="m-old"), {"q-a-1": [0.4]})
        self.assertEqual(history.scores(self.state, "r", "p", model="m-none"), {})
        self.assertEqual(history.scores(self.state, "r", "p"), {"q-a-1": [1.0, 0.4, 0.6], "q-a-2": [0.9]})

    def test_unreadable_file_does_not_raise_and_keeps_what_was_read(self):
        history.append(self.state, [{"repo": "r", "plugin": "p", "case": "q-a-1", "score": 1.0, "ok": True}])

        class Flaky:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def __iter__(self):
                yield json.dumps({"repo": "r", "plugin": "p", "case": "q-a-1", "score": 0.5, "ok": True}) + "\n"
                raise OSError(5, "Input/output error")

        err = io.StringIO()
        with mock.patch.object(history, "open", create=True, return_value=Flaky()), contextlib.redirect_stderr(err):
            self.assertEqual(history.scores(self.state, "r", "p"), {"q-a-1": [0.5]})
        self.assertIn("[history]", err.getvalue())
        self.assertEqual(len(err.getvalue().strip().splitlines()), 1)
        err = io.StringIO()
        with mock.patch.object(history, "open", create=True, side_effect=PermissionError(13, "Permission denied")), \
                contextlib.redirect_stderr(err):
            self.assertEqual(history.scores(self.state, "r", "p"), {})
        self.assertIn("[history]", err.getvalue())

    def test_append_is_sorted_json_lines(self):
        history.append(self.state, [{"b": 1, "a": "й"}])
        with open(os.path.join(self.state, history.FILE), encoding="utf-8") as fh:
            self.assertEqual(fh.read(), '{"a": "й", "b": 1}\n')

    def test_regressed(self):
        self.assertEqual(history.regressed([1, 1, 1, 1], 0.75), 1.0)
        self.assertIsNone(history.regressed([1, 1, 1, 1], 0.76))
        self.assertIsNone(history.regressed([0.9], 0.0))
        self.assertEqual(history.regressed([0, 0, 0, 0, 1, 1, 1, 1], 0.7), 1.0)
        self.assertEqual(history.regressed([0.9, 0.9], 0.65), 0.9)


if __name__ == "__main__":
    unittest.main()
