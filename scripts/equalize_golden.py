#!/usr/bin/env python3
# 교집합 통제 — 세 교수가 '모두 푼' 문제만 골라 교수별 골든셋을 동일 문제·동일 개수로.
# 데이터크기·주제선택 교란 제거 → 순수 교습 스타일 비교.
# 산출: code_<prof>_eq.jsonl (교집합, 각 교수 자기 풀이)
import json, os
G = "/mnt/cluster/sft_golden"
PROFS = ["claude", "codex", "grok"]

def load(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []

sets = {}
for P in PROFS:
    recs = load(f"{G}/code_{P}_gold.jsonl")
    # 중복 task_id(재시도 추가분) 제거: 마지막 것 유지
    by = {}
    for r in recs:
        by[r["task_id"]] = r
    sets[P] = by
    print(f"[{P}] 통과 {len(by)}건")

inter = set(sets[PROFS[0]])
for P in PROFS[1:]:
    inter &= set(sets[P])
print(f"교집합(모두 푼 문제): {len(inter)}건")

for P in PROFS:
    with open(f"{G}/code_{P}_eq.jsonl", "w") as f:
        for tid in sorted(inter):
            f.write(json.dumps(sets[P][tid], ensure_ascii=False) + "\n")
    print(f"  → code_{P}_eq.jsonl {len(inter)}건")
