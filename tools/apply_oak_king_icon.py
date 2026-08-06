#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw

EXPECTED_SOURCE_SHA256 = "32f41e65400142672a1f3dd16399a4494e30608d1e571e7a293143d7dc3ee6ed"
DEEP_GREEN = (20, 69, 31, 255)
EDGE_GREEN = (45, 112, 58, 255)


def write_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, "PNG", optimize=True)


def rounded_icon(shield: Image.Image, size: int) -> Image.Image:
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    background = Image.new("RGBA", (size, size), DEEP_GREEN)
    radius = round(size * 0.22)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)

    max_height = round(size * 0.88)
    max_width = round(size * 0.76)
    scale = min(max_width / shield.width, max_height / shield.height)
    art = shield.resize(
        (round(shield.width * scale), round(shield.height * scale)),
        Image.Resampling.LANCZOS,
    )
    x = (size - art.width) // 2
    y = (size - art.height) // 2
    background.alpha_composite(art, (x, y))

    edge = ImageDraw.Draw(background)
    edge.rounded_rectangle(
        (2, 2, size - 3, size - 3),
        radius=max(1, radius - 2),
        outline=EDGE_GREEN,
        width=max(1, round(size * 0.012)),
    )
    icon.paste(background, (0, 0), mask)
    return icon


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: apply_oak_king_icon.py PROJECT_DIR")

    project = Path(sys.argv[1]).resolve()
    res = project / "app" / "src" / "main" / "res"
    if not res.is_dir():
        raise SystemExit(f"Android resource directory not found: {res}")

    tool_dir = Path(__file__).resolve().parent
    encoded = "".join(
        (tool_dir / f"oak_king_icon_source.part{index:02d}.b64").read_text(encoding="ascii").strip()
        for index in range(1, 4)
    )
    source_bytes = base64.b64decode(encoded)
    actual_sha = hashlib.sha256(source_bytes).hexdigest()
    if actual_sha != EXPECTED_SOURCE_SHA256:
        raise SystemExit(f"Oak King source checksum mismatch: {actual_sha}")

    shield = Image.open(io.BytesIO(source_bytes)).convert("RGBA")

    for old in (
        res / "drawable" / "ic_launcher_foreground.xml",
        res / "mipmap-anydpi" / "ic_launcher.xml",
        res / "mipmap-anydpi" / "ic_launcher_round.xml",
    ):
        if old.exists():
            old.unlink()

    master = rounded_icon(shield, 1024)
    density_sizes = {
        "mdpi": 48,
        "hdpi": 72,
        "xhdpi": 96,
        "xxhdpi": 144,
        "xxxhdpi": 192,
    }
    outputs: list[Path] = []
    for density, size in density_sizes.items():
        image = master.resize((size, size), Image.Resampling.LANCZOS)
        target = res / f"mipmap-{density}"
        for name in ("ic_launcher.png", "ic_launcher_round.png"):
            path = target / name
            write_png(image, path)
            outputs.append(path)

    adaptive = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    inset = master.resize((360, 360), Image.Resampling.LANCZOS)
    adaptive.alpha_composite(inset, (36, 36))
    foreground = res / "drawable-nodpi" / "ic_launcher_foreground.png"
    write_png(adaptive, foreground)
    outputs.append(foreground)

    missing = [str(path) for path in outputs if not path.is_file() or path.stat().st_size < 500]
    if missing:
        raise SystemExit("Oak King icon output failed: " + ", ".join(missing))

    print(f"Oak King launcher installed from exact supplied carving: {shield.width}x{shield.height}")
    print(f"Source SHA-256: {actual_sha}")
    for path in outputs:
        print(f"{path.relative_to(project)} {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
