#!/usr/bin/env node
"use strict";

const crypto = require("crypto");
const fs = require("fs");

if (process.argv.length !== 4) {
  throw new Error("usage: verify_bos_v29.js BASE.html V29.html");
}

function readJsonString(text, start) {
  if (text[start] !== '"') throw new Error("Expected a JSON string");
  let escaped = false;
  for (let index = start + 1; index < text.length; index += 1) {
    const character = text[index];
    if (escaped) {
      escaped = false;
    } else if (character === "\\") {
      escaped = true;
    } else if (character === '"') {
      const end = index + 1;
      return { value: JSON.parse(text.slice(start, end)), end };
    }
  }
  throw new Error("Unclosed JSON string");
}

function pages(text) {
  const result = {};
  const assignment = /PAGES\.([A-Za-z0-9_]+)\s*=\s*/g;
  let match;
  while ((match = assignment.exec(text)) !== null) {
    const parsed = readJsonString(text, match.index + match[0].length);
    result[match[1]] = parsed.value;
    assignment.lastIndex = parsed.end;
  }
  return result;
}

function digest(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

const base = pages(fs.readFileSync(process.argv[2], "utf8"));
const output = pages(fs.readFileSync(process.argv[3], "utf8"));
const keys = [...new Set([...Object.keys(base), ...Object.keys(output)])].sort();
const changed = keys.filter((key) => digest(base[key] || "") !== digest(output[key] || ""));
if (changed.length !== 1 || changed[0] !== "scribe") {
  throw new Error(`Only PAGES.scribe may change; changed: ${changed.join(", ")}`);
}

const scribe = output.scribe;
const scripts = [...scribe.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\\?\/script>/gi)];
if (scripts.length !== 2) throw new Error(`Expected 2 Scribe scripts, found ${scripts.length}`);
scripts.forEach((match, index) => {
  try {
    // Parse without running the embedded application.
    Function(match[1]);
  } catch (error) {
    throw new Error(`Scribe script ${index + 1} is invalid: ${error.message}`);
  }
});

[
  "gmInkBosHand",
  "gmScribeConvertBtn",
  "gmScribeCancelJob",
  "gmBosJobModal",
  "gmBosJobCancel",
  "gmBosChapterContentsBtn",
].forEach((id) => {
  const count = (scribe.match(new RegExp(`id=\\"${id}\\"`, "g")) || []).length;
  if (count !== 1) throw new Error(`${id} count is ${count}, expected 1`);
});

if (scribe.includes('id="gmInkExportLastBoundBtn"')) {
  throw new Error("The duplicate legacy export button remains");
}
if (!scribe.includes("$('#gmBosChapterContentsBtn').onclick=()=>GM_BOS.chapterContents()")) {
  throw new Error("Chapter Contents navigation is not wired");
}

console.log(
  `V29 verified: only Scribe changed; ${scripts.length} scripts parse; required controls are unique.`,
);
