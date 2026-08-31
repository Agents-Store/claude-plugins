"""ocexec — the single door: what it refuses, what it redacts, what it locks.

Every openclaw CLI call in this plugin goes through ``ocexec.py``, so every rule
that protects an operator is enforced in exactly one file — and a regression
there is invisible until it has already run. These tests pin the four things
that were fixed after they went wrong in the field:

* the dry run prints a command line, and the TEXT branch redacts it as the JSON
  branch does — a preview is the output most likely to be pasted into a ticket;
* a credential mutation takes the fleet-wide front lock, because the runtime's
  own lock is per state directory and a refresh token rotates across the fleet;
* above R0 the door demands the plan behind the call, and the plan id is now a
  record that is looked up and burned, not a string that merely looks right;
* an alien instance and an impossible exec path are refused rather than guessed.

No Docker daemon and no gateway: ``discovery.discover`` and ``ocexec.execute``
are stubbed, and every path the tests write to is a temporary directory.
"""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import _support                                  # noqa: F401  (path bootstrap)
import config as cfgmod
import gate
import ocexec
import ocjson


# A token-shaped string that is not a token: right form, invented value.
FAKE_KEY = "sk-ant-api03-" + "A" * 24


def instance_record(name="alpha", state="ok", profile="template", **over):
    """One discovery record, the shape ``fleet-model`` documents."""
    rec = {
        "name": name, "ok": True, "error": None, "project": "acme-%s" % name,
        "state": state, "state_reasons": [], "profile": profile, "managed": True,
        "role": "standard",
        "container": {"id": "c0ffee", "service": "gateway", "image": "openclaw:1.2.3"},
        "paths": {"state_dir": "<data-root>/%s/state" % name},
        "capabilities": {"exec_mode": "hot", "cli": True, "run_with_infisical": True},
        "signals": {},
    }
    rec.update(over)
    return rec


class DoorTestCase(unittest.TestCase):
    """Shared harness: a config whose state dirs are temporary, and no daemon."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.plans = os.path.join(self.tmp.name, "plans")
        self.cfg = cfgmod.FleetConfig(
            {"project_prefix": "acme-", "instances": {"alpha": {}},
             "policy": {"plan_dir": self.plans, "lock_dir": os.path.join(self.tmp.name, "locks")}},
            path=os.path.join(self.tmp.name, "fleet.json"))
        self.record = instance_record()

    def run_door(self, argv, result=None, records=None):
        """Run ``ocexec.main`` with discovery and execution stubbed out."""
        result = result or ocjson.OcResult(["openclaw", "health"], 0, "{}\n", "")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(ocexec.cfgmod, "load_config", return_value=self.cfg), \
                mock.patch.object(ocexec.discovery, "discover",
                                  return_value=list(records or [self.record])), \
                mock.patch.object(ocexec, "execute",
                                  return_value=(result, ["docker"])) as executed, \
                redirect_stdout(out), redirect_stderr(err):
            code = ocexec.main(argv)
        self.executed = executed
        return code, out.getvalue(), err.getvalue()

    def mint(self, command="repair", target="alpha", risk="R2", **kw):
        return gate.make_plan_id(command, target, risk=risk, cfg=self.cfg, **kw)


class DryRunRedactionTest(DoorTestCase):
    """The preview is output too, and it is the output people paste."""

    ARGV = ["alpha", "--dry-run", "--", "config", "set", "provider.apiKey", FAKE_KEY]

    def test_the_text_branch_redacts_the_resolved_command_line(self):
        code, out, _ = self.run_door(list(self.ARGV))
        self.assertEqual(code, 0)
        self.assertNotIn(FAKE_KEY, out)
        self.assertIn("[REDACTED:anthropic-key:", out)

    def test_the_json_branch_redacts_the_same_line(self):
        code, out, _ = self.run_door(["alpha", "--dry-run", "--json"] + list(self.ARGV[2:]))
        self.assertEqual(code, 0)
        self.assertNotIn(FAKE_KEY, out)
        payload = json.loads(out)
        self.assertTrue(any("[REDACTED:" in part for part in payload["command"]))

    def test_the_preview_names_the_mode_the_class_and_the_missing_plan(self):
        _, out, _ = self.run_door(list(self.ARGV))
        self.assertIn("mode=hot", out)
        self.assertIn("risk=R2", out)
        self.assertIn("--plan-id", out)

    def test_a_dry_run_runs_nothing(self):
        self.run_door(list(self.ARGV))
        self.assertEqual(self.executed.call_count, 0)


class FleetLockTest(DoorTestCase):
    """A credential mutation serialises across the fleet, not across one state dir."""

    def test_the_auth_family_needs_the_front_lock(self):
        self.assertTrue(ocexec.needs_fleet_lock(["models", "auth", "login", "anthropic"], "R2"))
        self.assertTrue(ocexec.needs_fleet_lock(["models", "auth", "logout"], "R2"))

    def test_reading_the_profiles_does_not_take_it(self):
        risk, _ = ocexec.classify_argv(["models", "auth", "list"])
        self.assertEqual(risk, "R0")
        self.assertFalse(ocexec.needs_fleet_lock(["models", "auth", "list"], risk))

    def test_an_unrelated_mutation_does_not_take_it(self):
        self.assertFalse(ocexec.needs_fleet_lock(["gateway", "restart"], "R2"))

    def test_applying_an_auth_mutation_takes_and_releases_the_lock(self):
        plan_id = self.mint("auth")
        held = mock.MagicMock()
        with mock.patch.object(ocexec.gate, "fleet_lock", return_value=held) as taken:
            code, _, _ = self.run_door(["alpha", "--yes", "--plan-id", plan_id,
                                        "--", "models", "auth", "login", "anthropic"])
        self.assertEqual(code, 0)
        self.assertEqual(taken.call_args[0][0], gate.AUTH_LOCK)
        held.release.assert_called_once_with()

    def test_the_dry_run_says_the_lock_will_be_taken(self):
        _, out, _ = self.run_door(["alpha", "--dry-run", "--",
                                   "models", "auth", "login", "anthropic"])
        self.assertIn(gate.AUTH_LOCK, out)


class PlanAuthorityTest(DoorTestCase):
    """Above R0 the door wants the plan, and the id must be one that was issued."""

    MUTATION = ["alpha", "--yes", "--", "gateway", "restart"]

    def test_a_read_needs_no_plan(self):
        code, _, _ = self.run_door(["alpha", "--", "health"])
        self.assertEqual(code, 0)
        self.assertEqual(self.executed.call_count, 1)

    def test_yes_alone_does_not_authorise_a_mutation(self):
        code, _, err = self.run_door(list(self.MUTATION))
        self.assertEqual(code, ocexec.EXIT_REFUSED)
        self.assertIn("needs a plan behind it", err)
        self.assertEqual(self.executed.call_count, 0)

    def test_an_invented_id_of_the_right_shape_is_refused(self):
        code, _, err = self.run_door(["alpha", "--yes", "--plan-id",
                                      "repair/alpha/2020-01-01T00:00:00Z",
                                      "--", "gateway", "restart"])
        self.assertEqual(code, ocexec.EXIT_REFUSED)
        self.assertIn("was issued on this host", err)
        self.assertEqual(self.executed.call_count, 0)

    def test_an_issued_id_authorises_the_call(self):
        code, _, _ = self.run_door(["alpha", "--yes", "--plan-id", self.mint(),
                                    "--", "gateway", "restart"])
        self.assertEqual(code, 0)
        self.assertEqual(self.executed.call_count, 1)

    def test_the_id_is_burned_so_it_cannot_authorise_a_second_call(self):
        plan_id = self.mint()
        first, _, _ = self.run_door(["alpha", "--yes", "--plan-id", plan_id,
                                     "--", "gateway", "restart"])
        second, _, err = self.run_door(["alpha", "--yes", "--plan-id", plan_id,
                                        "--", "gateway", "restart"])
        self.assertEqual(first, 0)
        self.assertEqual(second, ocexec.EXIT_REFUSED)
        self.assertIn("already used", err)

    def test_an_id_minted_for_another_instance_is_refused(self):
        plan_id = self.mint(target="beta")
        code, _, err = self.run_door(["alpha", "--yes", "--plan-id", plan_id,
                                      "--", "gateway", "restart"])
        self.assertEqual(code, ocexec.EXIT_REFUSED)
        self.assertIn("minted for 'beta'", err)

    def test_r3_and_r4_argv_never_reach_the_escape_hatch(self):
        for argv in (["sessions", "prune"], ["gateway", "token"]):
            with self.subTest(argv=argv):
                code, _, err = self.run_door(["alpha", "--yes", "--plan-id", self.mint(),
                                              "--"] + argv)
                self.assertEqual(code, ocexec.EXIT_REFUSED)
                self.assertIn("does not build", err)


class RefusalTest(DoorTestCase):
    """The refusals that are never negotiable."""

    def test_an_alien_instance_runs_nothing_at_all(self):
        alien = instance_record(profile="alien", state="alien")
        code, _, err = self.run_door(["alpha", "--", "health"], records=[alien])
        self.assertEqual(code, ocexec.EXIT_REFUSED)
        self.assertIn("alien", err)

    def test_an_unmanaged_instance_is_read_on_the_host_side_only(self):
        neighbour = instance_record(managed=False, role="neighbour")
        code, _, err = self.run_door(["alpha", "--", "health"], records=[neighbour])
        self.assertEqual(code, ocexec.EXIT_REFUSED)
        self.assertIn("not managed", err)

    def test_a_probe_against_a_live_gateway_is_refused(self):
        code, _, err = self.run_door(["alpha", "--", "models", "status", "--probe"])
        self.assertEqual(code, ocexec.EXIT_REFUSED)
        self.assertIn("stopped gateway", err)

    def test_an_unknown_instance_is_a_target_error_not_a_refusal(self):
        code, _, err = self.run_door(["ghost", "--", "health"])
        self.assertEqual(code, ocexec.EXIT_TARGET)
        self.assertIn("no instance named", err)

    def test_a_banned_argument_is_refused_before_anything_else(self):
        code, _, err = self.run_door(["alpha", "--", "--accept-capabilities"])
        self.assertEqual(code, ocexec.EXIT_REFUSED)
        self.assertIn("accept-capabilities", err)


class ModeChoiceTest(DoorTestCase):
    """hot when there is a gateway, cold only when there is not — and never both."""

    def test_a_running_instance_resolves_to_hot(self):
        self.assertEqual(ocexec.choose_mode(instance_record(), "auto"), "hot")

    def test_a_degraded_instance_still_has_a_hot_path(self):
        self.assertEqual(ocexec.choose_mode(instance_record(state="degraded"), "auto"), "hot")

    def test_a_stopped_instance_falls_back_to_the_state_directory(self):
        self.assertEqual(ocexec.choose_mode(instance_record(state="down"), "auto"), "cold")

    def test_no_gateway_and_no_state_dir_is_refused_rather_than_guessed(self):
        with self.assertRaises(ocexec.Refusal):
            ocexec.choose_mode(instance_record(state="down", paths={}), "auto")

    def test_cold_over_a_running_state_directory_is_refused(self):
        with self.assertRaises(ocexec.Refusal):
            ocexec.check_policy(instance_record(), ["setup"], "R0", "cold", yes=False)

    def test_cold_runs_only_the_subcommands_safe_on_a_broken_instance(self):
        down = instance_record(state="down")
        self.assertTrue(ocexec.check_policy(down, ["database", "status"], "R0", "cold", yes=False))
        with self.assertRaises(ocexec.Refusal):
            ocexec.check_policy(down, ["health"], "R0", "cold", yes=False)

    def test_the_hot_line_keeps_the_flag_json_output_depends_on(self):
        cmd = ocexec.build_argv(instance_record(), ["health", "--json"], "hot")
        self.assertIn("-T", cmd)
        self.assertEqual(cmd[-2:], ["health", "--json"])


class BearerNeverOnArgvTest(unittest.TestCase):
    """A credential must never appear in an argument list.

    ``/proc`` publishes every process's argv to everything else in the container,
    so a header passed as ``-H`` would hand the gateway's operator token to
    anything that can run ``ps``. The probe battery is the one place in the
    plugin that holds a bearer token at all, and it is dispatched through the
    same door, so the rule is pinned here beside the door's other invariants.
    """

    TOKEN_ENVS = ["OPENCLAW_GATEWAY_TOKEN", "GATEWAY_TOKEN"]
    FAKE_TOKEN = "gw_" + "b" * 32

    def setUp(self):
        import healthcheck
        self.healthcheck = healthcheck

    def test_the_probe_script_passes_no_authorization_header_on_a_command_line(self):
        script = self.healthcheck._PROBE_SH
        self.assertNotIn("-H ", script)
        self.assertNotIn("--header", script)
        # curl reads its header from a config file on stdin; node from the
        # environment; wget from a mode-600 WGETRC. All three, never argv.
        self.assertIn("--config -", script)
        self.assertIn("WGETRC=", script)

    def test_only_the_names_of_the_token_variables_cross_the_boundary(self):
        seen = {}

        def fake_run(argv, timeout=None, input_text=None):
            seen["argv"] = argv
            return 0, "TOKEN\t%s\nCLIENT\tcurl\nPROBE\t/healthz\t0\t200\tok\n" % self.TOKEN_ENVS[0], ""

        with mock.patch.object(self.healthcheck.discovery, "run", fake_run):
            result = self.healthcheck.http_probes(instance_record(), 18789, self.TOKEN_ENVS)
        joined = " ".join(seen["argv"])
        self.assertIn("OC_TOKEN_ENVS=%s" % " ".join(self.TOKEN_ENVS), joined)
        # The host passes the NAMES to look under; the value is read by the
        # container from its own environment and never travels in the argv.
        self.assertNotIn(self.FAKE_TOKEN, joined)
        self.assertNotIn("-H", seen["argv"])
        self.assertNotIn("--header", seen["argv"])
        self.assertEqual(result["token_env"], self.TOKEN_ENVS[0])

    def test_the_exec_door_builds_no_header_arguments(self):
        for mode in ("hot", "cold"):
            with self.subTest(mode=mode):
                cmd = ocexec.build_argv(instance_record(state="down"), ["health"], mode)
                self.assertNotIn("-H", cmd)
                self.assertFalse(any("Bearer" in part for part in cmd))


if __name__ == "__main__":
    unittest.main()
