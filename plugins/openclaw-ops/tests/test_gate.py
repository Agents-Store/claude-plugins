"""gate — the dry-run plan, the gates it demands, and the batch direction.

These are enforcement rules, not advice, so the tests assert refusals as often
as they assert successes. The acceptance test behind the plan format is written
into the eight blocks themselves: a human holding only the printed plan, with
the plugin uninstalled, must be able to perform the rollback by hand — which is
why an unfilled block and a prose ROLLBACK both refuse to render.
"""

import os
import tempfile
import unittest

import _support                                  # noqa: F401  (path bootstrap)
import gate


EIGHT_BLOCKS = ["TARGET", "PRECHECK", "CHANGE", "BACKUP",
                "IMPACT", "VALIDATE", "ROLLBACK", "APPLY"]


def filled_plan(risk="R2", operation="restart gateway", target="alpha"):
    """A plan with every mandatory block filled and an executable rollback."""
    return gate.make_plan(
        operation, risk, target,
        TARGET="alpha (resolved by name, not by selector)",
        PRECHECK="container running, config readable, no crash loop",
        CHANGE="no file is edited; the container is replaced (deletions: 0)",
        BACKUP="not required at this risk class; the config is untouched",
        IMPACT="the gateway stops answering for about 10 seconds",
        VALIDATE="openclaw health --json  ->  ok: true",
        ROLLBACK="docker compose -p acme-alpha up -d gateway",
        APPLY="docker compose -p acme-alpha restart gateway",
    )


class PlanBlocksTest(unittest.TestCase):
    """All eight blocks, every time, or the plan does not render."""

    def test_the_format_declares_exactly_the_eight_blocks(self):
        self.assertEqual([name for name, _ in gate.BLOCKS], EIGHT_BLOCKS)

    def test_a_complete_plan_validates_and_prints_every_block(self):
        plan = filled_plan()
        self.assertEqual(plan.validate(), [])
        rendered = plan.render()
        for name in EIGHT_BLOCKS:
            with self.subTest(block=name):
                self.assertIn("%s:" % name, rendered)

    def test_a_missing_block_is_named_and_refuses_to_render(self):
        plan = filled_plan()
        plan.blocks.pop("APPLY")
        self.assertIn("missing block APPLY", plan.validate())
        with self.assertRaises(gate.GateError):
            plan.render()

    def test_a_blank_block_counts_as_missing(self):
        plan = filled_plan()
        plan.set("IMPACT", "   ")
        self.assertIn("missing block IMPACT", plan.validate())

    def test_an_unknown_block_name_is_refused(self):
        with self.assertRaises(gate.GateError):
            filled_plan().set("NOTES", "something")

    def test_the_rendered_plan_states_the_risk_class_and_its_gate(self):
        rendered = filled_plan().render()
        self.assertIn("risk R2", rendered)
        self.assertIn("Re-run with --yes to apply", rendered)


class RollbackTest(unittest.TestCase):
    """Prose is not a rollback: the block must be something a human can run."""

    def test_a_missing_rollback_is_an_error(self):
        plan = filled_plan()
        plan.blocks.pop("ROLLBACK")
        self.assertIn("missing block ROLLBACK", plan.validate())
        with self.assertRaises(gate.GateError):
            plan.render()

    def test_an_empty_rollback_is_an_error(self):
        plan = filled_plan()
        plan.set("ROLLBACK", "")
        self.assertIn("missing block ROLLBACK", plan.validate())

    def test_a_described_rollback_is_rejected(self):
        plan = filled_plan()
        plan.set("ROLLBACK", "restore the previous config from the backup")
        problems = plan.validate()
        self.assertTrue(any("executable command" in p for p in problems), problems)

    def test_a_command_rollback_is_accepted(self):
        plan = filled_plan()
        plan.set("ROLLBACK", "cp <snapshot> <data-root>/alpha/data/openclaw.json")
        self.assertEqual(plan.validate(), [])


class YesGateTest(unittest.TestCase):
    """R1 and above need --yes, and never in the turn the plan was first shown."""

    def test_a_read_needs_no_gate(self):
        plan = filled_plan(risk="R0")
        self.assertFalse(plan.requires_yes())
        self.assertTrue(gate.gate(plan))

    def test_a_read_with_an_effect_is_gated_like_a_write(self):
        plan = filled_plan(risk="R1", operation="probe models")
        self.assertTrue(plan.requires_yes())
        with self.assertRaises(gate.GateError):
            gate.gate(plan, yes=False)

    def test_r2_without_yes_is_refused(self):
        with self.assertRaisesRegex(gate.GateError, "dry run only"):
            gate.gate(filled_plan(), yes=False)

    def test_yes_in_the_same_turn_as_the_offer_is_refused(self):
        with self.assertRaisesRegex(gate.GateError, "same turn"):
            gate.gate(filled_plan(), yes=True, first_offer=True)

    def test_yes_after_an_answer_applies(self):
        self.assertTrue(gate.gate(filled_plan(), yes=True, first_offer=False))

    def test_an_incomplete_plan_is_refused_before_any_gate_is_considered(self):
        plan = filled_plan()
        plan.blocks.pop("VALIDATE")
        with self.assertRaisesRegex(gate.GateError, "not renderable"):
            gate.gate(plan, yes=True, first_offer=False)


class BackupAndConfirmTest(unittest.TestCase):
    """R3 needs a backup that exists; R4 needs a phrase typed at the target."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = os.path.join(self.tmp.name, "openclaw.json")
        with open(self.source, "w", encoding="utf-8") as fh:
            fh.write('{"agents": {}}\n')

    def _backup(self):
        return gate.snapshot(self.source, snapshot_dir=os.path.join(self.tmp.name, "snapshots"))

    def test_r3_without_an_attached_backup_does_not_validate(self):
        plan = filled_plan(risk="R3", operation="upgrade runtime")
        problems = plan.validate()
        self.assertTrue(any("backup" in p for p in problems), problems)

    def test_r3_with_a_taken_backup_validates_and_shows_its_fingerprint(self):
        plan = filled_plan(risk="R3", operation="upgrade runtime")
        record = self._backup()
        plan.set("IRREVERSIBLE", "the previous image layer may be pruned")
        plan.set("CONFIRM", plan.confirm_phrase())
        plan.attach_backup(record)
        self.assertEqual(plan.validate(), [])
        self.assertIn(record["fingerprint"], plan.render())

    def test_a_snapshot_is_taken_outside_the_cli_backup_ring(self):
        record = self._backup()
        self.assertTrue(os.path.isfile(record["path"]))
        self.assertNotIn(".bak.", record["path"])
        self.assertTrue(record["fingerprint"].startswith("fp:"))

    def _r4_plan(self):
        plan = filled_plan(risk="R4", operation="rotate gateway token")
        plan.set("IRREVERSIBLE", "every operator session is invalidated at once")
        plan.set("CONFIRM", plan.confirm_phrase())
        plan.attach_backup(self._backup())
        return plan

    def test_r4_demands_the_two_extra_blocks(self):
        plan = self._r4_plan()
        self.assertIn("IRREVERSIBLE", plan.required_blocks())
        self.assertIn("CONFIRM", plan.required_blocks())

    def test_the_phrase_carries_the_operation_and_the_target(self):
        plan = self._r4_plan()
        self.assertEqual(plan.confirm_phrase(), "ROTATE-GATEWAY-TOKEN alpha IRREVERSIBLE")

    def test_r4_without_the_phrase_is_refused(self):
        with self.assertRaisesRegex(gate.GateError, "irreversible"):
            gate.gate(self._r4_plan(), yes=True, first_offer=False, typed=None)

    def test_r4_with_the_wrong_phrase_is_refused(self):
        with self.assertRaises(gate.GateError):
            gate.gate(self._r4_plan(), yes=True, first_offer=False,
                      typed="ROTATE-GATEWAY-TOKEN beta IRREVERSIBLE")

    def test_r4_with_the_exact_phrase_applies(self):
        plan = self._r4_plan()
        self.assertTrue(gate.gate(plan, yes=True, first_offer=False,
                                  typed=plan.confirm_phrase()))

    def test_a_confirm_block_that_does_not_quote_the_phrase_does_not_validate(self):
        plan = self._r4_plan()
        plan.set("CONFIRM", "type yes to continue")
        problems = plan.validate()
        self.assertTrue(any("exact phrase" in p for p in problems), problems)


class PlanIdRegistryTest(unittest.TestCase):
    """A plan id is a record, not a shape.

    Checking the string with a regex made the barrier disciplinary: any well-formed
    id passed, and it passed for ever. So minting writes a record and the check
    reads it back — issued here, unexpired, this instance, this class — and burns
    it, because one plan authorises one mutation.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = os.path.join(self.tmp.name, "plans")

    def mint(self, command="repair", target="alpha", **kw):
        kw.setdefault("risk", "R2")
        return gate.make_plan_id(command, target, directory=self.dir, **kw)

    # -- the hole this closes --------------------------------------------- #
    def test_an_invented_id_of_the_right_shape_is_refused(self):
        with self.assertRaisesRegex(gate.GateError, "was issued on this host"):
            gate.check_plan_id("repair/alpha/2020-01-01T00:00:00Z", "alpha", directory=self.dir)

    def test_an_issued_id_is_accepted_once(self):
        plan_id = self.mint()
        parts = gate.check_plan_id(plan_id, "alpha", directory=self.dir, consume=True)
        self.assertEqual(parts["command"], "repair")
        self.assertEqual(parts["record"]["target"], "alpha")

    def test_a_used_id_cannot_authorise_a_second_mutation(self):
        plan_id = self.mint()
        gate.check_plan_id(plan_id, "alpha", directory=self.dir, consume=True)
        with self.assertRaisesRegex(gate.GateError, "already used"):
            gate.check_plan_id(plan_id, "alpha", directory=self.dir)

    def test_checking_without_consuming_leaves_the_record_live(self):
        plan_id = self.mint()
        gate.check_plan_id(plan_id, "alpha", directory=self.dir)
        self.assertTrue(gate.check_plan_id(plan_id, "alpha", directory=self.dir, consume=True))

    # -- the other three ways a well-formed id fails ----------------------- #
    def test_an_expired_record_is_refused(self):
        plan_id = self.mint(ttl=-1)
        with self.assertRaisesRegex(gate.GateError, "expired"):
            gate.check_plan_id(plan_id, "alpha", directory=self.dir)

    def test_an_id_minted_for_another_instance_does_not_widen(self):
        plan_id = self.mint(target="alpha")
        with self.assertRaisesRegex(gate.GateError, "minted for 'alpha'"):
            gate.check_plan_id(plan_id, "beta", directory=self.dir)

    def test_a_plan_authorises_its_own_class_and_below_only(self):
        plan_id = self.mint(risk="R2")
        self.assertTrue(gate.check_plan_id(plan_id, "alpha", risk="R1", directory=self.dir))
        with self.assertRaisesRegex(gate.GateError, "class R2"):
            gate.check_plan_id(plan_id, "alpha", risk="R3", directory=self.dir)

    # -- minting ----------------------------------------------------------- #
    def test_only_a_plan_building_command_mints(self):
        with self.assertRaises(gate.GateError):
            self.mint(command="exec")

    def test_the_record_carries_the_fingerprint_of_the_plan_it_stands_for(self):
        plan = filled_plan()
        plan_id = gate.make_plan_id("repair", "alpha", plan=plan, directory=self.dir)
        record = gate.check_plan_id(plan_id, "alpha", directory=self.dir)["record"]
        self.assertEqual(record["risk"], "R2")
        self.assertTrue(record["plan_hash"].startswith("fp:"))

    def test_an_id_is_not_minted_for_a_plan_that_does_not_render(self):
        plan = filled_plan()
        plan.blocks.pop("ROLLBACK")
        with self.assertRaisesRegex(gate.GateError, "does not render"):
            gate.make_plan_id("repair", "alpha", plan=plan, directory=self.dir)

    def test_an_id_is_not_minted_for_an_instance_the_plan_does_not_target(self):
        with self.assertRaisesRegex(gate.GateError, "the plan targets"):
            gate.make_plan_id("repair", "beta", plan=filled_plan(), directory=self.dir)

    def test_the_shape_check_stays_available_and_says_nothing_about_issuance(self):
        self.assertEqual(gate.parse_plan_id("repair/alpha/2020-01-01T00:00:00Z")["target"],
                         "alpha")
        with self.assertRaises(gate.GateError):
            gate.parse_plan_id("not-a-plan-id")

    def test_records_are_private_to_the_operator(self):
        self.mint()
        names = os.listdir(self.dir)
        self.assertEqual(len(names), 1)
        mode = os.stat(os.path.join(self.dir, names[0])).st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_the_registry_lists_what_it_issued(self):
        self.mint(when="2020-01-01T00:00:01Z")
        self.mint(when="2020-01-01T00:00:02Z")
        listed = gate.plan_records(directory=self.dir)
        self.assertEqual(len(listed), 2)
        self.assertTrue(all(r["command"] == "repair" for r in listed))


class BatchPolicyTest(unittest.TestCase):
    """Batch behaviour follows the direction of the transition, not the command."""

    def test_good_to_changed_stops_at_the_first_failure(self):
        policy = gate.batch_policy("good-to-changed")
        self.assertEqual(policy["mode"], "fail-fast")
        self.assertIn("no documented state", policy["why"])

    def test_broken_to_repair_finishes_the_run_and_reports(self):
        policy = gate.batch_policy("broken-to-repair")
        self.assertEqual(policy["mode"], "continue-and-report")

    def test_an_unnamed_direction_is_refused_rather_than_defaulted(self):
        with self.assertRaises(gate.GateError):
            gate.batch_policy("whatever")


if __name__ == "__main__":
    unittest.main()
