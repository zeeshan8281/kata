import { useEffect, useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Input,
  Label,
} from "@layr-labs/eigen-design";
import data from "./data.json";

type User = { login: string; avatar_url: string };
type Kata = { id: string; name: string; desc: string; diff: number };
type Row = {
  solver: string; name: string; model: string; score: number;
  cost: number; attempts: number; chars: number; self_reported?: boolean;
};

const KEY = "kata_user";
const DIFF = ["", "warm-up", "medium", "hard"] as const;

function useUser() {
  const [user, setUser] = useState<User | null>(null);
  useEffect(() => {
    try { setUser(JSON.parse(localStorage.getItem(KEY) || "null")); } catch { /* ignore */ }
  }, []);
  const save = (u: User | null) => {
    if (u) localStorage.setItem(KEY, JSON.stringify(u)); else localStorage.removeItem(KEY);
    setUser(u);
  };
  return { user, save };
}

function Mono({ children }: { children: React.ReactNode }) {
  return <span className="font-mono">{children}</span>;
}

function SignInDialog({ open, onOpenChange, onSignedIn }: {
  open: boolean; onOpenChange: (o: boolean) => void; onSignedIn: (u: User) => void;
}) {
  const [handle, setHandle] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function go() {
    const h = handle.trim().replace(/^@/, "");
    if (!h) return;
    setBusy(true); setErr("Checking…");
    try {
      const r = await fetch("https://api.github.com/users/" + encodeURIComponent(h));
      if (!r.ok) { setErr(`No GitHub user "${h}".`); setBusy(false); return; }
      const u = await r.json();
      onSignedIn({ login: u.login, avatar_url: u.avatar_url });
      onOpenChange(false); setErr(""); setBusy(false);
    } catch { setErr("Network error, try again."); setBusy(false); }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Set your GitHub handle</DialogTitle>
          <DialogDescription>
            This isn't a login — it just fills your handle into the commands below and remembers it locally.
            Your real identity is the account you open the PR from; CI checks the commit author before your row lands.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-2">
          <Label htmlFor="handle">GitHub handle</Label>
          <Input id="handle" placeholder="octocat" autoComplete="off" spellCheck={false}
            value={handle} onChange={(e) => setHandle(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && go()} />
          <p className="text-destructive text-xs min-h-4">{err}</p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={go} disabled={busy}>Set handle</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function HowToDialog({ open, onOpenChange, handle, user }: {
  open: boolean; onOpenChange: (o: boolean) => void; handle: string; user: User | null;
}) {
  const [copied, setCopied] = useState(false);
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>How to play</DialogTitle>
          <DialogDescription>
            {user ? `Handle set to @${user.login} — the commands below are filled in for you.` : "Five steps. Minutes, not hours."}
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-3">
          <Step n={1} title="Fork the repo">
            Everything lives on GitHub — the runner, the sealed katas, the leaderboard.{" "}
            <a className="text-primary underline-offset-4 hover:underline" href={data.repo + "/fork"} target="_blank" rel="noreferrer">Fork it →</a>
          </Step>
          <Step n={2} title="Copy the template">
            Start from the blank Skill and drop it under your handle.
            <Pre>{`cp submissions/_template/SKILL.md submissions/${handle}/001.md`}</Pre>
          </Step>
          <Step n={3} title="Write your Skill">
            The Skill body becomes the system prompt. Short and precise beats long and verbose — length is in the score.
          </Step>
          <Step n={4} title="Run it against any model">
            Any OpenAI-compatible endpoint. Bring your own key.
            <Pre>{`export ANTHROPIC_API_KEY=...
python runner.py --kata 001 \\
  --submission submissions/${handle}/001.md \\
  --model claude-haiku-4-5`}</Pre>
          </Step>
          <Step n={5} title="Open a PR with your score">
            Add your row to <Mono>leaderboard.yaml</Mono>. CI re-runs the submission, confirms the run hash, merges. The board re-renders.
          </Step>
        </div>
        <div className="mt-1">
          <div className="mb-2 flex items-center justify-between">
            <span className="font-mono text-sm text-muted-foreground">submissions/&lt;handle&gt;/&lt;kata&gt;.md</span>
            <Button variant="outline" size="sm" onClick={() => {
              navigator.clipboard.writeText(data.template); setCopied(true); setTimeout(() => setCopied(false), 1400);
            }}>{copied ? "Copied ✓" : "Copy template"}</Button>
          </div>
          <pre className="overflow-auto rounded-lg border border-border bg-foreground text-background p-4 font-mono text-xs leading-7">{data.template}</pre>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function App() {
  const { user, save } = useUser();
  const [open, setOpen] = useState(false);
  const [howOpen, setHowOpen] = useState(false);
  const handle = user?.login ?? "<your-handle>";

  const katas = data.katas as Kata[];
  const board = data.board as Record<string, Row[]>;
  const [kataId, setKataId] = useState(katas[0].id);
  const active = katas.find((k) => k.id === kataId) ?? katas[0];
  const rows = board[kataId] ?? [];
  const totalSubs = katas.reduce((s, k) => s + (board[k.id]?.length ?? 0), 0);

  return (
    <div className="min-h-screen">
      {/* nav */}
      <nav className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-5">
          <div className="flex items-center gap-2.5 font-semibold tracking-tight">
            <span className="size-2.5 rounded-md bg-primary" />Kata
          </div>
          <div className="flex items-center gap-4 text-sm">
            <button className="text-muted-foreground hover:text-foreground" onClick={() => setHowOpen(true)}>How to play</button>
            <a className="text-muted-foreground hover:text-foreground" href="#leaderboard">Leaderboard</a>
            <a className="text-muted-foreground hover:text-foreground" href={data.repo} target="_blank" rel="noreferrer">GitHub</a>
            {user ? (
              <span className="flex items-center gap-2 font-medium">
                <img src={user.avatar_url} alt="" className="size-6 rounded-full border border-border" />
                @{user.login}
                <span className="cursor-pointer text-xs font-normal text-muted-foreground hover:text-foreground"
                  onClick={() => save(null)}>clear</span>
              </span>
            ) : (
              <Button size="sm" onClick={() => setOpen(true)}>Set your handle</Button>
            )}
          </div>
        </div>
      </nav>

      {/* hero */}
      <header className="mx-auto max-w-5xl px-5 pb-10 pt-16 text-center">
        <Badge variant="outline" className="mb-4 font-mono">Eigen Builder Collective · Session 6</Badge>
        <h1 className="text-heading-xl font-heading mx-auto max-w-3xl">
          Write one Skill.<br /><span className="text-primary">Beat the leaderboard.</span>
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-lg text-muted-foreground">
          Each task is a kata. Submit one <Mono>SKILL.md</Mono> that makes Claude Code solve it — sealed
          tests grade it, the board ranks it. <span className="font-medium text-foreground">Cheaper, shorter, fewer tries wins.</span>
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-2.5">
          {!user && <Button onClick={() => setOpen(true)}>Set your handle</Button>}
          <Button variant="outline" asChild><a href={data.repo + "/fork"} target="_blank" rel="noreferrer">Fork the repo</a></Button>
          <Button variant="ghost" onClick={() => setHowOpen(true)}>How it works</Button>
        </div>
        <p className="mt-6 font-mono text-xs text-muted-foreground">
          {totalSubs} Skills submitted · {katas.length} katas · new kata each session
        </p>
      </header>

      {/* board — the page */}
      <main id="leaderboard" className="mx-auto max-w-5xl px-5 pb-20">
        <div className="border-t border-border pt-10">
          <div className="flex items-baseline justify-between">
            <h2 className="text-heading-md font-heading">Leaderboard</h2>
            <span className="hidden font-mono text-xs text-muted-foreground sm:block">score = cost·1000 + attempts·5 + chars/100 · lower wins</span>
          </div>
          <p className="mb-6 mt-1 text-muted-foreground">Pick a kata. Pass every sealed test, then land the lowest score.</p>

          <div className="grid gap-5 md:grid-cols-[230px_1fr]">
            {/* kata rail */}
            <div className="flex gap-2 overflow-x-auto pb-1 md:flex-col md:overflow-visible md:pb-0">
              {katas.map((k) => {
                const n = (board[k.id] ?? []).length;
                const on = k.id === kataId;
                return (
                  <button key={k.id} onClick={() => setKataId(k.id)}
                    className={`shrink-0 rounded-md border px-3 py-2.5 text-left transition-colors md:shrink ${on ? "border-primary bg-primary/5" : "border-border hover:bg-secondary"}`}>
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-mono text-sm font-medium">{k.name}</span>
                      <Badge variant={k.diff >= 3 ? "default" : "secondary"} className="text-[10px]">{DIFF[k.diff]}</Badge>
                    </div>
                    <div className="mt-0.5 font-mono text-xs text-muted-foreground">{k.id} · {n} sub{n !== 1 ? "s" : ""}</div>
                  </button>
                );
              })}
            </div>

            {/* board panel */}
            <div>
              <div className="mb-3">
                <div className="flex items-baseline gap-2">
                  <h3 className="font-mono text-lg font-semibold">{active.id} · {active.name}</h3>
                  <Badge variant={active.diff >= 3 ? "default" : "secondary"}>{DIFF[active.diff]}</Badge>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">{active.desc}</p>
              </div>
              <Card className="overflow-hidden">
                {rows.length === 0 ? (
                  <CardContent className="py-10 text-center text-muted-foreground">No submissions yet — open a PR and be first.</CardContent>
                ) : (
                  <table className="w-full border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-border text-xs uppercase tracking-wide text-muted-foreground">
                        <th className="w-10 px-3 py-2.5 text-left">#</th>
                        <th className="px-3 py-2.5 text-left">Solver</th>
                        <th className="px-3 py-2.5 text-right">Score</th>
                        <th className="hidden px-3 py-2.5 text-left sm:table-cell">Breakdown</th>
                        <th className="px-3 py-2.5 text-left">Model</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((r, i) => (
                        <tr key={i} className={`border-t border-border ${i === 0 ? "bg-primary/5" : ""}`}>
                          <td className={`px-3 py-2.5 font-mono ${i === 0 ? "font-bold text-primary" : "text-muted-foreground"}`}>{i + 1}</td>
                          <td className="px-3 py-2.5 font-medium">
                            @{r.solver}
                            {r.self_reported && <Badge variant="outline" className="ml-1.5 text-[10px]">self-reported</Badge>}
                          </td>
                          <td className="px-3 py-2.5 text-right font-mono text-base font-semibold">{r.score}</td>
                          <td className="hidden px-3 py-2.5 font-mono text-xs text-muted-foreground sm:table-cell">${r.cost.toFixed(4)} · {r.attempts} att · {r.chars} ch</td>
                          <td className="px-3 py-2.5"><Badge variant="secondary" className="font-mono text-xs">{r.model}</Badge></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </Card>
              <p className="mt-3 font-mono text-xs text-muted-foreground sm:hidden">score = cost·1000 + attempts·5 + chars/100 · lower wins</p>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-border py-10 text-center text-sm text-muted-foreground">
        Built for the Eigen Builder Collective · <a className="text-primary hover:underline" href={data.repo} target="_blank" rel="noreferrer">source on GitHub</a><br />
        Sibling to Prompt Golf (S4) and Loop Fail (S5).
      </footer>

      <SignInDialog open={open} onOpenChange={setOpen} onSignedIn={save} />
      <HowToDialog open={howOpen} onOpenChange={setHowOpen} handle={handle} user={user} />
    </div>
  );
}

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardContent className="flex gap-4 py-5">
        <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-primary font-mono text-sm font-semibold text-primary-foreground">{n}</span>
        <div>
          <h3 className="font-semibold">{title}</h3>
          <div className="mt-1 text-sm text-muted-foreground">{children}</div>
        </div>
      </CardContent>
    </Card>
  );
}

function Pre({ children }: { children: React.ReactNode }) {
  return <pre className="mt-2.5 overflow-auto rounded-lg border border-border bg-foreground p-3.5 font-mono text-xs leading-7 text-background">{children}</pre>;
}
