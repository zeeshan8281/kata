# Kata 002 · refactor-async

Convert the module below to `async`/`await`. Every top-level function must become a
coroutine (`async def`), and callers must `await` their callees. Behaviour must not
change — the same inputs return the same values.

Return **only** the complete rewritten Python source for `fetcher.py`. No markdown
fences, no prose.
