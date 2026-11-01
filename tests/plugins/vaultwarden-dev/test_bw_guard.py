"""Black-box tests for plugins/vaultwarden-dev/scripts/bw_guard.py."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

GUARD = Path(__file__).resolve().parents[3] / "plugins" / "vaultwarden-dev" / "scripts" / "bw_guard.py"


def run(payload):
    data = payload if isinstance(payload, str) else json.dumps(payload)
    proc = subprocess.run([sys.executable, str(GUARD)], input=data, capture_output=True, text=True, timeout=10)
    return proc.returncode, proc.stdout


def decision(command, tool="Bash"):
    code, out = run({"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": {"command": command}})
    if code != 0:
        raise AssertionError("guard exited %d" % code)
    if not out.strip():
        return None
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"]


class AsksBeforePrinting(unittest.TestCase):
    CASES = [
        "bw list items",
        "bw list items --search github | jq .",
        "bw --session \"$BW_SESSION\" list items --folderid null",
        "bw get item <item-id>",
        "bw get password github.com",
        "bw get totp <item-id>",
        "bw get notes <item-id>",
        "bw get attachment key.pem --itemid <item-id>",
        "bw unlock",
        "bw unlock --raw",
        "bw login user@example.com",
        "rbw get github",
        "cd /srv && bw get password x",
        "curl -s \"$BW_SERVE/object/password/<item-id>\"",
        "curl -s \"$BW_SERVE/list/object/items?search=db\" | jq .",
        "echo $BW_SESSION",
        "printf '%s' \"${BW_PASSWORD}\"",
        "printenv BW_CLIENTSECRET",
        "echo \"$VW_ADMIN_TOKEN\"",
        "echo $BW_SESSION | tee session.txt",
        "/usr/local/bin/bw get password <item-id>",
        "bw list items 2>/dev/null",
        "bw get item <item-id> | tee item.json",
    ]

    def test_asks(self):
        for cmd in self.CASES:
            with self.subTest(cmd=cmd):
                self.assertEqual(decision(cmd), "ask")


class AsksEvenWhenCaptured(unittest.TestCase):
    CASES = [
        "bw export --format json --output vault.json",
        "bw export",
        "X=\"$(bw export --format csv)\"",
        "bw serve --disable-origin-protection",
        "bw serve --hostname all --port 8087",
        "bw serve --hostname 0.0.0.0",
        "echo \"$(bw get password <item-id>)\"",
        "printf '%s\\n' \"$(bw get item <item-id>)\"",
        "cat <<<\"$(bw get password <item-id>)\"",
    ]

    def test_asks(self):
        for cmd in self.CASES:
            with self.subTest(cmd=cmd):
                self.assertEqual(decision(cmd), "ask")


class StaysSilent(unittest.TestCase):
    CASES = [
        "git status -sb",
        "export DB_PASS=\"$(bw get password <item-id>)\"",
        "export BW_SESSION=\"$(bw unlock --passwordenv BW_PASSWORD --raw)\"",
        "export BW_SESSION=`bw unlock --passwordfile pw.txt --raw`",
        "curl -u \"deploy:$(bw get password <item-id>)\" https://example.com/hook",
        "while read -r k v; do export \"$k=$v\"; done < <(bw get item <item-id> | jq -r '.fields[] | [.name, .value] | @tsv')",
        "bw login --apikey",
        "bw login --check",
        "bw logout",
        "bw lock",
        "bw sync",
        "bw status | jq '{serverUrl, status}'",
        "bw list folders",
        "bw list org-members --organizationid <org-uuid> | jq '.[] | {email, status}'",
        "bw get username <item-id>",
        "bw get attachment key.pem --itemid <item-id> --output ./key.pem",
        "bw export --format encrypted_json --password \"$EXPORT_PW\" --output vault.enc.json",
        "bw serve --port 8087",
        "bw serve --hostname localhost --port 8087",
        "bw generate -ulns --length 32",
        "rbw list",
        "echo $BW_SERVE",
        "kubectl get pods",
        "printf '%s' \"$VW_ADMIN_TOKEN\" | curl -sS -c \"$JAR\" --data-urlencode 'token@-' https://vault.example.com/admin",
        "bw get password <item-id> > secret.txt",
        "bw get password <item-id> | pbcopy",
        "bw get item <item-id> | jq -r .login.password > pw.txt",
        "bw list items --search db 2>/dev/null > items.json",
        "echo \"$(bw get username <item-id>)\"",
    ]

    def test_silent(self):
        for cmd in self.CASES:
            with self.subTest(cmd=cmd):
                self.assertIsNone(decision(cmd))


class FailsOpen(unittest.TestCase):
    def test_other_tool(self):
        self.assertIsNone(decision("bw list items", tool="Read"))

    def test_garbage_stdin(self):
        self.assertEqual(run("not json"), (0, ""))

    def test_empty_stdin(self):
        self.assertEqual(run(""), (0, ""))

    def test_missing_command(self):
        self.assertEqual(run({"tool_name": "Bash", "tool_input": {}}), (0, ""))


if __name__ == "__main__":
    unittest.main()
