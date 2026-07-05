#!/usr/bin/env python3
# 경쟁문제 태스크뱅크 (deepmind/code_contests) — 어려운 난이도로 headroom 확보.
# 각 태스크: {task_id, category='contest', difficulty, instruction(description), tests=[[in,out],...]}
# 테스트=public_tests(+generated 일부). stdin/stdout.
import os, sys, json, argparse
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
from datasets import load_dataset

def collect(split, n, max_tests, dmin, dmax):
    d = load_dataset("deepmind/code_contests", split=split, streaming=True)
    out = []
    for r in d:
        diff = r.get("difficulty") or 0
        if not (dmin <= diff <= dmax):
            continue
        pt = r.get("public_tests") or {}
        ins, outs = pt.get("input", []), pt.get("output", [])
        gt = r.get("generated_tests") or {}
        ins = ins + (gt.get("input", [])[:max_tests])
        outs = outs + (gt.get("output", [])[:max_tests])
        tests = [[i, o] for i, o in zip(ins, outs)][:max_tests]
        if not tests:
            continue
        out.append({"task_id": f"cc_{r['name'][:40].replace(' ','_')}", "category": "contest",
                    "difficulty": diff, "instruction": r["description"].strip(),
                    "tests_io": tests})
        if len(out) >= n:
            break
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/mnt/cluster/sft_golden/taskbank_contests")
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--max-tests", type=int, default=5)
    ap.add_argument("--dmin", type=int, default=6)
    ap.add_argument("--dmax", type=int, default=9)
    ap.add_argument("--split", default="train")
    a = ap.parse_args()
    tasks = collect(a.split, a.n, a.max_tests, a.dmin, a.dmax)
    with open(a.out + ".jsonl", "w") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    import statistics
    diffs = [t["difficulty"] for t in tasks]
    print(f"경쟁문제 {len(tasks)}개 → {a.out}.jsonl (난이도 {min(diffs)}~{max(diffs)}, 평균 {statistics.mean(diffs):.1f})")

if __name__ == "__main__":
    main()
