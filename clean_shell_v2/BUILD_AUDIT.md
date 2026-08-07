# Greenman 2.1 Clean Rebuild Audit

This branch deliberately starts from commit `27e9ec4447071a33d416dd6cf52ee8cafd4c3e32`, before the later Android print patch chain.

## App content baseline

The build starts with `GREENMAN_HEDGEWITCHERY_ANDROID_PROJECT_GATHER_FIXED*.zip` and applies the already-proven Supply Cupboard room-load repair.

Pre-print-adjustment `index.html` SHA-256:

`53224a35f792777ba70d2f13323d81f38a7037dadc9b2bb753b73157fee93cb2`

That is the original supplied app plus the Gather speed repair and Supply Cupboard room-load repair.

## Two Summary print restorations only

`clean_shell_v2/install_proven_summary_print.py` makes two controlled changes inside the existing spell-builder print system.

### Summary page 2 containment

The existing canonical `fitPage(page)` remains the only Summary page fitter. A final Summary-page-2-only containment stage is added inside that same function. It keeps the A4 page frame fixed at 756 x 1058 and, only when populated content exceeds the real page canvas, scales `.true-content` to fit both height and width.

The containment principle comes from the earlier locked A4 print-pack whole-page fit: measure the populated content after layout, calculate the required scale, and scale the content rather than shrinking or replacing the A4 page itself.

There is no second page fitter, no crop handler and no post-print scaling route.

### Black-and-white PDF / thermal print

The earlier locked print pack's dedicated black-and-white `@media print` rules are restored into the two generated Summary print documents only:

- Full A4 Page / A4 Pack document
- Lite / Simple Summary print document

Those print-only rules remove coloured backgrounds, force text to black, use black/grey borders and request economical print colour handling. The live Summary screen remains full colour.

Journal and Book of Shadows print generation are not changed by this installer.

Expected resulting `index.html` SHA-256 after these two restorations:

`da7cdc5a815fc48879a48d0b044845000bbb27b5d831a723e5b587a7ee4418a1`

## Android shell unchanged

`clean_shell_v2/MainActivity.java` SHA-256 remains:

`2ca67a0efc90f5c7efb3c93fb8f367a0a7a409792acc6af37f4926dfacd3d635`

The shell still has one Android print route only:

`app window.print()` -> `GreenmanAndroid.printDocument(...)` -> one attached print WebView -> Android PrintManager.

The print copy has JavaScript disabled. The print WebView permits WebView-internal `data:`, `about:` and `blob:` URLs. It uses the existing 820 x 1120 print-frame layout context and requests ISO A4 with zero Android margins.

No shell code is changed for the 2.1 Summary test.

## Explicitly absent

- no `printCurrentPage` fallback
- no `printHtml` relay chain
- no `nativePrintHtml`
- no `gmNativePrintHtml`
- no script-stripping snapshot path
- no hidden/off-screen alpha print WebView
- no second or fallback Android print owner
- no Journal or BoS print rewrite in this change

Draft PR #4 remains a phone/tablet test line only. Nothing should be merged to `main` until device testing passes.
