"""Sealed check for kata 001 (pr-review).

Grades the JSON audit against the planted issues in inputs/change.diff:
  - SQL injection in auth.login (string-formatted query)
  - hardcoded API_KEY secret in auth.py
  - N+1 query in orders.order_totals
  - missing test for verify_token
plus valid schema. 6 tests total.
"""
from __future__ import annotations

import json
import re


def _load_json(answer: str):
    s = answer.strip()
    s = re.sub(r"^```(?:json)?|```$", "", s, flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}", s, re.DOTALL)  # first {...} block
    return json.loads(m.group(0) if m else s)


def check(answer: str, inputs_dir: str):
    errors = []
    total = 6

    try:
        d = _load_json(answer)
    except Exception as e:
        return 0, total, [f"output is not valid JSON ({e})"]

    def arr(k):
        v = d.get(k)
        return v if isinstance(v, list) else None

    sec, perf, tests = arr("security_concerns"), arr("performance_impact"), arr("missing_tests")

    # 1. schema: three arrays present
    if sec is None or perf is None or tests is None:
        errors.append("must have array keys security_concerns, performance_impact, missing_tests")

    # 2. security entries well-formed
    sev_ok = all(
        isinstance(x, dict) and {"file", "line", "severity", "note"} <= set(x)
        and x["severity"] in ("low", "med", "high")
        for x in (sec or [])
    ) and bool(sec)
    if not sev_ok:
        errors.append("each security_concern needs file, line, severity(low|med|high), note")

    sec_blob = json.dumps(sec or []).lower()
    perf_blob = json.dumps(perf or []).lower()
    test_blob = json.dumps(tests or []).lower()

    # 3. SQL injection flagged in auth
    if not ("auth" in sec_blob and re.search(r"sql|inject", sec_blob)):
        errors.append("missed SQL injection in auth.login")
    # 4. hardcoded secret flagged
    if not re.search(r"secret|api[_ ]?key|hardcod|credential", sec_blob):
        errors.append("missed hardcoded API_KEY secret")
    # 5. N+1 perf in orders
    if not ("orders" in perf_blob and re.search(r"n\+1|per user|per-user|loop|each|query", perf_blob)):
        errors.append("missed N+1 query in orders.order_totals")
    # 6. missing test for verify_token
    if "verify_token" not in test_blob:
        errors.append("missed missing test for verify_token")

    passed = total - len(errors)
    return passed, total, errors
