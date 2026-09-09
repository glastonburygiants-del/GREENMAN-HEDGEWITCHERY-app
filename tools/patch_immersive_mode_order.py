#!/usr/bin/env python3
"""Real-device logcat (Acer tablet, Android 13) confirmed this crash on
every open:

  FATAL EXCEPTION: main
  java.lang.NullPointerException: Attempt to invoke virtual method
  'android.view.WindowInsetsController DecorView.getWindowInsetsController()'
  on a null object reference
      at com.android.internal.policy.PhoneWindow.getInsetsController(PhoneWindow.java:3924)
      at com.greenman.hedgewitchery.MainActivity.enterImmersiveMode(MainActivity.java:734)
      at com.greenman.hedgewitchery.MainActivity.onCreate(MainActivity.java:60)

onCreate() calls enterImmersiveMode() (which calls getWindow().getInsetsController())
before setContentView() runs. On this OEM's Android 13 build, calling
getInsetsController() before the window has a decor view attached throws
internally, even though it's tolerated on other devices. The fix is to
call enterImmersiveMode() after setContentView() instead of before -
nothing else in onCreate or enterImmersiveMode() changes.

Operates on the smali MainActivity.smali produced by `apktool d`, editing
it in place.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: patch_immersive_mode_order.py MainActivity.smali')

path = Path(sys.argv[1])
text = path.read_text(encoding='utf-8')

block = (
    "    .line 60\n"
    "    invoke-direct {p0}, Lcom/greenman/hedgewitchery/MainActivity;->enterImmersiveMode()V\n"
    "\n"
)
count = text.count(block)
if count != 1:
    raise SystemExit(f'expected exactly one enterImmersiveMode() call before setContentView, found {count}')
text_without_block = text.replace(block, '', 1)

anchor = "    invoke-virtual {p0, v0}, Lcom/greenman/hedgewitchery/MainActivity;->setContentView(Landroid/view/View;)V\n\n"
if text_without_block.count(anchor) != 1:
    raise SystemExit('setContentView(View) anchor in onCreate not found exactly once')
patched = text_without_block.replace(anchor, anchor + block, 1)

if patched == text:
    raise SystemExit('no change applied')

path.write_text(patched, encoding='utf-8')
print('enterImmersiveMode() moved to run after setContentView() in onCreate')
