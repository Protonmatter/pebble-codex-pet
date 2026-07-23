# Pebble Poses Codex Pet

Pebble Poses is a local custom pet package for ChatGPT desktop and compatible Codex CLI sessions. It installs under the separate ID `pebble-poses` and does not overwrite a pet named `pebble`.

## Runtime package

```text
pebble-poses/
├── pet.json
└── spritesheet.png
```

The runtime sprite sheet is a transparent PNG with the fixed Codex V1 geometry:

- `1536 × 1872` pixels
- `8 × 9` cells
- `192 × 208` pixels per cell
- fully transparent unused cells
- under the `20 MiB` upload limit

Official references:

- [ChatGPT Pets documentation](https://learn.chatgpt.com/docs/pets)
- [OpenAI hatch-pet skill](https://github.com/openai/skills/blob/main/skills/.curated/hatch-pet/SKILL.md)
- [Codex animation-row contract](https://github.com/openai/skills/blob/main/skills/.curated/hatch-pet/references/animation-rows.md)

## Animation contract

| Row | State | Used columns | Timing |
|---:|---|---:|---|
| 0 | `idle` | 0–5 | 280, 110, 110, 140, 140, 320 ms |
| 1 | `running-right` | 0–7 | 120 ms each; final 220 ms |
| 2 | `running-left` | 0–7 | 120 ms each; final 220 ms |
| 3 | `waving` | 0–3 | 140 ms each; final 280 ms |
| 4 | `jumping` | 0–4 | 140 ms each; final 280 ms |
| 5 | `failed` | 0–7 | 140 ms each; final 240 ms |
| 6 | `waiting` | 0–5 | 150 ms each; final 260 ms |
| 7 | `running` | 0–5 | 120 ms each; final 220 ms |
| 8 | `review` | 0–5 | 150 ms each; final 280 ms |

The exact pose selection and per-frame transforms are recorded in [`docs/animation-map.json`](docs/animation-map.json).

## Requirements

- Python 3.10 or later
- Pillow 10–12
- Bash for the installer

```bash
python3 -m pip install -r requirements.txt
```

## Build

Defaults are resolved relative to the repository, so the full build is:

```bash
python3 scripts/build_pebble_pose_pet.py
```

The build produces:

```text
pebble-poses/pet.json
pebble-poses/spritesheet.png
pebble-poses/spritesheet.webp
preview/pebble-poses-contact-sheet.png
preview/pebble-poses-animation-preview.gif
preview/rows/*.gif
source/poses/*.png
docs/animation-map.json
```

`spritesheet.png` is the packaged runtime asset. The lossless WebP is retained as an alternate QA/build artifact.

## Verify

```bash
python3 scripts/verify_pebble_pose_pet.py pebble-poses qa/validation.json
```

Validation fails on:

- incorrect metadata, dimensions, or file size
- nontransparent unused cells
- empty required frames
- clipped frames or insufficient padding
- disconnected sprite components
- fully transparent pixels retaining hidden RGB values
- animation rows with insufficient frame variation

## Install locally

```bash
./scripts/install_pebble_pose_pet.sh
```

Default destination:

```text
${CODEX_HOME:-$HOME/.codex}/pets/pebble-poses
```

A pre-existing `pebble-poses` installation is moved to a timestamped backup before replacement. A separate `pebble` folder is not touched.

Custom source or destination:

```bash
./scripts/install_pebble_pose_pet.sh \
  --source ./pebble-poses \
  --target "$HOME/.codex/pets/pebble-poses"
```

After installation, refresh the pet list in ChatGPT desktop or open the Codex CLI pet picker with `/pets`.

## Package releases

```bash
python3 scripts/package_release.py
```

This verifies the atlas before creating:

```text
dist/pebble-poses-runtime.zip
dist/pebble-poses-source.zip
dist/SHA256SUMS
```

The runtime archive contains only the installable pet folder. The source archive excludes `.git`, caches, bytecode, and previous release output.

## Source-art note

This version reconstructs all animation rows from the supplied 18-pose art board. Directional movement is represented as a shell-roll sequence because the source board does not contain a dedicated eight-frame gait in each direction. The next visual-quality step is to redraw those two directional strips and remove the remaining source-art ground pebbles at the artwork level while preserving Pebble’s identity.
