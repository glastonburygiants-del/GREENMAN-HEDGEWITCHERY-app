# Greenman HedgeWitchery — CURRENT V5.1 SOURCE OF TRUTH

**Canonical branch:** `current/v5.1-deity-gender-fix`

This is the coordination contract for the current Greenman app line. Every agent must use this ancestry and these hashes. Do **not** rebuild this line from the older Gradle/project ZIP and do **not** layer V1/V2/V3/V4 deity patches onto V5.1.

## Exact ancestry base

The approved ancestry base remains:

`GREENMAN_HEDGEWITCHERY_PHONE_BASELINE_AUTO_FILTER(2).apk`

- Size: `3,661,340` bytes
- SHA-256: `40aa1e3542ba7ac935f65a210a0b1442c4c921c031492f4c75fb1fa15d69f711`

**Forbidden fallback:** `GREENMAN_HEDGEWITCHERY_ANDROID_PROJECT_GATHER_FIXED (1).zip` and descendants are not the base for this line.

## Exact V5 parent

`GREENMAN_HEDGEWITCHERY_V5_FULL_STANDALONE.apk`

- Size: `6,691,113` bytes
- SHA-256: `b65f9e5d0ca2a886f5646bc263a0939733ca990f4e73e549a273b85ccb9d93de`

V5 itself was built from the exact ancestry base above. V5.1 starts from this exact V5 parent hash, not from an older app/project.

## Current V5.1 standalone

`GREENMAN_HEDGEWITCHERY_V5_1_DEITY_FIX.apk`

- Size: `6,690,801` bytes
- SHA-256: `a3e5f03bbd5560b7420626ec02b0c89ff0252a35200a650b9e8ea950bb2e2cdd`

V5.1 is complete in itself. It is not an incremental installer.

## Exact change from V5 to V5.1

Ignoring signature metadata, only **one APK entry changed**:

`assets/index.html`

Inside `const PAGES`, only the embedded **spellBuilder** page changed. Everything outside `const PAGES` in `assets/index.html` stayed byte-for-byte identical to V5.

- V5.1 `assets/index.html` SHA-256: `de2c377e7fe9ca11f120cdea5b3a6da3a2ef95a7c097448b792bb58073bec293`
- V5.1 embedded `spellBuilder` SHA-256: `7b4fcd320ec869ac8719649207235cffa8a7a38d4bd772402c4586b46b3a8692`

## Deity gender fault and repair

The app contained **110 deity records**. The `Deity Gender` field disagreed with the internally consistent `Polarity` / `Energy` fields in **41 records**. That corruption is why masculine gods could appear on the Goddess page.

The V5.1 rule is now explicit and single-owner:

- **Goddess page:** Feminine + Dual
- **God page before a Goddess is selected:** Masculine + Dual
- **God page after a Goddess is selected:** Masculine only
- Gender authority: **Polarity / Energy**

The two older competing deity visibility owners, V55 and V67, are retired rather than patched over. The authoritative renderer/filter is:

`gm-v75-final-deity-seven-card-owner`

The 41 corrected records are listed in:

`current-v5/deity_gender_audit_v51.json`

The exact repair and rebuild guards are:

- `tools/fix_deity_gender_v51.py`
- `tools/build_v51_deity_fix.py`

## V5 content that must remain

- Bower opens as a first-level app room.
- Ogham Treehouse remains a separate APK asset linked directly from the Bower.
- Scribe opens as a first-level app room.
- New BoS retains A4 containment repairs and per-box dynamic text fitting.
- BoS page zoom remains limited to the page area; the app tab bar stays fixed.
- Cupboard Bower entrance remains the small old log burner with glowing oval window and curved title **WOODS**.
- Rune Hall and Crystal Tumbler remain intact.
- Unrelated V5 code remains untouched.

## High-risk embedded-page rule

The authoritative cupboard page is the later assignment:

`PAGES.cupboard = ...`

Do not assume the initial `const PAGES = {...}` object owns the cupboard. When serialising an embedded HTML page back into `index.html`, protect inner script endings so an inner `</script>` cannot terminate the outer engine.

## GitHub is the coordination source

For this line, **GitHub is the canonical coordination route, not Google Drive**. The manifest, repair scripts, audit and guard Action live in this repository. Do not add private-Drive curl steps to the build path.

## Build discipline

1. Verify the exact parent V5 SHA-256 before any V5.1 rebuild.
2. Unpack into a fresh directory.
3. Patch only the embedded `spellBuilder` page for this repair.
4. Retire superseded deity filter owners instead of stacking another filter.
5. Protect inner script endings when serialising the page back into `index.html`.
6. Prove only `spellBuilder` changed inside `const PAGES` and nothing outside `const PAGES` changed.
7. Compare untouched APK entries against the exact V5 parent.
8. Sign once with the repository's established Greenman test key.
9. Verify package, signature and hashes.
10. Publish the complete standalone APK plus audit.

This file remains the source-of-truth contract until the user explicitly names a newer Greenman app baseline.
