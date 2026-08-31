"""discovery — layout fingerprint, mount reading, state classification, isolation.

Discovery is the layer every other one stands on: a wrong path here edits the
wrong file, a wrong profile mutates a legacy instance, and a swallowed error
hides the one instance that needed attention. All four are checked against
fixtures rather than against a live daemon, which is what makes the check
repeatable.
"""

import unittest
from unittest import mock

import _support                                  # noqa: F401  (path bootstrap)
import discovery


PREFIX = "acme-"


def _fake_run(stdout, rc=0, stderr=""):
    """Stand in for discovery.run(), which is the only door to a subprocess."""
    return lambda argv, **kwargs: (rc, stdout, stderr)


def _container(doc):
    """The container block discover_instance builds out of an inspect document."""
    state = doc["State"]
    labels = doc["Config"]["Labels"]
    return {
        "id": doc["Id"][:12],
        "name": doc["Name"].lstrip("/"),
        "service": labels["com.docker.compose.service"],
        "image": doc["Config"]["Image"],
        "state": state["Status"].lower(),
        "health": state["Health"]["Status"].lower(),
        "restart_count": doc["RestartCount"],
    }


def template_record():
    doc = _support.load_json("docker-inspect-gateway.json")[0]
    return {
        "name": "alpha",
        "project": "acme-alpha",
        "ok": True,
        "managed": True,
        "compose": {"config_files": ["<compose-root>/acme-alpha/docker-compose.yml"]},
        "container": _container(doc),
        "paths": discovery.mount_map(doc),
        "port": discovery.host_port(doc),
        "signals": {"config_present": True, "config_bytes": 4096, "log_age_hours": 1.0},
        "capabilities": {"cli": True},
        "fingerprint": {},
        "notes": [],
    }


def legacy_record():
    doc = _support.load_json("docker-inspect-legacy.json")[0]
    return {
        "name": "legacy-one",
        "project": "acme-legacy-one",
        "ok": True,
        "managed": True,
        "compose": {"config_files": ["<compose-root>/acme-legacy-one/compose.yml"]},
        "container": _container(doc),
        "paths": discovery.mount_map(doc),
        "port": discovery.host_port(doc),
        "signals": {},
        "capabilities": {},
        "fingerprint": {},
        "notes": [],
    }


class ComposeProjectsTest(unittest.TestCase):
    """The sweep must see stopped instances and must not see the neighbours."""

    def setUp(self):
        self.listing = _support.load_text("compose-ls.json")

    def test_prefix_selects_the_fleet_and_excludes_a_neighbour(self):
        with mock.patch.object(discovery, "run", _fake_run(self.listing)):
            rows = discovery.compose_projects(PREFIX)
        self.assertEqual([r["project"] for r in rows],
                         ["acme-alpha", "acme-beta", "acme-gamma", "acme-legacy-one"])

    def test_a_stopped_project_is_still_a_row(self):
        with mock.patch.object(discovery, "run", _fake_run(self.listing)):
            rows = discovery.compose_projects(PREFIX)
        stopped = [r for r in rows if r["project"] == "acme-gamma"]
        self.assertEqual(len(stopped), 1)
        self.assertIn("exited", stopped[0]["status"])

    def test_config_files_are_split_into_a_list(self):
        with mock.patch.object(discovery, "run", _fake_run(self.listing)):
            rows = discovery.compose_projects(PREFIX)
        self.assertEqual(rows[0]["config_files"],
                         ["<compose-root>/acme-alpha/docker-compose.yml"])

    def test_no_prefix_returns_every_project(self):
        with mock.patch.object(discovery, "run", _fake_run(self.listing)):
            rows = discovery.compose_projects(None)
        self.assertEqual(len(rows), 5)

    def test_a_refusing_daemon_raises_rather_than_returning_an_empty_fleet(self):
        with mock.patch.object(discovery, "run", _fake_run("", rc=1, stderr="permission denied")):
            with self.assertRaises(discovery.DockerError):
                discovery.compose_projects(PREFIX)

    def test_instance_name_is_the_project_without_the_prefix(self):
        self.assertEqual(discovery.instance_name("acme-alpha", PREFIX), "alpha")
        self.assertEqual(discovery.instance_name("unrelated", PREFIX), "unrelated")


class MountMapTest(unittest.TestCase):
    """Paths come from the container's own mount table, never from a constant."""

    def setUp(self):
        self.doc = _support.load_json("docker-inspect-gateway.json")[0]
        self.paths = discovery.mount_map(self.doc)

    def test_every_documented_destination_maps_to_its_host_path(self):
        self.assertEqual(self.paths["state_dir"], "<data-root>/alpha/data")
        self.assertEqual(self.paths["auth_secrets"], "<data-root>/alpha/auth-secrets")
        self.assertEqual(self.paths["claude_dir"], "<data-root>/alpha/claude")
        self.assertEqual(self.paths["claude_json"], "<data-root>/alpha/claude.json")
        self.assertEqual(self.paths["codex_home"], "<data-root>/alpha/codex-home")

    def test_shared_trees_are_recognised_by_the_tail_of_the_destination(self):
        self.assertEqual(self.paths["shared_skills"], "<data-root>/shared/skills")
        self.assertEqual(self.paths["shared_plugins"], "<data-root>/shared/plugins")

    def test_the_config_file_is_derived_from_the_mounted_state_dir(self):
        self.assertEqual(self.paths["config_file"], "<data-root>/alpha/data/openclaw.json")

    def test_an_unknown_mount_is_reported_rather_than_dropped(self):
        destinations = [m["destination"] for m in self.paths["extra"]]
        self.assertIn("/opt/openclaw-tools", destinations)

    def test_read_only_mode_survives(self):
        modes = {m["destination"]: m["mode"] for m in self.paths["extra"]}
        self.assertEqual(modes["/opt/openclaw-tools"], "ro")


class HostPortTest(unittest.TestCase):
    """Where a gateway is published is a security answer, not a cosmetic one."""

    def test_loopback_publish_is_reported_as_loopback(self):
        doc = _support.load_json("docker-inspect-gateway.json")[0]
        port = discovery.host_port(doc)
        self.assertTrue(port["loopback"])
        self.assertEqual(port["host_ip"], "127.0.0.1")
        self.assertIsInstance(port["host_port"], int)

    def test_a_publish_on_every_interface_is_not_loopback(self):
        doc = _support.load_json("docker-inspect-legacy.json")[0]
        self.assertFalse(discovery.host_port(doc)["loopback"])

    def test_an_unpublished_gateway_reports_nothing_rather_than_guessing(self):
        port = discovery.host_port({"NetworkSettings": {"Ports": {"18789/tcp": None}}})
        self.assertIsNone(port["host_port"])
        self.assertIsNone(port["loopback"])


class LayoutProfileTest(unittest.TestCase):
    """The prefix matches a legacy instance too, so the prefix proves nothing."""

    def test_every_marker_present_is_a_template_instance(self):
        record = template_record()
        self.assertEqual(discovery.layout_profile(record), "template")
        self.assertTrue(all(record["fingerprint"]["markers"].values()))

    def test_recognisably_openclaw_but_shaped_differently_is_legacy(self):
        record = legacy_record()
        self.assertEqual(discovery.layout_profile(record), "legacy")
        self.assertFalse(record["fingerprint"]["markers"]["state_mount"])

    def test_a_missing_marker_downgrades_a_template_to_legacy(self):
        record = template_record()
        record["paths"].pop("auth_secrets")
        self.assertEqual(discovery.layout_profile(record), "legacy")

    def test_an_unrecognisable_neighbour_is_alien_not_invisible(self):
        record = {
            "paths": {},
            "container": {"id": "abc123def456", "image": "docker.io/library/postgres:16",
                          "name": "acme-beta-db-1"},
            "compose": {"config_files": []},
        }
        self.assertEqual(discovery.layout_profile(record), "alien")


class ClassifyStateTest(unittest.TestCase):
    """Cheap evidence only: container state, config presence, log movement."""

    def test_a_healthy_instance_with_a_moving_log_is_ok(self):
        record = template_record()
        record["profile"] = "template"
        self.assertEqual(discovery.classify_state(record), "ok")
        self.assertEqual(record["state_reasons"], [])

    def test_a_silent_log_degrades_a_running_container(self):
        record = template_record()
        record["profile"] = "template"
        record["signals"]["log_age_hours"] = 96.0
        self.assertEqual(discovery.classify_state(record, stale_log_hours=24.0), "degraded")
        self.assertTrue(any("log silent" in r for r in record["state_reasons"]))

    def test_a_missing_config_degrades(self):
        record = template_record()
        record["profile"] = "template"
        record["signals"]["config_present"] = False
        self.assertEqual(discovery.classify_state(record), "degraded")
        self.assertTrue(any("openclaw.json" in r for r in record["state_reasons"]))

    def test_a_stopped_container_is_down(self):
        record = template_record()
        record["profile"] = "template"
        record["container"]["state"] = "exited"
        self.assertEqual(discovery.classify_state(record), "down")

    def test_no_gateway_container_at_all_is_down(self):
        record = template_record()
        record["profile"] = "template"
        record["container"] = {}
        self.assertEqual(discovery.classify_state(record), "down")

    def test_a_restart_loop_is_down_and_says_so(self):
        record = legacy_record()
        record["profile"] = "legacy"
        self.assertEqual(discovery.classify_state(record), "down")
        self.assertTrue(any("restart loop" in r for r in record["state_reasons"]))

    def test_a_restart_count_alone_is_not_a_loop(self):
        record = legacy_record()
        record["profile"] = "legacy"
        record["container"]["health"] = "healthy"
        self.assertNotEqual(discovery.classify_state(record), "down")

    def test_an_alien_profile_short_circuits_every_other_signal(self):
        record = template_record()
        record["profile"] = "alien"
        self.assertEqual(discovery.classify_state(record), "alien")

    def test_an_unmanaged_instance_is_alien_however_healthy(self):
        record = template_record()
        record["profile"] = "template"
        record["managed"] = False
        self.assertEqual(discovery.classify_state(record), "alien")


class LogAgeTest(unittest.TestCase):
    """The zombie detector's raw signal, parsed from a docker timestamp."""

    def test_a_months_old_last_line_reads_as_stale(self):
        with mock.patch.object(discovery, "run", _fake_run(_support.load_text("logs/zombie.log"))):
            zombie = discovery._log_age_hours("cid")
        self.assertIsNotNone(zombie)
        self.assertGreater(zombie, 24.0)

    def test_a_crash_loop_is_noisy_but_not_stale(self):
        with mock.patch.object(discovery, "run", _fake_run(_support.load_text("logs/zombie.log"))):
            zombie = discovery._log_age_hours("cid")
        with mock.patch.object(discovery, "run",
                               _fake_run(_support.load_text("logs/crash-loop.log"))):
            loop = discovery._log_age_hours("cid")
        self.assertIsNotNone(loop)
        self.assertLess(loop, zombie)

    def test_an_unreadable_log_is_unknown_rather_than_zero(self):
        with mock.patch.object(discovery, "run", _fake_run("", rc=1)):
            self.assertIsNone(discovery._log_age_hours("cid"))


class SweepIsolationTest(unittest.TestCase):
    """One broken instance must never blind the operator to the other seven."""

    def setUp(self):
        self.rows = [
            {"project": "acme-alpha", "status": "running(2)",
             "config_files": ["<compose-root>/acme-alpha/docker-compose.yml"]},
            {"project": "acme-beta", "status": "running(2)", "config_files": []},
            {"project": "acme-gamma", "status": "exited(2)", "config_files": []},
        ]
        self.doc = _support.load_json("docker-inspect-gateway.json")[0]

    def _sweep(self):
        def gateway(project, service_hint="gateway", timeout=30):
            if project == "acme-beta":
                raise discovery.DockerError("docker inspect refused for this project")
            if project == "acme-alpha":
                return {"id": self.doc["Id"][:12], "name": "acme-alpha-gateway-1",
                        "image": self.doc["Config"]["Image"], "status": "Up 3 days",
                        "state": "running"}
            return None

        with mock.patch.object(discovery, "docker_available", lambda: (True, None)), \
                mock.patch.object(discovery, "compose_projects", lambda *a, **k: self.rows), \
                mock.patch.object(discovery, "gateway_container", gateway), \
                mock.patch.object(discovery, "inspect_container", lambda *a, **k: self.doc):
            return discovery.discover(prefix=PREFIX, probe=False)

    def test_a_failing_instance_does_not_shorten_the_inventory(self):
        records = self._sweep()
        self.assertEqual([r["name"] for r in records], ["alpha", "beta", "gamma"])

    def test_the_failure_is_recorded_on_its_own_row(self):
        beta = [r for r in self._sweep() if r["name"] == "beta"][0]
        self.assertFalse(beta["ok"])
        self.assertIn("refused", beta["error"])
        self.assertEqual(beta["state"], "down")

    def test_its_neighbours_are_described_normally(self):
        alpha = [r for r in self._sweep() if r["name"] == "alpha"][0]
        self.assertTrue(alpha["ok"])
        self.assertEqual(alpha["profile"], "template")
        self.assertEqual(alpha["paths"]["state_dir"], "<data-root>/alpha/data")


if __name__ == "__main__":
    unittest.main()
