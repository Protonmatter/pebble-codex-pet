#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

FRAME_W = 192
FRAME_H = 208
COLS = 8
ROWS = 9
SHEET_W = FRAME_W * COLS
SHEET_H = FRAME_H * ROWS

PET_ID = "pebble-poses"
DISPLAY_NAME = "Pebble Poses"
DESCRIPTION = "Pebble, a focused stone companion for Codex activity states."

POSE_NAMES = [
    "idle_neutral",
    "look_up",
    "alert",
    "sitting_shell",
    "wave_start",
    "wave_mid",
    "inspect",
    "build",
    "push",
    "review",
    "success_excited",
    "success_settle",
    "confused",
    "head_down",
    "disapprove",
    "sleepy",
    "tucked_shell",
    "peek",
]

# Source sheet layout for Photo 2: 6 columns x 3 rows.
CELL_X = [0, 213, 426, 640, 853, 1066, 1280]
ROW_Y = [(85, 276), (318, 560), (618, 825)]


@dataclass(frozen=True)
class FrameSpec:
    pose: int
    dx: float = 0.0
    dy: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotate: float = 0.0
    mirror: bool = False


@dataclass(frozen=True)
class AnimationRow:
    key: str
    purpose: str
    durations_ms: tuple[int, ...]
    frames: tuple[FrameSpec, ...]


# Current Codex V1 atlas contract: rows and used columns are fixed. Unused
# cells are intentionally left transparent.
ANIMATION_ROWS: tuple[AnimationRow, ...] = (
    AnimationRow(
        "idle",
        "Calm, low-distraction breathing and a brief curious glance.",
        (280, 110, 110, 140, 140, 320),
        (
            FrameSpec(1, scale_y=0.996),
            FrameSpec(1, dy=-0.4, scale_x=1.002, scale_y=1.004),
            FrameSpec(1, dy=-0.8, scale_x=1.004, scale_y=1.010),
            FrameSpec(1, dy=-0.4, scale_x=1.002, scale_y=1.004),
            FrameSpec(2, dy=-0.5),
            FrameSpec(1, scale_y=0.996),
        ),
    ),
    AnimationRow(
        "running-right",
        "Directional shell-roll locomotion toward the right.",
        (120, 120, 120, 120, 120, 120, 120, 220),
        (
            FrameSpec(17, dx=-4.0, dy=0.8, rotate=-5.0, mirror=True),
            FrameSpec(17, dx=-2.0, dy=0.2, rotate=-2.5, mirror=True),
            FrameSpec(18, dx=-0.5, dy=-0.5, rotate=-1.0, mirror=True),
            FrameSpec(17, dx=1.0, dy=-0.2, rotate=1.5, mirror=True),
            FrameSpec(17, dx=2.5, dy=0.4, rotate=4.0, mirror=True),
            FrameSpec(18, dx=4.0, dy=-0.8, rotate=2.0, mirror=True),
            FrameSpec(17, dx=5.0, dy=0.0, rotate=6.0, mirror=True),
            FrameSpec(18, dx=6.0, dy=-0.4, rotate=3.0, mirror=True),
        ),
    ),
    AnimationRow(
        "running-left",
        "Directional shell-roll locomotion toward the left.",
        (120, 120, 120, 120, 120, 120, 120, 220),
        (
            FrameSpec(17, dx=4.0, dy=0.8, rotate=5.0),
            FrameSpec(17, dx=2.0, dy=0.2, rotate=2.5),
            FrameSpec(18, dx=0.5, dy=-0.5, rotate=1.0),
            FrameSpec(17, dx=-1.0, dy=-0.2, rotate=-1.5),
            FrameSpec(17, dx=-2.5, dy=0.4, rotate=-4.0),
            FrameSpec(18, dx=-4.0, dy=-0.8, rotate=-2.0),
            FrameSpec(17, dx=-5.0, dy=0.0, rotate=-6.0),
            FrameSpec(18, dx=-6.0, dy=-0.4, rotate=-3.0),
        ),
    ),
    AnimationRow(
        "waving",
        "Greeting with a clear raise, wave, and return.",
        (140, 140, 140, 280),
        (
            FrameSpec(1),
            FrameSpec(5, dy=-0.7),
            FrameSpec(6, dx=0.8, dy=-2.0, rotate=0.3),
            FrameSpec(5, dy=-0.4),
        ),
    ),
    AnimationRow(
        "jumping",
        "Anticipation, lift, peak, descent, and settle.",
        (140, 140, 140, 140, 280),
        (
            FrameSpec(12, dy=1.0, scale_x=1.01, scale_y=0.985),
            FrameSpec(11, dy=-3.0, scale_x=1.004, scale_y=1.005),
            FrameSpec(11, dy=-8.0, scale_x=1.012, scale_y=1.012),
            FrameSpec(11, dy=-3.5, scale_x=1.004, scale_y=1.005),
            FrameSpec(12, dy=0.5, scale_x=1.005, scale_y=0.992),
        ),
    ),
    AnimationRow(
        "failed",
        "Readable confused, deflated, and head-down failure reaction.",
        (140, 140, 140, 140, 140, 140, 140, 240),
        (
            FrameSpec(10),
            FrameSpec(13, dy=-0.5),
            FrameSpec(15, dx=-0.4),
            FrameSpec(14, dy=0.5),
            FrameSpec(16, dy=0.8),
            FrameSpec(14, dy=0.7),
            FrameSpec(15, dx=0.3),
            FrameSpec(10),
        ),
    ),
    AnimationRow(
        "waiting",
        "Expectant asking pose for approval, help, or user input.",
        (150, 150, 150, 150, 150, 260),
        (
            FrameSpec(1),
            FrameSpec(2, dy=-0.6),
            FrameSpec(7, dx=-0.6),
            FrameSpec(7, dx=0.4, dy=-0.4),
            FrameSpec(13, dy=-0.4),
            FrameSpec(1),
        ),
    ),
    AnimationRow(
        "running",
        "Focused processing, inspecting, building, and active work.",
        (120, 120, 120, 120, 120, 220),
        (
            FrameSpec(7, dx=-0.5),
            FrameSpec(8, dx=0.2, dy=-0.6),
            FrameSpec(8, dx=0.9, dy=-1.0, scale_y=1.004),
            FrameSpec(9, dx=-1.0, dy=-0.3),
            FrameSpec(10, dx=0.4),
            FrameSpec(7),
        ),
    ),
    AnimationRow(
        "review",
        "Focused inspection, thought, decision, and return.",
        (150, 150, 150, 150, 150, 280),
        (
            FrameSpec(10),
            FrameSpec(7, dx=-0.5),
            FrameSpec(2, dy=-0.6),
            FrameSpec(13, dy=-0.5),
            FrameSpec(15, dx=-0.3),
            FrameSpec(10),
        ),
    ),
)


@dataclass
class Pose:
    image: Image.Image
    bbox: tuple[int, int, int, int]


def is_background(pixel: tuple[int, int, int]) -> bool:
    r, g, b = pixel
    return r > 236 and g > 236 and b > 236 and max(r, g, b) - min(r, g, b) < 28


def flood_background_alpha(image: Image.Image) -> Image.Image:
    """Remove connected near-white background without erasing shell highlights."""
    rgb = image.convert("RGB")
    width, height = rgb.size
    bg = Image.new("L", (width, height), 0)
    bg_px = bg.load()
    rgb_px = rgb.load()
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if x < 0 or y < 0 or x >= width or y >= height:
            continue
        if bg_px[x, y] or not is_background(rgb_px[x, y]):
            continue
        bg_px[x, y] = 255
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    alpha = bg.point(lambda p: 0 if p else 255).filter(ImageFilter.GaussianBlur(0.35))
    rgba = image.convert("RGBA")
    rgba.putalpha(alpha)
    return rgba


def alpha_components(alpha: Image.Image, threshold: int = 10) -> list[dict[str, object]]:
    width, height = alpha.size
    px = alpha.load()
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, object]] = []

    for sy in range(height):
        for sx in range(width):
            if (sx, sy) in seen or px[sx, sy] <= threshold:
                continue
            queue: deque[tuple[int, int]] = deque([(sx, sy)])
            seen.add((sx, sy))
            points: list[tuple[int, int]] = []
            x0 = x1 = sx
            y0 = y1 = sy
            while queue:
                x, y = queue.popleft()
                points.append((x, y))
                x0, x1 = min(x0, x), max(x1, x)
                y0, y1 = min(y0, y), max(y1, y)
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in seen and px[nx, ny] > threshold:
                        seen.add((nx, ny))
                        queue.append((nx, ny))
            components.append({"points": points, "bbox": (x0, y0, x1 + 1, y1 + 1), "area": len(points)})
    return components




def remove_floor_artifacts(image: Image.Image) -> Image.Image:
    """Remove pale source-sheet floor/shadow residue near the sprite baseline."""
    rgba = image.convert("RGBA")
    px = rgba.load()
    start_y = int(rgba.height * 0.68)
    for y in range(start_y, rgba.height):
        for x in range(rgba.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            saturation = max(r, g, b) - min(r, g, b)
            brightness = (r + g + b) / 3
            if saturation < 22 and brightness > 105:
                px[x, y] = (0, 0, 0, 0)
    return normalize_transparent_pixels(rgba)

def keep_primary_component(image: Image.Image) -> Image.Image:
    """Keep one connected sprite component; remove labels and detached effects."""
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    components = alpha_components(alpha)
    if not components:
        return rgba
    main = max(components, key=lambda c: int(c["area"]))
    mask = Image.new("L", rgba.size, 0)
    mask_px = mask.load()
    for x, y in main["points"]:
        mask_px[x, y] = alpha.getpixel((x, y))
    cleaned = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    cleaned.paste(rgba, mask=mask)
    cleaned = remove_floor_artifacts(cleaned)

    # Floor cleanup may disconnect tiny residue; keep the primary component again.
    components = alpha_components(cleaned.getchannel("A"))
    if components:
        main = max(components, key=lambda c: int(c["area"]))
        final_mask = Image.new("L", cleaned.size, 0)
        final_px = final_mask.load()
        alpha2 = cleaned.getchannel("A")
        for x, y in main["points"]:
            final_px[x, y] = alpha2.getpixel((x, y))
        final = Image.new("RGBA", cleaned.size, (0, 0, 0, 0))
        final.paste(cleaned, mask=final_mask)
        cleaned = final
    return normalize_transparent_pixels(cleaned)


def remove_tiny_components(image: Image.Image, min_area: int = 64) -> Image.Image:
    """Remove isolated antialias fragments that are too small to be sprite content."""
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    px = rgba.load()
    for component in alpha_components(alpha, threshold=10):
        if int(component["area"]) >= min_area:
            continue
        for x, y in component["points"]:
            px[x, y] = (0, 0, 0, 0)
    return normalize_transparent_pixels(rgba)


def normalize_transparent_pixels(image: Image.Image) -> Image.Image:
    """Zero RGB channels wherever alpha is zero."""
    rgba = image.convert("RGBA")
    data = bytearray(rgba.tobytes())
    for index in range(0, len(data), 4):
        if data[index + 3] == 0:
            data[index] = data[index + 1] = data[index + 2] = 0
    return Image.frombytes("RGBA", rgba.size, bytes(data))


def crop_pose(sheet: Image.Image, pose_index: int) -> Pose:
    idx = pose_index - 1
    row = idx // 6
    col = idx % 6
    x0, x1 = CELL_X[col], CELL_X[col + 1]
    y0, y1 = ROW_Y[row]
    crop = sheet.crop((x0, y0, x1, y1))
    rgba = keep_primary_component(flood_background_alpha(crop))
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError(f"pose {pose_index} has no extracted foreground")
    margin = 4
    bbox = (
        max(0, bbox[0] - margin),
        max(0, bbox[1] - margin),
        min(rgba.width, bbox[2] + margin),
        min(rgba.height, bbox[3] + margin),
    )
    image = rgba.crop(bbox)
    image_bbox = image.getchannel("A").getbbox()
    assert image_bbox is not None
    return Pose(image=image, bbox=image_bbox)


def transform_pose(pose: Pose, spec: FrameSpec) -> Image.Image:
    image = ImageOps.mirror(pose.image) if spec.mirror else pose.image
    base_w = pose.bbox[2] - pose.bbox[0]
    base_h = pose.bbox[3] - pose.bbox[1]
    base_scale = min(176 / base_w, 176 / base_h, 1.08)
    new_size = (
        max(1, round(image.width * base_scale * spec.scale_x)),
        max(1, round(image.height * base_scale * spec.scale_y)),
    )
    transformed = image.resize(new_size, Image.Resampling.LANCZOS)
    if spec.rotate:
        transformed = transformed.rotate(spec.rotate, resample=Image.Resampling.BICUBIC, expand=True)
    return normalize_transparent_pixels(transformed)


def render_frame(pose: Pose, spec: FrameSpec) -> Image.Image:
    sprite = transform_pose(pose, spec)
    bbox = sprite.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("transformed pose has no visible pixels")
    x0, y0, x1, y1 = bbox
    center_x = (x0 + x1) / 2
    x = round(FRAME_W / 2 + spec.dx - center_x)
    y = round(FRAME_H - 9 + spec.dy - y1)

    frame = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    frame.alpha_composite(sprite, (x, y))
    bbox = frame.getchannel("A").getbbox()
    if bbox is not None:
        shift_x = 0
        shift_y = 0
        if bbox[0] < 3:
            shift_x = 3 - bbox[0]
        elif bbox[2] > FRAME_W - 3:
            shift_x = FRAME_W - 3 - bbox[2]
        if bbox[1] < 3:
            shift_y = 3 - bbox[1]
        if shift_x or shift_y:
            shifted = Image.new("RGBA", frame.size, (0, 0, 0, 0))
            shifted.alpha_composite(frame, (shift_x, shift_y))
            frame = shifted
    frame = keep_primary_component(frame)
    frame = remove_tiny_components(frame)
    return normalize_transparent_pixels(frame)


def build_sheet(poses: list[Pose]) -> Image.Image:
    sheet = Image.new("RGBA", (SHEET_W, SHEET_H), (0, 0, 0, 0))
    for row_index, row in enumerate(ANIMATION_ROWS):
        if len(row.frames) != len(row.durations_ms):
            raise ValueError(f"row {row.key} frame/duration count mismatch")
        if len(row.frames) > COLS:
            raise ValueError(f"row {row.key} exceeds {COLS} columns")
        for col, spec in enumerate(row.frames):
            frame = render_frame(poses[spec.pose - 1], spec)
            sheet.alpha_composite(frame, (col * FRAME_W, row_index * FRAME_H))
    return normalize_transparent_pixels(sheet)


def preview_frame(frame: Image.Image, background: tuple[int, int, int] = (44, 44, 42)) -> Image.Image:
    rendered = Image.new("RGB", frame.size, background)
    rendered.paste(frame, mask=frame.getchannel("A"))
    return rendered


def make_contact_sheet(sheet: Image.Image, path: Path) -> None:
    preview = preview_frame(sheet)
    preview.thumbnail((960, 1170), Image.Resampling.LANCZOS)
    preview.save(path)


def make_animation_previews(sheet: Image.Image, output_gif: Path, rows_dir: Path) -> None:
    rows_dir.mkdir(parents=True, exist_ok=True)
    combined: list[Image.Image] = []
    combined_durations: list[int] = []
    for row_index, row in enumerate(ANIMATION_ROWS):
        frames: list[Image.Image] = []
        for col in range(len(row.frames)):
            frame = sheet.crop((col * FRAME_W, row_index * FRAME_H, (col + 1) * FRAME_W, (row_index + 1) * FRAME_H))
            rendered = preview_frame(frame).resize((288, 312), Image.Resampling.LANCZOS)
            frames.append(rendered)
            combined.append(rendered)
        combined_durations.extend(row.durations_ms)
        frames[0].save(
            rows_dir / f"{row_index:02d}-{row.key}.gif",
            save_all=True,
            append_images=frames[1:],
            duration=list(row.durations_ms),
            loop=0,
            optimize=False,
        )

    combined[0].save(
        output_gif,
        save_all=True,
        append_images=combined[1:],
        duration=combined_durations,
        loop=0,
        optimize=False,
    )


def write_pet_json(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "id": PET_ID,
                "displayName": DISPLAY_NAME,
                "description": DESCRIPTION,
                "spritesheetPath": "spritesheet.png",
            },
            indent=2,
        )
        + "\n"
    )


def write_animation_map(path: Path) -> None:
    data = {
        "contract": "Codex custom pet V1",
        "frameSize": {"width": FRAME_W, "height": FRAME_H},
        "grid": {"columns": COLS, "rows": ROWS},
        "poseNames": {str(i): name for i, name in enumerate(POSE_NAMES, start=1)},
        "rows": [
            {
                "index": index,
                "key": row.key,
                "purpose": row.purpose,
                "usedColumns": f"0-{len(row.frames) - 1}",
                "durationsMs": list(row.durations_ms),
                "frames": [asdict(frame) | {"poseName": POSE_NAMES[frame.pose - 1]} for frame in row.frames],
            }
            for index, row in enumerate(ANIMATION_ROWS)
        ],
    }
    path.write_text(json.dumps(data, indent=2) + "\n")


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Build the Codex-compatible Pebble pet atlas.")
    parser.add_argument(
        "--source",
        type=Path,
        default=project_root / "source" / "photo-2-clean-sprite-art-pass.jpg",
    )
    parser.add_argument("--out-dir", type=Path, default=project_root / "pebble-poses")
    parser.add_argument("--poses-dir", type=Path, default=project_root / "source" / "poses")
    parser.add_argument(
        "--contact-sheet",
        type=Path,
        default=project_root / "preview" / "pebble-poses-contact-sheet.png",
    )
    parser.add_argument(
        "--gif",
        type=Path,
        default=project_root / "preview" / "pebble-poses-animation-preview.gif",
    )
    parser.add_argument("--rows-dir", type=Path, default=project_root / "preview" / "rows")
    parser.add_argument(
        "--animation-map",
        type=Path,
        default=project_root / "docs" / "animation-map.json",
    )
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.poses_dir.mkdir(parents=True, exist_ok=True)
    args.contact_sheet.parent.mkdir(parents=True, exist_ok=True)
    args.gif.parent.mkdir(parents=True, exist_ok=True)
    args.animation_map.parent.mkdir(parents=True, exist_ok=True)

    source = Image.open(args.source).convert("RGB")
    poses: list[Pose] = []
    for pose_number, pose_name in enumerate(POSE_NAMES, start=1):
        pose = crop_pose(source, pose_number)
        pose.image.save(args.poses_dir / f"{pose_number:02d}_{pose_name}.png")
        poses.append(pose)

    sheet = build_sheet(poses)
    png_path = args.out_dir / "spritesheet.png"
    webp_path = args.out_dir / "spritesheet.webp"
    sheet.save(png_path)
    sheet.save(webp_path, format="WEBP", lossless=True, method=6)
    write_pet_json(args.out_dir / "pet.json")
    write_animation_map(args.animation_map)
    make_contact_sheet(sheet, args.contact_sheet)
    make_animation_previews(sheet, args.gif, args.rows_dir)

    print(f"wrote {png_path} ({SHEET_W}x{SHEET_H})")
    print(f"wrote {webp_path}")
    print(f"wrote {args.out_dir / 'pet.json'}")
    print(f"wrote {args.contact_sheet}")
    print(f"wrote {args.gif}")
    print(f"wrote {args.animation_map}")


if __name__ == "__main__":
    main()
