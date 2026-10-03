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
        for argv in (["sessions", "cleanup"], ["update", "cleanup"],
                     ["doctor", "--generate-gateway-token"]):
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


class RiskMarkerTest(unittest.TestCase):
    """The markers name commands that exist. A marker on a missing command classifies nothing.

    Upstream reshaped the tree: there is no ``backup list`` and no ``database status``,
    ``sessions prune`` became ``sessions cleanup``, ``secrets set`` became
    ``secrets store set`` and the token generator is a doctor flag. A READ_ONLY entry
    for a command that does not exist is harmless; an R3 or R4 marker for one is not,
    because the real command then falls through to the default class.
    """

    def risk(self, *argv):
        return ocexec.classify_argv(list(argv))[0]

    def test_commands_that_do_not_exist_are_not_on_the_read_only_list(self):
        self.assertNotIn(("backup", "list"), ocexec.READ_ONLY)
        self.assertNotIn(("database", "status"), ocexec.READ_ONLY)
        self.assertNotEqual(self.risk("backup", "list"), "R0")
        self.assertNotEqual(self.risk("database", "status"), "R0")

    def test_the_documented_reads_are_r0(self):
        for argv in (("backup", "verify", "<archive>"),
                     ("backup", "sqlite", "list"),
                     ("backup", "sqlite", "verify", "<snapshot>"),
                     ("database", "preflight"),
                     ("database", "ownership", "status"),
                     ("update", "status"),
                     ("update", "status", "--json"),
                     ("gateway", "health"),
                     ("gateway", "probe"),
                     ("secrets", "audit", "--check"),
                     ("channels", "status"),
                     ("doctor", "--lint", "--severity-min", "info"),
                     ("doctor", "--post-upgrade", "--json")):
            with self.subTest(argv=argv):
                self.assertEqual(self.risk(*argv), "R0")

    def test_sessions_cleanup_is_r3_and_the_old_name_is_not_a_marker(self):
        self.assertEqual(self.risk("sessions", "cleanup"), "R3")
        self.assertEqual(self.risk("sessions", "cleanup", "--enforce"), "R3")
        self.assertNotIn(("sessions", "prune"), ocexec.R3_MARKERS)

    def test_update_cleanup_is_r4_because_it_retires_the_recovery_originals(self):
        self.assertEqual(self.risk("update", "cleanup", "--yes"), "R4")
        self.assertEqual(self.risk("update", "cleanup", "--dry-run"), "R4")
        self.assertEqual(self.risk("update"), "R4")
        self.assertEqual(self.risk("update", "--tag", "<good>"), "R4")

    def test_update_status_is_a_read_even_though_update_is_r4(self):
        self.assertEqual(self.risk("update", "status"), "R0")
        # but a write-shaped flag on it falls back to the family class
        self.assertEqual(self.risk("update", "status", "--fix"), "R4")

    def test_memory_commands_that_delete_or_rebuild_are_r3(self):
        for argv in (("memory", "reset", "--agent", "<id>", "--yes"),
                     ("memory", "forget", "--agent", "<id>", "--session", "<s>"),
                     ("memory", "index", "--force", "--agent", "<id>"),
                     ("update", "repair")):
            with self.subTest(argv=argv):
                self.assertEqual(self.risk(*argv), "R3")

    def test_memory_reset_is_not_swallowed_by_the_top_level_reset_command(self):
        # `reset` (wipe the whole install) is R4 only as the first command word
        self.assertEqual(self.risk("reset"), "R4")
        self.assertEqual(self.risk("memory", "reset", "--yes"), "R3")
        self.assertNotEqual(self.risk("browser", "reset-profile"), "R4")

    def test_a_memory_status_that_reindexes_is_not_a_plain_read(self):
        self.assertEqual(self.risk("memory", "status", "--agent", "<id>"), "R0")
        self.assertEqual(self.risk("memory", "status", "--index", "--agent", "<id>"), "R1")

    def test_state_and_session_database_maintenance_is_r3(self):
        self.assertEqual(self.risk("doctor", "--state-sqlite", "compact"), "R3")
        for mode in ("compact", "import", "recover", "restore"):
            with self.subTest(mode=mode):
                self.assertEqual(self.risk("doctor", "--session-sqlite", mode), "R3")
        # the equals form is the same flag
        self.assertEqual(self.risk("doctor", "--session-sqlite=compact"), "R3")
        self.assertEqual(self.risk("doctor", "--state-sqlite=compact"), "R3")

    def test_the_secret_store_writes_and_apply_are_r4(self):
        for argv in (("secrets", "store", "set", "NAME"),
                     ("secrets", "store", "rm", "NAME"),
                     ("secrets", "store", "import", "--from", "<file>"),
                     ("secrets", "apply", "--from", "<plan>")):
            with self.subTest(argv=argv):
                self.assertEqual(self.risk(*argv), "R4")

    def test_the_gateway_token_generator_is_a_doctor_flag_and_r4(self):
        self.assertEqual(self.risk("doctor", "--generate-gateway-token"), "R4")
        self.assertNotIn(("gateway", "token"), ocexec.R4_MARKERS)

    def test_destructive_top_level_commands_are_r4(self):
        for argv in (("reset", "--scope", "full"), ("uninstall",), ("fleet", "rm", "<tenant>"),
                     ("migrate", "apply", "<provider>"), ("doctor", "--fix"),
                     ("security", "audit", "--fix")):
            with self.subTest(argv=argv):
                self.assertEqual(self.risk(*argv), "R4")

    def test_a_global_option_in_front_does_not_hide_a_head_only_command(self):
        # `--profile work reset` must not read as a command called `work`
        self.assertEqual(self.risk("--profile", "work", "reset"), "R4")
        self.assertEqual(self.risk("--container", "gw", "uninstall"), "R4")
        self.assertEqual(self.risk("--log-level", "debug", "--dev", "reset"), "R4")
        self.assertEqual(self.risk("--profile", "work", "memory", "reset"), "R3")
        self.assertEqual(self.risk("--profile", "work", "update", "status"), "R0")

    def test_repair_is_the_documented_alias_of_fix_and_cannot_bypass_the_r4(self):
        for argv in (("doctor", "--repair"),
                     ("doctor", "--repair", "--non-interactive"),
                     ("doctor", "--lint", "--repair"),
                     ("doctor", "--lint", "--severity-min", "info", "--repair"),
                     ("--profile", "work", "doctor", "--repair"),
                     ("--log-level", "debug", "doctor", "--lint", "--repair")):
            with self.subTest(argv=argv):
                self.assertEqual(self.risk(*argv), "R4")

    def test_doctor_yes_enters_repair_maintenance_and_is_an_r4(self):
        # upstream: --yes accepts defaults and enters repair maintenance without prompting
        self.assertEqual(self.risk("doctor", "--yes"), "R4")
        self.assertEqual(self.risk("doctor", "--non-interactive", "--yes"), "R4")

    def test_bare_doctor_and_non_interactive_are_not_reads(self):
        # ordinary doctor can copy legacy config and migrate state even without --fix
        for argv in (("doctor",), ("doctor", "--non-interactive")):
            with self.subTest(argv=argv):
                self.assertEqual(self.risk(*argv), "R2")

    def test_the_root_update_shorthand_is_the_update_command(self):
        # `openclaw --update` is documented as a shorthand for `openclaw update`
        self.assertEqual(self.risk("--update"), "R4")
        self.assertEqual(self.risk("--update", "--yes"), "R4")
        self.assertEqual(self.risk("--profile", "work", "--update"), "R4")

    def test_a_bare_triage_hands_the_installation_to_a_coding_agent_and_is_an_r4(self):
        self.assertEqual(self.risk("triage"), "R4")
        self.assertEqual(self.risk("--profile", "work", "triage"), "R4")
        self.assertEqual(self.risk("triage", "--update-result", "<path>"), "R4")

    def test_triage_collects_read_only_only_with_the_json_or_non_interactive_flag(self):
        self.assertEqual(self.risk("triage", "--json"), "R0")
        self.assertEqual(self.risk("triage", "--non-interactive"), "R0")
        self.assertEqual(self.risk("--profile", "work", "triage", "--json"), "R0")
        # selecting an agent, or asking for the embedded repair turn, is a repair
        self.assertEqual(self.risk("triage", "--run"), "R4")
        self.assertEqual(self.risk("triage", "--json", "--run"), "R4")
        self.assertEqual(self.risk("triage", "--agent", "codex"), "R4")

    def test_the_triage_read_form_keeps_the_generic_write_flag_and_marker_passes(self):
        # `triage --json` is a read only until something else on the line says otherwise:
        # the highest class wins, exactly as it does for every other command
        for argv, want in ((("triage", "--json", "--fix"), "R2"),
                           (("triage", "--json", "--apply"), "R2"),
                           (("triage", "--json", "--force"), "R2"),
                           (("triage", "--non-interactive", "--force"), "R2"),
                           (("triage", "--json", "--allow-exec"), "R1"),
                           (("triage", "--json", "update"), "R4"),
                           (("triage", "--json", "doctor", "--generate-gateway-token"), "R4"),
                           (("triage", "--json", "--output", "<dir>"), "R2"),
                           (("triage", "--json"), "R0")):
            with self.subTest(argv=argv):
                self.assertEqual(self.risk(*argv), want)

    def test_the_agent_handoff_stays_r4_whatever_else_is_on_the_line(self):
        self.assertEqual(self.risk("triage", "--json", "--run", "--allow-exec"), "R4")
        self.assertEqual(self.risk("triage", "--allow-exec"), "R4")

    def test_doctor_json_is_the_documented_read_only_advisory_posture(self):
        self.assertEqual(self.risk("doctor", "--json"), "R0")
        self.assertEqual(self.risk("doctor", "--json", "--non-interactive"), "R0")
        # but the repair-shaped flags upstream rejects there are classified by their own markers
        self.assertEqual(self.risk("doctor", "--json", "--fix"), "R4")
        self.assertEqual(self.risk("doctor", "--json", "--repair"), "R4")
        self.assertEqual(self.risk("doctor", "--json", "--yes"), "R4")
        self.assertEqual(self.risk("doctor", "--json", "--generate-gateway-token"), "R4")
        self.assertEqual(self.risk("doctor", "--json", "--force"), "R2")
        self.assertEqual(self.risk("doctor", "--json", "--state-sqlite", "compact"), "R3")

    def test_the_diagnostics_export_is_judged_like_triage_json(self):
        # both write only a sanitized support export and change no config or state: one rule.
        # A destination the caller chooses is the difference, and that is not a read.
        self.assertEqual(self.risk("gateway", "diagnostics", "export", "--json"), "R0")
        self.assertEqual(self.risk("gateway", "diagnostics", "export"), "R0")
        self.assertEqual(self.risk("gateway", "diagnostics", "export", "--output", "<zip>"), "R2")
        self.assertEqual(self.risk("triage", "--json", "--output", "<dir>"), "R2")

    def test_a_read_that_executes_configured_commands_is_not_a_plain_read(self):
        # --allow-exec lets doctor and the secrets audit run exec SecretRefs
        self.assertEqual(self.risk("secrets", "audit", "--check"), "R0")
        self.assertEqual(self.risk("secrets", "audit", "--check", "--allow-exec"), "R1")
        self.assertEqual(self.risk("doctor", "--lint", "--allow-exec"), "R1")

    def test_a_dotted_config_path_or_a_head_only_word_as_a_value_is_still_a_read(self):
        # `update.channel` is one token that is not `update`; `reset` is R4 only as a first word.
        # (A bare value spelled exactly `update` is still read as the update family: a known
        # over-classification, the safe direction, deliberately not "fixed" by loosening it.)
        self.assertEqual(self.risk("config", "get", "update.channel"), "R0")
        self.assertEqual(self.risk("config", "get", "reset"), "R0")


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
        self.assertTrue(ocexec.check_policy(down, ["database", "preflight"], "R0", "cold",
                                            yes=False))
        with self.assertRaises(ocexec.Refusal):
            ocexec.check_policy(down, ["health"], "R0", "cold", yes=False)

    def test_cold_admits_doctor_because_it_is_the_documented_recovery_path(self):
        # a gateway that exited unable to migrate its state is brought back by running
        # the same image once with doctor against the same mounts
        down = instance_record(state="down")
        for argv in (["doctor", "--lint"], ["doctor", "--post-upgrade"],
                     ["database", "ownership", "status"]):
            with self.subTest(argv=argv):
                self.assertTrue(ocexec.check_policy(down, argv, "R0", "cold", yes=False))

    def test_a_global_option_cannot_smuggle_a_command_past_the_cold_gate(self):
        down = instance_record(state="down")
        # the value of --log-level is not a command: the command here is `config`
        with self.assertRaises(ocexec.Refusal):
            ocexec.check_policy(down, ["--log-level", "setup", "config", "set", "a", "b"],
                                "R0", "cold", yes=False)
        with self.assertRaises(ocexec.Refusal):
            ocexec.check_policy(down, ["--profile=setup", "health"], "R0", "cold", yes=False)
        # and a real safe command behind a global option is still admitted
        self.assertTrue(ocexec.check_policy(down, ["--profile", "work", "doctor", "--lint"],
                                            "R0", "cold", yes=False))

    def test_cold_doctor_fix_is_still_a_planned_r4_not_a_free_pass(self):
        down = instance_record(state="down")
        risk, _ = ocexec.classify_argv(["doctor", "--fix"])
        self.assertEqual(risk, "R4")
        with self.assertRaises(ocexec.Refusal) as caught:
            ocexec.check_policy(down, ["doctor", "--fix"], risk, "cold", yes=True)
        self.assertIn("R4", str(caught.exception))

    def test_the_refusal_names_doctor_among_the_cold_safe_set(self):
        down = instance_record(state="down")
        with self.assertRaises(ocexec.Refusal) as caught:
            ocexec.check_policy(down, ["health"], "R0", "cold", yes=False)
        self.assertIn("doctor", str(caught.exception))

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
