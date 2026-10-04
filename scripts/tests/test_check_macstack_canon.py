# scripts/tests/test_check_macstack_canon.py
"""scripts/check-macstack-canon.sh: the bundled mirrors must equal the canon.

No network: the canon is served from a temp directory through file:// (the script's
MACSTACK_CANON_BASE), the mirrors live in another temp directory
(MACSTACK_MIRROR_DIR), and nothing is written outside them.
"""
import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPT = os.path.join(ROOT, "scripts", "check-macstack-canon.sh")
BUNDLED = os.path.join(ROOT, "plugins", "macstack-dev", "skills", "lint", "references")

# mirror file name -> path of the canon file under <base>/<org>/<repo>/<ref>/
CANON = {
    "macstack.schema.json": "macstacks/macstack/main/schema/macstack.schema.json",
    "coverage-areas.json": "macstacks/registry/main/coverage-areas.json",
    "software-categories.json": "macstacks/registry/main/software-categories.json",
}


def put(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def digest(data):
    return hashlib.sha256(data).hexdigest()


@unittest.skipUnless(shutil.which("curl") and shutil.which("bash"), "curl and bash are required")
class CanonGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="canon-guard-")
        self.canon = os.path.join(self.tmp, "canon")
        self.mirror = os.path.join(self.tmp, "mirror")
        os.makedirs(self.mirror)
        self.data = {}
        for name, remote in CANON.items():
            self.data[name] = ('{"file": "%s", "token": "TOKEN-SHOULD-NEVER-BE-PRINTED"}\n'
                               % name).encode()
            put(os.path.join(self.canon, remote), self.data[name])
            put(os.path.join(self.mirror, name), self.data[name])

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_guard(self, **extra):
        env = dict(os.environ)
        env.pop("MACSTACK_CANON_OFFLINE", None)
        env.update({"MACSTACK_CANON_BASE": "file://" + self.canon,
                    "MACSTACK_MIRROR_DIR": self.mirror})
        env.update(extra)
        proc = subprocess.run(["bash", SCRIPT], env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, universal_newlines=True)
        return proc.returncode, proc.stdout, proc.stderr

    def test_identical_mirrors_pass(self):
        code, out, err = self.run_guard()
        self.assertEqual(code, 0, out + err)
        for name in CANON:
            self.assertIn("ok   %s" % name, out)
        self.assertIn("3 mirrors equal the canon", out)

    def test_a_differing_schema_fails_and_names_the_file_and_both_digests(self):
        drifted = self.data["macstack.schema.json"] + b" "
        put(os.path.join(self.mirror, "macstack.schema.json"), drifted)
        code, out, err = self.run_guard()
        self.assertEqual(code, 1, out + err)
        self.assertIn("DIFF macstack.schema.json", err)
        self.assertIn(digest(drifted), err)
        self.assertIn(digest(self.data["macstack.schema.json"]), err)
        self.assertNotIn("DIFF coverage-areas.json", err)

    def test_every_differing_file_is_reported_not_just_the_first(self):
        for name in CANON:
            put(os.path.join(self.mirror, name), b"{}\n")
        code, _out, err = self.run_guard()
        self.assertEqual(code, 1)
        for name in CANON:
            self.assertIn("DIFF %s" % name, err)

    def test_a_missing_mirror_fails(self):
        os.remove(os.path.join(self.mirror, "coverage-areas.json"))
        code, _out, err = self.run_guard()
        self.assertEqual(code, 1)
        self.assertIn("coverage-areas.json", err)

    def test_an_unreachable_canon_is_exit_2_and_says_how_to_skip(self):
        shutil.rmtree(self.canon)
        code, _out, err = self.run_guard()
        self.assertEqual(code, 2, err)
        self.assertIn("MACSTACK_CANON_OFFLINE=1", err)

    def test_the_offline_flag_skips_without_touching_the_network(self):
        shutil.rmtree(self.canon)
        put(os.path.join(self.mirror, "macstack.schema.json"), b"drifted")
        code, out, err = self.run_guard(MACSTACK_CANON_OFFLINE="1")
        self.assertEqual(code, 0, err)
        self.assertIn("skipped", out)

    def test_file_contents_are_never_printed(self):
        put(os.path.join(self.mirror, "macstack.schema.json"), b"TOKEN-SHOULD-NEVER-BE-PRINTED")
        code, out, err = self.run_guard()
        self.assertEqual(code, 1)
        self.assertNotIn("TOKEN-SHOULD-NEVER-BE-PRINTED", out + err)

    def test_file_contents_are_never_printed_on_a_match_either(self):
        # The `ok` line is the other place a careless echo would leak a file.
        marker = b"TOKEN-SHOULD-NEVER-BE-PRINTED"
        for name, remote in CANON.items():
            put(os.path.join(self.canon, remote), marker + name.encode())
            put(os.path.join(self.mirror, name), marker + name.encode())
        code, out, err = self.run_guard()
        self.assertEqual(code, 0, out + err)
        self.assertNotIn(marker.decode(), out + err)

    def test_a_fetch_failure_names_curls_reason(self):
        # Without curl's own line a 404, a 429 and a timeout all read the same.
        os.remove(os.path.join(self.canon, CANON["coverage-areas.json"]))
        code, _out, err = self.run_guard()
        self.assertEqual(code, 2, err)
        self.assertIn("curl:", err)

    def test_the_default_mirror_directory_holds_the_three_bundled_files(self):
        for name in CANON:
            self.assertTrue(os.path.isfile(os.path.join(BUNDLED, name)), name)

    def test_the_ref_is_configurable(self):
        for name, remote in CANON.items():
            put(os.path.join(self.canon, remote.replace("/main/", "/v9/")), self.data[name])
            os.remove(os.path.join(self.canon, remote))
        code, out, err = self.run_guard(MACSTACK_CANON_REF="v9")
        self.assertEqual(code, 0, out + err)


class CiWiring(unittest.TestCase):
    WF = os.path.join(ROOT, ".github", "workflows")

    def read(self, name):
        with open(os.path.join(self.WF, name)) as fh:
            return fh.read()

    def test_a_workflow_of_its_own_runs_the_guard(self):
        self.assertIn("scripts/check-macstack-canon.sh", self.read("macstack-canon.yml"))

    def test_the_guard_does_not_gate_unrelated_pull_requests(self):
        # It needs the network and other repositories: a canon change or a fetch
        # hiccup must not turn a PR that never touched macstack-dev red.
        text = self.read("macstack-canon.yml")
        self.assertIn("plugins/macstack-dev/**", text)
        self.assertIn("schedule:", text)
        self.assertNotIn("check-macstack-canon", self.read("scrub.yml"))

    def test_the_guard_is_not_part_of_the_no_network_unit_tests(self):
        # The plugin's own suite and the `tests` job must stay runnable offline.
        with open(os.path.join(ROOT, "plugins", "macstack-dev", "run-tests.sh")) as fh:
            self.assertNotIn("check-macstack-canon", fh.read())

    def test_the_tests_job_runs_the_macstack_dev_suite(self):
        text = self.read("scrub.yml")
        start = text.index("\n  tests:")
        self.assertIn("run-tests.sh", text[start:])
        self.assertIn("plugins/macstack-dev", text[start:])

if __name__ == "__main__":
    unittest.main()
