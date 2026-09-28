"""Batches for the Claude Code sub-agent evaluation (method approved 2026-09-27).

A sub-agent never sees labels, proposals, reasons, class counts or other passes: `show` prints
exactly the classifier/llm.py system prompt and, for each row of one batch, the same user
message llm.py would send (pseudonymized reply + last outbound). Nothing else.

  plan   --real DATASET --out DIR          batch ids (<= 20 per batch, fixed seeds) -> DIR/plan.local.json
  show   --real DATASET --plan FILE --batch KEY
  check  --plan FILE --dir DIR --prefix P  validates DIR/P-KEY.local.jsonl like llm.parse_answer
Real text is read from DATASET (outside the repo) and only printed to the sub-agent.
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from classifier import llm  # noqa: E402
from labels import LABELS  # noqa: E402

BATCH = 20
STAB_BATCH = 15
SEED_ORDER, SEED_STAB_SAMPLE, SEED_STAB_ORDER = 20260930, 20260927, 20261001


def _real(dataset):
    with open(dataset, encoding="utf-8") as f:
        return {r["reply_id"]: (r["reply_text_scrubbed"], r["mensaje_saliente"]) for r in csv.DictReader(f) if not r["filtro"]}


def _synthetic():
    from data import synthetic
    return {x["id"]: (x["reply_text"], x["outbound_text"]) for x in synthetic.rows()}


def _chunks(ids, n, prefix):
    return {f"{prefix}{i // n + 1:02d}": ids[i:i + n] for i in range(0, len(ids), n)}


def plan(dataset):
    real = sorted(_real(dataset))
    syn = sorted(_synthetic())
    r_order, s_order = real[:], syn[:]
    random.Random(SEED_ORDER).shuffle(r_order)
    random.Random(SEED_ORDER).shuffle(s_order)
    # Stability: the same 30-row sample as run_eval.py's stability, re-ordered and re-batched
    # (15 per batch), so every row gets different batch-mates than in its first run.
    stab = random.Random(SEED_STAB_SAMPLE).sample(real, 30)
    random.Random(SEED_STAB_ORDER).shuffle(stab)
    return {"batch_size": BATCH, "stability_batch_size": STAB_BATCH, "seeds": [SEED_ORDER, SEED_STAB_SAMPLE, SEED_STAB_ORDER],
            **_chunks(r_order, BATCH, "R"), **_chunks(s_order, BATCH, "S"), **_chunks(stab, STAB_BATCH, "E")}


def show(dataset, plan_file, key):
    ids = json.loads(Path(plan_file).read_text(encoding="utf-8"))[key]
    src = _synthetic() if key.startswith("S") else _real(dataset)
    out = ["=== SYSTEM PROMPT (identical to classifier/llm.py) ===", llm.SYSTEM_PROMPT, "",
           f"=== BATCH {key}: {len(ids)} rows. Classify each one independently. ==="]
    for rid in ids:
        reply, outbound = src[rid]
        out += ["", f"### {rid}", llm.build_user_message(reply, outbound)]
    print("\n".join(out))


def validate(line):
    """Same rules as llm.parse_answer: a class from the guide and a boolean opt-out."""
    # Some sub-agents write with PowerShell, which prepends a UTF-8 BOM to the file: strip it
    # (encoding only; the answer itself is validated exactly as before).
    d = json.loads(line.lstrip("﻿"))
    if d.get("label") not in LABELS or not isinstance(d.get("explicit_opt_out"), bool):
        raise ValueError(f"invalid answer for {d.get('id')}")
    return {"id": d["id"], "label": d["label"], "explicit_opt_out": bool(d["explicit_opt_out"] and d["label"] == "no_interesado")}


def check(plan_file, out_dir, prefix):
    p = json.loads(Path(plan_file).read_text(encoding="utf-8"))
    report = {}
    for key, ids in p.items():
        if not isinstance(ids, list) or not key[0] in "RSE":
            continue
        f = Path(out_dir) / f"{prefix}-{key}.local.jsonl"
        if not f.exists():
            continue
        got, bad = [], 0
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    got.append(validate(line))
                except (ValueError, json.JSONDecodeError):
                    bad += 1
        report[key] = {"expected": len(ids), "valid": len(got), "invalid": bad,
                       "ids_match": sorted(g["id"] for g in got) == sorted(ids)}
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["plan", "show", "check"])
    ap.add_argument("--real")
    ap.add_argument("--plan")
    ap.add_argument("--batch")
    ap.add_argument("--out")
    ap.add_argument("--dir")
    ap.add_argument("--prefix")
    a = ap.parse_args()
    if a.cmd == "plan":
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        pl = plan(a.real)
        (out / "plan.local.json").write_text(json.dumps(pl, indent=1), encoding="utf-8")
        print({k: len(v) for k, v in pl.items() if isinstance(v, list) and k[0] in "RSE"})
    elif a.cmd == "show":
        show(a.real, a.plan, a.batch)
    else:
        check(a.plan, a.dir, a.prefix)
