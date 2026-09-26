#!/usr/bin/env node

/**
 * Encrypt a JSON file using AES-256-GCM with PBKDF2 key derivation.
 *
 * Usage: node encrypt.js <input.json> <output.enc> <passphrase>
 * Output: JSON to stdout { success: true, outputPath: "..." }
 */

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const ALGORITHM = 'aes-256-gcm';
const KDF_ITERATIONS = 100000;
const KDF_HASH = 'sha512';
const KEY_LENGTH = 32;
const SALT_LENGTH = 32;
const IV_LENGTH = 16;

function encrypt(inputPath, outputPath, passphrase) {
  // Read input
  if (!fs.existsSync(inputPath)) {
    return { success: false, error: `File not found: ${inputPath}` };
  }
  const plaintext = fs.readFileSync(inputPath, 'utf8');

  // Generate random salt and IV
  const salt = crypto.randomBytes(SALT_LENGTH);
  const iv = crypto.randomBytes(IV_LENGTH);

  // Derive key from passphrase
  const key = crypto.pbkdf2Sync(passphrase, salt, KDF_ITERATIONS, KEY_LENGTH, KDF_HASH);

  // Encrypt
  const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
  let ciphertext = cipher.update(plaintext, 'utf8', 'base64');
  ciphertext += cipher.final('base64');
  const authTag = cipher.getAuthTag();

  // Build encrypted file
  const encryptedData = {
    version: 1,
    algorithm: ALGORITHM,
    kdf: 'pbkdf2',
    kdfIterations: KDF_ITERATIONS,
    kdfHash: KDF_HASH,
    salt: salt.toString('base64'),
    iv: iv.toString('base64'),
    authTag: authTag.toString('base64'),
    ciphertext: ciphertext,
  };

  // Ensure output directory exists
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(outputPath, JSON.stringify(encryptedData, null, 2));
  return { success: true, outputPath: path.resolve(outputPath) };
}

// CLI
const args = process.argv.slice(2);
if (args.length < 3 || args[0] === '--help') {
  console.log(JSON.stringify({
    success: false,
    error: 'Usage: node encrypt.js <input.json> <output.enc> <passphrase>',
  }));
  process.exit(args[0] === '--help' ? 0 : 1);
}

const result = encrypt(args[0], args[1], args[2]);
console.log(JSON.stringify(result));
process.exit(result.success ? 0 : 1);
