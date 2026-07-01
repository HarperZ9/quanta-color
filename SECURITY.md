# Security Policy

## Supported

Build Color follows a rolling release. Until a 2.0 line exists, only the latest release
on the default branch is supported for fixes.

## Reporting a vulnerability

Report suspected vulnerabilities privately via GitHub Security Advisories — the
"Security" tab of this repository, then "Report a vulnerability". Do NOT open a public
issue for an unfixed vulnerability.

Please include the affected module and version, a minimal reproduction, and the impact.
The maintainer will acknowledge within a stated window and agree a disclosure date.

## Attack surface (the honest part)

Build Color is a deterministic, offline numeric library. Its surface is small by design:

- **No network.** The core performs no network access. Nothing is fetched or sent.
- **No code evaluation.** Inputs are numbers, arrays, and file paths; the library never
  `eval`s or executes input.
- **File I/O is the real surface.** `image_io`, `lut_io`, and `icc` read and write files.
  Treat untrusted `.cube`, ICC, and image files as untrusted input: parsing is bounded to
  documented formats, but callers should not point the library at attacker-controlled
  paths with elevated privileges. Malformed files should raise, not corrupt state.
- **Optional dependencies carry their own surface.** Pillow (imaging) and PyQt6 (GUI) are
  optional; when installed, their own advisories apply. The numpy-only core is unaffected
  by them.

## What does not count

- A malformed-file parse that raises a normal exception is expected behavior, not a
  vulnerability. A parse that reads out of bounds, hangs unboundedly, or corrupts memory
  in the pure-Python/numpy path is in scope.
- Numerical inaccuracy relative to a reference is a correctness issue (open a normal
  issue with the reference), not a security vulnerability.
