/**
 * Kata runner — load a SKILL.md, drive it against a sealed kata, score it.
 *
 *     export ANTHROPIC_API_KEY=...
 *     npx tsx runner.ts --kata 001 --submission submissions/<handle>/001.md --model claude-haiku-4-5
 *
 * Talks to any OpenAI-compatible endpoint. Defaults to Anthropic's compat endpoint;
 * point elsewhere with --base-url (or KATA_BASE_URL) for OpenAI/local models.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { parseArgs } from "node:util";
import { parse as parseYaml } from "yaml";

import { costUsd, score } from "./scorer.ts";
import { kataDir, verify } from "./verifier.ts";

export type Args = {
  kata: string;
  submission: string;
  model: string;
  baseUrl?: string;
  priceIn?: number;
  priceOut?: number;
};

type Skill = { meta: Record<string, unknown>; body: string; chars: number };

export function parseSkill(path: string): Skill {
  const raw = readFileSync(path, "utf-8");
  if (!raw.startsWith("---")) throw new Error(`${path}: Skill must start with '---' front-matter`);
  const parts = raw.split("---");
  const meta = (parseYaml(parts[1]) as Record<string, unknown>) ?? {};
  const body = parts.slice(2).join("---"); // keep any '---' inside the body, like Python's maxsplit=2
  for (const k of ["name", "description"]) {
    if (!meta[k]) throw new Error(`${path}: front-matter missing '${k}'`);
  }
  return { meta, body: body.trim(), chars: raw.length };
}

export function loadInputs(kataId: string): string {
  const kdir = kataDir(kataId);
  const parts = ["# TASK\n" + readFileSync(join(kdir, "task.md"), "utf-8")];
  let files: string[] = [];
  try {
    files = readdirSync(join(kdir, "inputs")).sort();
  } catch {
    /* no inputs dir */
  }
  for (const f of files) {
    if (f.startsWith(".")) continue; // skip .gitkeep etc., matching Python glob("*")
    const content = readFileSync(join(kdir, "inputs", f), "utf-8");
    parts.push(`\n# FILE: ${f}\n\`\`\`\n${content}\n\`\`\``);
  }
  return parts.join("\n");
}

async function callModel(
  client: import("openai").default,
  model: string,
  messages: import("openai").default.Chat.ChatCompletionMessageParam[],
  priceIn?: number,
  priceOut?: number,
): Promise<[string, number]> {
  const resp = await client.chat.completions.create({ model, temperature: 0, messages });
  const u = resp.usage!;
  const text = resp.choices[0].message.content ?? "";
  const cost = costUsd(model, u.prompt_tokens, u.completion_tokens, priceIn, priceOut);
  return [text, cost];
}

export type Result = {
  kata: string;
  name: unknown;
  model: string;
  solver: string;
  submission: string;
  chars: number;
  attempts: number;
  passed: number;
  total: number;
  cost: number;
  ok: boolean;
  errors: string[];
  score: number | null;
};

/** Run one submission against one kata. Returns a result object (no printing). */
export async function execute(a: Args): Promise<Result> {
  const { meta, body, chars } = parseSkill(a.submission);
  const km = (parseYaml(readFileSync(join(kataDir(a.kata), "meta.yaml"), "utf-8")) as Record<string, unknown>) ?? {};
  const cap = (km.attempt_cap as number) ?? 3;

  const { default: OpenAI } = await import("openai"); // deferred so `tsx scorer.ts` etc. need no key/dep
  const baseUrl = a.baseUrl || process.env.KATA_BASE_URL || "https://api.anthropic.com/v1/";
  const key = process.env.KATA_API_KEY || process.env.ANTHROPIC_API_KEY || process.env.OPENAI_API_KEY;
  if (!key) throw new Error("set ANTHROPIC_API_KEY (or KATA_API_KEY / OPENAI_API_KEY)");
  const client = new OpenAI({ baseURL: baseUrl, apiKey: key });

  const messages: import("openai").default.Chat.ChatCompletionMessageParam[] = [
    { role: "system", content: body },
    { role: "user", content: loadInputs(a.kata) },
  ];

  let totalCost = 0;
  let answer = "";
  let passed = 0;
  let total = 0;
  let errors: string[] = ["no attempt"];
  let attempts = 0;
  for (attempts = 1; attempts <= cap; attempts++) {
    const [text, cost] = await callModel(client, a.model, messages, a.priceIn, a.priceOut);
    answer = text;
    totalCost += cost;
    ({ passed, total, errors } = verify(a.kata, answer));
    if (total && passed === total) break;
    messages.push({ role: "assistant", content: answer });
    messages.push({
      role: "user",
      content: "Verification failed: " + errors.join("; ") + ". Return the full corrected output only.",
    });
  }

  const ok = Boolean(total) && passed === total;
  const solver = a.submission.includes("/") ? a.submission.split("/").slice(-2)[0] : "?";
  return {
    kata: a.kata,
    name: meta.name,
    model: a.model,
    solver,
    submission: a.submission,
    chars,
    attempts,
    passed,
    total,
    cost: Math.round(totalCost * 1e6) / 1e6,
    ok,
    errors,
    score: ok ? score(totalCost, attempts, chars) : null,
  };
}

async function run(a: Args): Promise<number> {
  const r = await execute(a);
  console.log(`── kata ${r.kata} · ${r.name} ─────────`);
  console.log(`solver:     @${r.solver}`);
  console.log(`skill:      ${r.submission}  (${r.chars} chars)`);
  console.log(`model:      ${r.model}`);
  console.log(`attempts:   ${r.attempts}`);
  console.log(`passed:     ${r.passed} of ${r.total} sealed tests`);
  console.log(`cost:       $${r.cost.toFixed(4)}`);
  console.log(`score:      ${r.ok ? r.score : "— (must pass all tests)"}`);
  console.log("─────────────────────────────────");
  if (!r.ok) console.error("errors:     " + r.errors.join("; "));
  return r.ok ? 0 : 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const { values } = parseArgs({
    options: {
      kata: { type: "string" },
      submission: { type: "string" },
      model: { type: "string", default: "claude-haiku-4-5" },
      "base-url": { type: "string" },
      "price-in": { type: "string" },
      "price-out": { type: "string" },
    },
  });
  if (!values.kata || !values.submission) {
    console.error("usage: tsx runner.ts --kata <id> --submission <path> [--model <m>]");
    process.exit(2);
  }
  const a: Args = {
    kata: values.kata,
    submission: values.submission,
    model: values.model!,
    baseUrl: values["base-url"],
    priceIn: values["price-in"] ? Number(values["price-in"]) : undefined,
    priceOut: values["price-out"] ? Number(values["price-out"]) : undefined,
  };
  run(a).then((code) => process.exit(code));
}
