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
let found = 0;
let checked = 0;
let failed = 0;
let pageStoreFound = false;

function checkScripts(documentText, scope) {
  scriptPattern.lastIndex = 0;
  let match;
  let scopeIndex = 0;
  while ((match = scriptPattern.exec(documentText)) !== null) {
    found += 1;
    scopeIndex += 1;
    const attrs = match[1] || '';
    let source = match[2];

    // A few legacy rooms wrap executable JavaScript in an HTML CDATA marker.
    // Browsers ignore that wrapper; remove it before asking V8 to parse the JS.
    const trimmedSource = source.trim();
    if (trimmedSource.startsWith('<![CDATA[') && trimmedSource.endsWith(']]>')) {
      source = trimmedSource.slice(9, -3);
    }

    if (/\bsrc\s*=/i.test(attrs)) continue;
    const type = attrs.match(/\btype\s*=\s*["']([^"']+)["']/i);
    if (type && !/^(?:text|application)\/javascript$/i.test(type[1])) continue;

    checked += 1;
    if (source.includes('const PAGES = ')) pageStoreFound = true;
    const safeScope = scope.replace(/[^a-z0-9_-]+/gi, '-');
    const scriptName = `${safeScope}-script-${scopeIndex}.js`;
    try {
      new vm.Script(source, {filename: scriptName});
    } catch (error) {
      failed += 1;
      const escapedName = scriptName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const location = String(error.stack || '').match(new RegExp(`${escapedName}:\\d+`));
      console.error(
        `Invalid ${scope} script ${scopeIndex} at byte ${match.index}` +
        `${location ? ` (${location[0]})` : ''}: ${error.message}`
      );
    }
  }
}

function readJsonValue(text, start) {
  while (/\s/.test(text[start] || '')) start += 1;
  const first = text[start];
  if (!'{["-0123456789tfn'.includes(first || '')) {
    throw new Error(`No JSON value at byte ${start}`);
  }
  let inString = false;
  let escaped = false;
  let depth = 0;
  for (let i = start; i < text.length; i += 1) {
    const char = text[i];
    if (inString) {
      if (escaped) escaped = false;
      else if (char === '\\') escaped = true;
      else if (char === '"') {
        inString = false;
        if (first === '"' && depth === 0) return {value: JSON.parse(text.slice(start, i + 1)), end: i + 1};
      }
      continue;
    }
    if (char === '"') inString = true;
    else if (char === '{' || char === '[') depth += 1;
    else if (char === '}' || char === ']') {
      depth -= 1;
      if (depth === 0) return {value: JSON.parse(text.slice(start, i + 1)), end: i + 1};
    } else if (depth === 0 && /[;,\s]/.test(char) && i > start) {
      return {value: JSON.parse(text.slice(start, i)), end: i};
    }
  }
  throw new Error(`Unterminated JSON value at byte ${start}`);
}

checkScripts(html, 'outer app');

// The shell stores whole HTML rooms as JSON strings. Their JavaScript must be
// parsed too: a valid outer store can still contain a broken Scribe or BoS room.
const pagesMarker = 'const PAGES = ';
const pagesAt = html.indexOf(pagesMarker);
if (pagesAt >= 0) {
  const parsed = readJsonValue(html, pagesAt + pagesMarker.length);
  const pages = parsed.value;
  const assignmentPattern = /\bPAGES\.([A-Za-z_$][\w$]*)\s*=\s*/g;
  let assignment;
  while ((assignment = assignmentPattern.exec(html)) !== null) {
    try {
      const assigned = readJsonValue(html, assignmentPattern.lastIndex);
      if (typeof assigned.value === 'string') pages[assignment[1]] = assigned.value;
      assignmentPattern.lastIndex = assigned.end;
    } catch (_) {
      // Ignore non-JSON runtime assignments; embedded page assignments are JSON.
    }
  }
  for (const [pageName, pageHtml] of Object.entries(pages)) {
    if (typeof pageHtml === 'string' && /<script\b/i.test(pageHtml)) {
      checkScripts(pageHtml, `embedded page ${pageName}`);
    }
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
