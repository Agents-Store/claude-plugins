/**
 * Shared utilities for document generation scripts.
 * Margin normalization, preferences checking, and common helpers.
 */

const fs = require("fs");
const path = require("path");

// --- Margin Normalization ---

const TWIPS_PER_INCH = 1440;
const MM_PER_INCH = 25.4;

const PDF_DEFAULTS = { top: "28mm", bottom: "22mm", left: "18mm", right: "18mm" };
const DOCX_DEFAULTS = { top: 1440, bottom: 1440, left: 1080, right: 1080 };

/**
 * Normalize margins to the target format.
 * Handles twips (numbers) ↔ CSS strings ("28mm") conversion.
 *
 * @param {object|undefined} margins - Input margins object
 * @param {"pdf"|"docx"} targetFormat - Target format
 * @returns {object} Normalized margins
 */
function normalizeMargins(margins, targetFormat) {
  const defaults = targetFormat === "pdf" ? PDF_DEFAULTS : DOCX_DEFAULTS;
  if (!margins) return { ...defaults };

  const result = {};
  for (const side of ["top", "bottom", "left", "right"]) {
    const val = margins[side];
    if (val == null) {
      result[side] = defaults[side];
      continue;
    }

    if (targetFormat === "pdf") {
      // Need CSS string output
      if (typeof val === "number") {
        // twips → mm
        result[side] = `${Math.round((val / TWIPS_PER_INCH) * MM_PER_INCH)}mm`;
      } else {
        result[side] = val; // already a CSS string
      }
    } else {
      // Need twips (number) output
      if (typeof val === "string") {
        // CSS string → twips
        const num = parseFloat(val);
        if (val.endsWith("mm")) {
          result[side] = Math.round((num / MM_PER_INCH) * TWIPS_PER_INCH);
        } else if (val.endsWith("in")) {
          result[side] = Math.round(num * TWIPS_PER_INCH);
        } else if (val.endsWith("cm")) {
          result[side] = Math.round(((num * 10) / MM_PER_INCH) * TWIPS_PER_INCH);
        } else if (val.endsWith("px")) {
          // 1px ≈ 0.75pt, 1pt = 20 twips
          result[side] = Math.round(num * 0.75 * 20);
        } else {
          // Assume mm if no unit
          result[side] = Math.round((num / MM_PER_INCH) * TWIPS_PER_INCH);
        }
      } else {
        result[side] = val; // already a number (twips)
      }
    }
  }
  return result;
}

// --- Preferences Check ---

const PREFS_PATH = path.join(
  process.env.HOME || process.env.USERPROFILE || "",
  ".document-generator",
  "preferences.json"
);

/**
 * Check if user preferences exist and are valid JSON.
 * Returns the parsed preferences or null if missing/invalid.
 */
function loadPreferences() {
  try {
    const raw = fs.readFileSync(PREFS_PATH, "utf-8");
    return JSON.parse(raw);
  } catch (_) {
    return null;
  }
}

/**
 * Check if preferences exist. Does NOT block generation.
 *
 * If preferences.json is missing, generation continues with built-in defaults.
 * Returns { exists: boolean, warning?: string } so the agent can decide
 * whether to run onboarding after the document is delivered.
 *
 * @param {object} input - Parsed JSON input from the agent
 * @returns {{ exists: boolean, warning?: string }}
 */
function requirePreferences(input) {
  if (input.skipOnboardingCheck) return { exists: true };
  const prefs = loadPreferences();
  if (!prefs) {
    return {
      exists: false,
      warning:
        "ONBOARDING_NOT_DONE: User preferences not found at ~/.document-generator/preferences.json. " +
        "Using built-in defaults. Run /setup to configure style, company info, and logo.",
    };
  }
  return { exists: true };
}

/**
 * Auto-merge user preferences into the input's template.styling.
 *
 * Priority (lowest → highest):
 *   1. Built-in defaults (hardcoded in getDefaults)
 *   2. User preferences from ~/.document-generator/preferences.json
 *   3. Explicit template.styling values passed by the agent
 *
 * Call this after requirePreferences() in each generator script.
 * Mutates input.template.styling in place.
 *
 * Also injects company info (logoBase64, company name) if not already present.
 *
 * @param {object} input - Parsed JSON input (has .data, .template)
 * @returns {object} The merged preferences (or null if not found)
 */
function mergePreferences(input) {
  const prefs = loadPreferences();
  if (!prefs) return null;

  // Ensure template and styling exist
  if (!input.template) input.template = {};
  if (!input.template.styling) input.template.styling = {};

  const styling = input.template.styling;
  const prefsStyle = prefs.style || {};

  // Merge style: preferences fill in any missing values, explicit input wins
  const styleFields = [
    ["primaryColor", "primaryColor"],
    ["accentColor", "accentColor"],
    ["textColor", "textColor"],
    ["mutedColor", "mutedColor"],
    ["borderColor", "borderColor"],
    ["backgroundColor", "backgroundColor"],
    ["fontHeading", "fontHeading"],
    ["fontBody", "fontBody"],
    ["lineSpacing", "lineSpacing"],
  ];

  for (const [inputKey, prefsKey] of styleFields) {
    if (!styling[inputKey] && prefsStyle[prefsKey]) {
      styling[inputKey] = prefsStyle[prefsKey];
    }
  }

  // Merge defaults (language, currency, paper size, date format)
  const prefsDefaults = prefs.defaults || {};

  if (!input.template.currencySymbol && !input.data?.currencySymbol && prefsDefaults.currencySymbol) {
    if (!input.template) input.template = {};
    input.template.currencySymbol = prefsDefaults.currencySymbol;
  }

  if (!styling.pageSize && prefsDefaults.paperSize) {
    styling.pageSize = prefsDefaults.paperSize;
  }

  if (!input.data?.language && prefsDefaults.language) {
    if (!input.data) input.data = {};
    input.data.language = prefsDefaults.language;
  }

  // Inject company info from the default profile if not already provided
  const companies = prefs.companies || {};
  const defaultCompanyKey = Object.keys(companies)[0]; // first company is default
  const defaultCompany = defaultCompanyKey ? companies[defaultCompanyKey] : null;

  if (defaultCompany && input.data) {
    // Company info for invoices/proposals/contracts
    if (!input.data.companyInfo) input.data.companyInfo = {};
    const ci = input.data.companyInfo;

    if (!ci.name && defaultCompany.name) ci.name = defaultCompany.name;
    if (!ci.address && defaultCompany.address) ci.address = defaultCompany.address;
    if (!ci.phone && defaultCompany.phone) ci.phone = defaultCompany.phone;
    if (!ci.email && defaultCompany.email) ci.email = defaultCompany.email;
    if (!ci.website && defaultCompany.website) ci.website = defaultCompany.website;
    if (!ci.reg && defaultCompany.reg) ci.reg = defaultCompany.reg;

    // Logo: try to load base64 from stored file
    if (!ci.logoBase64 && !input.data.logoBase64 && defaultCompany.logoFile) {
      const logoB64Path = path.join(
        process.env.HOME || process.env.USERPROFILE || "",
        ".document-generator",
        "logos",
        `${defaultCompanyKey}-logo.b64`
      );
      try {
        const b64 = fs.readFileSync(logoB64Path, "utf-8").trim();
        if (b64) ci.logoBase64 = b64;
      } catch (_) {}
    }

    // Also set companyName at top level if missing (used by proposals/reports cover)
    if (!input.data.companyName && ci.name) {
      input.data.companyName = ci.name;
    }
  }

  return prefs;
}

module.exports = {
  normalizeMargins,
  loadPreferences,
  requirePreferences,
  mergePreferences,
  PREFS_PATH,
  PDF_DEFAULTS,
  DOCX_DEFAULTS,
};
