"""Sealed check for kata 002 (refactor-async).

Exec the submitted module, require the public functions to be coroutines, and
require awaiting them to return the same values as the sync original.
"""
from __future__ import annotations

import asyncio
import inspect
import re
import types


def _extract_code(answer: str) -> str:
    s = answer.strip()
    m = re.search(r"```(?:python)?\n(.*?)```", s, re.DOTALL)
    return (m.group(1) if m else s).strip()


def check(answer: str, inputs_dir: str):
    total = 4
    errors = []
    mod = types.ModuleType("submission")
    try:
        exec(compile(_extract_code(answer), "submission.py", "exec"), mod.__dict__)
    except Exception as e:
        return 0, total, [f"module does not import/compile ({e})"]

    public = ["fetch_user", "fetch_orders", "total_spend"]
    for name in public:
        fn = getattr(mod, name, None)
        if not inspect.iscoroutinefunction(fn):
            errors.append(f"{name} must be `async def`")

    if errors:  # can't safely await if signatures are wrong
        return total - len(errors), total, errors

    try:
        async def _drive():
            return (await mod.fetch_user(1), await mod.fetch_orders(2), await mod.total_spend(1))
        user, orders, spend = asyncio.run(_drive())
    except Exception as e:
        return 1, total, [f"awaiting the functions raised {e}"]

    # 4th test: behaviour preserved
    if (user, orders, spend) != ("ada", [5], 60):
        errors.append(f"wrong values: got {(user, orders, spend)}, expected ('ada', [5], 60)")

    passed = total - len(errors)
    return passed, total, errors
