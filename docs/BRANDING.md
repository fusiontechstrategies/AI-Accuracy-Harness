# Repository graphics

The repository includes three original graphics under `docs/assets`:

- `harness-flow.svg` explains the operating model in the README.
- `qualification-results.svg` summarizes the recorded qualification results.
- `social-preview.png` is a 1280×640 sharing card for GitHub's social preview setting.

The corresponding `social-preview.svg` is the editable source for the sharing card. If a result
changes, update the source values from the qualification summaries, regenerate the PNG at exactly
1280×640, rebuild the package manifest, and rerun the integrity verifier.

Do not update the metrics for promotional reasons. Every number shown in a graphic must remain
traceable to a committed qualification summary.

