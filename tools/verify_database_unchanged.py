#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

BLOCKS = {
    "admin": ["EDITOR_DATA", "STOCK_MASTER", "COLUMN_MAP"],
    "grimoire": ["ITEMS", "SPELLS", "CANDLES", "NUMEROLOGY", "GM_SABBAT_DATA", "GM_MOON_PHASE_DATA", "GM_NAMED_MOON_DATA"],
    "spellBuilder": ["PAGE_DEFS"],
    "cupboard": ["ITEMS", "INCENSE_TYPE_BY_NAME", "SPELL_CUPBOARD_ART", "FILTERS"],
    "moon": ["itemData", "phases", "MOON_NAMES"],
    "numerology": ["numData"],
    "planetTiming": ["FALLBACK_ITEMS", "PLANETS", "MOON_PHASES"],
    "planets": ["byPlanet", "byPhase"],
}


def digest(value) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def pages(text: str) -> dict[str, str]:
    marker = "const PAGES = "
    start = text.index(marker) + len(marker)
    result, used = json.JSONDecoder().raw_decode(text[start:])
    tail_start = start + used
    for match in re.finditer(r"PAGES\.([A-Za-z_$][\w$]*)\s*=\s*", text[tail_start:]):
        absolute = tail_start + match.end()
        try:
            value, _ = json.JSONDecoder().raw_decode(text[absolute:])
        except Exception:
            continue
        if isinstance(value, str):
            result[match.group(1)] = value
    return result


def balanced(text: str, start: int, opener: str) -> str:
    closer = "}" if opener == "{" else "]"
    depth = 0
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    index = start
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if line_comment:
            if char == "\n":
                line_comment = False
        elif block_comment:
            if char == "*" and nxt == "/":
                block_comment = False
                index += 1
        elif quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        else:
            if char == "/" and nxt == "/":
                line_comment = True
                index += 1
            elif char == "/" and nxt == "*":
                block_comment = True
                index += 1
            elif char in "'\"`":
                quote = char
            elif char == opener:
                depth += 1
            elif char == closer:
                depth -= 1
                if depth == 0:
                    return text[start:index + 1]
        index += 1
    raise ValueError("Unclosed data block")


def declaration(text: str, name: str):
    match = re.search(r"\b(?:const|let|var)\s+" + re.escape(name) + r"\s*=\s*([\[{])", text)
    if not match:
        return None
    raw = balanced(text, match.end() - 1, match.group(1))
    return json.loads(raw)


def storage_keys(all_pages: dict[str, str]) -> list[str]:
    found = set()
    pattern = re.compile(r"localStorage\s*\.\s*(?:getItem|setItem|removeItem)\s*\(\s*(['\"])(.*?)\1", re.S)
    for text in all_pages.values():
        for match in pattern.finditer(text):
            found.add(match.group(2))
    return sorted(found)


def contract(path: Path):
    text = path.read_text(encoding="utf-8")
    all_pages = pages(text)
    hashes = {}
    schemas = {}
    for page, names in BLOCKS.items():
        page_text = all_pages.get(page)
        if page_text is None:
            raise SystemExit(f"Missing embedded page: {page}")
        for name in names:
            value = declaration(page_text, name)
            if value is None:
                raise SystemExit(f"Missing database block: {page}.{name}")
            key = f"{page}.{name}"
            hashes[key] = digest(value)
            if isinstance(value, list) and value and all(isinstance(row, dict) for row in value):
                schemas[key] = sorted(set().union(*(row.keys() for row in value)))
            elif isinstance(value, dict):
                schemas[key] = {
                    section: sorted(set().union(*(row.keys() for row in rows)))
                    for section, rows in value.items()
                    if isinstance(rows, list) and rows and all(isinstance(row, dict) for row in rows)
                }
    return {
        "file": str(path),
        "database_hashes": hashes,
        "database_schemas": schemas,
        "literal_localStorage_keys": storage_keys({"outer-shell": text, **all_pages}),
    }


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("Usage: verify_database_unchanged.py BASELINE.html CANDIDATE.html REPORT.json")
    baseline = contract(Path(sys.argv[1]))
    candidate = contract(Path(sys.argv[2]))
    changed = [key for key, value in baseline["database_hashes"].items() if candidate["database_hashes"].get(key) != value]
    schema_changed = [key for key, value in baseline["database_schemas"].items() if candidate["database_schemas"].get(key) != value]
    storage_changed = baseline["literal_localStorage_keys"] != candidate["literal_localStorage_keys"]
    report = {
        "baseline": baseline,
        "candidate": candidate,
        "database_blocks_checked": len(baseline["database_hashes"]),
        "changed_database_blocks": changed,
        "changed_database_schemas": schema_changed,
        "localStorage_key_set_changed": storage_changed,
        "passed": not changed and not schema_changed and not storage_changed,
    }
    Path(sys.argv[3]).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not report["passed"]:
        raise SystemExit("DATABASE CONTRACT FAILED: " + json.dumps({"blocks": changed, "schemas": schema_changed, "storage_keys": storage_changed}))
    print(f"Database contract passed: {report['database_blocks_checked']} blocks unchanged; localStorage key set unchanged.")


if __name__ == "__main__":
    main()
