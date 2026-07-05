#!/usr/bin/env python3
# 경쟁문제(stdin/stdout) 교수 러너 — 교수가 프로그램 작성 → public_tests로 채점.
# 사용: python prof_run_stdio.py --professor claude|codex|grok --bank taskbank_contests.jsonl --out <prof>_cc.jsonl
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_stdio import run_stdio
from prof_run import extract_code, call

def build_prompt(task):
    return ("You are an expert competitive programmer. Solve the problem below in Python 3.\n"
            "Read input from standard input (stdin) and write the answer to standard output (stdout).\n\n"
            "Problem:\n" + task["instruction"][:4000] +
            "\n\nProvide a brief plan, then EXACTLY ONE python code block containing the complete program "
            "(a runnable script using input()/print()). No tests, no extra text after the code block.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--professor", required=True)
    ap.add_argument("--bank", default="/mnt/cluster/sft_golden/taskbank_contests.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=200)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    raw_path = a.out.replace(".jsonl", "_raw.jsonl")
    n = passed = 0
    with open(a.bank) as fb, open(a.out, "w") as fo, open(raw_path, "w") as fr:
        for line in fb:
            line = line.strip()
            if not line: continue
            task = json.loads(line); n += 1
            if a.limit and n > a.limit: break
            text = call(a.professor, build_prompt(task), a.timeout)
            code = extract_code(text)
            tests = [(t[0], t[1]) for t in task["tests_io"]]
            ok, detail = run_stdio(code, tests, timeout=8) if code else (False, "NO_CODE")
            fr.write(json.dumps({"task_id": task["task_id"], "code": code, "detail": detail}, ensure_ascii=False) + "\n")
            fr.flush()   # 강제종료 대비 즉시 기록(NFS 버퍼링 방지)
            if ok:
                passed += 1
                fo.write(json.dumps({"instruction": task["instruction"], "input": "",
                                     "output": text.strip(), "task_id": task["task_id"],
                                     "professor": a.professor, "category": "contest",
                                     "difficulty": task.get("difficulty")}, ensure_ascii=False) + "\n")
                fo.flush()   # 통과분 즉시 기록
                print(f"  PASS {task['task_id']} (d{task.get('difficulty')})", flush=True)
            else:
                print(f"  FAIL {task['task_id']} :: {detail}", flush=True)
    print(f"\n=== [{a.professor}] 경쟁문제 {passed}/{n} 통과 ({100*passed/max(n,1):.1f}%) ===", flush=True)

if __name__ == "__main__":
    main()
