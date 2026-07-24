#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PET_DIR = ROOT / "pebble-poses"
VERIFY = ROOT / "scripts" / "verify_pebble_pose_pet.py"
RUNTIME_ZIP = DIST / "pebble-poses-runtime.zip"
SOURCE_ZIP = DIST / "pebble-poses-source.zip"
CHECKSUMS = DIST / "SHA256SUMS"

EXCLUDED_DIRS = {".git", "dist", "build", "__pycache__", ".pytest_cache", ".mypy_cache"}
EXCLUDED_FILES = {".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
# Machine-generated report with host-specific paths; regenerated per run.
EXCLUDED_RELATIVE = {Path("qa/validation.json")}


def should_include(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if relative in EXCLUDED_RELATIVE:
        return False
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False
    if path.name in EXCLUDED_FILES or path.suffix in EXCLUDED_SUFFIXES:
        return False
    return path.is_file()


def add_file(archive: zipfile.ZipFile, path: Path, arcname: str) -> None:
    archive.write(path, arcname=arcname, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    subprocess.run(
        [sys.executable, str(VERIFY), str(PET_DIR), str(ROOT / "qa" / "validation.json")],
        check=True,
    )

    DIST.mkdir(parents=True, exist_ok=True)
    for archive in (RUNTIME_ZIP, SOURCE_ZIP):
        archive.unlink(missing_ok=True)

    with zipfile.ZipFile(RUNTIME_ZIP, "w") as archive:
        add_file(archive, PET_DIR / "pet.json", "pebble-poses/pet.json")
        add_file(archive, PET_DIR / "spritesheet.png", "pebble-poses/spritesheet.png")

    with zipfile.ZipFile(SOURCE_ZIP, "w") as archive:
        for path in sorted(ROOT.rglob("*")):
            if should_include(path):
                add_file(archive, path, path.relative_to(ROOT).as_posix())

    CHECKSUMS.write_text(
        "\n".join(f"{sha256(path)}  {path.name}" for path in (RUNTIME_ZIP, SOURCE_ZIP)) + "\n"
    )

    print(f"wrote {RUNTIME_ZIP}")
    print(f"wrote {SOURCE_ZIP}")
    print(f"wrote {CHECKSUMS}")


if __name__ == "__main__":
    main()
