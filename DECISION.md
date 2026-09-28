# Decision: Haiku vs Sonnet vs rules

**Closed on quality only.** Cost and latency were not measured. That was a deliberate choice,
not an omission; see *What would change the decision*.

## Question

Claude Haiku 4.5 vs Claude Sonnet 5 vs a rule baseline: how much is lost with the cheaper
model, and in which errors? The reference labels come from a larger model, Claude Opus 5.5,
following the same written guide (v2, SHA-256 `fbf4d505…`).

## Evidence (real set, n = 164)

| | Agreement with Claude labels (95 % CI) | Macro-F1 | Costly errors |
|---|---|---|---|
| Rules | 71.3 % (64.0–78.0) | 0.68 | 17 |
| Claude Haiku 4.5 (ran as `claude-haiku-4-5-20251001`) | 93.9 % (90.2–97.6) | 0.95 | 4 |
| Claude Sonnet 5 (ran as `claude-sonnet-5`) | 97.6 % (95.1–99.4) | 0.98 | 2 |

**Source:** Claude Code sub-agents with a pinned model, given exactly the `classifier/llm.py`
prompt and input. Full tables, the definition of a costly error and stability are in
`eval/results.md`.

## Decision

- **On quality, Claude Sonnet 5** (it ran as `claude-sonnet-5`).
- **Claude Haiku 4.5 is not ruled out** (it ran as `claude-haiku-4-5-20251001`).
  - Its 3.7-point gap to Sonnet has overlapping 95 % confidence intervals at n = 164.
  - Its 2 extra costly errors are within the noise.
- **Neither model leaves unattended a person who asked to be contacted, and neither misses an
  explicit opt-out.**
  - Haiku would call 2 people who asked to be written to instead.
  - Both leave the same 2 questions unanswered.
- **The rules do not go to production:** 17 costly errors.

## What would change the decision

**Cost and latency were not measured, on purpose:** the evaluation ran through sub-agents,
not through the API.

**If the cost per message measured through the API clearly favours Haiku, Haiku becomes the
choice**, because on quality it does not separate from Sonnet.

## Limitation

- **Everything here is the Claude family,** measured against labels produced by Claude Opus
  5.5.
- **0 rows were verified by a person.**
- **The agreement measures consistency with those labels, not correctness.**
