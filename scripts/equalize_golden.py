#!/usr/bin/env python3
# Intersection control — keep only problems that ALL teachers solved, giving each teacher's golden
# set the same problems and the same count. Removes data-size / topic-selection confounds -> a pure
# comparison of teaching style. Output: code_<prof>_eq.jsonl (intersection, each teacher's own solution).
import json, os
G = "/mnt/cluster/sft_golden"
PROFS = ["claude", "codex", "grok"]

def load(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []

sets = {}
for P in PROFS:
    recs = load(f"{G}/code_{P}_gold.jsonl")
    # drop duplicate task_ids (retry additions): keep the last one
    by = {}
    for r in recs:
        by[r["task_id"]] = r
    sets[P] = by
    print(f"[{P}] passed {len(by)}")

inter = set(sets[PROFS[0]])
for P in PROFS[1:]:
    inter &= set(sets[P])
print(f"intersection (solved by all): {len(inter)}")

for P in PROFS:
    with open(f"{G}/code_{P}_eq.jsonl", "w") as f:
        for tid in sorted(inter):
            f.write(json.dumps(sets[P][tid], ensure_ascii=False) + "\n")
    print(f"  -> code_{P}_eq.jsonl {len(inter)}")
