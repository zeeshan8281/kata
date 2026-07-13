"""Sealed check for kata 004 (bug-hunt).

Exec the submitted calc.py and run the same three assertions test_calc.py uses.
"""
from __future__ import annotations

import re
import types


def _extract_code(answer: str) -> str:
    s = answer.strip()
    m = re.search(r"```(?:python)?\n(.*?)```", s, re.DOTALL)
    return (m.group(1) if m else s).strip()


def check(answer: str, inputs_dir: str):
    cases = [([3, 1, 2], 2), ([1, 2, 3, 4], 2.5), ([7], 7)]
    total = len(cases)
    mod = types.ModuleType("calc")
    try:
        exec(compile(_extract_code(answer), "calc.py", "exec"), mod.__dict__)
        median = mod.median
    except Exception as e:
        return 0, total, [f"calc.py does not compile / no median ({e})"]

    errors = []
    for xs, want in cases:
        try:
            got = median(list(xs))
        except Exception as e:
            errors.append(f"median({xs}) raised {e}")
            continue
        if got != want:
            errors.append(f"median({xs}) == {got}, expected {want}")
    return total - len(errors), total, errors
