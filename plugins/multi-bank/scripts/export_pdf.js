#!/usr/bin/env node

/**
 * Export financial report as PDF.
 *
 * Usage: node export_pdf.js <input.json>
 * Input JSON: { outputPath, title, dateRange, accounts, categoryBreakdown, budgetStatus, recentTransactions, totals }
 * Output: JSON to stdout { success: true, outputPath: "..." }
 * Requires: pdfkit (npm install pdfkit)
 */

const fs = require('fs');
const path = require('path');

function exportPDF(inputPath) {
  if (!fs.existsSync(inputPath)) {
    return { success: false, error: `File not found: ${inputPath}` };
  }

  let config;
  try {
    config = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  } catch (err) {
    return { success: false, error: `Invalid JSON input: ${err.message}` };
  }

  const { outputPath, title, dateRange, accounts, categoryBreakdown, budgetStatus, recentTransactions, totals, currencySymbol = '₴' } = config;

  if (!outputPath) {
    return { success: false, error: 'outputPath is required in input JSON' };
  }

  let PDFDocument;
  try {
    PDFDocument = require('pdfkit');
  } catch (err) {
    return { success: false, error: 'pdfkit not installed. Run: npm install pdfkit' };
  }

  // Ensure output directory exists
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  return new Promise((resolve) => {
    const doc = new PDFDocument({ size: 'A4', margin: 50 });
    const stream = fs.createWriteStream(outputPath);
    doc.pipe(stream);

    // Title
    doc.fontSize(20).font('Helvetica-Bold').text(title || 'Financial Report', { align: 'center' });
    if (dateRange) {
      doc.fontSize(12).font('Helvetica').text(`${dateRange.start} — ${dateRange.end}`, { align: 'center' });
    }
    doc.moveDown(1.5);

    // Account Summary
    if (accounts && accounts.length > 0) {
      doc.fontSize(14).font('Helvetica-Bold').text('Account Summary');
      doc.moveDown(0.5);
      doc.fontSize(10).font('Helvetica');

      for (const acct of accounts) {
        const balance = typeof acct.currentBalance === 'number' ? `${currencySymbol}${acct.currentBalance.toLocaleString('uk-UA', { minimumFractionDigits: 2 })}` : 'N/A';
        doc.text(`${acct.institution} — ${acct.name}`, 50, doc.y, { continued: true, width: 350 });
        doc.text(balance, { align: 'right' });
      }

      if (totals?.totalBalance) {
        doc.moveDown(0.3);
        doc.font('Helvetica-Bold');
        doc.text('Total', 50, doc.y, { continued: true, width: 350 });
        doc.text(`${currencySymbol}${totals.totalBalance.toLocaleString('uk-UA', { minimumFractionDigits: 2 })}`, { align: 'right' });
        doc.font('Helvetica');
      }
      doc.moveDown(1);
    }

    // Category Breakdown
    if (categoryBreakdown && categoryBreakdown.length > 0) {
      doc.fontSize(14).font('Helvetica-Bold').text('Spending by Category');
      doc.moveDown(0.5);
      doc.fontSize(10).font('Helvetica');

      for (const cat of categoryBreakdown) {
        const barWidth = Math.min(200, (cat.percent / 100) * 200);
        const y = doc.y;

        doc.text(cat.category, 50, y, { width: 100 });
        doc.rect(155, y + 2, barWidth, 10).fill('#4A90D9');
        doc.fill('#000000');
        doc.text(`${currencySymbol}${cat.amount.toFixed(2)} (${cat.percent}%)`, 365, y, { width: 150 });
        doc.moveDown(0.3);
      }
      doc.moveDown(1);
    }

    // Budget Status
    if (budgetStatus && budgetStatus.length > 0) {
      doc.fontSize(14).font('Helvetica-Bold').text('Budget Status');
      doc.moveDown(0.5);
      doc.fontSize(10).font('Helvetica');

      for (const b of budgetStatus) {
        const pct = b.percent || 0;
        const color = pct >= 100 ? '#E74C3C' : pct >= 75 ? '#F39C12' : '#27AE60';
        const barWidth = Math.min(200, (pct / 100) * 200);
        const y = doc.y;

        doc.text(b.category, 50, y, { width: 100 });
        doc.rect(155, y + 2, 200, 10).fill('#E0E0E0');
        doc.rect(155, y + 2, barWidth, 10).fill(color);
        doc.fill('#000000');
        doc.text(`${pct.toFixed(0)}% (${currencySymbol}${b.spent.toFixed(2)} / ${currencySymbol}${b.budget.toFixed(2)})`, 365, y, { width: 180 });
        doc.moveDown(0.3);
      }
      doc.moveDown(1);
    }

    // Recent Transactions
    if (recentTransactions && recentTransactions.length > 0) {
      doc.fontSize(14).font('Helvetica-Bold').text('Recent Transactions');
      doc.moveDown(0.5);
      doc.fontSize(8).font('Helvetica');

      // Header
      const headerY = doc.y;
      doc.font('Helvetica-Bold');
      doc.text('Date', 50, headerY, { width: 70 });
      doc.text('Account', 120, headerY, { width: 100 });
      doc.text('Merchant', 220, headerY, { width: 120 });
      doc.text('Category', 340, headerY, { width: 80 });
      doc.text('Amount', 420, headerY, { width: 80 });
      doc.font('Helvetica');
      doc.moveDown(0.5);

      for (const txn of recentTransactions.slice(0, 20)) {
        const y = doc.y;
        if (y > 750) break; // Don't overflow page
        doc.text(txn.date || '', 50, y, { width: 70 });
        doc.text(txn.account || '', 120, y, { width: 100 });
        doc.text(txn.merchant || '', 220, y, { width: 120 });
        doc.text(txn.category || '', 340, y, { width: 80 });
        const amt = typeof txn.amount === 'number' ? `${currencySymbol}${txn.amount.toFixed(2)}` : '';
        doc.text(amt, 420, y, { width: 80 });
        doc.moveDown(0.2);
      }
    }

    // Totals footer
    if (totals) {
      doc.moveDown(1);
      doc.fontSize(10).font('Helvetica-Bold');
      if (totals.netChange !== undefined) {
        const sign = totals.netChange >= 0 ? '+' : '';
        doc.text(`Net Change: ${sign}${currencySymbol}${totals.netChange.toFixed(2)}`, { align: 'right' });
      }
    }

    doc.end();

    stream.on('finish', () => {
      const stats = fs.statSync(outputPath);
      resolve({
        success: true,
        outputPath: path.resolve(outputPath),
        size: stats.size,
      });
    });

    stream.on('error', (err) => {
      resolve({ success: false, error: `Write error: ${err.message}` });
    });
  });
}

// CLI
const args = process.argv.slice(2);
if (args.length < 1 || args[0] === '--help') {
  console.log(JSON.stringify({
    success: false,
    error: 'Usage: node export_pdf.js <input.json>',
  }));
  process.exit(args[0] === '--help' ? 0 : 1);
}

exportPDF(args[0]).then(result => {
  console.log(JSON.stringify(result));
  process.exit(result.success ? 0 : 1);
});
