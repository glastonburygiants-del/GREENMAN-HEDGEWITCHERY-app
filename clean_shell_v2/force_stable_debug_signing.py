#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit('usage: force_stable_debug_signing.py APP_BUILD_GRADLE')

p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
marker = '// GREENMAN_STABLE_DEBUG_SIGNING_V1'
if marker in s:
    print('Stable Greenman debug signing already configured')
    raise SystemExit(0)

block = r'''

// GREENMAN_STABLE_DEBUG_SIGNING_V1
// Keep every test APK on one certificate so Android can accept later updates.
android {
    signingConfigs {
        debug {
            storeFile file(System.getenv('HOME') + '/.android/debug.keystore')
            storePassword 'android'
            keyAlias 'androiddebugkey'
            keyPassword 'android'
        }
    }
    buildTypes {
        debug {
            signingConfig signingConfigs.debug
        }
    }
}
'''
p.write_text(s + block, encoding='utf-8')
print('Forced stable Greenman debug signing configuration')
