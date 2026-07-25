# Contributing

## Development setup

Use Python 3.10 or later. Install the fully hashed dependency lock:

```bash
python3 -m pip install --require-hashes --requirement requirements.txt
```

When changing dependencies, edit `requirements.in` and regenerate the lock:

```bash
uv pip compile requirements.in \
  --output-file requirements.txt \
  --generate-hashes \
  --python-version 3.12
```

## Required validation

```bash
python3 -m unittest discover --start-directory tests --verbose
python3 scripts/build_pebble_pose_pet.py
python3 scripts/verify_pebble_pose_pet.py pebble-poses qa/validation.json
python3 scripts/package_release.py
```

Generated runtime, pose, documentation, and preview artifacts belong in the
same change as the source or build-logic change that produced them.

## Artwork changes

- Preserve Pebble's material, proportions, palette, and readable silhouette.
- Keep each state visually distinct at a 192×208 cell size.
- Do not add floor scenery, detached particles, text, UI, shadows, or effects.
- Use a shared scale and registration within an animation row.
- Record the source and derivation in `docs/ASSET-PROVENANCE.md`.
- Inspect the contact sheet and all looping row previews before requesting review.

## Pull requests

Explain the root cause, generated artifacts affected, verification performed,
and whether the runtime package or animation semantics changed.
