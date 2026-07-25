from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image, ImageOps

from scripts.compare_build_outputs import compare_image
from scripts.package_release import add_file

ROOT = Path(__file__).resolve().parents[1]
VERIFY = ROOT / "scripts" / "verify_pebble_pose_pet.py"
INSTALL = ROOT / "scripts" / "install_pebble_pose_pet.sh"
PET_DIR = ROOT / "pebble-poses"


class VerifierAdversarialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.pet_dir = Path(self.temporary.name) / "pet"
        shutil.copytree(PET_DIR, self.pet_dir)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_verify(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VERIFY), str(self.pet_dir)],
            text=True,
            capture_output=True,
            check=False,
        )

    def mutate_sheet(self, callback) -> None:
        sheet_path = self.pet_dir / "spritesheet.png"
        with Image.open(sheet_path) as source:
            image = source.convert("RGBA")
        callback(image)
        image.save(sheet_path, format="PNG")

    def test_committed_package_passes(self) -> None:
        result = self.run_verify()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_tiff_masquerading_as_png_is_rejected(self) -> None:
        sheet_path = self.pet_dir / "spritesheet.png"
        with Image.open(sheet_path) as source:
            source.convert("RGBA").save(sheet_path, format="TIFF", compression="tiff_deflate")
        result = self.run_verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PNG-encoded bytes", result.stderr + result.stdout)

    def test_artwork_in_unused_cell_is_rejected(self) -> None:
        self.mutate_sheet(lambda image: image.putpixel((7 * 192 + 96, 96), (1, 1, 1, 255)))
        result = self.run_verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unused column 7", result.stderr + result.stdout)

    def test_clipping_is_rejected(self) -> None:
        self.mutate_sheet(lambda image: image.putpixel((0, 100), (1, 1, 1, 255)))
        result = self.run_verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("clipped or lacks safe padding", result.stderr + result.stdout)

    def test_duplicate_animation_frames_are_rejected(self) -> None:
        def duplicate_frames(image: Image.Image) -> None:
            first = image.crop((0, 3 * 208, 192, 4 * 208))
            for column in range(1, 4):
                image.paste(first, (column * 192, 3 * 208))

        self.mutate_sheet(duplicate_frames)
        result = self.run_verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("distinct frames", result.stderr + result.stdout)

    def test_hidden_rgb_residue_is_rejected(self) -> None:
        self.mutate_sheet(lambda image: image.putpixel((7 * 192 + 96, 96), (7, 0, 0, 0)))
        result = self.run_verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("non-zero RGB residue", result.stderr + result.stdout)

    def test_malformed_metadata_is_rejected_cleanly(self) -> None:
        (self.pet_dir / "pet.json").write_text("{", encoding="utf-8")
        result = self.run_verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("valid UTF-8 JSON", result.stderr + result.stdout)
        self.assertNotIn("Traceback", result.stderr + result.stdout)

    def test_oversize_payload_is_rejected(self) -> None:
        with (self.pet_dir / "spritesheet.png").open("ab") as stream:
            stream.write(b"\0" * (20 * 1024 * 1024))
        result = self.run_verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exceeds 20 MiB", result.stderr + result.stdout)


class BuildComparisonTests(unittest.TestCase):
    def test_pixel_identical_png_encodings_compare_equal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.png"
            second = root / "second.png"
            image = Image.new("RGBA", (32, 32), (40, 80, 120, 128))
            image.save(first, format="PNG", compress_level=0)
            image.save(second, format="PNG", compress_level=9)
            self.assertNotEqual(
                hashlib.sha256(first.read_bytes()).digest(),
                hashlib.sha256(second.read_bytes()).digest(),
            )
            compare_image(first, second)

    def test_pixel_difference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.png"
            second = root / "second.png"
            Image.new("RGBA", (8, 8), (0, 0, 0, 0)).save(first)
            changed = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
            changed.putpixel((4, 4), (1, 1, 1, 255))
            changed.save(second)
            with self.assertRaises(SystemExit):
                compare_image(first, second)


class PackagingAndInstallerTests(unittest.TestCase):
    def test_zip_member_metadata_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "payload.txt"
            source.write_text("same bytes\n", encoding="utf-8")
            outputs = []
            for index, timestamp in enumerate((1_700_000_000, 1_800_000_000)):
                os.utime(source, (timestamp, timestamp))
                archive_path = root / f"archive-{index}.zip"
                with zipfile.ZipFile(archive_path, "w") as archive:
                    add_file(archive, source, "payload.txt")
                outputs.append(archive_path.read_bytes())
            self.assertEqual(outputs[0], outputs[1])

    def test_installer_rejects_source_as_target(self) -> None:
        result = subprocess.run(
            [str(INSTALL), "--source", str(PET_DIR), "--target", str(PET_DIR)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Source and target must be different", result.stderr)

    def test_installer_uses_collision_safe_backup_name(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "pets" / "pebble-poses"
            target.mkdir(parents=True)
            (target / "old.txt").write_text("old install\n", encoding="utf-8")

            fixed_timestamp = "20260724T120000Z"
            first_backup = Path(f"{target}.backup.{fixed_timestamp}")
            first_backup.mkdir()
            (first_backup / "sentinel.txt").write_text("keep me\n", encoding="utf-8")

            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_date = fake_bin / "date"
            fake_date.write_text(
                f"#!/usr/bin/env sh\nprintf '%s\\n' '{fixed_timestamp}'\n",
                encoding="utf-8",
            )
            fake_date.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = f"{fake_bin}{os.pathsep}{environment['PATH']}"

            result = subprocess.run(
                [str(INSTALL), "--source", str(PET_DIR), "--target", str(target)],
                text=True,
                capture_output=True,
                check=False,
                env=environment,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue((target / "spritesheet.png").is_file())
            self.assertEqual(
                (first_backup / "sentinel.txt").read_text(encoding="utf-8"),
                "keep me\n",
            )
            self.assertEqual(
                (Path(f"{first_backup}.1") / "old.txt").read_text(encoding="utf-8"),
                "old install\n",
            )


class MetadataTests(unittest.TestCase):
    def test_animation_map_is_valid_json(self) -> None:
        data = json.loads((ROOT / "docs" / "animation-map.json").read_text(encoding="utf-8"))
        self.assertEqual(data["grid"], {"columns": 8, "rows": 9})


class ArtworkRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with Image.open(PET_DIR / "spritesheet.png") as source:
            cls.sheet = source.convert("RGBA")

    @classmethod
    def frame(cls, row: int, column: int) -> Image.Image:
        return cls.sheet.crop(
            (
                column * 192,
                row * 208,
                (column + 1) * 192,
                (row + 1) * 208,
            )
        )

    def test_left_locomotion_is_exact_mirror_of_right(self) -> None:
        for column in range(8):
            right = self.frame(1, column)
            left = self.frame(2, column)
            self.assertEqual(ImageOps.mirror(right).tobytes(), left.tobytes())

    def test_wave_returns_to_neutral_registration(self) -> None:
        first_bbox = self.frame(3, 0).getchannel("A").getbbox()
        last_bbox = self.frame(3, 3).getchannel("A").getbbox()
        self.assertIsNotNone(first_bbox)
        self.assertIsNotNone(last_bbox)
        assert first_bbox is not None and last_bbox is not None
        for first_value, last_value in zip(first_bbox, last_bbox, strict=True):
            self.assertLessEqual(abs(first_value - last_value), 3)

    def test_waiting_and_review_use_distinct_frames(self) -> None:
        waiting = {self.frame(6, column).tobytes() for column in range(6)}
        review = {self.frame(8, column).tobytes() for column in range(6)}
        self.assertTrue(waiting.isdisjoint(review))

    def test_active_work_registration_is_stable(self) -> None:
        bboxes = [
            self.frame(7, column).getchannel("A").getbbox()
            for column in range(6)
        ]
        self.assertTrue(all(bbox is not None for bbox in bboxes))
        widths = [bbox[2] - bbox[0] for bbox in bboxes if bbox is not None]
        heights = [bbox[3] - bbox[1] for bbox in bboxes if bbox is not None]
        self.assertLessEqual(max(widths) - min(widths), 8)
        self.assertLessEqual(max(heights) - min(heights), 10)


if __name__ == "__main__":
    unittest.main()
