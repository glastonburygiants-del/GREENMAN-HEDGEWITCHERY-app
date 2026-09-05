#!/usr/bin/env python3
from pathlib import Path
import sys


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_register_scribe_service.py AndroidManifest.xml")
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8")

    application_anchor = "    <application "
    permissions = "\n".join(
        [
            "    <uses-permission android:name=\"android.permission.FOREGROUND_SERVICE\"/>",
            "    <uses-permission android:name=\"android.permission.FOREGROUND_SERVICE_DATA_SYNC\"/>",
        ]
    ) + "\n    <application "
    if text.count(application_anchor) != 1:
        raise SystemExit(f"application anchor count: {text.count(application_anchor)}")
    text = text.replace(application_anchor, permissions, 1)

    application_end = "    </application>"
    service = """        <service
            android:enabled="true"
            android:exported="false"
            android:foregroundServiceType="dataSync"
            android:name="com.greenman.hedgewitchery.ScribePdfService"
            android:process=":bosrender"/>
    </application>"""
    if text.count(application_end) != 1:
        raise SystemExit(f"application end anchor count: {text.count(application_end)}")
    text = text.replace(application_end, service, 1)

    required = [
        "android.permission.FOREGROUND_SERVICE_DATA_SYNC",
        "com.greenman.hedgewitchery.ScribePdfService",
        'android:process=":bosrender"',
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit("Missing service manifest entries: " + ", ".join(missing))
    path.write_text(text, encoding="utf-8")
    print("Registered isolated BoS PDF renderer service.")


if __name__ == "__main__":
    main()
