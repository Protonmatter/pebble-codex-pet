# Asset Provenance

All artwork in this repository was created specifically for the Pebble Poses
project; no third-party stock assets are included.

| Asset | Origin | Derivation |
|---|---|---|
| `source/photo-1-concept-poses.jpg` | Initial Pebble concept-art session | Original project concept board |
| `source/photo-2-clean-sprite-art-pass.jpg` | Pebble production-art session | Identity-preserving refinement of the concept board |
| `source/poses/*.png` | Repository build output | Deterministically extracted from the production-art board |
| `source/rows/{idle,waving,jumping,failed,waiting,running,review}/*.png` | Project animation-art pass | State-specific, identity-preserving animation frames on transparency |
| `source/rows/running-right/*.png` | Project locomotion-art pass | Approved right-facing shell-drag sequence |
| `source/rows/running-left/*.png` | Repository derivation | Deterministic horizontal mirror of the matching right-facing frame |
| `pebble-poses/spritesheet.*` | Repository build output | Deterministically composed from approved source-row frames |
| `preview/*` | Repository build output | Rendered from the runtime atlas |

The repository's MIT license applies to the committed source and generated
assets. Future contributions must document externally sourced references,
licenses, and material transformations before merge.
