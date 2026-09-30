#!/usr/bin/env node

// hooks/src/setup-telemetry.mts
import { isDauTelemetryEnabled } from "./telemetry.mjs";
function main() {
  if (!isDauTelemetryEnabled()) {
    process.stdout.write(
      [
        "Telemetry is off. This AGENTS.STORE build of the Vercel plugin sends nothing unless you opt in.",
        "To opt in, set VERCEL_PLUGIN_TELEMETRY=on: a once-per-day DAU phone-home (dau:active_today) and the name of each vercel-plugin skill loaded via the Skill tool (skill:invoked). Skill arguments and non-plugin skill names are never sent.",
        ""
      ].join("\n")
    );
    process.exit(0);
  }
  process.stdout.write(
    [
      "Telemetry is on (VERCEL_PLUGIN_TELEMETRY=on): a once-per-day DAU phone-home (dau:active_today) and the name of each vercel-plugin skill loaded via the Skill tool (skill:invoked). Skill arguments and non-plugin skill names are never sent.",
      "To turn it off, unset VERCEL_PLUGIN_TELEMETRY or set it to off.",
      ""
    ].join("\n")
  );
  process.exit(0);
}
main();
