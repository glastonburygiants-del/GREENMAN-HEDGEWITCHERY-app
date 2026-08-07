# Greenman Brand-New Shell Build Audit

This branch deliberately starts from commit `27e9ec4447071a33d416dd6cf52ee8cafd4c3e32`, before the later Android print patch chain.

## App content baseline

The build starts with `GREENMAN_HEDGEWITCHERY_ANDROID_PROJECT_GATHER_FIXED*.zip` and applies only the already-proven Supply Cupboard room-load repair.

Expected resulting `index.html` SHA-256:

`53224a35f792777ba70d2f13323d81f38a7037dadc9b2bb753b73157fee93cb2`

That is the exact `GREENMAN_HEDGEWITCHERY_GATHER_FAST_SUPPLY_ROOM_FIXED.html` app: original supplied app + Gather speed repair + Supply Cupboard room-load repair.

## Original print owners protected

The following print functions in the rebuilt app are byte-for-byte identical to the user's supplied original `GREENMAN_HEDGEWITCHERY.html`:

- `renderPrint(pages,kind)` SHA-256 `8c3f5fce0d707d716353faf1ee8517657a36262868f31598634cb145eabfe55b`
- `buildPack()` SHA-256 `69c9e84326536139de75cc9a0dd5f0c1364159c390d40f52fa5520c37ddd010e`
- `buildPage()` SHA-256 `ad1bb0b1ea951826fdab0a4f99872aae0aa597ac1e9202317400d422279a88f9`
- `printLiteThree()` SHA-256 `c76b0982f4a40e66ca8d983b7dce6b02ea1549ded98473330567792ad8792d88`
- Book of Shadows `printAll()` SHA-256 `66d18fe18cd28447b87ce029301423c409513af78a5dbb55babc173265c527ca`
- Journal/BoS `printWholeBos()` SHA-256 `97fa2e0cd29721281a014ddca556f2eeac7163219ea54bf96316eca5b59f619b`
- canonical `fitPage(page)` SHA-256 `be4d590a0ad4e176355e1155ce1fb4bb2c6aa3725c985b6b904f2b6946e80b96`

No customer-print patch, Lite bridge patch, outer print relay patch, Android lifecycle patch, mono patch, or later print-owner rewrite is applied to the HTML.

## Brand-new Android shell

`clean_shell_v2/MainActivity.java` SHA-256:

`2ca67a0efc90f5c7efb3c93fb8f367a0a7a409792acc6af37f4926dfacd3d635`

The new shell has one Android print route only:

`original app window.print()` -> `GreenmanAndroid.printDocument(...)` -> one attached print WebView -> Android PrintManager.

The print copy has JavaScript disabled. Therefore the shell cannot rerun the whole app or activate old print scripts in the isolated print WebView. It freezes the already-built live DOM, including nested same-origin iframe contents, and carries that result to Android.

The print WebView permits WebView-internal `data:`, `about:` and `blob:` URLs so Android does not produce the earlier `ERR_HTTP_RESPONSE_CODE_FAILURE` page.

The shell uses the original print-frame layout context of 820 x 1120 and requests ISO A4 with zero Android margins. Page construction, scaling, fitting, page breaks and pack selection remain owned by the original HTML.

## Explicitly absent from the new shell

- no `printCurrentPage` fallback
- no `printHtml` relay chain
- no `nativePrintHtml`
- no `gmNativePrintHtml`
- no script-stripping snapshot path
- no hidden/off-screen alpha print WebView
- no second or fallback Android print owner

Nothing on this branch should be merged to `main` until the APK has been tested on the user's phone/tablet.
