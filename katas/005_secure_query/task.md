# Kata 005 · secure-query

`users.py` (below) builds SQL by string interpolation — it's injectable. Rewrite it so
every user-supplied value is passed as a **query parameter** (the `?` placeholder plus a
params tuple), never interpolated into the SQL string. Behaviour must not change for
legitimate inputs.

The `db` object gives you a cursor: `db.cursor().execute(sql, params=())` and
`.fetchone()` / `.fetchall()`. Use `?` placeholders.

Return **only** the complete rewritten source for `users.py`. No markdown fences, no prose.
