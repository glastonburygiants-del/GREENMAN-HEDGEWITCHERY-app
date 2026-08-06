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


def declaration_source(text: str, name: str) -> str | None:
    match = re.search(
        r"\b(?:const|let|var)\s+" + re.escape(name) + r"\s*=\s*([\[{])",
        text,
    )
    if not match:
        return None
    return balanced(text, match.end() - 1, match.group(1))


def source_fingerprint(raw: str) -> dict[str, object]:
    payload = raw.encode("utf-8")
    return {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "utf8_bytes": len(payload),
    }


def storage_keys(all_pages: dict[str, str]) -> list[str]:
    found = set()
    pattern = re.compile(
        r"localStorage\s*\.\s*(?:getItem|setItem|removeItem)\s*\(\s*(['\"])(.*?)\1",
        re.S,
    )
    for text in all_pages.values():
        for match in pattern.finditer(text):
            found.add(match.group(2))
    return sorted(found)


def contract(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    all_pages = pages(text)
    blocks: dict[str, dict[str, object]] = {}

    for page, names in BLOCKS.items():
        page_text = all_pages.get(page)
        if page_text is None:
            raise SystemExit(f"Missing embedded page: {page}")

        for name in names:
            raw = declaration_source(page_text, name)
            if raw is None:
                raise SystemExit(f"Missing database block: {page}.{name}")
            blocks[f"{page}.{name}"] = source_fingerprint(raw)

    return {
        "file": str(path),
        "database_blocks": blocks,
        "literal_localStorage_keys": storage_keys({"outer-shell": text, **all_pages}),
        "protection_method": (
            "Exact balanced JavaScript source fingerprints. Any record, field, value, "
            "schema, order or formatting change inside a protected block changes its SHA-256."
        ),
    }


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(
            "Usage: verify_database_unchanged.py BASELINE.html CANDIDATE.html REPORT.json"
        )

    baseline = contract(Path(sys.argv[1]))
    candidate = contract(Path(sys.argv[2]))

    baseline_blocks = baseline["database_blocks"]
    candidate_blocks = candidate["database_blocks"]
    changed = [
        key
        for key, fingerprint in baseline_blocks.items()
        if candidate_blocks.get(key) != fingerprint
    ]
    missing = sorted(set(baseline_blocks) - set(candidate_blocks))
    added = sorted(set(candidate_blocks) - set(baseline_blocks))
    storage_changed = (
        baseline["literal_localStorage_keys"]
        != candidate["literal_localStorage_keys"]
    )

    passed = not changed and not missing and not added and not storage_changed
    report = {
        "baseline": baseline,
        "candidate": candidate,
        "database_blocks_checked": len(baseline_blocks),
        "changed_database_blocks": changed,
        "missing_database_blocks": missing,
        "added_database_blocks": added,
        "schema_protection": (
            "Schema changes are covered by the exact protected-block fingerprints."
        ),
        "localStorage_key_set_changed": storage_changed,
        "passed": passed,
    }
    Path(sys.argv[3]).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if not passed:
        raise SystemExit(
            "DATABASE CONTRACT FAILED: "
            + json.dumps(
                {
                    "changed": changed,
                    "missing": missing,
                    "added": added,
                    "storage_keys": storage_changed,
                }
            )
        )

    print(
        "Database contract passed: "
        f"{len(baseline_blocks)} exact blocks unchanged; "
        "literal localStorage key set unchanged."
    )


if __name__ == "__main__":
    main()
