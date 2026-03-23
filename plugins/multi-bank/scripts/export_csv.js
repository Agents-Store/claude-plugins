#!/usr/bin/env node

/**
 * Export transactions to CSV format.
 *
 * Usage: node export_csv.js <input.json>
 * Input JSON: { outputPath, dateRange, columns, transactions, includeHeaders, includeSummary }
 * Output: JSON to stdout { success: true, outputPath: "..." }
 */

const fs = require('fs');
const path = require('path');

function escapeCSV(value) {
  if (value === null || value === undefined) return '';
  const str = String(value);
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return '"' + str.replace(/"/g, '""') + '"';
  }
  return str;
}

function formatAmount(amount) {
  if (typeof amount !== 'number') return '';
  return amount.toFixed(2);
}

function exportCSV(inputPath) {
  if (!fs.existsSync(inputPath)) {
    return { success: false, error: `File not found: ${inputPath}` };
  }

  let config;
  try {
    config = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  } catch (err) {
    return { success: false, error: `Invalid JSON input: ${err.message}` };
  }

  const {
    outputPath,
    columns = ['date', 'account', 'merchant', 'category', 'amount', 'balance'],
    transactions = [],
    includeHeaders = true,
    includeSummary = true,
  } = config;

  if (!outputPath) {
    return { success: false, error: 'outputPath is required in input JSON' };
  }

  const lines = [];

  // BOM for Excel UTF-8 compatibility
  const BOM = '\uFEFF';

  // Headers
  if (includeHeaders) {
    lines.push(columns.map(escapeCSV).join(','));
  }

  // Transaction rows
  let totalDebits = 0;
  let totalCredits = 0;

  for (const txn of transactions) {
    const row = columns.map(col => {
      const val = txn[col];
      if (col === 'amount' || col === 'balance') return formatAmount(val);
      if (col === 'tags' && Array.isArray(val)) return val.join('; ');
      return escapeCSV(val);
    });
    lines.push(row.join(','));

    if (typeof txn.amount === 'number') {
      if (txn.amount < 0) totalDebits += txn.amount;
      else totalCredits += txn.amount;
    }
  }

  // Summary
  if (includeSummary && transactions.length > 0) {
    lines.push(''); // blank line
    const pad = columns.length - 2;
    const padCols = new Array(Math.max(0, pad)).fill('').join(',');
    lines.push(`${padCols},SUMMARY,`);
    lines.push(`${padCols},Total Transactions,${transactions.length}`);
    lines.push(`${padCols},Total Debits,${formatAmount(totalDebits)}`);
    lines.push(`${padCols},Total Credits,${formatAmount(totalCredits)}`);
    lines.push(`${padCols},Net Change,${formatAmount(totalDebits + totalCredits)}`);
  }

  // Write file
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const content = BOM + lines.join('\n') + '\n';
  fs.writeFileSync(outputPath, content, 'utf8');

  const stats = fs.statSync(outputPath);
  return {
    success: true,
    outputPath: path.resolve(outputPath),
    size: stats.size,
    transactionCount: transactions.length,
  };
}

// CLI
const args = process.argv.slice(2);
if (args.length < 1 || args[0] === '--help') {
  console.log(JSON.stringify({
    success: false,
    error: 'Usage: node export_csv.js <input.json>',
  }));
  process.exit(args[0] === '--help' ? 0 : 1);
}

const result = exportCSV(args[0]);
console.log(JSON.stringify(result));
process.exit(result.success ? 0 : 1);
