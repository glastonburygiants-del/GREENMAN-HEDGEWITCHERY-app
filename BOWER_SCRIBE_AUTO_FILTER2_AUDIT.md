# Bower + Scribe AUTO_FILTER2 audit

This build is based on the exact user-supplied `GREENMAN_HEDGEWITCHERY_PHONE_BASELINE_AUTO_FILTER(2).apk`, not the older Android project stored in this repository.

## Locked source hashes

- Baseline APK SHA-256: `40aa1e3542ba7ac935f65a210a0b1442c4c921c031492f4c75fb1fa15d69f711`
- Bower HTML SHA-256: `1b05165d959a7528bc821e77fd6db045aa7a8553f05db2a3d63a160dcc2e9f69`
- Scribe HTML SHA-256: `9e1940d60c87781092ba4109e54a111aa0ce593331fa8d5596e9c0993b2b1deb`
- Audited unsigned patched APK SHA-256: `434cc8727921d9cc2f356f44d40ef41b228357de508a437d44c267f655c2a17d`

## Baseline signing certificate

SHA-256 fingerprint: `FC:8D:A0:F2:EE:B9:C1:46:01:11:D6:86:4B:A9:AC:C4:19:C0:3E:84:BB:33:C2:40:5F:CA:3F:E2:8E:C2:69:B8`

The Actions build verifies the repository Greenman signing key against this fingerprint before signing.

## Scope of APK changes

Local byte-level audit before upload showed that, excluding the old APK signature files which must be replaced when resigning:

- the only pre-existing APK entry changed is `assets/index.html`;
- `assets/greenman_bower.html` is added byte-for-byte from the supplied Bower source;
- `assets/greenman_scribe.html` is added byte-for-byte from the supplied Scribe source.

The existing cupboard full-screen room mechanism is reused. Bower and Scribe are added as physical cupboard fronts, not as generic navigation buttons. Bower Treehouse parent-message navigation is relayed inside the Bower iframe so the supplied Treehouse flow remains available.

## Validation performed before Actions

- outer `assets/index.html` JavaScript syntax check: pass
- patched cupboard JavaScript syntax check: pass
- supplied Bower JavaScript syntax check: pass
- supplied Scribe JavaScript syntax check: pass
- exact Bower asset byte comparison after APK rebuild: pass
- exact Scribe asset byte comparison after APK rebuild: pass
- app baseline certificate captured and locked above

The GitHub Actions workflow repeats the room hashes, patch markers, app identity, APK alignment and signing-certificate checks before publishing the downloadable artifact.
