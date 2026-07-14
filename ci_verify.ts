/**
 * CI: validate the leaderboard, and (with a key) re-run entries to confirm scores.
 *
 *   tsx ci_verify.ts --dry                 structural checks only, no API key, no model calls.
 *   tsx ci_verify.ts --dry --author <login> also enforce: newly-added rows must be your own.
 *   tsx ci_verify.ts                       the above, then re-run each non-self-reported entry.
 *
 * Fails (exit 1) if any entry is malformed, points a solver at a submission that isn't
 * theirs, adds a row under someone else's handle, or (full mode) doesn't pass the tests /
 * claims a score more than SLACK below what we recompute. Self-reported (⚑) rows run on
 * endpoints CI can't reach, so the re-run is skipped — but structural checks still apply.
 */
import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, statSync } from "node:fs";
import { parseArgs } from "node:util";
import { parse as parseYaml } from "yaml";

import { kataDir } from "./verifier.ts";

const SLACK = 3; // allowed score drift from provider-side cost/token jitter
const REQUIRED = ["solver", "skill", "model", "name", "score"] as const;

type Row = Record<string, unknown>;

/** Structural validation — no network. Returns a list of error strings. */
export function checkRow(kid: string, row: Row): string[] {
  const tag = `${kid} @${row.solver ?? "?"}`;
  const errs: string[] = [];
  for (const k of REQUIRED) {
    if (row[k] === undefined || row[k] === null || row[k] === "") errs.push(`${tag}: missing '${k}'`);
  }
  if (errs.length) return errs;

  if (typeof row.score !== "number") errs.push(`${tag}: score must be a number, got ${JSON.stringify(row.score)}`);

  // solver↔submission binding: your row must point at your own submissions dir,
  // and stay inside it — no pointing at someone else's file or path traversal.
  const skill = String(row.skill);
  const solver = String(row.solver);
  const prefix = `submissions/${solver}/`;
  if (!skill.startsWith(prefix) || skill.split("/").includes("..")) {
    errs.push(`${tag}: skill '${skill}' must live under ${prefix} (no other dirs, no '..')`);
  } else if (!existsSync(skill) || !statSync(skill).isFile()) {
    errs.push(`${tag}: skill file '${skill}' does not exist`);
  }
  try {
    kataDir(kid); // kata must exist
  } catch (e) {
    errs.push(`${tag}: ${(e as Error).message}`);
  }
  return errs;
}

/** Keys (kata|solver|skill) already present in the base ref, so we only gate NEW rows. */
function baseRowKeys(baseRef: string): Set<string> {
  const keys = new Set<string>();
  try {
    const raw = execFileSync("git", ["show", `${baseRef}:leaderboard.yaml`], { encoding: "utf-8" });
    const data = (parseYaml(raw) as Record<string, Row[]>) ?? {};
    for (const [kid, rows] of Object.entries(data)) {
      for (const r of rows ?? []) keys.add(`${kid}|${r.solver}|${r.skill}`);
    }
  } catch {
    /* no base (first push, shallow clone) — treat every row as new */
  }
  return keys;
}

async function main(): Promise<void> {
  const { values } = parseArgs({
    options: {
      dry: { type: "boolean", default: false },
      author: { type: "string" },
      "base-ref": { type: "string", default: "origin/main" },
    },
  });
  const author = values.author && values.author.trim() ? values.author.trim() : null;

  let data: Record<string, Row[]>;
  try {
    data = (parseYaml(readFileSync("leaderboard.yaml", "utf-8")) as Record<string, Row[]>) ?? {};
  } catch (e) {
    console.error(`leaderboard.yaml is not valid YAML: ${(e as Error).message}`);
    process.exit(1);
  }
  const base = author ? baseRowKeys(values["base-ref"]!) : new Set<string>();
  const failures: string[] = [];

  for (const [kid, rows] of Object.entries(data)) {
    for (const row of rows ?? []) {
      const tag = `${kid} @${row.solver ?? "?"}`;
      const rowErrs = checkRow(kid, row);
      if (rowErrs.length) {
        failures.push(...rowErrs);
        continue;
      }
      // author binding: a PR can only ADD rows under its own author's handle.
      if (author) {
        const key = `${kid}|${row.solver}|${row.skill}`;
        if (!base.has(key) && row.solver !== author) {
          failures.push(`${tag}: PR by @${author} can't add a row for @${row.solver} — submit under your own handle`);
          continue;
        }
      }
      if (values.dry) {
        console.log(`ok   ${tag}: well-formed`);
        continue;
      }
      if (row.self_reported) {
        console.log(`skip ${tag}: self-reported ⚑ (structure ok, re-run skipped)`);
        continue;
      }
      const { execute } = await import("./runner.ts"); // deferred: needs the openai dep + a key
      const r = await execute({ kata: kid, submission: String(row.skill), model: String(row.model) });
      if (!r.ok) {
        failures.push(`${tag}: failed tests — ${r.errors.join("; ")}`);
      } else if ((row.score as number) < r.score! - SLACK) {
        failures.push(`${tag}: claimed ${row.score} but re-ran to ${r.score}`);
      } else {
        console.log(`ok   ${tag}: score ${r.score} (claimed ${row.score})`);
      }
    }
  }

  if (failures.length) {
    console.error("\nVERIFY FAILED:\n  " + failures.join("\n  "));
    process.exit(1);
  }
  console.log("all leaderboard entries verified" + (values.dry ? " (structure only)" : ""));
}

if (import.meta.url === `file://${process.argv[1]}`) main();
