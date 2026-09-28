# Results

> **Agreement with Claude-generated labels**, not accuracy. Reference labels: guide v2
> (SHA-256 `fbf4d505…`), labeled by **Claude Opus 5.5 (`claude-opus-5-5`)**. **0 rows verified by a person.**
>
> **How these numbers were produced:** Claude Code sub-agents with a pinned model, **not**
> `classifier/llm.py` (the API classifier was not run: no API key). Each sub-agent received exactly
> the `llm.py` system prompt and user messages, in batches of at most 20 rows (15 for the stability
> re-run), fixed-seed order, and returned JSON validated like `llm.parse_answer`. The model of every
> sub-agent was confirmed from the `model` field Claude Code records in its transcript.
> **Not measured:** cost per call and latency. **All evaluated models are Claude, the same family as
> the labeler.** ⚠ marks the labeling model itself: a self-consistency ceiling, not an evaluated model.

## Configuration

| Classifier | Model (confirmed) | How it ran | Effort / thinking | Temperature |
|---|---|---|---|---|
| Rules | – | Python, deterministic | – | – |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | 15 Claude Code sub-agents (alias `haiku`) | **not controlled** (sub-agent defaults) | **not controlled** |
| Claude Sonnet 5 | `claude-sonnet-5` | 11 Claude Code sub-agents (alias `sonnet`) | **not controlled** (sub-agent defaults) | **not controlled** |
| ⚠ Labeler passes A/B (ceiling) | `claude-opus-5-5` | the existing v2 labeling passes, no new calls | not controlled | not controlled |

## Real set (n = 164, private text)

| Classifier | Agreement (95 % CI) | Macro-F1 (95 % CI) | Mean error cost | Costly errors | Hard rows v1 (14) | Hard rows v2 (2) |
|---|---|---|---|---|---|---|
| Rules (`baseline/rules.py`) | 71.3 % (64.0 %–78.0 %) | 0.68 (0.54–0.77) | 0.57 | 17 | 7 / 14 | 0 / 2 |
| Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) | 93.9 % (90.2 %–97.6 %) | 0.95 (0.90–0.98) | 0.11 | 4 | 11 / 14 | 0 / 2 |
| Claude Sonnet 5 (`claude-sonnet-5`) | 97.6 % (95.1 %–99.4 %) | 0.98 (0.95–1.00) | 0.05 | 2 | 13 / 14 | 1 / 2 |

## Self-consistency ceiling of the labeler (not an evaluated model)

The reference labels are the reconciliation of two passes of the labeling model (Claude Opus 5.5) over the same
164 rows. Each pass compared with the reconciled label shows how consistent the labeler is with itself: the
ceiling any classifier can reach against these labels, not a competitor.

| Pass | Agreement (95 % CI) | Macro-F1 | Costly errors |
|---|---|---|---|
| ⚠ Labeler v2 pass A (`claude-opus-5-5`) | 100.0 % (100.0 %–100.0 %) | 1.00 | 0 |
| ⚠ Labeler v2 pass B (`claude-opus-5-5`) | 99.4 % (98.2 %–100.0 %) | 0.99 | 0 |

Pass A agrees 100 % **by construction**: the reconciled label equals pass A wherever A and B agree, and in the one unresolved disagreement. **Pass B (99.4 %) is the meaningful ceiling.**

## Real set, per class (precision / recall vs Claude labels)

| Class | n | Rules (`baseline/rules.py`) | Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) | Claude Sonnet 5 (`claude-sonnet-5`) |
|---|---|---|---|---|
| pide_informacion | 35 | 0.77 / 0.69 | 0.97 / 0.94 | 1.00 / 0.94 |
| quiere_contacto | 25 | 0.95 / 0.72 | 0.86 / 1.00 | 1.00 / 1.00 |
| prefiere_escrito | 25 | 0.93 / 0.56 | 1.00 / 0.92 | 1.00 / 1.00 |
| pospone | 10 | 0.60 / 0.30 | 0.90 / 0.90 | 0.91 / 1.00 |
| no_interesado | 26 | 1.00 / 0.65 | 1.00 / 0.96 | 1.00 / 0.96 |
| sin_intencion | 41 | 0.53 / 0.98 | 0.90 / 0.90 | 0.93 / 0.98 |
| fuera_de_tema | 2 | 1.00 / 0.50 | 1.00 / 1.00 | 1.00 / 1.00 |

## Costly errors on the real set (cost > 1, see DECISION.md)

| Classifier | Claude label → predicted | Count |
|---|---|---|
| Rules (`baseline/rules.py`) | pide_informacion → sin_intencion | 11 |
| Rules (`baseline/rules.py`) | quiere_contacto → sin_intencion | 5 |
| Rules (`baseline/rules.py`) | explicit opt-out → not no_interesado | 1 |
| Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) | pide_informacion → sin_intencion | 2 |
| Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) | prefiere_escrito → quiere_contacto | 2 |
| Claude Sonnet 5 (`claude-sonnet-5`) | pide_informacion → sin_intencion | 2 |

## Synthetic set (n = 70, public)

| Classifier | Agreement | Macro-F1 | Note |
|---|---|---|---|
| Rules (`baseline/rules.py`) | 100.0 % | 1.00 | **not comparable: the rules were tuned on this set** |
| Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) | 100.0 % | 1.00 |  |
| Claude Sonnet 5 (`claude-sonnet-5`) | – | – | not run (not in the approved plan) |

## Stability (30 real rows re-classified, different order and batch-mates)

| Classifier | Rows that changed class |
|---|---|
| Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) | 1 / 30 (reply_0021) |
| Claude Sonnet 5 (`claude-sonnet-5`) | 0 / 30 |

## Confusion matrices (real set; rows = Claude label, columns = prediction)

**Rules (`baseline/rules.py`)**

| Claude label \ pred | pide_info | quiere_co | prefiere_ | pospone | no_intere | sin_inten | fuera_de_ |
|---|---|---|---|---|---|---|---|
| pide_informacion | 24 | 0 | 0 | 0 | 0 | 11 | 0 |
| quiere_contacto | 1 | 18 | 1 | 0 | 0 | 5 | 0 |
| prefiere_escrito | 5 | 0 | 14 | 0 | 0 | 6 | 0 |
| pospone | 0 | 1 | 0 | 3 | 0 | 6 | 0 |
| no_interesado | 0 | 0 | 0 | 2 | 17 | 7 | 0 |
| sin_intencion | 1 | 0 | 0 | 0 | 0 | 40 | 0 |
| fuera_de_tema | 0 | 0 | 0 | 0 | 0 | 1 | 1 |

**Claude Haiku 4.5 (`claude-haiku-4-5-20251001`)**

| Claude label \ pred | pide_info | quiere_co | prefiere_ | pospone | no_intere | sin_inten | fuera_de_ |
|---|---|---|---|---|---|---|---|
| pide_informacion | 33 | 0 | 0 | 0 | 0 | 2 | 0 |
| quiere_contacto | 0 | 25 | 0 | 0 | 0 | 0 | 0 |
| prefiere_escrito | 0 | 2 | 23 | 0 | 0 | 0 | 0 |
| pospone | 0 | 0 | 0 | 9 | 0 | 1 | 0 |
| no_interesado | 0 | 0 | 0 | 0 | 25 | 1 | 0 |
| sin_intencion | 1 | 2 | 0 | 1 | 0 | 37 | 0 |
| fuera_de_tema | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

**Claude Sonnet 5 (`claude-sonnet-5`)**

| Claude label \ pred | pide_info | quiere_co | prefiere_ | pospone | no_intere | sin_inten | fuera_de_ |
|---|---|---|---|---|---|---|---|
| pide_informacion | 33 | 0 | 0 | 0 | 0 | 2 | 0 |
| quiere_contacto | 0 | 25 | 0 | 0 | 0 | 0 | 0 |
| prefiere_escrito | 0 | 0 | 25 | 0 | 0 | 0 | 0 |
| pospone | 0 | 0 | 0 | 10 | 0 | 0 | 0 |
| no_interesado | 0 | 0 | 0 | 0 | 25 | 1 | 0 |
| sin_intencion | 0 | 0 | 0 | 1 | 0 | 40 | 0 |
| fuera_de_tema | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

## Definition of a costly error (as in `eval/run_eval.py`, constant `EXPENSIVE`)

A correct prediction costs 0 and any other error costs 1, except these pairs (Claude label → predicted):

| Claude label | Predicted | Cost |
|---|---|---|
| quiere_contacto | sin_intencion | 5 |
| quiere_contacto | pospone | 5 |
| quiere_contacto | no_interesado | 5 |
| prefiere_escrito | quiere_contacto | 3 |
| pide_informacion | sin_intencion | 3 |
| explicit opt-out (any label) | anything but no_interesado | 5 |

A **costly error** is one with cost > 1. The mean error cost is the total cost divided by the number of rows.

## Data-handling note: BOM in 3 Haiku outputs

Three Haiku sub-agent output files (batches R03, R05, R09) started with a UTF-8 byte-order mark, because the
sub-agent wrote them through PowerShell. The first line of each file then failed JSON parsing. The validator
(`eval/subagent_batch.validate`) strips a leading BOM before parsing; the answer itself is validated exactly as
`llm.parse_answer` does (a class from the guide, a boolean opt-out, opt-out only with no_interesado). After that,
164/164 Haiku and 164/164 Sonnet answers were valid. No answer was edited.

## Not run

- `classifier/llm.py` against the Claude API (Opus 5.5 / Sonnet 5 / Haiku): no API key in the session. Its results may differ from the sub-agent results above (different harness, effort and sampling defaults).
- Cost per 1,000 classifications and latency: not measurable with sub-agents.

