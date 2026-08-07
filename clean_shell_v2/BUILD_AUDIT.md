# Greenman 2.2 Clean Rebuild Audit

This branch deliberately starts from commit `27e9ec4447071a33d416dd6cf52ee8cafd4c3e32`, before the later Android print patch chain.

## App baseline

The build starts with `GREENMAN_HEDGEWITCHERY_ANDROID_PROJECT_GATHER_FIXED*.zip` and applies the already-proven Supply Cupboard room-load repair.

Pre-print-adjustment `index.html` SHA-256:

`53224a35f792777ba70d2f13323d81f38a7037dadc9b2bb753b73157fee93cb2`

## Summary print restoration retained from 2.1

`clean_shell_v2/install_proven_summary_print.py` retains the two controlled Summary print changes tested in 2.1:

- Summary page 2 final containment inside the existing canonical fitter, keeping the A4 frame fixed while fitting only overflowing page-2 content.
- Dedicated black-and-white print rules in the generated Full A4 Page/A4 Pack and Lite/Simple Summary documents only.

Intermediate `index.html` SHA-256 after those print changes:

`da7cdc5a815fc48879a48d0b044845000bbb27b5d831a723e5b587a7ee4418a1`

Journal and Book of Shadows print generation remain untouched.

## 2.2 UI-only repairs

`clean_shell_v2/install_ui_feedback.py` makes three UI changes without adding or replacing any print owner.

### Gather completion

The browser `about:blank` alert is removed. The earlier Greenman completion card is restored with:

- `✦ Your Spell Is Gathered ✦`
- the Journal Quick List explanation
- `Open Journal`
- `Begin Another Spell`

The earlier phrase `full working` is not used; the card says `full spell`.

### Summary print feedback

The existing Summary print functions show a Greenman status message immediately after one tap and hide it immediately before the existing `window.print()` handoff:

- `The Greenman is getting your A4 page ready to print…`
- `The Greenman is getting your A4 pack ready to print…`
- `The Greenman is getting your Lite pack ready to print…`

The messages do not alter page building, fitting, PDF content or Android printing.

### Lite to full-mode fullscreen return

The app asks the native shell to re-enter Android immersive mode after switching out of Lite mode and again when entering a full-room view such as Rune Hall or Crystal Tumbler.

Final `index.html` SHA-256:

`f26222e0a4a71db8cea7180472f5fd980fc66c048c64074ee81bf82e7d7551ec`

## Android shell

The original clean single-print-owner shell is copied first. `clean_shell_v2/install_fullscreen_bridge.py` adds one JavaScript-interface method, `refreshImmersive()`, which only calls the shell's existing `enterImmersiveMode()` routine and repeats it briefly after mode changes.

Resulting `MainActivity.java` SHA-256:

`08f6e0919be07f805cdac350a2d16b549789037fde724d58760488fd8486cad3`

The Android print route remains exactly one owner:

`app window.print()` -> `GreenmanAndroid.printDocument(...)` -> one attached print WebView -> Android PrintManager.

The 2.2 fullscreen bridge does not modify `printDocument`, `openPrintDocument`, `printWebViewDocument`, the print WebView settings, ISO A4 selection, margins, or the HTML freeze/handoff.

## Explicitly absent

- no `printCurrentPage` fallback
- no `printHtml` relay chain
- no `nativePrintHtml`
- no `gmNativePrintHtml`
- no script-stripping snapshot path
- no hidden/off-screen alpha print WebView
- no second or fallback Android print owner
- no Journal or BoS print rewrite

Version: `2.2-ui-feedback`, code `13`.

Draft PR #4 remains a phone/tablet test line only. Nothing should be merged to `main` until device testing passes.
