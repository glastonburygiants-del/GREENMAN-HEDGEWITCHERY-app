#!/usr/bin/env python3
"""Confirmed via real device logcat on an Acer/Android 13 tablet:

    Caused by: java.lang.NullPointerException: Attempt to invoke virtual
    method 'android.view.WindowInsetsController...' on a null object reference
        at com.android.internal.policy.PhoneWindow.getInsetsController(PhoneWindow.java:3924)
        at com.greenman.hedgewitchery.MainActivity.enterImmersiveMode(MainActivity.java:734)
        at com.greenman.hedgewitchery.MainActivity.onCreate(MainActivity.java:60)

onCreate() called enterImmersiveMode() - which calls
getWindow().getInsetsController() - BEFORE setContentView(). Most devices
tolerate this, but this OEM's PhoneWindow.getInsetsController()
implementation throws internally when called before the window has a decor
view attached. Our own "if (controller != null)" check never gets a chance
to run: the NPE happens inside Android's own getter, before it returns
anything to us.

Not a print or icon bug - this crashed on open regardless of anything else
in the build, which is exactly why removing the icon entirely (a prior
diagnostic build) did not help.

Fix: call enterImmersiveMode() only after setContentView() has run, and
wrap its body in a try/catch as a defensive backstop against this exact
class of OEM windowing quirk recurring elsewhere (onResume,
onWindowFocusChanged already call it too, after the window is long since
attached, so those call sites are unaffected but get the same safety net).
"""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit('usage: repair_immersive_mode_crash.py INPUT OUTPUT')

src = Path(sys.argv[1])
out = Path(sys.argv[2])
s = src.read_text(encoding='utf-8')

# 1. Move the first-call site: enterImmersiveMode() must run after setContentView().
old_oncreate = '''    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        enterImmersiveMode();

        root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(42, 26, 8));
        setContentView(root);
'''
new_oncreate = '''    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);

        root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(42, 26, 8));
        setContentView(root);
        enterImmersiveMode();
'''
count = s.count(old_oncreate)
if count != 1:
    raise SystemExit(f'onCreate anchor count was {count}, expected 1')
s = s.replace(old_oncreate, new_oncreate, 1)

# 2. Defensive try/catch around the whole method body, so any future OEM
# windowing quirk here degrades to "no immersive mode" instead of a crash.
old_method = '''    private void enterImmersiveMode() {
        if (android.os.Build.VERSION.SDK_INT >= 30) {
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.hide(WindowInsets.Type.statusBars() | WindowInsets.Type.navigationBars());
                controller.setSystemBarsBehavior(
                        WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
            }
        } else {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                            | View.SYSTEM_UI_FLAG_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
        }
    }'''
new_method = '''    private void enterImmersiveMode() {
        try {
            if (android.os.Build.VERSION.SDK_INT >= 30) {
                WindowInsetsController controller = getWindow().getInsetsController();
                if (controller != null) {
                    controller.hide(WindowInsets.Type.statusBars() | WindowInsets.Type.navigationBars());
                    controller.setSystemBarsBehavior(
                            WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
                }
            } else {
                getWindow().getDecorView().setSystemUiVisibility(
                        View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                                | View.SYSTEM_UI_FLAG_FULLSCREEN
                                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
            }
        } catch (Exception immersiveError) {
            // Some OEM PhoneWindow implementations throw internally here (confirmed
            // on an Acer/Android 13 device via getInsetsController()). Losing the
            // immersive status/nav bar hide is acceptable; crashing the app is not.
        }
    }'''
count2 = s.count(old_method)
if count2 != 1:
    raise SystemExit(f'enterImmersiveMode anchor count was {count2}, expected 1')
s = s.replace(old_method, new_method, 1)

if 'enterImmersiveMode();\n\n        root = new FrameLayout' in s:
    raise SystemExit('enterImmersiveMode still called before setContentView')
if 'setContentView(root);\n        enterImmersiveMode();' not in s:
    raise SystemExit('enterImmersiveMode is not called right after setContentView')
if 'private void enterImmersiveMode() {\n        try {' not in s:
    raise SystemExit('defensive try/catch missing from enterImmersiveMode')

out.write_text(s, encoding='utf-8')
print('enterImmersiveMode() moved to run after setContentView(), and wrapped defensively')
