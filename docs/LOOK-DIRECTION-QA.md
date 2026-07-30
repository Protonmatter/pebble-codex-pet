# Look-Direction QA

Pebble Poses V2 includes 16 clockwise look directions across atlas rows 9 and
10. The four cardinals are hard gates: 000 up, 090 screen-right, 180 down, and
270 screen-left.

## Accepted evidence

- Three isolated reviewers classified a randomized, unlabeled A/B direction
  sheet. Both hard cardinal pairs passed by strict majority.
- Thirteen of fourteen intermediate axis pairs passed. The remaining 157.5
  horizontal component was ambiguous in isolation but was accepted as a
  warning after labeled loop review confirmed a continuous down-right pose.
- The final continuity report contains no alpha-hole candidates. Its remaining
  metric warnings were visually reviewed and show no clipping, identity drift,
  semantic reversal, or conspicuous size pop.
- A final independent reviewer passed all nine standard animation rows and the
  complete 16-direction loop after both coherent look rows were uniformly
  scaled by 1.30, recentered, and planted at the shared y=203 baseline.
- Both the repository verifier and the hatch-pet V2 atlas validator pass the
  final source-driven WebP with zero structural or chroma warnings.

Machine-readable semantic verdicts are stored in
qa/direction-semantics.json; the final visual disposition is stored in
qa/final-visual-qa.json.

## Accepted warnings

- 157.5 has a subtle screen-right cue when viewed alone; the ordered
  135 -> 157.5 -> 180 loop preserves the intended down-right progression.
- 112.5 -> 135 is a pixel-difference outlier caused by the bowed-pose
  transition, with no visible snap at normal pet size.
- 337.5 -> 000 has an 11.5-pixel center shift and 1.15 area ratio as Pebble
  returns to the full upward pose. The planted baseline, identity, and
  clockwise direction semantics remain stable.
