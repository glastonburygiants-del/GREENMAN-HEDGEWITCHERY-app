#!/usr/bin/env node
'use strict';

const fs = require('fs');
const vm = require('vm');

if (process.argv.length !== 3) {
  console.error('usage: verify_inline_scripts.js FILE.html');
  process.exit(2);
}

const file = process.argv[2];
const html = fs.readFileSync(file, 'utf8');
const scriptPattern = /<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi;
let match;
let found = 0;
let checked = 0;
let failed = 0;
let pageStoreFound = false;

while ((match = scriptPattern.exec(html)) !== null) {
  found += 1;
  const attrs = match[1] || '';
  const source = match[2];

  if (/\bsrc\s*=/i.test(attrs)) continue;
  const type = attrs.match(/\btype\s*=\s*["']([^"']+)["']/i);
  if (type && !/^(?:text|application)\/javascript$/i.test(type[1])) continue;

  checked += 1;
  if (source.includes('const PAGES = ')) pageStoreFound = true;
  try {
    new vm.Script(source, {filename: `inline-script-${found}.js`});
  } catch (error) {
    failed += 1;
    const location = String(error.stack || '').match(/inline-script-\d+\.js:\d+/);
    console.error(
      `Invalid inline script ${found} at HTML byte ${match.index}` +
      `${location ? ` (${location[0]})` : ''}: ${error.message}`
    );
  }
}

if (!found) {
  console.error('No inline scripts found');
  process.exit(1);
}
if (!pageStoreFound) {
  console.error('The executable embedded PAGES store was not found');
  process.exit(1);
}
if (failed) {
  console.error(`${failed} of ${checked} executable inline scripts failed syntax parsing`);
  process.exit(1);
}

console.log(`Inline script check passed: ${checked} executable scripts parsed cleanly`);
