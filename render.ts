/**
 * Render leaderboard.yaml into the README table and the React app's data.json.
 *
 * Single source of truth is leaderboard.yaml. The deployed site is the Vite app in
 * web/ (Vercel builds it), which imports web/src/data.json — so that's what we emit.
 * Run after any change (CI does too, on push to main).
 */
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { parse as parseYaml } from "yaml";

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = "https://github.com/zeeshan8281/kata";

// id -> [name, one-line description, difficulty 1-3]
const KATA_META: Record<string, [string, string, number]> = {
  "001": ["pr-review", "Audit a PR diff → JSON of security concerns, perf hotspots, missing tests.", 1],
  "002": ["refactor-async", "Convert a sync Python module to async/await, behaviour unchanged.", 1],
  "003": ["cron-next", "next_run(expr, after) for 5-field cron — steps, ranges, the day-of-month/day-of-week OR rule, leap years.", 3],
  "004": ["bug-hunt", "Make a failing test pass with the smallest fix.", 1],
  "005": ["secure-query", "Rewrite an injectable DB module to parameterized queries — functional AND injection tests.", 3],
  "006": ["optimize", "Rewrite an O(n²) function to O(n). Correct on edge cases, or it times out.", 2],
  "007": ["task-pool", "async run_pool(tasks, limit) — bounded concurrency, results in input order.", 3],
  "008": ["semver", "compare(a, b) per SemVer 2.0.0 — the full pre-release precedence chain.", 2],
};

type Row = Record<string, any>;

// lower score wins; tie -> earlier created date takes the crown
function ordered(rows: Row[]): Row[] {
  return [...rows].sort(
    (a, b) => a.score - b.score || String(a.created ?? "9999").localeCompare(String(b.created ?? "9999")),
  );
}

function readmeTable(data: Record<string, Row[]>): string {
  const out: string[] = [];
  for (const [kid, [name]] of Object.entries(KATA_META)) {
    out.push(`\n### ${kid} · ${name}\n`);
    const rows = ordered(data[kid] ?? []);
    if (!rows.length) {
      out.push("_No submissions yet — [be first](#how-to-play)._");
      continue;
    }
    out.push("| | Solver | Skill | Score | Breakdown | Model |");
    out.push("|---|---|---|---|---|---|");
    rows.forEach((r, i) => {
      const crown = i === 0 ? "🏆" : "";
      const badge = r.self_reported ? " ⚑" : "";
      out.push(
        `| ${crown} | @${r.solver}${badge} | \`${r.name}\` | **${r.score}** | ` +
          `$${Number(r.cost).toFixed(4)} · ${r.attempts} att · ${r.chars} chars | ` +
          `${r.model} (${r.provider ?? "?"}) |`,
      );
    });
  }
  return out.join("\n");
}

function updateReadme(table: string): void {
  const path = join(HERE, "README.md");
  const txt = readFileSync(path, "utf-8");
  const A = "<!-- LEADERBOARD:START -->";
  const B = "<!-- LEADERBOARD:END -->";
  const [pre, rest] = txt.split(A);
  const [, post] = rest.split(B);
  writeFileSync(path, `${pre}${A}\n${table}\n${B}${post}`);
}

function writeWebData(data: Record<string, Row[]>): void {
  const payload = {
    repo: REPO,
    template: readFileSync(join(HERE, "submissions", "_template", "SKILL.md"), "utf-8"),
    katas: Object.entries(KATA_META).map(([id, [name, desc, diff]]) => ({ id, name, desc, diff })),
    board: Object.fromEntries(Object.keys(KATA_META).map((k) => [k, ordered(data[k] ?? [])])),
  };
  const path = join(HERE, "web", "src", "data.json");
  if (existsSync(dirname(path))) writeFileSync(path, JSON.stringify(payload, null, 2) + "\n");
}

const data = (parseYaml(readFileSync(join(HERE, "leaderboard.yaml"), "utf-8")) as Record<string, Row[]>) ?? {};
writeWebData(data);
updateReadme(readmeTable(data));
console.log("rendered -> README.md + web/src/data.json");
