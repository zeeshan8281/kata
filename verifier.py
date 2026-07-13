"""Runs a kata's sealed check against a Skill's answer.

Each kata dir has a check.py exposing:  check(answer: str, inputs_dir: str) -> (passed:int, total:int, errors:list[str])

v1 "sealed" = the check runs deterministically and the runner's run_hash + CI
re-run are the anti-cheat (PRD §11/§14). Hash-locked test archives are a later item.
"""
from __future__ import annotations

import importlib.util
import glob
import os


def kata_dir(kata_id: str) -> str:
    hits = glob.glob(os.path.join(os.path.dirname(__file__), "katas", f"{kata_id}_*"))
    if not hits:
        raise SystemExit(f"no kata {kata_id} under katas/")
    return hits[0]


def verify(kata_id: str, answer: str):
    kdir = kata_dir(kata_id)
    spec = importlib.util.spec_from_file_location(f"check_{kata_id}", os.path.join(kdir, "check.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check(answer, os.path.join(kdir, "inputs"))
