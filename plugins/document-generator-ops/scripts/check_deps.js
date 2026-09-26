#!/usr/bin/env node

/**
 * Dependency Checker & Auto-Installer for Document Generator Plugin
 *
 * Checks all required dependencies (Node modules + system tools)
 * and optionally auto-installs missing ones.
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

function main() {
  const platform = getPlatform();
  const missing = [];
  const installCommands = [];
  const autoInstalled = [];

  // --- Node Modules ---
  const nodeModules = ["docx", "playwright", "pptxgenjs", "pdfkit", "pdf-parse", "pdf-lib"];
  const missingModules = nodeModules.filter((m) => !checkNodeModule(m));

  if (missingModules.length > 0) {
    const cmd = `cd "${pluginDir}" && npm install`;
    missing.push({
      type: "node_modules",
      names: missingModules,
      description: `Missing npm packages: ${missingModules.join(", ")}`,
    });
    installCommands.push({ description: "Install npm dependencies", command: cmd });

    if (autoInstall) {
      if (runInstall(cmd, "npm dependencies")) {
        autoInstalled.push("node_modules");
      }
    }
  }

  // --- Playwright browsers ---
  const hasPlaywright = checkNodeModule("playwright");
  if (hasPlaywright) {
    // Check if Chromium browser is installed for Playwright
    const playwrightBrowserPath = path.join(pluginDir, "node_modules", "playwright-core", ".local-browsers");
    const hasBrowsers = fs.existsSync(playwrightBrowserPath) ||
      process.env.PLAYWRIGHT_BROWSERS_PATH ||
      checkSystemTool("chromium");

    if (!hasBrowsers) {
      const cmd = `cd "${pluginDir}" && npx playwright install chromium`;
      missing.push({
        type: "playwright_browsers",
        name: "chromium",
        description: "Playwright Chromium browser not installed",
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

  // --- PDF Engines for pandoc ---
  const pdfEngines = [
    { name: "weasyprint", label: "WeasyPrint (recommended — best CSS support)" },
    { name: "wkhtmltopdf", label: "wkhtmltopdf (good HTML->PDF)" },
    { name: "pdflatex", label: "pdflatex (LaTeX->PDF)" },
  ];

  const availablePdfEngines = pdfEngines.filter((e) => checkSystemTool(e.name));

  if (availablePdfEngines.length === 0) {
    const cmd =
      platform === "macos"
        ? "pip3 install weasyprint"
        : platform === "linux"
          ? "pip3 install weasyprint"
          : "pip3 install weasyprint";
    missing.push({
      type: "pdf_engine",
      name: "weasyprint",
      description:
        "No PDF engine found for pandoc-based conversions. " +
        "WeasyPrint recommended. Playwright/Puppeteer handles primary PDF generation.",
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

  const ready = nowMissingModules.length === 0;
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

main();
