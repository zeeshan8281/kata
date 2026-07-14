#!/usr/bin/env python3
"""CI: validate the leaderboard, and (with a key) re-run entries to confirm scores.

Two modes:
  python ci_verify.py --dry   structural checks only, no API key, no model calls.
                              Safe to run on untrusted fork PRs.
  python ci_verify.py         the above, then re-run each non-self-reported entry
                              against the sealed tests and confirm the claimed score.

Fails (exit 1) if any entry is malformed, points a solver at a submission that
isn't theirs, or (full mode) doesn't pass the tests / claims a score more than
SLACK below what we recompute. Self-reported (⚑) rows run on endpoints CI can't
reach, so the re-run is skipped for them — but the structural checks still apply.
"""
from __future__ import annotations

import argparse
import os
import sys
import types

import yaml

from verifier import kata_dir

SLACK = 3  # allowed score drift from provider-side cost/token jitter

REQUIRED = ("solver", "skill", "model", "name", "score")


def ns(**kw):
    a = types.SimpleNamespace(base_url=None, price_in=None, price_out=None)
    a.__dict__.update(kw)
    return a


def check_row(kid: str, row: dict) -> list[str]:
    """Structural validation — no network. Returns a list of error strings."""
    tag = f"{kid} @{row.get('solver', '?')}"
    errs = []
    for k in REQUIRED:
        if row.get(k) in (None, ""):
            errs.append(f"{tag}: missing '{k}'")
    if errs:
        return errs
    if not isinstance(row["score"], (int, float)):
        errs.append(f"{tag}: score must be a number, got {row['score']!r}")
    # solver↔submission binding: your row must point at your own submissions dir,
    # and stay inside it — no pointing at someone else's file or path traversal.
    skill, solver = str(row["skill"]), str(row["solver"])
    prefix = f"submissions/{solver}/"
    if not skill.startswith(prefix) or ".." in skill.split("/"):
        errs.append(f"{tag}: skill '{skill}' must live under {prefix} (no other dirs, no '..')")
    elif not os.path.isfile(skill):
        errs.append(f"{tag}: skill file '{skill}' does not exist")
    try:
        kata_dir(kid)  # kata must exist
    except SystemExit as e:
        errs.append(f"{tag}: {e}")
    return errs


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry", action="store_true", help="structural checks only, no API calls")
    args = p.parse_args()

    data = yaml.safe_load(open("leaderboard.yaml")) or {}
    failures = []
    for kid, rows in data.items():
        for row in rows or []:
            tag = f"{kid} @{row.get('solver', '?')}"
            row_errs = check_row(kid, row)
            if row_errs:
                failures.extend(row_errs)
                continue
            if args.dry:
                print(f"ok   {tag}: well-formed")
                continue
            if row.get("self_reported"):
                print(f"skip {tag}: self-reported ⚑ (structure ok, re-run skipped)")
                continue
            from runner import execute  # deferred: needs the openai dep + a key
            r = execute(ns(kata=kid, submission=row["skill"], model=row["model"]))
            if not r["ok"]:
                failures.append(f"{tag}: failed tests — {'; '.join(r['errors'])}")
            elif row["score"] < r["score"] - SLACK:
                failures.append(f"{tag}: claimed {row['score']} but re-ran to {r['score']}")
            else:
                print(f"ok   {tag}: score {r['score']} (claimed {row['score']})")

    if failures:
        print("\nVERIFY FAILED:\n  " + "\n  ".join(failures), file=sys.stderr)
        sys.exit(1)
    print("all leaderboard entries verified" + (" (structure only)" if args.dry else ""))


if __name__ == "__main__":
    main()
