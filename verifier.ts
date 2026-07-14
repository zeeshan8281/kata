/**
 * Runs a kata's sealed Python check against a Skill's answer.
 *
 * Kata answers are Python programs and each kata's check.py `exec`s them, so the
 * checks stay Python. We bridge to them via katas/_run_check.py (see verify()).
 *
 * v1 "sealed" = the check runs deterministically and the CI re-run is the anti-cheat.
 * Hash-locked / held-out test archives are a later item.
 */
import { spawnSync } from "node:child_process";
import { mkdtempSync, readdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));

export function kataDir(kataId: string): string {
  const dir = join(HERE, "katas");
  const hit = readdirSync(dir).find((d) => d.startsWith(`${kataId}_`));
  if (!hit) throw new Error(`no kata ${kataId} under katas/`);
  return join(dir, hit);
}

export type CheckResult = { passed: number; total: number; errors: string[] };

export function verify(kataId: string, answer: string): CheckResult {
  const kdir = kataDir(kataId);
  const tmp = mkdtempSync(join(tmpdir(), "kata-"));
  const answerFile = join(tmp, "answer.txt");
  writeFileSync(answerFile, answer, "utf-8");

  const shim = join(HERE, "katas", "_run_check.py");
  const proc = spawnSync("python3", [shim, kdir, answerFile], {
    encoding: "utf-8",
    maxBuffer: 64 * 1024 * 1024,
    timeout: 120_000, // a check may run the answer (asyncio, perf caps); generous ceiling
  });
  if (proc.status !== 0) {
    const why = (proc.stderr || proc.stdout || String(proc.error ?? "unknown")).trim();
    return { passed: 0, total: 0, errors: [`check harness failed: ${why}`] };
  }
  try {
    const line = proc.stdout.trim().split("\n").pop() ?? "{}";
    const out = JSON.parse(line);
    return { passed: out.passed, total: out.total, errors: out.errors ?? [] };
  } catch {
    return { passed: 0, total: 0, errors: [`could not parse check output: ${proc.stdout}`] };
  }
}
