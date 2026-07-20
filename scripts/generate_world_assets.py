"""Process Phase 1 world plates into content-hashed WebPs + digest manifest.

Reads raw generated plates from .handoff/phase1-plates/ (local-only art
staging, gitignored — the shipped artifacts below are the source of truth,
hash-verified by the manifest and tests/test_world_assets.py).

Outputs to app/static/img/world/ as <name>-<width>.<sha10>.webp, where <sha10>
is the first 10 hex chars of the sha256 of the output bytes. The full digests
land in app/static/img/world/manifest.json. World assets are immutable and
exempt from the ?v= lockstep by design (see docs/2026-07-20-phase1-forest-world.md).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / ".handoff" / "phase1-plates"
OUT_DIR = ROOT / "app" / "static" / "img" / "world"

# (source name, widths, quality, top_crop_fraction or None)
PLATES = (
    ("clearing", (1376, 760), 32, None),
    ("waypoints", (1376, 760), 32, None),
    ("grove", (1376, 760), 32, None),
    ("overlook", (1376, 760), 40, None),
    ("dusk-treeline", (1376, 760), 32, None),
    ("stage-tools", (1376, 760), 32, None),
    ("canopy-edge", (1376,), 32, 0.45),
    ("fern-corner-left", (640,), 32, None),
    ("fern-corner-right", (640,), 32, None),
    ("owl", (320,), 40, None),
    ("leaves", (320,), 40, None),
    ("glyph-sheet", (960,), 80, None),
)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for stale in OUT_DIR.glob("*.webp"):
        stale.unlink()
    manifest: dict[str, str] = {}
    for name, widths, quality, top_crop in PLATES:
        source = SOURCE_DIR / f"{name}.png"
        with Image.open(source) as image:
            image = image.convert("RGB")
            if top_crop is not None:
                image = image.crop((0, 0, image.width, round(image.height * top_crop)))
            for width in widths:
                if width < image.width:
                    height = round(image.height * (width / image.width))
                    resized = image.resize((width, height), Image.Resampling.LANCZOS)
                else:
                    resized = image
                tmp = OUT_DIR / f"{name}-{width}.tmp.webp"
                resized.save(tmp, "WEBP", quality=quality, method=6)
                digest = hashlib.sha256(tmp.read_bytes()).hexdigest()
                final = OUT_DIR / f"{name}-{width}.{digest[:10]}.webp"
                tmp.rename(final)
                manifest[final.name] = digest
                print(f"{final.relative_to(ROOT)} {resized.width}x{resized.height} {final.stat().st_size} bytes")
    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{manifest_path.relative_to(ROOT)} ({len(manifest)} entries)")


if __name__ == "__main__":
    main()
