"""Kata scoring. Lower wins. This is the whole formula — read it, it's the game.

    score = round(cost_usd*1000  +  attempts*5  +  skill_chars/100)

- cost dominates: cheapest correct Skill wins.
- attempts: penalty per model call it took to converge (right shape first try = cheap).
- skill_chars: bloat penalty. Long verbose Skills lose to short precise ones.
"""
from __future__ import annotations  # ponytail: lets `float | None` annotations run on py3.9


def score(cost_usd: float, attempts: int, skill_chars: int) -> int:
    return round(cost_usd * 1000 + attempts * 5 + skill_chars / 100)


# Price table, USD per 1M tokens (input, output). One place, PRs update it.
# Unknown models fall back to DEFAULT and print a warning — cost stays consistent
# for everyone because everyone scores against this same table.
PRICES = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-8": (15.00, 75.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
}
DEFAULT_PRICE = (1.00, 5.00)  # ponytail: guess for unlisted models; override with --price-in/out


def cost_usd(model: str, in_tokens: int, out_tokens: int,
             price_in: float | None = None, price_out: float | None = None) -> float:
    if price_in is None or price_out is None:
        pi, po = next((v for k, v in PRICES.items() if k in model), DEFAULT_PRICE)
        price_in = price_in if price_in is not None else pi
        price_out = price_out if price_out is not None else po
    return in_tokens / 1e6 * price_in + out_tokens / 1e6 * price_out


if __name__ == "__main__":
    # ponytail self-check. NOTE: the PRD result block shows score 142 for
    # ($0.006, 3 attempts, 412 chars) — that contradicts the PRD's own formula
    # (6 + 15 + 4.12 = 25.12 -> 25). The formula is canonical; 142 is a PRD typo.
    assert score(0.006, 3, 412) == 25, score(0.006, 3, 412)
    assert score(0, 0, 0) == 0
    assert score(0.05, 1, 800) > score(0.006, 3, 412)  # expensive+bloated loses
    print("scorer ok — example scores", score(0.006, 3, 412))
