"""Builds eval/results.md from eval/metrics/*.json. Aggregates and reply ids only, never text."""
import json
from collections import Counter
from pathlib import Path

from labels import LABELS

ROWS = [("rules", "Rules (`baseline/rules.py`)"),
        ("subagent-haiku", "Claude Haiku 4.5 (`claude-haiku-4-5-20251001`)"),
        ("subagent-sonnet", "Claude Sonnet 5 (`claude-sonnet-5`)")]
# The labeler is NOT an evaluated model: its own v2 passes give a self-consistency ceiling.
CEILING = [("labeler-pass-a", "⚠ Labeler v2 pass A (`claude-opus-5-5`)"),
           ("labeler-pass-b", "⚠ Labeler v2 pass B (`claude-opus-5-5`)")]


def _p(x):
    return "–" if x is None else f"{x * 100:.1f} %"


def _f(x):
    return "–" if x is None else f"{x:.2f}"


def write(metrics_dir, out_path):
    m = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(metrics_dir).glob("*.json"))}
    L = ["# Results", "",
         "> **Agreement with Claude-generated labels**, not accuracy. Reference labels: guide v2",
         "> (SHA-256 `fbf4d505…`), labeled by **Claude Opus 5.5 (`claude-opus-5-5`)**. **0 rows verified by a person.**",
         ">",
         "> **How these numbers were produced:** Claude Code sub-agents with a pinned model, **not**",
         "> `classifier/llm.py` (the API classifier was not run: no API key). Each sub-agent received exactly",
         "> the `llm.py` system prompt and user messages, in batches of at most 20 rows (15 for the stability",
         "> re-run), fixed-seed order, and returned JSON validated like `llm.parse_answer`. The model of every",
         "> sub-agent was confirmed from the `model` field Claude Code records in its transcript.",
         "> **Not measured:** cost per call and latency. **All evaluated models are Claude, the same family as",
         "> the labeler.** ⚠ marks the labeling model itself: a self-consistency ceiling, not an evaluated model.",
         "",
         "## Configuration", "",
         "| Classifier | Model (confirmed) | How it ran | Effort / thinking | Temperature |", "|---|---|---|---|---|",
         "| Rules | – | Python, deterministic | – | – |",
         "| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` | 15 Claude Code sub-agents (alias `haiku`) | **not controlled** (sub-agent defaults) | **not controlled** |",
         "| Claude Sonnet 5 | `claude-sonnet-5` | 11 Claude Code sub-agents (alias `sonnet`) | **not controlled** (sub-agent defaults) | **not controlled** |",
         "| ⚠ Labeler passes A/B (ceiling) | `claude-opus-5-5` | the existing v2 labeling passes, no new calls | not controlled | not controlled |",
         "", "## Real set (n = 164, private text)", "",
         "| Classifier | Agreement (95 % CI) | Macro-F1 (95 % CI) | Mean error cost | Expensive errors | Hard rows v1 (14) | Hard rows v2 (2) |",
         "|---|---|---|---|---|---|---|"]
    for key, name in ROWS:
        d = m.get(f"run-{key}-real")
        if not d:
            L.append(f"| {name} | not run | | | | | |")
            continue
        a, f = d["agreement_ci95"], d["macro_f1_ci95"]
        L.append(f"| {name} | {_p(d['agreement'])} ({_p(a[0])}–{_p(a[1])}) | {_f(d['macro_f1'])} ({_f(f[0])}–{_f(f[1])}) | "
                 f"{_f(d['error_cost']['mean_cost'])} | {d['error_cost']['expensive_errors']} | "
                 f"{d['hard_v1']['agree_rows']} / {d['hard_v1']['n']} | {d['hard_v2']['agree_rows']} / {d['hard_v2']['n']} |")
    L += ["", "## Self-consistency ceiling of the labeler (not an evaluated model)", "",
          "The reference labels are the reconciliation of two passes of the labeling model (Claude Opus 5.5) over the same",
          "164 rows. Each pass compared with the reconciled label shows how consistent the labeler is with itself: the",
          "ceiling any classifier can reach against these labels, not a competitor.", "",
          "| Pass | Agreement (95 % CI) | Macro-F1 | Expensive errors |", "|---|---|---|---|"]
    for key, name in CEILING:
        d = m.get(f"run-{key}-real")
        if d:
            a = d["agreement_ci95"]
            L.append(f"| {name} | {_p(d['agreement'])} ({_p(a[0])}–{_p(a[1])}) | {_f(d['macro_f1'])} | {d['error_cost']['expensive_errors']} |")
    L += ["", "Pass A agrees 100 % **by construction**: the reconciled label equals pass A wherever A and B agree, and in the "
          "one unresolved disagreement. **Pass B (99.4 %) is the meaningful ceiling.**", "",
          "## Real set, per class (precision / recall vs Claude labels)", "",
          "| Class | n | " + " | ".join(n for _, n in ROWS[:3]) + " |", "|---|---|---|---|---|"]
    for c in LABELS:
        cells, n = [], "–"
        for key, _ in ROWS[:3]:
            d = m.get(f"run-{key}-real")
            p, r, n = d["per_class"][c] if d else (None, None, "–")
            cells.append(f"{_f(p)} / {_f(r)}")
        L.append(f"| {c} | {n} | " + " | ".join(cells) + " |")
    L += ["", "## Expensive errors on the real set (cost > 1, see DECISION.md)", "",
          "| Classifier | Claude label → predicted | Count |", "|---|---|---|"]
    for key, name in ROWS[:3]:
        d = m.get(f"run-{key}-real")
        if not d:
            continue
        pairs = Counter()
        rows = {}
        for g in LABELS:
            for p in LABELS:
                if g != p and d["confusion"][g][p] and (g, p) in EXPENSIVE_PAIRS:
                    pairs[(g, p)] = d["confusion"][g][p]
        if not pairs:
            L.append(f"| {name} | none | 0 |")
        for (g, p), k in pairs.most_common():
            L.append(f"| {name} | {g} → {p} | {k} |")
        missed_opt_out = d["error_cost"]["expensive_errors"] - sum(pairs.values())
        if missed_opt_out:
            L.append(f"| {name} | explicit opt-out → not no_interesado | {missed_opt_out} |")
    L += ["", "## Synthetic set (n = 70, public)", "",
          "| Classifier | Agreement | Macro-F1 | Note |", "|---|---|---|---|"]
    for key, name, note in [("rules", ROWS[0][1], "**not comparable: the rules were tuned on this set**"),
                            ("subagent-haiku", ROWS[1][1], ""),
                            ("subagent-sonnet", ROWS[2][1], "not run (not in the approved plan)")]:
        d = m.get(f"run-{key}-synthetic")
        L.append(f"| {name} | {_p(d['agreement']) if d else '–'} | {_f(d['macro_f1']) if d else '–'} | {note} |")
    L += ["", "## Stability (30 real rows re-classified, different order and batch-mates)", "",
          "| Classifier | Rows that changed class |", "|---|---|"]
    for key, name in ROWS[1:3]:
        d = m.get(f"stability-{key}-real")
        L.append(f"| {name} | {d['changed']} / {d['n']}" + (f" ({', '.join(d['changed_ids'])})" if d and d['changed'] else "") + " |"
                 if d else f"| {name} | not run |")
    L += ["", "## Confusion matrices (real set; rows = Claude label, columns = prediction)", ""]
    for key, name in ROWS[:3]:
        d = m.get(f"run-{key}-real")
        if not d:
            continue
        L += [f"**{name}**", "", "| Claude label \\ pred | " + " | ".join(x[:9] for x in LABELS) + " |",
              "|---|" + "---|" * len(LABELS)]
        for g in LABELS:
            L.append(f"| {g} | " + " | ".join(str(d["confusion"][g][p]) for p in LABELS) + " |")
        L.append("")
    from eval.run_eval import EXPENSIVE, OPT_OUT_MISSED
    L += ["## Definition of an expensive error (as in `eval/run_eval.py`)", "",
          "A correct prediction costs 0 and any other error costs 1, except these pairs (Claude label → predicted):", "",
          "| Claude label | Predicted | Cost |", "|---|---|---|"]
    for (g, p), c in EXPENSIVE.items():
        L.append(f"| {g} | {p} | {c} |")
    L += [f"| explicit opt-out (any label) | anything but no_interesado | {OPT_OUT_MISSED} |", "",
          "An **expensive error** is one with cost > 1. The mean error cost is the total cost divided by the number of rows.", "",
          "## Data-handling note: BOM in 3 Haiku outputs", "",
          "Three Haiku sub-agent output files (batches R03, R05, R09) started with a UTF-8 byte-order mark, because the",
          "sub-agent wrote them through PowerShell. The first line of each file then failed JSON parsing. The validator",
          "(`eval/subagent_batch.validate`) strips a leading BOM before parsing; the answer itself is validated exactly as",
          "`llm.parse_answer` does (a class from the guide, a boolean opt-out, opt-out only with no_interesado). After that,",
          "164/164 Haiku and 164/164 Sonnet answers were valid. No answer was edited.", "",
          "## Not run", "",
          "- `classifier/llm.py` against the Claude API (Opus 5.5 / Sonnet 5 / Haiku): no API key in the session. "
          "Its results may differ from the sub-agent results above (different harness, effort and sampling defaults).",
          "- Cost per 1,000 classifications and latency: not measurable with sub-agents.", ""]
    Path(out_path).write_text("\n".join(L) + "\n", encoding="utf-8")


EXPENSIVE_PAIRS = {("quiere_contacto", "sin_intencion"), ("quiere_contacto", "pospone"), ("quiere_contacto", "no_interesado"),
                   ("prefiere_escrito", "quiere_contacto"), ("pide_informacion", "sin_intencion")}
