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
| `source/rows/look-directions-{a,b}/*.png` | Pebble V2 hatch-pet upgrade | Approved normalized cells from two coherent 8-pose look families; cardinal, blind-axis, labeled-semantic, continuity, and final visual QA passed |
| `pebble-poses/spritesheet.*` | Repository build output | Deterministically composed from approved source-row frames |
| `preview/*` | Repository build output | Rendered from the runtime atlas |

The V2 migration reassembled the coherent look strips against the current
`main` neutral frame, applied hatch-pet's deterministic edge-local chroma-spill
suppression once to the complete atlas, and extracted the approved post-cleanup
cells into `source/rows/`. Alpha was preserved during despill. Repository builds
compose those committed cells directly and do not repeat chroma cleanup. A
blind-review failure at `000` caused row 9 to be regenerated as a complete
coherent family. Both final look rows were then uniformly normalized to a
shared practical scale and baseline before the final visual pass.

The repository's MIT license applies to the committed source and generated
assets. Future contributions must document externally sourced references,
licenses, and material transformations before merge.
