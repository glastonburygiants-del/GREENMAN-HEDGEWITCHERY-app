#!/usr/bin/env python3
"""Android 13+ tablets (e.g. Acer, API 31+) crash right after the splash
screen with a static app icon in the middle of a green background - that
screen and its handoff are governed by values-v31/styles.xml, which only
applies on API 31+.

android:windowSplashScreenAnimatedIcon was set to @drawable/ic_launcher_foreground,
an ordinary <inset> wrapping a static WebP bitmap - not an AnimatedVectorDrawable.
The Splash Screen API (API 31+) expects that attribute to be something it can
treat as animatable; different OEM Android builds enforce this with different
strictness, so a static bitmap there can crash on some vendor skins while
working fine on others (or on phones running an older Android version that
never hits values-v31 at all) - matching "works on phone, crashes on this
tablet" exactly.

Drops windowSplashScreenAnimatedIcon, its paired IconBackgroundColor, and the
now-meaningless AnimationDuration, so Android 12+/13+ falls back to its normal
default splash behaviour (still using the app's real launcher icon via the
manifest) instead of trying to animate a drawable that was never built to be
animated. windowSplashScreenBackground (a plain colour, not the icon) is kept.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: repair_splash_screen_icon.py ANDROID_PROJECT_DIR')

project = Path(sys.argv[1])
styles = project / 'app/src/main/res/values-v31/styles.xml'
text = styles.read_text(encoding='utf-8')

doomed_lines = [
    '        <item name="android:windowSplashScreenAnimatedIcon">@drawable/ic_launcher_foreground</item>\n',
    '        <item name="android:windowSplashScreenIconBackgroundColor">@color/greenman_deep_green</item>\n',
    '        <item name="android:windowSplashScreenAnimationDuration">250</item>\n',
]

for line in doomed_lines:
    count = text.count(line)
    if count != 1:
        raise SystemExit(f'expected exactly one occurrence of {line.strip()!r}, found {count}')
    text = text.replace(line, '', 1)

if 'windowSplashScreenAnimatedIcon' in text:
    raise SystemExit('windowSplashScreenAnimatedIcon survived removal')
if 'windowSplashScreenIconBackgroundColor' in text:
    raise SystemExit('windowSplashScreenIconBackgroundColor survived removal')
if 'windowSplashScreenAnimationDuration' in text:
    raise SystemExit('windowSplashScreenAnimationDuration survived removal')
if 'android:windowSplashScreenBackground' not in text:
    raise SystemExit('windowSplashScreenBackground (a plain colour, meant to stay) is missing')

styles.write_text(text, encoding='utf-8')
print('Removed windowSplashScreenAnimatedIcon/IconBackgroundColor/AnimationDuration from values-v31/styles.xml')
print('Static bitmap drawable is no longer used as an animatable splash icon; splash background colour retained')
