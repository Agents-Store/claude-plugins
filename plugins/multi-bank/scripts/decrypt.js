#!/usr/bin/env node

/**
 * Decrypt an AES-256-GCM encrypted file produced by encrypt.js.
 *
 * Usage: node decrypt.js <input.enc> <output.json> <passphrase>
 * Output: JSON to stdout { success: true, outputPath: "..." }
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

function decrypt(inputPath, outputPath, passphrase) {
  // Read encrypted file
  if (!fs.existsSync(inputPath)) {
    return { success: false, error: `File not found: ${inputPath}` };
  }

  let encryptedData;
  try {
    encryptedData = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
  } catch (err) {
    return { success: false, error: `Invalid encrypted file format: ${err.message}` };
  }

  // Validate version
  if (encryptedData.version !== 1) {
    return { success: false, error: `Unsupported encryption version: ${encryptedData.version}` };
  }

  // Extract components
  const salt = Buffer.from(encryptedData.salt, 'base64');
  const iv = Buffer.from(encryptedData.iv, 'base64');
  const authTag = Buffer.from(encryptedData.authTag, 'base64');
  const ciphertext = encryptedData.ciphertext;

  // Derive key from passphrase using same parameters
  const key = crypto.pbkdf2Sync(
    passphrase,
    salt,
    encryptedData.kdfIterations,
    32, // key length
    encryptedData.kdfHash
  );

  // Decrypt
  try {
    const decipher = crypto.createDecipheriv(encryptedData.algorithm, key, iv);
    decipher.setAuthTag(authTag);
    let plaintext = decipher.update(ciphertext, 'base64', 'utf8');
    plaintext += decipher.final('utf8');

    // Ensure output directory exists
    const outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    fs.writeFileSync(outputPath, plaintext);
    return { success: true, outputPath: path.resolve(outputPath) };
  } catch (err) {
    return { success: false, error: 'Decryption failed — invalid passphrase or corrupted data' };
  }
}

// CLI
const args = process.argv.slice(2);
if (args.length < 3 || args[0] === '--help') {
  console.log(JSON.stringify({
    success: false,
    error: 'Usage: node decrypt.js <input.enc> <output.json> <passphrase>',
  }));
  process.exit(args[0] === '--help' ? 0 : 1);
}

const result = decrypt(args[0], args[1], args[2]);
console.log(JSON.stringify(result));
process.exit(result.success ? 0 : 1);
