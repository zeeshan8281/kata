# Kata 007 · task-pool

Implement `async def run_pool(tasks, limit)`.

`tasks` is a list of zero-argument **async functions**. Run them with **at most `limit`
running concurrently**, and return a list of their results **in the same order as
`tasks`** — input order, not completion order.

Running them one at a time is wrong (too slow). Running them all at once is wrong
(ignores `limit`). Bound the concurrency and preserve order.

Return **only** the complete Python source exposing `async def run_pool(tasks, limit)`.
Import from the stdlib as needed. No markdown fences, no prose.
