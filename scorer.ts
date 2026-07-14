/**
 * Kata scoring. Lower wins. This is the whole formula — read it, it's the game.
 *
 *     score = round(cost_usd*1000  +  attempts*5  +  skill_chars/100)
 *
 * - cost dominates: cheapest correct Skill wins.
 * - attempts: penalty per model call it took to converge (right shape first try = cheap).
 * - skill_chars: bloat penalty. Long verbose Skills lose to short precise ones.
 */

export function score(costUsd: number, attempts: number, skillChars: number): number {
  return Math.round(costUsd * 1000 + attempts * 5 + skillChars / 100);
}

// Price table, USD per 1M tokens [input, output]. One place, PRs update it.
// Unknown models fall back to DEFAULT_PRICE — cost stays consistent for everyone
// because everyone scores against this same table. Insertion order = match order.
export const PRICES: Record<string, [number, number]> = {
  "claude-haiku-4-5": [1.0, 5.0],
  "claude-sonnet-4-6": [3.0, 15.0],
  "claude-opus-4-8": [15.0, 75.0],
  "gpt-4o-mini": [0.15, 0.6],
  "gpt-4o": [2.5, 10.0],
};
export const DEFAULT_PRICE: [number, number] = [1.0, 5.0]; // guess for unlisted models; override with --price-in/out

export function costUsd(
  model: string,
  inTokens: number,
  outTokens: number,
  priceIn?: number,
  priceOut?: number,
): number {
  if (priceIn === undefined || priceOut === undefined) {
    const hit = Object.entries(PRICES).find(([k]) => model.includes(k));
    const [pi, po] = hit ? hit[1] : DEFAULT_PRICE;
    priceIn = priceIn ?? pi;
    priceOut = priceOut ?? po;
  }
  return (inTokens / 1e6) * priceIn + (outTokens / 1e6) * priceOut;
}

// ponytail self-check: `tsx scorer.ts`. Same asserts the Python had.
function selfCheck(): void {
  const assert = (cond: boolean, msg: string) => {
    if (!cond) throw new Error("scorer self-check failed: " + msg);
  };
  assert(score(0.006, 3, 412) === 25, String(score(0.006, 3, 412)));
  assert(score(0, 0, 0) === 0, "zero");
  assert(score(0.05, 1, 800) > score(0.006, 3, 412), "expensive+bloated must lose");
  console.log("scorer ok — example score", score(0.006, 3, 412));
}

if (import.meta.url === `file://${process.argv[1]}`) selfCheck();
