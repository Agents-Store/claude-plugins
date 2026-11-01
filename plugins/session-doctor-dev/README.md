# session-doctor-dev

Read-only audit of a Claude Code session: where it runs, what context it loaded, which model
and effort it used, the skills it invoked, every HTTP request with its status code, and the
status of each API token seen in the session — with concrete fixes.

## Usage

```
/session-doctor-dev:audit [full] [session-id]
```

Without arguments it audits the current session and prints a short report. `full` adds the
detail sections. A `session-id` audits another session of the same project.

## Guarantees

- Read-only: it never changes settings, transcripts or files in your project.
- Never prints a secret: tokens are redacted before anything is shown.
- Makes no network requests.

## Prerequisites

- `python3` 3.8 or newer. No third-party packages.
