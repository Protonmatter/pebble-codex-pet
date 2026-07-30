#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path

from PIL import Image, UnidentifiedImageError

FRAME_W = 192
FRAME_H = 208
COLS = 8
ROWS = 11
EXPECTED_SIZE = (FRAME_W * COLS, FRAME_H * ROWS)
MAX_BYTES = 20 * 1024 * 1024
ROW_COUNTS = (7, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8)
ROW_NAMES = (
    "idle",
    "running-right",
    "running-left",
    "waving",
    "jumping",
    "failed",
    "waiting",
    "running",
    "review",
    "look-directions-a",
    "look-directions-b",
)


def fail(message: str) -> None:
    raise SystemExit(f"verify failed: {message}")


def component_count(alpha: Image.Image, threshold: int = 10) -> int:
    width, height = alpha.size
    px = alpha.load()
    seen: set[tuple[int, int]] = set()
    count = 0
    for sy in range(height):
        for sx in range(width):
            if (sx, sy) in seen or px[sx, sy] <= threshold:
                continue
            count += 1
            queue: deque[tuple[int, int]] = deque([(sx, sy)])
            seen.add((sx, sy))
            while queue:
                x, y = queue.popleft()
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in seen and px[nx, ny] > threshold:
                        seen.add((nx, ny))
                        queue.append((nx, ny))
    return count


def frame_hash(frame: Image.Image) -> str:
    return hashlib.sha256(frame.tobytes()).hexdigest()


def verify_pet(pet_dir: Path, report_path: Path | None = None) -> dict[str, object]:
    metadata_path = pet_dir / "pet.json"
    sheet_path = pet_dir / "spritesheet.webp"

    if not metadata_path.exists():
        fail(f"missing {metadata_path}")
    if not sheet_path.exists():
        fail(f"missing {sheet_path}")
    if sheet_path.stat().st_size > MAX_BYTES:
        fail(f"spritesheet exceeds 20 MiB: {sheet_path.stat().st_size} bytes")

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(f"could not read valid UTF-8 JSON from {metadata_path}: {exc}")
    expected_metadata = {
        "id": "pebble-poses",
        "displayName": "Pebble Poses",
        "description": "Pebble, a focused stone companion for Codex activity states.",
        "spriteVersionNumber": 2,
        "spritesheetPath": "spritesheet.webp",
    }
    if metadata != expected_metadata:
        fail(f"pet.json does not match expected metadata: {metadata}")

    try:
        with Image.open(sheet_path) as source:
            detected_format = source.format
            detected_mime = Image.MIME.get(detected_format or "")
            if detected_format != "WEBP" or detected_mime != "image/webp":
                fail(
                    "spritesheet.webp must contain WebP-encoded bytes, "
                    f"got format={detected_format!r} mime={detected_mime!r}"
                )
            if source.size != EXPECTED_SIZE:
                fail(f"spritesheet must be {EXPECTED_SIZE}, got {source.size}")
            if source.mode not in {"RGBA", "LA"}:
                fail(f"spritesheet WebP must support transparency, got mode {source.mode!r}")
            source.load()
            image = source.convert("RGBA")
    except (OSError, UnidentifiedImageError) as exc:
        fail(f"could not decode {sheet_path} as WebP: {exc}")

    raw = image.tobytes()
    residue_pixels = 0
    for index in range(0, len(raw), 4):
        r, g, b, a = raw[index : index + 4]
        if a == 0 and (r or g or b):
            residue_pixels += 1
    if residue_pixels:
        fail(f"found {residue_pixels} fully transparent pixels with non-zero RGB residue")

    rows_report: list[dict[str, object]] = []
    for row_index, (name, used_count) in enumerate(zip(ROW_NAMES, ROW_COUNTS, strict=True)):
        hashes: list[str] = []
        cells: list[dict[str, object]] = []
        for col in range(COLS):
            frame = image.crop(
                (
                    col * FRAME_W,
                    row_index * FRAME_H,
                    (col + 1) * FRAME_W,
                    (row_index + 1) * FRAME_H,
                )
            )
            alpha = frame.getchannel("A")
            bbox = alpha.getbbox()
            if col < used_count:
                if bbox is None:
                    fail(f"row {row_index} {name} column {col} is empty")
                required_padding = 1 if name.startswith("look-directions-") else 2
                if (
                    bbox[0] < required_padding
                    or bbox[1] < required_padding
                    or bbox[2] > FRAME_W - required_padding
                    or bbox[3] > FRAME_H
                ):
                    fail(f"row {row_index} {name} column {col} is clipped or lacks safe padding: {bbox}")
                components = component_count(alpha)
                if components != 1:
                    fail(f"row {row_index} {name} column {col} has {components} disconnected components")
                hashes.append(frame_hash(frame))
                cells.append({"column": col, "bbox": bbox, "components": components, "used": True})
            else:
                if bbox is not None:
                    fail(f"row {row_index} {name} unused column {col} is not transparent")
                cells.append({"column": col, "bbox": None, "components": 0, "used": False})

        unique_frames = len(set(hashes))
        minimum_unique = 4 if name == "idle" else min(used_count, 3)
        if unique_frames < minimum_unique:
            fail(f"row {row_index} {name} has only {unique_frames} distinct frames")
        rows_report.append(
            {
                "index": row_index,
                "name": name,
                "usedColumns": used_count,
                "uniqueFrames": unique_frames,
                "cells": cells,
            }
        )

    report = {
        "ok": True,
        "petDir": str(pet_dir.resolve()),
        "spritesheet": str(sheet_path.resolve()),
        "format": detected_format,
        "mimeType": detected_mime,
        "size": list(image.size),
        "bytes": sheet_path.stat().st_size,
        "transparentRgbResiduePixels": residue_pixels,
        "rows": rows_report,
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {report_path}")
    print("verify ok")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the Pebble Poses runtime package.")
    parser.add_argument(
        "pet_dir",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "pebble-poses",
    )
    parser.add_argument("report_path", nargs="?", type=Path)
    args = parser.parse_args()
    verify_pet(args.pet_dir, args.report_path)


if __name__ == "__main__":
    main()
