#!/usr/bin/env python3
"""Verify the Greenman V5 exact-baseline handoff.

Usage:
  python tools/verify_current_v5.py \
    baseline.apk current-v5.apk bower.html treehouse.html scribe.html

This verifier is deliberately strict. It refuses a different base and checks that
all baseline APK entries remain byte-identical except for the expected V5 edits.
"""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

BASELINE_NAME = "GREENMAN_HEDGEWITCHERY_PHONE_BASELINE_AUTO_FILTER(2).apk"
BASELINE_SIZE = 3_661_340
BASELINE_SHA256 = "40aa1e3542ba7ac935f65a210a0b1442c4c921c031492f4c75fb1fa15d69f711"

V5_SIZE = 6_691_113
V5_SHA256 = "b65f9e5d0ca2a886f5646bc263a0939733ca990f4e73e549a273b85ccb9d93de"
V5_INDEX_SHA256 = "d0eb2b87bfa1b8b937c242548cbfdac1de671f562dfbf921049fc2b93fe2c278"

ASSETS = {
    "assets/greenman_bower.html": (
        1_605_303,
        "df152b24f0a2b89acf0ebf0150821e43efdc9fc6352cbbba1c38ad7d5f942742",
    ),
    "assets/greenman_treehouse.html": (
        750_420,
        "1d96a09eebed509557f769aa933fa8addc60128da7ca66d9817111882bad768f",
    ),
    "assets/greenman_scribe.html": (
        8_215_600,
        "e086fd31c5f30ab6b9e95432b9964247a41774c619f35d2b23650ebecf06aac3",
    ),
}

EXPECTED_BASELINE_CHANGES = {
    "assets/index.html",
    "META-INF/MANIFEST.MF",
    "META-INF/ANDROIDD.SF",
    "META-INF/ANDROIDD.RSA",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(message: str) -> None:
    raise SystemExit(f"VERIFY FAILED: {message}")


def check_file(path: Path, size: int, digest: str, label: str) -> None:
    if not path.is_file():
        fail(f"missing {label}: {path}")
    actual_size = path.stat().st_size
    if actual_size != size:
        fail(f"{label} size {actual_size} != {size}")
    actual_digest = sha256_file(path)
    if actual_digest != digest:
        fail(f"{label} SHA-256 {actual_digest} != {digest}")


def zip_map(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path, "r") as zf:
        return {name: zf.read(name) for name in zf.namelist() if not name.endswith("/")}


def check_cupboard_raw(index_text: str) -> None:
    marker = "PAGES.cupboard = "
    if marker not in index_text:
        fail("authoritative PAGES.cupboard assignment missing")
    start = index_text.index(marker) + len(marker)
    cupboard, consumed = json.JSONDecoder().raw_decode(index_text[start:])
    raw = index_text[start : start + consumed]

    # Decoded cupboard legitimately contains its own closing script tags. In the
    # outer JS string they must be protected as <\\/script>.
    if "</script>" in raw:
        fail("unescaped inner </script> found inside raw PAGES.cupboard JS string")
    if raw.count("<\\/script>") != cupboard.count("</script>"):
        fail("cupboard script-boundary protection count mismatch")

    required = (
        "WOODS",
        "openBower",
        "openScribe",
        "gmCupboardHardwareBack",
    )
    for token in required:
        if token not in cupboard:
            fail(f"cupboard marker missing: {token}")


def main() -> int:
    if len(sys.argv) != 6:
        print(__doc__.strip())
        return 2

    baseline = Path(sys.argv[1])
    v5 = Path(sys.argv[2])
    bower = Path(sys.argv[3])
    treehouse = Path(sys.argv[4])
    scribe = Path(sys.argv[5])

    if baseline.name != BASELINE_NAME:
        fail(f"wrong baseline filename: {baseline.name}")

    check_file(baseline, BASELINE_SIZE, BASELINE_SHA256, "exact baseline APK")
    check_file(v5, V5_SIZE, V5_SHA256, "current V5 standalone APK")

    external_sources = {
        "assets/greenman_bower.html": bower,
        "assets/greenman_treehouse.html": treehouse,
        "assets/greenman_scribe.html": scribe,
    }
    for asset_name, source_path in external_sources.items():
        size, digest = ASSETS[asset_name]
        check_file(source_path, size, digest, source_path.name)

    base_entries = zip_map(baseline)
    v5_entries = zip_map(v5)

    for name, base_data in base_entries.items():
        if name in EXPECTED_BASELINE_CHANGES:
            continue
        if name not in v5_entries:
            fail(f"baseline entry disappeared from V5: {name}")
        if sha256_bytes(base_data) != sha256_bytes(v5_entries[name]):
            fail(f"unexpected baseline entry change: {name}")

    expected_added = set(ASSETS)
    actual_added = set(v5_entries) - set(base_entries)
    if actual_added != expected_added:
        fail(
            "unexpected added APK entries: "
            f"expected {sorted(expected_added)}, got {sorted(actual_added)}"
        )

    for asset_name, source_path in external_sources.items():
        apk_data = v5_entries.get(asset_name)
        if apk_data is None:
            fail(f"V5 asset missing: {asset_name}")
        source_data = source_path.read_bytes()
        if apk_data != source_data:
            fail(f"V5 asset differs from canonical source: {asset_name}")

    index_data = v5_entries.get("assets/index.html")
    if index_data is None:
        fail("V5 assets/index.html missing")
    if sha256_bytes(index_data) != V5_INDEX_SHA256:
        fail("V5 index SHA-256 does not match source-of-truth value")

    index_text = index_data.decode("utf-8")
    check_cupboard_raw(index_text)

    for token in ("greenman_bower.html", "greenman_scribe.html"):
        if token not in index_text:
            fail(f"V5 shell route missing: {token}")

    print("VERIFY OK")
    print(f"baseline_sha256={BASELINE_SHA256}")
    print(f"v5_sha256={V5_SHA256}")
    print(f"unchanged_baseline_entries_checked={len(base_entries) - len(EXPECTED_BASELINE_CHANGES)}")
    print(f"canonical_added_assets={len(expected_added)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
