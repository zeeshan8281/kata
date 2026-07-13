#!/usr/bin/env python3
"""Kata runner — load a SKILL.md, drive it against a sealed kata, score it.

    export ANTHROPIC_API_KEY=...
    python runner.py --kata 001 --submission submissions/<handle>/001.md --model claude-haiku-4-5

Talks to any OpenAI-compatible endpoint. Defaults to Anthropic's compat endpoint;
point elsewhere with --base-url (or KATA_BASE_URL) for OpenAI/Darkbloom/local models.
"""
from __future__ import annotations

import argparse
import hashlib
import glob
import os
import sys

import yaml

import scorer
from verifier import verify, kata_dir


def parse_skill(path: str):
    """Return (front_matter_dict, body_str, raw_char_count). Validates format."""
    raw = open(path, encoding="utf-8").read()
    if not raw.startswith("---"):
        raise SystemExit(f"{path}: Skill must start with '---' front-matter")
    _, fm, body = raw.split("---", 2)
    meta = yaml.safe_load(fm) or {}
    for k in ("name", "description"):
        if not meta.get(k):
            raise SystemExit(f"{path}: front-matter missing '{k}'")
    return meta, body.strip(), len(raw)


def load_inputs(kata_id: str) -> str:
    kdir = kata_dir(kata_id)
    parts = ["# TASK\n" + open(os.path.join(kdir, "task.md")).read()]
    for f in sorted(glob.glob(os.path.join(kdir, "inputs", "*"))):
        parts.append(f"\n# FILE: {os.path.basename(f)}\n```\n{open(f).read()}\n```")
    return "\n".join(parts)


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def call_model(client, model, messages, price_in, price_out):
    resp = client.chat.completions.create(model=model, temperature=0, messages=messages)
    u = resp.usage
    text = resp.choices[0].message.content or ""
    cost = scorer.cost_usd(model, u.prompt_tokens, u.completion_tokens, price_in, price_out)
    return text, cost


def execute(a) -> dict:
    """Run one submission against one kata. Returns a result dict (no printing)."""
    meta, body, skill_chars = parse_skill(a.submission)
    km = yaml.safe_load(open(os.path.join(kata_dir(a.kata), "meta.yaml")))
    cap = km.get("attempt_cap", 3)

    from openai import OpenAI  # imported here so `python scorer.py` etc. work without the dep
    base_url = a.base_url or os.environ.get("KATA_BASE_URL") or "https://api.anthropic.com/v1/"
    key = (os.environ.get("KATA_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
           or os.environ.get("OPENAI_API_KEY"))
    if not key:
        raise SystemExit("set ANTHROPIC_API_KEY (or KATA_API_KEY / OPENAI_API_KEY)")
    client = OpenAI(base_url=base_url, api_key=key)

    messages = [
        {"role": "system", "content": body},
        {"role": "user", "content": load_inputs(a.kata)},
    ]
    total_cost = 0.0
    answer, passed, total, errors = "", 0, 0, ["no attempt"]
    attempts = 0
    for attempts in range(1, cap + 1):
        answer, cost = call_model(client, a.model, messages, a.price_in, a.price_out)
        total_cost += cost
        passed, total, errors = verify(a.kata, answer)
        if total and passed == total:
            break
        messages += [
            {"role": "assistant", "content": answer},
            {"role": "user", "content": "Verification failed: " + "; ".join(errors)
                + ". Return the full corrected output only."},
        ]

    ok = bool(total) and passed == total
    return {
        "kata": a.kata, "name": meta["name"], "model": a.model,
        "solver": a.submission.split("/")[-2] if "/" in a.submission else "?",
        "submission": a.submission, "chars": skill_chars,
        "attempts": attempts, "passed": passed, "total": total,
        "cost": round(total_cost, 6), "ok": ok, "errors": errors,
        "score": scorer.score(total_cost, attempts, skill_chars) if ok else None,
        "run_hash": sha("|".join([a.kata, sha(open(a.submission).read()), a.model, answer.strip()])),
    }


def run(a):
    r = execute(a)
    print(f"── kata {r['kata']} · {r['name']} ─────────")
    print(f"solver:     @{r['solver']}")
    print(f"skill:      {r['submission']}  ({r['chars']} chars)")
    print(f"model:      {r['model']}")
    print(f"attempts:   {r['attempts']}")
    print(f"passed:     {r['passed']} of {r['total']} sealed tests")
    print(f"cost:       ${r['cost']:.4f}")
    print(f"score:      {r['score'] if r['ok'] else '— (must pass all tests)'}")
    print(f"run_hash:   {r['run_hash'][:12]}")
    print("─────────────────────────────────")
    if not r["ok"]:
        print("errors:     " + "; ".join(r["errors"]), file=sys.stderr)
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--kata", required=True)
    p.add_argument("--submission", required=True)
    p.add_argument("--model", default="claude-haiku-4-5")
    p.add_argument("--base-url")
    p.add_argument("--price-in", type=float, help="USD per 1M input tokens (override)")
    p.add_argument("--price-out", type=float, help="USD per 1M output tokens (override)")
    sys.exit(run(p.parse_args()))
