# Greenman HedgeWitchery — CURRENT V5 SOURCE OF TRUTH

**Canonical branch:** `current/v5-exact-baseline`

This branch exists so every agent uses the same app ancestry. Do **not** rebuild this line from the older Gradle/project ZIP and do **not** layer V1/V2/V3/V4 patch code onto V5.

## Exact base

The only approved base for this line is:

`GREENMAN_HEDGEWITCHERY_PHONE_BASELINE_AUTO_FILTER(2).apk`

- Size: `3,661,340` bytes
- SHA-256: `40aa1e3542ba7ac935f65a210a0b1442c4c921c031492f4c75fb1fa15d69f711`

Any build step must verify both the filename/source identity and SHA-256 before editing. If the hash does not match, stop.

**Forbidden fallback:** `GREENMAN_HEDGEWITCHERY_ANDROID_PROJECT_GATHER_FIXED (1).zip` and descendants are not the base for this V5 line.

## Current V5 standalone

`GREENMAN_HEDGEWITCHERY_V5_FULL_STANDALONE.apk`

- Size: `6,691,113` bytes
- SHA-256: `b65f9e5d0ca2a886f5646bc263a0939733ca990f4e73e549a273b85ccb9d93de`

The V5 APK is complete in itself. It is not an incremental installer and must not depend on V4 being present.

## Canonical V5 room/source assets

| APK asset | Canonical source | Size | SHA-256 |
|---|---|---:|---|
| `assets/greenman_bower.html` | `Greenman_Bower_Treehouse_V14_APP_DIRECT_UPPER.html` | 1,605,303 | `df152b24f0a2b89acf0ebf0150821e43efdc9fc6352cbbba1c38ad7d5f942742` |
| `assets/greenman_treehouse.html` | `greenman_treehouse.html` | 750,420 | `1d96a09eebed509557f769aa933fa8addc60128da7ca66d9817111882bad768f` |
| `assets/greenman_scribe.html` | `greenman_scribe_v5.html` | 8,215,600 | `e086fd31c5f30ab6b9e95432b9964247a41774c619f35d2b23650ebecf06aac3` |
| `assets/index.html` | V5 shell/index | 16,246,417 | `d0eb2b87bfa1b8b937c242548cbfdac1de671f562dfbf921049fc2b93fe2c278` |

## V5 content that must remain

- Bower opens as a first-level app room.
- Ogham Treehouse is a separate APK asset and is linked directly from the Bower.
- Scribe opens as a first-level app room.
- New BoS has A4 containment repairs and per-box dynamic text fitting.
- BoS page zoom is limited to the page area; the app tab bar remains fixed.
- Cupboard Bower entrance is the small old log burner with glowing oval window and curved title **WOODS**.
- Rune Hall and Crystal Tumbler remain intact.
- Unrelated baseline app code remains untouched.

## High-risk embedded-page rule

The authoritative cupboard page is the later assignment:

`PAGES.cupboard = ...`

Do not assume the initial `const PAGES = {...}` object owns the cupboard. When serialising an embedded HTML page back into `index.html`, protect inner script endings so an inner `</script>` cannot terminate the outer engine. Before release, validate the outer engine and the cupboard's embedded scripts.

## Connected source staging

For agents that also have access to the user's connected Google Drive, the exact files were staged in folder:

`GREENMAN_GITHUB_STAGING_V5`

Drive folder id: `1GRcXqubcj225YQ_v01eAgHCxcao6HSdp`

Current staged file IDs:

- Exact baseline APK: `1qXbdPgBX2jneMyvtqFAC5oBU1bwuZCN7`
- V5 standalone APK: `15_JqUeDv7VV_qQ_xTsgbjEkCjR0w-KMx`
- Bower V5 source: `1rARVzPRAvFHJ053h5RfM5Ii0_eRMIeQc`
- Treehouse V5 source: `1W7CmE-XdMz_9Z6b5BmZvaG8dWjHPwCle`
- Scribe V5 source: `1hsc6NdDAlH3YPI7ehSej19i5KAZc68KC`

These Drive files are private. A GitHub Action must **not** use unauthenticated Drive `curl` and pretend that path is viable.

## Build discipline

1. Start from the exact APK hash above.
2. Unpack that APK into a fresh directory.
3. Remove old signature metadata only when repacking requires it.
4. Make only the requested changes.
5. Add/replace the canonical room assets.
6. Validate embedded-script boundaries and JavaScript syntax.
7. Compare every untouched APK entry against the exact baseline and report unexpected differences.
8. Sign once with the repository's established Greenman test key.
9. Verify package, signature, asset hashes and final APK hash.
10. Publish the complete standalone APK plus an audit report.

This file is the coordination contract for V5 and later changes until the user explicitly names a newer source of truth.
