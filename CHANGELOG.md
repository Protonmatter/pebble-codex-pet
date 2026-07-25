# Changelog

## 2.1.0 - 2026-07-24

- Rebuilt all nine runtime rows from dedicated, state-specific source frames.
- Added a true mirrored left/right locomotion pair, a complete wave-to-idle
  cycle, distinct waiting and review actions, and consistently registered
  active-work frames.
- Removed floor debris and disconnected alpha fragments from runtime artwork.
- Strengthened validation to reject disguised non-PNG files, malformed
  metadata, hidden RGB residue, clipping, unused-cell artwork, disconnected
  components, oversized payloads, and insufficient animation variation.
- Added adversarial regression tests and semantic reproducibility checks for
  decoded images, GIF frames and timing, and JSON outputs.
- Made release ZIPs byte-reproducible and hardened atomic installation,
  including same-path rejection and collision-safe backups.
- Locked Python dependencies with hashes and pinned GitHub Actions to immutable
  commits with automated dependency updates.
- Added tagged releases with checksums and build-provenance attestations.
- Added contribution, security, and asset-provenance documentation.

## 2.0.0 - 2026-07-23

- Corrected the atlas to the current Codex V1 8-column by 9-row animation contract.
- Added exact used-column counts and frame timing metadata for all nine animation rows.
- Added calm idle breathing, directional shell-roll movement, waving, jumping, failure, waiting, active-work, and review sequences.
- Added deterministic background extraction, detached-artifact cleanup, floor-residue reduction, and transparent-pixel RGB normalization.
- Added strict validation for atlas dimensions, file size, metadata, frame occupancy, transparent unused cells, margins, component count, and animation uniqueness.
- Added contact-sheet, combined GIF, per-row GIF, and machine-readable animation-map outputs.
- Added atomic local installation and release packaging with SHA-256 checksums.
- Removed Git internals and build caches from release archives.
