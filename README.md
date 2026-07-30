# Pebble Poses Codex Pet

Pebble Poses is a local custom pet package for ChatGPT desktop and compatible Codex CLI sessions. It installs under the separate ID `pebble-poses` and does not overwrite a pet named `pebble`.

## Runtime package

```text
pebble-poses/
├── pet.json
└── spritesheet.webp
```

The runtime sprite sheet is a lossless transparent WebP with the Codex V2 geometry:

- `1536 × 2288` pixels
- `8 × 11` cells
- `192 × 208` pixels per cell
- fully transparent unused cells
- 16 clockwise look directions in rows 9–10
- under the `20 MiB` upload limit

Official references:

- [ChatGPT Pets documentation](https://learn.chatgpt.com/docs/pets)
- [OpenAI hatch-pet skill](https://github.com/openai/skills/blob/main/skills/.curated/hatch-pet/SKILL.md)
- [Codex animation-row contract](https://github.com/openai/skills/blob/main/skills/.curated/hatch-pet/references/animation-rows.md)

## Animation contract

| Row | State | Used columns | Timing |
|---:|---|---:|---|
| 0 | `idle` | 0–6 | 0–5 animate at 280, 110, 110, 140, 140, 320 ms; 6 is the V2 neutral look frame |
| 1 | `running-right` | 0–7 | 120 ms each; final 220 ms |
| 2 | `running-left` | 0–7 | 120 ms each; final 220 ms |
| 3 | `waving` | 0–3 | 140 ms each; final 280 ms |
| 4 | `jumping` | 0–4 | 140 ms each; final 280 ms |
| 5 | `failed` | 0–7 | 140 ms each; final 240 ms |
| 6 | `waiting` | 0–5 | 150 ms each; final 260 ms |
| 7 | `running` | 0–5 | 120 ms each; final 220 ms |
| 8 | `review` | 0–5 | 150 ms each; final 280 ms |
| 9 | `look-directions-a` | 0–7 | 000° through 157.5° in 22.5° steps |
| 10 | `look-directions-b` | 0–7 | 180° through 337.5° in 22.5° steps |

`000°` means up. The direction rows proceed clockwise in screen coordinates;
neutral pointer input falls back to the idle animation.

The exact approved source frame for every runtime cell is recorded in
[`docs/animation-map.json`](docs/animation-map.json).

## Requirements

- Python 3.10 or later
- Pillow 12.3.0
- Bash for the installer

```bash
python3 -m pip install --require-hashes --requirement requirements.txt
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

`spritesheet.webp` is the packaged runtime asset. The PNG is retained as a
lossless decoded QA/build artifact.
Runtime rows are composed from the approved 192×208 PNG frames in
`source/rows/`; `source/poses/` remains a deterministic extraction of the
original production-art board for reference. The committed source-row cells
already contain the single approved V2 edge-despill result, so ordinary rebuilds
must not apply chroma cleanup a second time.

## Verify

```bash
python3 scripts/verify_pebble_pose_pet.py pebble-poses qa/validation.json
```

Validation fails on:

- invalid file encoding, incorrect metadata, dimensions, or file size
- nontransparent unused cells
- empty required frames
- clipped frames or insufficient padding
- disconnected sprite components
- fully transparent pixels retaining hidden RGB values
- animation rows with insufficient frame variation

Run the regression and adversarial tests with:

```bash
python3 -m unittest discover --start-directory tests --verbose
```

CI also rebuilds every generated artifact in isolation and compares decoded
pixels, GIF timing, and JSON semantics with the committed outputs.

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

This verifies the atlas before creating byte-reproducible archives:

```text
dist/pebble-poses-runtime.zip
dist/pebble-poses-source.zip
dist/SHA256SUMS
```

The runtime archive contains only the installable pet folder. The source archive excludes `.git`, caches, bytecode, and previous release output.
Pushing a `v*` tag runs the same verification and reproducibility gates,
publishes both archives with checksums, and attaches a GitHub build-provenance
attestation.

## Source-art note

The runtime atlas uses dedicated, state-specific animation frames derived from
the Pebble production art. The left movement row is a deterministic mirror of
the approved right movement row, keeping frame order, scale, and registration
exactly paired. The two coherent look rows form one approved clockwise 16-pose
loop with unmistakable cardinal directions. Runtime frames contain no floor
scenery or detached debris.
See [`docs/ASSET-PROVENANCE.md`](docs/ASSET-PROVENANCE.md) for derivation
details.
