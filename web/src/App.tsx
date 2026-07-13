import { useEffect, useState } from "react";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
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
          <DialogTitle>Sign in with GitHub</DialogTitle>
          <DialogDescription>
            Your GitHub handle is your identity — the same one you submit PRs with. No password, no OAuth.
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
          <Button onClick={go} disabled={busy}>Continue</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function App() {
  const { user, save } = useUser();
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const handle = user?.login ?? "<your-handle>";

  return (
    <div className="min-h-screen">
      {/* nav */}
      <nav className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-5">
          <div className="flex items-center gap-2.5 font-semibold tracking-tight">
            <span className="size-2.5 rounded-md bg-primary" />Kata
          </div>
          <div className="flex items-center gap-4 text-sm">
            <a className="text-muted-foreground hover:text-foreground" href="#how">How to play</a>
            <a className="text-muted-foreground hover:text-foreground" href="#leaderboard">Leaderboard</a>
            <a className="text-muted-foreground hover:text-foreground" href={data.repo} target="_blank" rel="noreferrer">GitHub</a>
            {user ? (
              <span className="flex items-center gap-2 font-medium">
                <img src={user.avatar_url} alt="" className="size-6 rounded-full border border-border" />
                @{user.login}
                <span className="cursor-pointer text-xs font-normal text-muted-foreground hover:text-foreground"
                  onClick={() => save(null)}>sign out</span>
              </span>
            ) : (
              <Button size="sm" onClick={() => setOpen(true)}>Sign in with GitHub</Button>
            )}
          </div>
        </div>
      </nav>

      {/* hero */}
      <header className="mx-auto max-w-5xl px-5 pb-14 pt-20 text-center">
        <div className="mx-auto mb-6 h-[3px] w-14 rounded-full bg-gradient-to-r from-primary to-[--color-chart-1]" />
        <Badge variant="outline" className="mb-4 font-mono">Eigen Builder Collective · Session 6</Badge>
        <h1 className="text-heading-xl mx-auto max-w-3xl">
          Write one Skill.<br /><span className="text-[--color-chart-1]">Beat the leaderboard.</span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-muted-foreground">
          A coding kata is a practiced form. Each task is a kata — you submit a single{" "}
          <Mono>SKILL.md</Mono> that makes Claude Code solve it, run it against sealed tests, and post your score.
        </p>
        <p className="mt-2 text-lg font-semibold">Cheaper, shorter, fewer tries wins.</p>
        <div className="mt-8 flex flex-wrap justify-center gap-2.5">
          {!user && <Button onClick={() => setOpen(true)}>Sign in with GitHub</Button>}
          <Button variant="outline" asChild><a href={data.repo + "/fork"} target="_blank" rel="noreferrer">Fork the repo</a></Button>
          <Button variant="ghost" asChild><a href="#how">How it works</a></Button>
        </div>
      </header>

      {/* how to play */}
      <Section id="how" title="How to play"
        sub={user ? `Signed in as @${user.login} — the commands below are filled in for you.` : "Five steps. Barrier to entry is minutes, not hours."}>
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
      </Section>

      {/* submission template */}
      <Section id="skill" title="The submission" sub="One file. Valid front-matter, then the Skill body. That's the whole thing.">
        <Card>
          <CardHeader className="border-b">
            <CardTitle className="font-mono text-sm text-muted-foreground">submissions/&lt;handle&gt;/&lt;kata&gt;.md</CardTitle>
            <div className="col-start-2 row-span-2 row-start-1 self-start justify-self-end">
              <Button variant="outline" size="sm" onClick={() => {
                navigator.clipboard.writeText(data.template); setCopied(true); setTimeout(() => setCopied(false), 1400);
              }}>{copied ? "Copied ✓" : "Copy template"}</Button>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            <pre className="overflow-auto rounded-lg border border-border bg-black p-4 font-mono text-xs leading-7">{data.template}</pre>
          </CardContent>
        </Card>
      </Section>

      {/* katas */}
      <Section id="katas" title="Katas" sub="Three warm-ups and five that punish a lazy Skill. One new kata drops per session.">
        <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-3">
          {(data.katas as { id: string; name: string; desc: string; diff: number }[]).map((k) => (
            <Card key={k.id}>
              <CardHeader>
                <CardTitle className="font-mono">{k.name}</CardTitle>
                <CardDescription className="font-mono">{k.id}</CardDescription>
                <div className="col-start-2 row-span-2 row-start-1 self-start justify-self-end">
                  <Badge variant={k.diff >= 3 ? "default" : "secondary"}>{DIFF[k.diff]}</Badge>
                </div>
              </CardHeader>
              <CardContent><p className="text-sm text-muted-foreground">{k.desc}</p></CardContent>
            </Card>
          ))}
        </div>
      </Section>

      {/* scoring */}
      <Section id="scoring" title="Scoring" sub="Lower wins. You must pass every sealed test for a kata or you don't score.">
        <Card>
          <CardContent className="py-6 text-center font-mono text-base sm:text-lg">
            score = round( cost<span className="text-muted-foreground">·1000</span> + attempts<span className="text-muted-foreground">·5</span> + skill_chars<span className="text-muted-foreground">/100</span> )
          </CardContent>
        </Card>
        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          <Fact title="Cost dominates.">The cheapest correct Skill wins — a good Skill on a cheap model beats a bad Skill on a frontier one.</Fact>
          <Fact title="Attempts.">Each model call it takes to converge. Right shape first try = cheap.</Fact>
          <Fact title="Length.">Bloat penalty. Stops the "throw more instructions at it" trap.</Fact>
        </div>
      </Section>

      {/* leaderboard */}
      <Section id="leaderboard" title="Leaderboard"
        sub={<>🏆 current leader · <Badge variant="outline" className="mx-1">⚑</Badge> self-reported (run on an endpoint CI can't re-run).</>}>
        <div className="grid gap-6">
          {(data.katas as { id: string; name: string }[]).map((k) => {
            const rows = ((data.board as Record<string, Row[]>)[k.id]) || [];
            return (
              <div key={k.id}>
                <div className="mb-2 flex items-baseline justify-between">
                  <h3 className="text-lg font-semibold">{k.id} · {k.name}</h3>
                  <span className="font-mono text-xs text-muted-foreground">{rows.length} submission{rows.length !== 1 ? "s" : ""}</span>
                </div>
                <Card>
                  {rows.length === 0 ? (
                    <CardContent className="py-5 text-muted-foreground">No submissions yet — sign in and be first.</CardContent>
                  ) : (
                    <table className="w-full border-collapse text-sm">
                      <thead>
                        <tr className="text-xs uppercase tracking-wide text-muted-foreground">
                          <th className="p-3 text-left" /><th className="p-3 text-left">Solver</th>
                          <th className="p-3 text-left">Skill</th><th className="p-3 text-left">Score</th>
                          <th className="p-3 text-left">Breakdown</th><th className="p-3 text-left">Model</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((r, i) => (
                          <tr key={i} className="border-t border-border">
                            <td className="p-3 text-lg">{i === 0 ? "🏆" : i + 1}</td>
                            <td className="p-3 font-semibold">@{r.solver}{r.self_reported && <Badge variant="outline" className="ml-1.5">⚑</Badge>}</td>
                            <td className="p-3"><code className="font-mono">{r.name}</code></td>
                            <td className="p-3 font-mono text-base font-semibold">{r.score}</td>
                            <td className="p-3 font-mono text-xs text-muted-foreground">${r.cost.toFixed(4)} · {r.attempts} att · {r.chars} ch</td>
                            <td className="p-3"><Badge variant="secondary" className="font-mono">{r.model}</Badge></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </Card>
              </div>
            );
          })}
        </div>
      </Section>

      <footer className="border-t border-border py-10 text-center text-sm text-muted-foreground">
        Built for the Eigen Builder Collective · <a className="text-primary hover:underline" href={data.repo} target="_blank" rel="noreferrer">source on GitHub</a><br />
        Sibling to Prompt Golf (S4) and Loop Fail (S5).
      </footer>

      <SignInDialog open={open} onOpenChange={setOpen} onSignedIn={save} />
    </div>
  );
}

function Section({ id, title, sub, children }: { id: string; title: string; sub: React.ReactNode; children: React.ReactNode }) {
  return (
    <section id={id} className="border-t border-border py-12">
      <div className="mx-auto max-w-5xl px-5">
        <h2 className="text-heading-md">{title}</h2>
        <p className="mb-6 mt-1 text-muted-foreground">{sub}</p>
        {children}
      </div>
    </section>
  );
}

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardContent className="flex gap-4 py-5">
        <span className="flex size-7 shrink-0 items-center justify-center rounded-md bg-primary font-mono text-sm font-semibold text-white">{n}</span>
        <div>
          <h3 className="font-semibold">{title}</h3>
          <div className="mt-1 text-sm text-muted-foreground">{children}</div>
        </div>
      </CardContent>
    </Card>
  );
}

function Pre({ children }: { children: React.ReactNode }) {
  return <pre className="mt-2.5 overflow-auto rounded-lg border border-border bg-black p-3.5 font-mono text-xs leading-7 text-foreground">{children}</pre>;
}

function Fact({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card><CardContent className="py-4 text-sm text-muted-foreground">
      <b className="text-foreground">{title}</b> {children}
    </CardContent></Card>
  );
}
