"""Sealed check for kata 008 (semver).

CHAIN is the canonical strictly-increasing precedence order from semver.org §11.
For each adjacent pair we require compare(lo, hi) == -1 and compare(hi, lo) == 1.
EQ pairs must compare equal (build metadata ignored).
"""
from __future__ import annotations

import re
import types

CHAIN = [
    "1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta", "1.0.0-beta",
    "1.0.0-beta.2", "1.0.0-beta.11", "1.0.0-rc.1", "1.0.0",
    "1.0.1", "1.1.0", "2.0.0", "2.1.0", "2.1.1",
]
EQ = [("1.0.0", "1.0.0+build.1"), ("1.2.3+a", "1.2.3+b"), ("1.0.0-alpha", "1.0.0-alpha")]
EXTRA_LT = [("1.0.0-1", "1.0.0-alpha")]  # numeric identifier < alphanumeric


def _extract_code(answer: str) -> str:
    m = re.search(r"```(?:python)?\n(.*?)```", answer.strip(), re.DOTALL)
    return (m.group(1) if m else answer).strip()


def check(answer: str, inputs_dir: str):
    total = (len(CHAIN) - 1) + len(EQ) + len(EXTRA_LT)
    mod = types.ModuleType("semver")
    try:
        exec(compile(_extract_code(answer), "semver.py", "exec"), mod.__dict__)
        compare = mod.compare
    except Exception as e:
        return 0, total, [f"module has no compare ({e})"]

    errors = []

    def expect(a, b, want):
        try:
            got = compare(a, b)
        except Exception as e:
            errors.append(f"compare({a!r}, {b!r}) raised {e}")
            return
        if got != want:
            errors.append(f"compare({a!r}, {b!r}) == {got}, expected {want}")

    for lo, hi in zip(CHAIN, CHAIN[1:]):
        # one test per adjacent pair — both directions must be right
        before = len(errors)
        expect(lo, hi, -1)
        expect(hi, lo, 1)
        if len(errors) > before:
            # collapse to a single failed test for this pair
            del errors[before + 1:]
    for a, b in EQ:
        expect(a, b, 0)
    for a, b in EXTRA_LT:
        expect(a, b, -1)

    return total - len(errors), total, errors
