#!/usr/bin/env node

/**
 * Dependency Checker & Auto-Installer for Document Generator Plugin
 *
 * Checks all required dependencies (Node modules + system tools)
 * and optionally auto-installs missing ones.
 *
 * npm packages: for a plugin installed from a marketplace Claude Code installs
 * them itself from package-lock.json. They are missing only when the plugin is
 * loaded in place (--plugin-dir, local-directory marketplace) — then `npm ci`
 * in the plugin directory fixes it. The Playwright browser is never installed
 * by npm; it lives in the global Playwright cache and survives plugin updates.
 *
 * Usage:
 *   node check_deps.js              # Check only, report missing
 *   node check_deps.js --install    # Check and auto-install missing deps
 *
 * Output: JSON { ready, missing[], installed{}, installCommands[] }
 */

const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const pluginDir = path.resolve(__dirname, "..");
const autoInstall = process.argv.includes("--install");

function checkNodeModule(name) {
  try {
    require.resolve(name, { paths: [path.join(pluginDir, "node_modules")] });
    return true;
  } catch (_) {
    return false;
  }
}

/**
 * True when Playwright can start its Chromium. Cheap check first (the binary
 * Playwright expects in its browser cache, honouring PLAYWRIGHT_BROWSERS_PATH),
 * then a real headless launch — which also covers a headless-shell-only install.
 */
async function checkPlaywrightChromium() {
  let chromium;
  try {
    ({ chromium } = require(require.resolve("playwright", { paths: [path.join(pluginDir, "node_modules")] })));
  } catch (_) {
    return false;
  }
  try {
    if (fs.existsSync(chromium.executablePath())) return true;
  } catch (_) {
    // fall through to the launch probe
  }
  try {
    const browser = await chromium.launch({ args: ["--no-sandbox", "--disable-setuid-sandbox"], timeout: 20000 });
    await browser.close();
    return true;
  } catch (_) {
    return false;
  }
}

function checkSystemTool(name) {
  try {
    execSync(`which ${name} 2>/dev/null`, { encoding: "utf-8" });
    return true;
  } catch (_) {
    return false;
  }
}

function getPlatform() {
  const p = process.platform;
  if (p === "darwin") return "macos";
  if (p === "linux") return "linux";
  if (p === "win32") return "windows";
  return p;
}

function runInstall(cmd, description) {
  try {
    console.error(`[check_deps] Installing: ${description}...`);
    execSync(cmd, { encoding: "utf-8", stdio: ["pipe", "pipe", "pipe"], timeout: 300000 });
    console.error(`[check_deps] Installed: ${description}`);
    return true;
  } catch (err) {
    console.error(`[check_deps] Failed to install ${description}: ${err.message}`);
    return false;
  }
}

async function main() {
  const platform = getPlatform();
  const missing = [];
  const installCommands = [];
  const autoInstalled = [];

  // --- Node.js version (pdfkit >= 0.19 and Playwright need Node 20+; see "engines" in package.json) ---
  const nodeMajor = Number(process.versions.node.split(".")[0]);
  const nodeTooOld = nodeMajor < 20;
  if (nodeTooOld) {
    missing.push({
      type: "node_version",
      description: `Node.js ${process.versions.node} is too old: pdfkit and Playwright need Node.js 20 or newer`,
      required: true,
    });
  }

  // --- Node Modules ---
  const nodeModules = ["docx", "playwright", "pptxgenjs", "pdfkit", "pdf-parse"];
  const missingModules = nodeModules.filter((m) => !checkNodeModule(m));

  if (missingModules.length > 0) {
    // Install exactly what package-lock.json pins (what Claude Code does on a marketplace install).
    const hasLock = fs.existsSync(path.join(pluginDir, "package-lock.json"));
    const cmd = `cd "${pluginDir}" && ${hasLock ? "npm ci" : "npm install"}`;
    missing.push({
      type: "node_modules",
      names: missingModules,
      description:
        `Missing npm packages: ${missingModules.join(", ")}. ` +
        "Claude Code installs them on a marketplace install; they are missing when the plugin is loaded in place (--plugin-dir)",
    });
    installCommands.push({ description: "Install npm dependencies", command: cmd });

    if (autoInstall) {
      if (runInstall(cmd, "npm dependencies")) {
        autoInstalled.push("node_modules");
      }
    }
  }

  // --- Playwright browsers ---
  // (not probed on Node < 20: requiring Playwright there prints an error and exits)
  if (!nodeTooOld && checkNodeModule("playwright")) {
    const hasBrowsers = await checkPlaywrightChromium();

    if (!hasBrowsers) {
      const cmd = `cd "${pluginDir}" && npx playwright install chromium`;
      missing.push({
        type: "playwright_browsers",
        name: "chromium",
        description:
          "Playwright Chromium browser not installed (a browserless PDF is possible with engine: pdfkit). " +
          "The browser goes to the global Playwright cache and survives plugin updates",
      });
      installCommands.push({ description: "Install Playwright Chromium", command: cmd });

      if (autoInstall) {
        if (runInstall(cmd, "Playwright Chromium browser")) {
          autoInstalled.push("playwright_chromium");
        }
      }
    }
  }

  // --- Pandoc (for format conversion + DOCX pandoc engine) ---
  if (!checkSystemTool("pandoc")) {
    const cmd =
      platform === "macos"
        ? "brew install pandoc"
        : platform === "linux"
          ? "sudo apt install -y pandoc"
          : "choco install pandoc";
    missing.push({
      type: "system_tool",
      name: "pandoc",
      description: "Document format converter (needed for DOCX pandoc engine and format conversion)",
      required: false,
      usedBy: "convert.sh, generate_docx.js (pandoc engine), docx_to_pdf.js",
    });
    installCommands.push({ description: "Install pandoc", command: cmd });

    if (autoInstall && platform === "macos") {
      runInstall(cmd, "pandoc") && autoInstalled.push("pandoc");
    }
  }

  // --- PDF Engines for pandoc (convert.sh) ---
  // wkhtmltopdf is deprecated in the pandoc manual and is no longer used.
  const pdfEngines = [
    { name: "weasyprint", label: "WeasyPrint (recommended — best CSS support)" },
    { name: "typst", label: "Typst (lightweight, no LaTeX needed)" },
    { name: "pdflatex", label: "pdflatex (LaTeX; needs extra setup for Cyrillic)" },
  ];

  const availablePdfEngines = pdfEngines.filter((e) => checkSystemTool(e.name));

  if (availablePdfEngines.length === 0) {
    // pip can refuse on distributions with PEP 668 — prefer the system package manager.
    const cmd =
      platform === "macos"
        ? "brew install weasyprint"
        : platform === "linux"
          ? "sudo apt install -y weasyprint"
          : "pip install weasyprint";
    missing.push({
      type: "pdf_engine",
      name: "weasyprint",
      description:
        "No PDF engine found for pandoc-based conversions (convert.sh). " +
        "WeasyPrint recommended. Playwright handles primary PDF generation and does not need one.",
      required: false,
      alternatives: pdfEngines.map((e) => e.label),
    });
    installCommands.push({
      description: "Install WeasyPrint (PDF engine for pandoc conversions)",
      command: cmd,
    });
  }

  // --- Summary ---
  // Re-check after auto-install
  const nowMissingModules = autoInstall
    ? nodeModules.filter((m) => !checkNodeModule(m))
    : missingModules;

  const ready = nowMissingModules.length === 0 && !nodeTooOld;
  const result = {
    ready,
    platform,
    missing: autoInstall ? missing.filter((m) => !autoInstalled.includes(m.type)) : missing,
    installCommands: autoInstall ? installCommands.filter((c) => !autoInstalled.some((a) => c.description.toLowerCase().includes(a.replace("_", " ")))) : installCommands,
    installed: {
      nodeModules: nodeModules.filter((m) => checkNodeModule(m)),
      pandoc: checkSystemTool("pandoc"),
      pdfEngines: availablePdfEngines.map((e) => e.name),
      playwright: checkNodeModule("playwright"),
      puppeteer: checkNodeModule("puppeteer"),
    },
    autoInstalled: autoInstall ? autoInstalled : undefined,
  };

  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error(`[check_deps] ${err.message}`);
  process.exit(1);
});
