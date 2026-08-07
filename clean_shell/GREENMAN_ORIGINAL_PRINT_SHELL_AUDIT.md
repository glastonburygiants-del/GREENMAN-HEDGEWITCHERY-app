# Greenman Original Print Shell Audit

## Clean source line
- Git branch starts from the last successful pre-print-patch commit: `87968268a19e57f44d443021346e72a319df8446`.
- App source: `GREENMAN_HEDGEWITCHERY_ANDROID_PROJECT_GATHER_FIXED.zip`.
- App HTML SHA-256: `90dd2304a3292124893ab2dba441762d1eb84b08173cf5e329bf0e04998618ef`.
- Android shell Java SHA-256: `57d87d78d803623d5cc5f2227f16563899d0b5038d7d49b33327c1359e0ee771`.

## Protected original print owners
The complete print builders in these embedded pages are retained from the Gather-fixed app:
- `spellBuilder`: `525cab3dd4f93086f4ef34b479f1647fa6365363094298347b66c5d098d0d0c9`
- `journal`: `365b3cc4d9bb81fe427c514a6f291eff032c82f477c689b62bd9c9004474d7cd`
- `bos`: `ba4b1162dd3d31c71e7c1bf502ff056a2ce11799b09950cf2a83dd8a09700dfd`
- `grimoire`: `bd51e25c4b4f4810535eafa482f2b1f9a47ab1ae4c787c279b9854e32729d8e7`
- `admin`: `c10723d73e60df6da919282e5439fe65bafcdc21595f9307f5ab6fc29b7e3007`

No A4 builder, fit calculation, page size, page break, Summary layout, Lite pack, Journal print area, BoS print area, Grimoire print area, database block, or storage key is rewritten by this build.

## Android handoff only
- One complete `MainActivity.java` replaces the former shell class.
- It intercepts `print()` recursively in the app page and same-origin nested print frames.
- It copies the exact document produced by the original print owner after `beforeprint` layout.
- Android renders that document in a full-size, visible A4 print WebView behind the app.
- ISO A4 and zero Android margins are requested. The app's original CSS remains the layout owner.
- The print WebView remains attached while Android's PDF service reads it.

## Build safeguards
- The workflow refuses to build if the app HTML hash differs from the clean Gather-fixed source.
- The workflow refuses to build if the complete shell Java hash differs.
- Version: `1.7-clean-shell`, code `8`.
- The existing app resources and styling are retained in this print recovery build.
