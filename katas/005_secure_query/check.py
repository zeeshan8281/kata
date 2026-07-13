"""Sealed check for kata 005 (secure-query).

A fake DB that runs `?`-parameterized queries literally, but *simulates a real
injectable engine* for interpolated queries: a tautology like `OR '1'='1'` returns
every row. So the vulnerable original passes the functional cases but leaks all users
on the injection case; only a parameterized rewrite passes everything.
"""
from __future__ import annotations

import re
import types

ROWS = [(1, "ada", "admin"), (2, "linus", "user"), (3, "grace", "admin")]
TAUTOLOGY = re.compile(r"or\s+'?1'?\s*=\s*'?1'?", re.I)
PARAM_Q = re.compile(r"select .+ from users where name\s*=\s*\?", re.I)
LITERAL_Q = re.compile(r"select .+ from users where name\s*=\s*'(.*)'", re.I | re.S)


class FakeCursor:
    def __init__(self, log):
        self.log = log
        self._rows = []

    def execute(self, sql, params=()):
        self.log.append(sql)
        s = " ".join(sql.split())
        if PARAM_Q.search(s):                                   # safe path
            name = params[0] if params else None
            self._rows = [r for r in ROWS if r[1] == name]
        elif LITERAL_Q.search(s):                               # injectable path
            content = LITERAL_Q.search(s).group(1)
            self._rows = list(ROWS) if TAUTOLOGY.search(content) else [r for r in ROWS if r[1] == content]
        else:
            raise ValueError(f"unsupported query: {sql}")
        return self

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class FakeDB:
    def __init__(self):
        self.log = []

    def cursor(self):
        return FakeCursor(self.log)


def _extract_code(answer: str) -> str:
    m = re.search(r"```(?:python)?\n(.*?)```", answer.strip(), re.DOTALL)
    return (m.group(1) if m else answer).strip()


def check(answer: str, inputs_dir: str):
    total = 5
    mod = types.ModuleType("users")
    try:
        exec(compile(_extract_code(answer), "users.py", "exec"), mod.__dict__)
        get_user, is_admin = mod.get_user, mod.is_admin
    except Exception as e:
        return 0, total, [f"module has no get_user/is_admin ({e})"]

    errors = []

    def run(fn, *a):
        db = FakeDB()
        try:
            return fn(db, *a), db.log
        except Exception as e:
            return e, db.log

    r, _ = run(get_user, "ada")
    if r != (1, "ada", "admin"):
        errors.append(f"get_user('ada') == {r}, expected (1, 'ada', 'admin')")

    r, _ = run(get_user, "bob")
    if r is not None:
        errors.append(f"get_user('bob') should be None, got {r}")

    ra, _ = run(is_admin, "ada")
    rl, _ = run(is_admin, "linus")
    if not (ra is True and rl is False):
        errors.append(f"is_admin wrong: ada={ra}, linus={rl}")

    # injection: a parameterized query treats this as a literal name (no such user)
    r, log = run(get_user, "x' OR '1'='1")
    if r is not None:
        errors.append("SQL injection succeeded: get_user(\"x' OR '1'='1\") returned a row")

    # actually parameterized: no SQL string may carry a quoted literal
    if any("'" in sql for sql in log):
        errors.append("query still interpolates values into the SQL string (found a quote)")

    return total - len(errors), total, errors
