# Kata

A coding kata is a practiced form. Each task here is a kata — you write **one `SKILL.md`** that makes Claude Code solve it, run it against sealed tests, and post your score. **Cheaper, shorter, fewer tries wins.** Built for the Eigen Builder Collective (Session 6 · The Three Primitives).

Sibling to Prompt Golf (Session 4) and Loop Fail (Session 5). Prompt Golf optimizes one prompt; Loop Fail optimizes a squad; Kata optimizes the reusable Skill in between.

## Scoring

```
score = round(cost_usd*1000  +  attempts*5  +  skill_chars/100)     # lower wins
```

Cost dominates — the cheapest correct Skill wins. Attempts penalize Skills that don't produce the right shape on the first try. Length penalizes bloat. You must pass **all** sealed tests for a kata or you don't score. Full formula: [`scorer.py`](scorer.py).

## How to play

1. Fork this repo.
2. Copy the template: `cp submissions/_template/SKILL.md submissions/<your-handle>/001.md`
3. Write your Skill.
4. Run it locally against any OpenAI-compatible endpoint (Node 20+; Python 3.11+ runs the sealed kata checks):
   ```bash
   npm install
   export ANTHROPIC_API_KEY=...            # or KATA_API_KEY / OPENAI_API_KEY
   npx tsx runner.ts --kata 001 --submission submissions/<handle>/001.md --model claude-haiku-4-5
   # other providers: add --base-url https://your-endpoint/v1/
   ```
5. Add your row to [`leaderboard.yaml`](leaderboard.yaml) under `submissions/<your-handle>/`, open a PR. CI re-runs it, recomputes your score, merges. Leaderboard re-renders.

Your `SKILL.md` is public — anyone can read it, copy it, and beat it. That's the point.

## Katas

Warm-ups (001, 002, 004) and the ones that actually punish a lazy Skill (003, 005, 006, 007, 008):

| ID  | Name             | What your Skill has to do | Bite |
|-----|------------------|---------------------------|------|
| 001 | `pr-review`      | Audit a PR diff → JSON of security concerns, perf hotspots, missing tests. | ▚ |
| 002 | `refactor-async` | Convert a sync Python module to async/await, behaviour unchanged. | ▚ |
| 003 | `cron-next`      | Implement `next_run(expr, after)` for 5-field cron — steps, ranges, the day-of-month/day-of-week OR rule, leap years. | ▚▚▚ |
| 004 | `bug-hunt`       | Make a failing test pass with the smallest fix. | ▚ |
| 005 | `secure-query`   | Rewrite an injectable DB module to parameterized queries — passes functional **and** injection tests. | ▚▚▚ |
| 006 | `optimize`       | Rewrite an O(n²) function to O(n). Correct on edge cases, or it times out. | ▚▚ |
| 007 | `task-pool`      | `async run_pool(tasks, limit)` — bounded concurrency, results in input order. Sequential or unbounded both fail. | ▚▚▚ |
| 008 | `semver`         | `compare(a, b)` per SemVer 2.0.0 — the full pre-release precedence chain, build metadata ignored. | ▚▚ |

One new kata drops per Builder Collective session.

## Leaderboard

Also rendered as a page: [`docs/leaderboard.html`](docs/leaderboard.html). 🏆 = current leader · ⚑ = self-reported (run on an endpoint CI can't reach).

<!-- LEADERBOARD:START -->

### 001 · pr-review

| | Solver | Skill | Score | Breakdown | Model |
|---|---|---|---|---|---|
| 🏆 | @eigen ⚑ | `pr-review` | **14** | $0.0030 · 1 att · 573 chars | claude-haiku-4-5 (Anthropic) |

### 002 · refactor-async

| | Solver | Skill | Score | Breakdown | Model |
|---|---|---|---|---|---|
| 🏆 | @eigen ⚑ | `refactor-async` | **10** | $0.0020 · 1 att · 326 chars | claude-haiku-4-5 (Anthropic) |

### 003 · cron-next

_No submissions yet — [be first](#how-to-play)._

### 004 · bug-hunt

| | Solver | Skill | Score | Breakdown | Model |
|---|---|---|---|---|---|
| 🏆 | @eigen ⚑ | `bug-hunt` | **9** | $0.0010 · 1 att · 284 chars | claude-haiku-4-5 (Anthropic) |

### 005 · secure-query

_No submissions yet — [be first](#how-to-play)._

### 006 · optimize

| | Solver | Skill | Score | Breakdown | Model |
|---|---|---|---|---|---|
| 🏆 | @zeeshan8281 ⚑ | `optimize` | **11** | $0.0007 · 1 att · 533 chars | claude-haiku-4-5 (Anthropic) |

### 007 · task-pool

| | Solver | Skill | Score | Breakdown | Model |
|---|---|---|---|---|---|
| 🏆 | @zeeshan8281 ⚑ | `task-pool` | **12** | $0.0008 · 1 att · 610 chars | claude-haiku-4-5 (Anthropic) |

### 008 · semver

_No submissions yet — [be first](#how-to-play)._
<!-- LEADERBOARD:END -->

## Trust

Small invited group, honor system where it can be, deterministic verification where it matters:
- **run_hash** — the runner pins `temperature=0` and hashes `(kata, skill_sha, model, answer)`. Same submission → same hash.
- **CI re-run** — every PR re-runs the submission on repo credits for the same model and confirms the hash. Self-hosted/gated endpoints get a ⚑ badge instead.
- **Public Skills** — every score is backed by a file in `submissions/`. Hardcoded answers are visible and against the spirit; call them out.

Sealed-test hardening (hash-locked archives) is a later item — for v1 the public CI re-run is the anti-cheat.

## Repo

TypeScript harness (run with `tsx`): `runner.ts` attempt loop · `scorer.ts` formula · `verifier.ts` → per-kata Python `katas/*/check.py` (via `katas/_run_check.py`) · `ci_verify.ts` PR validation + re-run · `render.ts` yaml→README + `web/src/data.json`. The kata checks stay Python because they execute the submitted Python answers. Frontend: the Vite/React app in `web/`.
