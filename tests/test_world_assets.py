"""World-asset integrity: manifest digests match bytes on disk (Phase 1 Stage 0).

World assets are content-hashed and immutable (exempt from the ?v= lockstep);
this test is the guarantee that a filename's hash segment can be trusted.
See docs/2026-07-20-phase1-forest-world.md.
"""

import hashlib
import json
from pathlib import Path

WORLD_DIR = Path(__file__).resolve().parents[1] / "app" / "static" / "img" / "world"
MANIFEST = WORLD_DIR / "manifest.json"


def test_manifest_exists_and_covers_every_world_asset():
    assert MANIFEST.is_file(), "world manifest missing"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    on_disk = {p.name for p in WORLD_DIR.glob("*.webp")}
    assert on_disk == set(manifest), (
        "world dir and manifest disagree: "
        f"unlisted={sorted(on_disk - set(manifest))} missing={sorted(set(manifest) - on_disk)}"
    )


def test_every_world_asset_digest_matches_manifest_and_filename():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest, "world manifest is empty"
    for name, digest in manifest.items():
        path = WORLD_DIR / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == digest, f"{name}: bytes do not match manifest digest"
        stem_hash = name.rsplit(".", 2)[-2]
        assert digest.startswith(stem_hash), f"{name}: filename hash segment does not match digest"
