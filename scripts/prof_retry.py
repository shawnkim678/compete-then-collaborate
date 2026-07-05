#!/usr/bin/env python3
# Teacher self-correction (retry) pass — re-solve failed problems given the failing error + previous code.
# Mimics a real teacher revising their answer. Newly passing items are appended to the golden set.
# Usage: python prof_retry.py --professor claude|codex|grok --retries 2
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_code import run_one
from prof_run import build_prompt, extract_code, call

G = "/mnt/cluster/sft_golden"

def load_jsonl(p):
    out = []
    if os.path.exists(p):
        for l in open(p):
            l = l.strip()
            if l:
                out.append(json.loads(l))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--professor", required=True)
    ap.add_argument("--bank", default=f"{G}/taskbank_full.jsonl")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()
    P = a.professor

    bank = {t["task_id"]: t for t in load_jsonl(a.bank)}
    gold = load_jsonl(f"{G}/code_{P}_gold.jsonl")
    gold_ids = {g["task_id"] for g in gold}
    raw = {r["task_id"]: r for r in load_jsonl(f"{G}/code_{P}_gold_raw.jsonl")}
    failed = [tid for tid in bank if tid not in gold_ids]
    print(f"[{P}] passed {len(gold_ids)} / failed {len(failed)} -> starting self-correction", flush=True)

    fixed = 0
    with open(f"{G}/code_{P}_gold.jsonl", "a") as gf:
        for tid in failed:
            task = bank[tid]
            prev = (raw.get(tid) or {}).get("code", "")
            ok, err = run_one(prev, task["tests"], 10, 8, 1024) if prev else (False, "NO_CODE")
            for attempt in range(a.retries):
                rp = (build_prompt(task) +
                      f"\n\n[Previous attempt failed] The code below failed the tests.\nFailure: {err[:300]}\nPrevious code:\n```python\n{prev}\n```\n"
                      f"Fix the error above and resubmit the correct solution with an explanation as EXACTLY ONE python code block.")
                text = call(P, rp, a.timeout)
                code = extract_code(text)
                ok2, err2 = run_one(code, task["tests"], 10, 8, 1024) if code else (False, "NO_CODE")
                if ok2:
                    gf.write(json.dumps({"instruction": task["instruction"], "input": task.get("input", ""),
                                         "output": text.strip(), "task_id": tid, "professor": P,
                                         "category": task["category"], "retry": attempt + 1}, ensure_ascii=False) + "\n")
                    gf.flush()
                    fixed += 1
                    print(f"  FIXED {tid} (retry {attempt+1})", flush=True)
                    break
                prev, err = code, err2
            else:
                print(f"  STILL_FAIL {tid}", flush=True)
    print(f"\n=== [{P}] self-correction: {fixed}/{len(failed)} newly passed -> {len(gold_ids)+fixed} golden total ===", flush=True)

if __name__ == "__main__":
    main()
