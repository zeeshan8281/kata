# Kata 003 · cron-next

Implement `next_run(expr, after)` — given a standard 5-field cron expression and a
`datetime`, return the next `datetime` (minute resolution, seconds = 0) that the
expression fires at, **strictly after** `after`.

Fields: `minute hour day-of-month month day-of-week`. Support `*`, lists (`1,15`),
ranges (`1-5`), and steps (`*/10`, `0-30/10`).

Day-of-week is `0-6` with Sunday = 0 (and `7` also means Sunday). Watch the classic
rule: **if both day-of-month and day-of-week are restricted (not `*`), a match on
*either* fires.** If only one is restricted, only that one applies.

Return **only** the complete Python source for a module exposing
`next_run(expr: str, after: datetime) -> datetime`. Import whatever you need from the
stdlib. No markdown fences, no prose.
