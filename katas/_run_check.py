#!/usr/bin/env python3
"""Bridge from the TypeScript verifier to a kata's Python sealed check.

The kata answers are Python programs and the checks `exec` them, so the checks
stay Python. verifier.ts spawns:

    python3 katas/_run_check.py <kata_dir> <answer_file>

and reads a single JSON line: {"passed": int, "total": int, "errors": [str]}.
Stdlib only — no pip install needed.
"""
import importlib.util
import json
import os
import sys


def main():
    kdir, answer_file = sys.argv[1], sys.argv[2]
    with open(answer_file, encoding="utf-8") as f:
        answer = f.read()
    spec = importlib.util.spec_from_file_location("check", os.path.join(kdir, "check.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    passed, total, errors = mod.check(answer, os.path.join(kdir, "inputs"))
    print(json.dumps({"passed": passed, "total": total, "errors": list(errors)}))


if __name__ == "__main__":
    main()
