#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("usage: patch_web_v2_shell.py input.html output.html")

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
text = src.read_text(encoding="utf-8")

if "gm-web-app-access-v1" not in text:
    raise SystemExit("Web App V1 patch must be applied first")
if "v2-account-sync.js" in text:
    raise SystemExit("Web App V2 shell patch already applied")

old = '''<div id="gmWebAccessScreen" aria-modal="true" role="dialog" aria-label="HedgeWitchery Web App access">
  <div id="gmWebAccessCard">
    <h1>Greenman HedgeWitchery Apothecary</h1>
    <div class="gm-web-sub">HedgeWitchery Web App</div>
    <p class="gm-web-intro">Choose Web App access, or use an access key or promo code.</p>
    <div class="gm-web-pay-grid">
      <button class="gm-web-pay" id="gmWebPayMonthly" type="button">1 MONTH · £5.99<small>PayPal sandbox</small></button>
      <button class="gm-web-pay" id="gmWebPayYearly" type="button">1 YEAR · £49.99<small>PayPal sandbox</small></button>
    </div>
    <div class="gm-web-or">Access key or promo code</div>
    <input id="gmWebAccessKey" type="text" inputmode="text" autocomplete="off" maxlength="14" placeholder="GM-XXXX-XXXX" aria-label="Web App access key or promo code">
    <button id="gmWebUseKey" type="button">OPEN WITH KEY</button>
    <div id="gmWebAccessMsg" aria-live="polite"></div>
    <div class="gm-web-backup-row">
      <button id="gmWebAccessExport" type="button">EXPORT BACKUP</button>
      <button id="gmWebAccessImport" type="button">IMPORT BACKUP</button>
    </div>
    <div class="gm-web-sandbox">Sandbox payment testing only.</div>
  </div>
</div>'''

new = '''<div id="gmWebAccessScreen" aria-modal="true" role="dialog" aria-label="HedgeWitchery Web App access">
  <div id="gmWebAccessCard">
    <h1>Greenman HedgeWitchery Apothecary</h1>
    <div class="gm-web-sub">HedgeWitchery Web App</div>
    <p class="gm-web-intro">Sign in so your subscription and your saved HedgeWitchery work can follow you between devices.</p>

    <div id="gmWebLoginBox">
      <div id="gmWebSignedOut">
        <label for="gmWebLoginEmail">Email</label>
        <input id="gmWebLoginEmail" type="email" autocomplete="email" placeholder="you@example.com">
        <div class="gm-web-login-row">
          <button class="gm-web-login-btn" id="gmWebSendCode" type="button">SEND LOGIN CODE</button>
          <span></span>
        </div>
        <div id="gmWebCodeArea" style="display:none;margin-top:10px">
          <label for="gmWebLoginCode">6-digit code</label>
          <div class="gm-web-login-row">
            <input id="gmWebLoginCode" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="123456">
            <button class="gm-web-login-btn" id="gmWebVerifyCode" type="button">SIGN IN</button>
          </div>
        </div>
        <div id="gmWebLoginMsg" aria-live="polite"></div>
      </div>
      <div id="gmWebSignedIn">
        <span id="gmWebSignedInText"></span>
        <button class="gm-web-login-btn secondary" id="gmWebSignOut" type="button">SIGN OUT</button>
      </div>
    </div>

    <div id="gmWebAccessChoices">
      <div class="gm-web-pay-grid">
        <button class="gm-web-pay" id="gmWebPayMonthly" type="button">1 MONTH · £5.99<small>PayPal sandbox</small></button>
        <button class="gm-web-pay" id="gmWebPayYearly" type="button">1 YEAR · £49.99<small>PayPal sandbox</small></button>
      </div>
      <div class="gm-web-or">Access key or promo code</div>
      <input id="gmWebAccessKey" type="text" inputmode="text" autocomplete="off" maxlength="14" placeholder="GM-XXXX-XXXX" aria-label="Web App access key or promo code">
      <button id="gmWebUseKey" type="button">OPEN WITH KEY</button>
    </div>

    <div id="gmWebAccessMsg" aria-live="polite"></div>
    <div class="gm-web-backup-row">
      <button id="gmWebAccessExport" type="button">EXPORT BACKUP</button>
      <button id="gmWebAccessImport" type="button">IMPORT BACKUP</button>
    </div>
    <div class="gm-web-sandbox">Sandbox payment testing only.</div>
  </div>
</div>'''

if text.count(old) != 1:
    raise SystemExit(f"V1 access markup anchor count {text.count(old)}")
text = text.replace(old, new, 1)

head = "</head>"
if text.count(head) < 1:
    raise SystemExit("outer head close missing")
text = text.replace(
    head,
    '<link rel="stylesheet" href="v2-account-sync.css">\\n' + head,
    1,
)

startup = "buildTabs(); syncModeClass(); showPage('home'); gmAccessRestoreOnLaunch(); gmWebAccessBoot();"
if text.count(startup) != 1:
    raise SystemExit(f"V1 startup anchor count {text.count(startup)}")
text = text.replace(
    startup,
    "buildTabs(); syncModeClass(); showPage('home'); gmAccessRestoreOnLaunch();",
    1,
)

body_end = text.rfind("</body>")
if body_end < 0:
    raise SystemExit("outer body close missing")
text = text[:body_end] + '<script src="v2-account-sync.js"></script>\\n' + text[body_end:]

checks = [
    "gmWebLoginEmail",
    "SEND LOGIN CODE",
    "gmWebAccessChoices",
    "v2-account-sync.css",
    "v2-account-sync.js",
    "1 MONTH · £5.99",
    "1 YEAR · £49.99",
]
for marker in checks:
    if marker not in text:
        raise SystemExit("missing V2 shell marker: " + marker)

dst.write_text(text, encoding="utf-8")
print("patched HedgeWitchery Web App V2 account shell")
