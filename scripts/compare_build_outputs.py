#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageSequence

STATIC_IMAGE_PATHS = (
    "pebble-poses/spritesheet.png",
    "pebble-poses/spritesheet.webp",
    "preview/pebble-poses-contact-sheet.png",
)
JSON_PATHS = (
    "pebble-poses/pet.json",
    "docs/animation-map.json",
)
GIF_PATHS = (
    "preview/pebble-poses-animation-preview.gif",
    "preview/rows/00-idle.gif",
    "preview/rows/01-running-right.gif",
    "preview/rows/02-running-left.gif",
    "preview/rows/03-waving.gif",
    "preview/rows/04-jumping.gif",
    "preview/rows/05-failed.gif",
    "preview/rows/06-waiting.gif",
    "preview/rows/07-running.gif",
    "preview/rows/08-review.gif",
    "preview/rows/09-look-directions-a.gif",
    "preview/rows/10-look-directions-b.gif",
)


def fail(message: str) -> None:
    raise SystemExit(f"compare failed: {message}")


def compare_json(expected: Path, actual: Path) -> None:
    try:
        expected_data = json.loads(expected.read_text(encoding="utf-8"))
        actual_data = json.loads(actual.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"could not read JSON: {exc}")
    if expected_data != actual_data:
        fail(f"JSON differs: {expected} != {actual}")


def compare_image(expected: Path, actual: Path) -> None:
    with Image.open(expected) as expected_image, Image.open(actual) as actual_image:
        expected_rgba = expected_image.convert("RGBA")
        actual_rgba = actual_image.convert("RGBA")
        if expected_rgba.size != actual_rgba.size:
            fail(f"image dimensions differ: {expected} != {actual}")
        if expected_rgba.tobytes() != actual_rgba.tobytes():
            fail(f"decoded image pixels differ: {expected} != {actual}")


def gif_signature(path: Path) -> tuple[object, ...]:
    with Image.open(path) as image:
        frames: list[tuple[tuple[int, int], int, bytes]] = []
        for frame in ImageSequence.Iterator(image):
            rgba = frame.convert("RGBA")
            frames.append((rgba.size, int(frame.info.get("duration", 0)), rgba.tobytes()))
        return (int(image.info.get("loop", 0)), tuple(frames))


def compare_gif(expected: Path, actual: Path) -> None:
    if gif_signature(expected) != gif_signature(actual):
        fail(f"decoded GIF frames or timing differ: {expected} != {actual}")


def require_files(root: Path, paths: tuple[str, ...]) -> None:
    for relative in paths:
        if not (root / relative).is_file():
            fail(f"missing {root / relative}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare committed and rebuilt pet artifacts semantically."
    )
    parser.add_argument("expected_root", type=Path)
    parser.add_argument("actual_root", type=Path)
    args = parser.parse_args()

    pose_paths = tuple(
        path.relative_to(args.expected_root).as_posix()
        for path in sorted((args.expected_root / "source" / "poses").glob("*.png"))
    )
    if not pose_paths:
        fail("expected root has no source pose PNG files")

    all_paths = JSON_PATHS + STATIC_IMAGE_PATHS + GIF_PATHS + pose_paths
    require_files(args.expected_root, all_paths)
    require_files(args.actual_root, all_paths)

    for relative in JSON_PATHS:
        compare_json(args.expected_root / relative, args.actual_root / relative)
    for relative in STATIC_IMAGE_PATHS + pose_paths:
        compare_image(args.expected_root / relative, args.actual_root / relative)
    for relative in GIF_PATHS:
        compare_gif(args.expected_root / relative, args.actual_root / relative)

    print(f"compare ok: {len(all_paths)} generated artifacts are semantically identical")


if __name__ == "__main__":
    main()
