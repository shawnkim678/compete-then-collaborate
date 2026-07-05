#!/usr/bin/env python3
# 교수 자기교정(retry) 패스 — 틀린 문제를 '실패 에러+이전코드'와 함께 다시 풀게 해 교정.
# 실제 교수의 복습/교정을 모사. 통과분은 골든셋에 추가.
# 사용: python prof_retry.py --professor claude|codex|grok --retries 2
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
    print(f"[{P}] 통과 {len(gold_ids)} / 실패 {len(failed)} → 자기교정 시작", flush=True)

    fixed = 0
    with open(f"{G}/code_{P}_gold.jsonl", "a") as gf:
        for tid in failed:
            task = bank[tid]
            prev = (raw.get(tid) or {}).get("code", "")
            ok, err = run_one(prev, task["tests"], 10, 8, 1024) if prev else (False, "NO_CODE")
            for attempt in range(a.retries):
                rp = (build_prompt(task) +
                      f"\n\n[이전 시도 실패] 아래 코드가 테스트에서 실패했습니다.\n실패내용: {err[:300]}\n이전코드:\n```python\n{prev}\n```\n"
                      f"위 오류를 고쳐 올바른 해답을 설명과 함께 EXACTLY ONE python 코드블록으로 다시 제출하시오.")
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
    print(f"\n=== [{P}] 자기교정: {fixed}/{len(failed)} 추가통과 → 골든 총 {len(gold_ids)+fixed}건 ===", flush=True)

if __name__ == "__main__":
    main()
