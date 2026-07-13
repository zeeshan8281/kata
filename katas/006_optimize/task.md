# Kata 006 · optimize

`count_pairs(nums, target)` returns how many unordered index pairs `i < j` satisfy
`nums[i] + nums[j] == target`. The version below is correct but **O(n²)** — it times
out on large inputs.

Rewrite it to run in **O(n)** time. It must stay correct for duplicates, negatives,
and empty input.

Return **only** the complete rewritten source (keep the name `count_pairs`). No fences, no prose.
