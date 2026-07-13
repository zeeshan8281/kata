#!/usr/bin/env python3
"""CI: re-run every non-self-reported leaderboard entry and confirm it stands up.

Fails (exit 1) if any entry: doesn't pass all sealed tests, or claims a score more
than SLACK below what we recompute (cost drifts slightly across runs — PRD open q #2).
Self-reported (⚑) rows run on endpoints CI can't reach, so they're skipped here.
"""
from __future__ import annotations

import sys
import types

import yaml

from runner import execute

SLACK = 3  # allowed score drift from provider-side cost/token jitter


def ns(**kw):
    a = types.SimpleNamespace(base_url=None, price_in=None, price_out=None)
    a.__dict__.update(kw)
    return a


def main():
    data = yaml.safe_load(open("leaderboard.yaml")) or {}
    failures = []
    for kid, rows in data.items():
        for row in rows or []:
            tag = f"{kid} @{row['solver']}"
            if row.get("self_reported"):
                print(f"skip {tag} (self-reported ⚑)")
                continue
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
    print("all leaderboard entries verified")


if __name__ == "__main__":
    main()
