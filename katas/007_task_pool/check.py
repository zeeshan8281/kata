"""Sealed check for kata 007 (task-pool).

Each task increments a shared live-counter and records the peak. From the results we
verify order preservation; from the peak we verify concurrency was actually bounded to
`limit` AND actually reached it (so neither the sequential nor the unbounded solution
passes).
"""
from __future__ import annotations

import asyncio
import re
import types


def _extract_code(answer: str) -> str:
    m = re.search(r"```(?:python)?\n(.*?)```", answer.strip(), re.DOTALL)
    return (m.group(1) if m else answer).strip()


def _make_tasks(n, state):
    def make(i):
        async def task():
            state["cur"] += 1
            state["max"] = max(state["max"], state["cur"])
            await asyncio.sleep(0.02)
            state["cur"] -= 1
            return i
        return task
    return [make(i) for i in range(n)]


def check(answer: str, inputs_dir: str):
    mod = types.ModuleType("pool")
    try:
        exec(compile(_extract_code(answer), "pool.py", "exec"), mod.__dict__)
        run_pool = mod.run_pool
    except Exception as e:
        return 0, 5, [f"module has no run_pool ({e})"]

    def trial(n, limit):
        state = {"cur": 0, "max": 0}
        res = asyncio.run(run_pool(_make_tasks(n, state), limit))
        return res, state["max"]

    checks = [
        # (n, limit, expected_results, expected_peak, label)
        (0, 3, [], 0, "empty task list -> []"),
        (12, 4, list(range(12)), 4, "n=12 limit=4: ordered results, peak concurrency == 4"),
        (5, 1, list(range(5)), 1, "limit=1: sequential, peak == 1, order preserved"),
        (4, 10, list(range(4)), 4, "limit>n: peak == n"),
        (20, 5, list(range(20)), 5, "n=20 limit=5: bounded at 5"),
    ]
    total = len(checks)
    errors = []
    for n, limit, want_res, want_peak, label in checks:
        try:
            res, peak = trial(n, limit)
        except Exception as e:
            errors.append(f"{label}: raised {e}")
            continue
        if list(res) != want_res:
            errors.append(f"{label}: wrong/out-of-order results ({res})")
        elif peak != want_peak:
            errors.append(f"{label}: peak concurrency was {peak}, expected {want_peak}")
    return total - len(errors), total, errors
