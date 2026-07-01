# Build Color Enterprise Readiness

Build Color is the color-science engine of the build/Project Telos family: a
dependency-light, deterministic library that turns color operations into reproducible,
inspectable results. It is designed to be used alone as a library or CLI, and as a
component other flagships (Calibrate Pro, the build tooling) depend on.

## Enterprise role

- Convert between color spaces, adapt white points, map gamuts, tone-map HDR, and measure
  perceptual difference with published-reference correctness.
- Generate and parse ICC profiles and 3D LUTs so results move cleanly between tools.
- Keep the numeric core free of heavy or network dependencies, so it installs and runs in
  constrained and offline environments.

## Operator surface

- `build-color` CLI for scriptable color operations (JSON-friendly where applicable).
- The importable Python API (`build_color.spaces`, `.difference`, `.gamut`, `.tonemap`,
  `.adaptation`, `.spectral`, `.icc`, `.lut_io`, …) for embedding in pipelines.
- An optional PyQt6 workbench (`pip install ".[gui]"`) for interactive inspection.

## Reproducibility and provenance

- Conversions are pure functions of their inputs: the same input yields the same output,
  which makes results reproducible and diffable across runs and machines.
- File outputs (ICC, `.cube` LUT, images) are the durable artifacts; they can be
  re-generated from the same inputs and checked byte-for-byte where the format is stable.
- When used inside Project Telos, color operations and their outputs can be referenced by
  content hash rather than carrying raw pixel data through every context window.

## Dependencies and boundary

- **Runtime core:** `numpy` only. No network, no code evaluation.
- **Optional:** `scipy` (select numeric routines), `Pillow` (image I/O), `PyQt6` (GUI).
  Each is isolated behind an extra so the core stays minimal.
- The GUI and CLI consume the core; they are never a dependency of it.

## Quality gates

- `ruff check .` (style), `mypy` (types — the numeric core is type-clean; the GUI adapter
  is boundary-typed), and `pytest` with coverage run in CI on every push and pull request.
- Releases are built and published to PyPI via OIDC trusted publishing; no API token is
  stored in the repository.

## Honest limits

- Color science is reference-relative: correctness claims are against published formulae
  and datasets, and are validated by the test suite. Report a deviation with its reference.
- The optional imaging and GUI layers inherit the maturity and advisories of Pillow and
  PyQt6; the guarantees above describe the numpy-only core.
