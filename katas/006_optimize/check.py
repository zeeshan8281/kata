"""Sealed check for kata 006 (optimize).

Correctness is graded against a brute-force oracle on small + medium inputs.
Complexity is graded by wall clock on a large input.

ponytail: the perf gate is a time cap, not an op count — O(n^2) at n=120k is ~7e9
Python iterations (minutes), O(n) is milliseconds, so a 5s cap separates them robustly
across machines. If someone's box is absurdly slow, bump CAP_S; the margin is huge.
"""
from __future__ import annotations

import re
import signal
import time
import types


def _oracle(nums, target):
    c = 0
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                c += 1
    return c


def _extract_code(answer: str) -> str:
    m = re.search(r"```(?:python)?\n(.*?)```", answer.strip(), re.DOTALL)
    return (m.group(1) if m else answer).strip()


CAP_S = 5.0


def check(answer: str, inputs_dir: str):
    small = [
        ([], 0),
        ([1, 1, 1], 2),          # 3 pairs
        ([2, 4, -2, 0], 2),      # (2,0),(4,-2)
        ([-1, -1, 2, 3], -2),    # (-1,-1)
        ([5, 5, 5, 5], 10),      # C(4,2)=6
    ]
    total = len(small) + 2  # + medium correctness + perf
    mod = types.ModuleType("pairs")
    try:
        exec(compile(_extract_code(answer), "pairs.py", "exec"), mod.__dict__)
        count_pairs = mod.count_pairs
    except Exception as e:
        return 0, total, [f"module has no count_pairs ({e})"]

    errors = []
    for nums, target in small:
        want = _oracle(nums, target)
        try:
            got = count_pairs(list(nums), target)
        except Exception as e:
            errors.append(f"count_pairs({nums}, {target}) raised {e}")
            continue
        if got != want:
            errors.append(f"count_pairs({nums}, {target}) == {got}, expected {want}")

    # medium correctness: deterministic list with dups & negatives
    med = [(i * 7919) % 1000 - 500 for i in range(4000)]
    try:
        if count_pairs(list(med), 0) != _oracle(med, 0):
            errors.append("wrong result on medium input (n=4000, target=0)")
    except Exception as e:
        errors.append(f"medium input raised {e}")

    # perf: must finish the large input under the cap (proves sub-quadratic).
    # SIGALRM interrupts a still-O(n^2) submission at the cap instead of hanging
    # the runner for minutes. ponytail: SIGALRM is Unix-only (mac/linux/CI) — on
    # Windows this falls back to a plain timed run.
    big = [(i * 7919) % 2000 - 1000 for i in range(120000)]

    def _timeout(*_):
        raise TimeoutError()

    has_alarm = hasattr(signal, "SIGALRM")
    if has_alarm:
        signal.signal(signal.SIGALRM, _timeout)
        signal.setitimer(signal.ITIMER_REAL, CAP_S)
    t0 = time.perf_counter()
    try:
        count_pairs(big, 0)
        dt = time.perf_counter() - t0
        if not has_alarm and dt > CAP_S:
            errors.append(f"too slow on n=120000: {dt:.1f}s > {CAP_S}s cap (still O(n^2)?)")
    except TimeoutError:
        errors.append(f"too slow on n=120000: exceeded {CAP_S}s cap (still O(n^2)?)")
    except Exception as e:
        errors.append(f"large input raised {e}")
    finally:
        if has_alarm:
            signal.setitimer(signal.ITIMER_REAL, 0)

    return total - len(errors), total, errors
