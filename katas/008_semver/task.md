# Kata 008 · semver

Implement `compare(a, b)` returning `-1`, `0`, or `1` per **Semantic Versioning 2.0.0**
precedence.

- Compare `major.minor.patch` numerically.
- A pre-release version has **lower** precedence than the normal version: `1.0.0-alpha < 1.0.0`.
- Compare pre-release identifiers left to right: numeric identifiers compared numerically,
  alphanumeric compared in ASCII order, a numeric identifier is **lower** than an alphanumeric one,
  and if all preceding identifiers are equal, the version with **more** identifiers wins.
- **Build metadata** (`+...`) is ignored for precedence.

So: `1.0.0-alpha < 1.0.0-alpha.1 < 1.0.0-alpha.beta < 1.0.0-beta < 1.0.0-beta.2 < 1.0.0-beta.11 < 1.0.0-rc.1 < 1.0.0`.

Return **only** the complete Python source exposing `compare(a: str, b: str) -> int`.
No markdown fences, no prose.
