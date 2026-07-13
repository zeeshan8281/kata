# Kata 001 · pr-review

Audit the PR diff below. Return **JSON only** (no prose, no markdown fences) with exactly these keys:

- `security_concerns`: array of `{ "file", "line", "severity", "note" }` where severity is one of `"low"`, `"med"`, `"high"`.
- `performance_impact`: array of `{ "file", "hotspot", "expected_delta" }`.
- `missing_tests`: array of `{ "file", "function", "why" }`.

Find the real issues. Empty arrays are allowed but a clean diff this is not.
