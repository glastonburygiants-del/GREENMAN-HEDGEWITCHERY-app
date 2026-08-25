# Greenman HedgeWitchery — CURRENT V6 SOURCE OF TRUTH

## Canonical ancestry

V6 stays on the exact app line requested by the user.

Canonical base:

`GREENMAN_HEDGEWITCHERY_PHONE_BASELINE_AUTO_FILTER(2).apk`

- Size: `3,661,340` bytes
- SHA-256: `40aa1e3542ba7ac935f65a210a0b1442c4c921c031492f4c75fb1fa15d69f711`

V6 is derived from the verified complete V5 standalone that was itself built from that exact base:

`GREENMAN_HEDGEWITCHERY_V5_FULL_STANDALONE.apk`

- Size: `6,691,113` bytes
- SHA-256: `b65f9e5d0ca2a886f5646bc263a0939733ca990f4e73e549a273b85ccb9d93de`

Do **not** return to `GREENMAN_HEDGEWITCHERY_ANDROID_PROJECT_GATHER_FIXED (1).zip` or any descendant as the app base.

## V6 issue and repair

A legacy data inconsistency was exposed on the Spell Builder Goddess page. The `Deity Gender` field conflicts with the internally consistent `Polarity` and `Energy` fields on 41 deity records.

Conflict breakdown:

- 19 records: `Deity Gender = God` while Polarity/Energy are Feminine
- 17 records: `Deity Gender = Goddess` while Polarity/Energy are Masculine
- 3 records: `Deity Gender = Goddess` while Polarity/Energy are Both
- 2 records: `Deity Gender = Both` while Polarity/Energy are Feminine

Examples of the exposed masculine records include THOR, ODIN, PAN, JUPITER and MARS. Examples of feminine records carrying the opposite legacy label include BRIGID, FREYJA, FRIGG, SELENE and THE MORRIGAN.

The V6 repair does not rewrite the deity database. It changes the active Spell Builder deity classifiers so:

1. `Polarity` and `Energy` decide Goddess / God / Dual when present.
2. `Deity Gender` is fallback only when those fields are blank.
3. Goddess stage allows Feminine + Dual only.
4. God stage allows Masculine only, except when a genuinely Dual deity was selected in the Goddess slot, in which case the existing Dual continuation rule is retained.
5. Any invalid deity already stored in the spell state by the old filter is cleared when the deity stage opens.

Repair script:

`tools/patch_v6_deity_gender.py`

## Current V6 APK

`GREENMAN_HEDGEWITCHERY_V6_DEITY_FIX.apk`

- Size: `6,691,449` bytes
- SHA-256: `2c46957751b31a1d15114c05ff15ff72572d6c06b1f1effe2a6bdeeaa4ecf61c`
- Drive file ID: `1wkiPRsIaTGOVq5JMyVWisW5Kqx-Keq8h`
- Signer certificate SHA-256: `BD22A5C3FF7335237A0E725032816EB563D2E350789E6E555369B0FE32E0C19E`

Only `assets/index.html` differs from V5. Bower, Treehouse, Scribe, native shell, resources, fonts and all other APK payload files are byte-identical to V5.

## Validation

- All 38 decoded Spell Builder script blocks pass JavaScript syntax checking.
- Encoded Spell Builder contains zero literal inner `</script>` boundaries.
- The V6 APK verifies with the same Greenman signing certificate used by V5.
- THOR, ODIN, PAN, JUPITER and MARS classify as God.
- BRIGID, FREYJA, FRIGG, SELENE and THE MORRIGAN classify as Goddess.

`current-v6/manifest.json` is the machine-readable coordination record for other agents.
