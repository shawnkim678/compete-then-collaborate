#!/usr/bin/env python3
# 교수 실행 래퍼 — 공유 태스크뱅크를 한 교수가 풀게 하고 히든테스트로 채점.
# 동일 프롬프트(공정) → CLI 호출 → 파이썬 코드블록 추출 → verify_code.run_one 검증 → 통과분만 골든셋.
# 사용: python prof_run.py --professor claude|codex|grok --bank taskbank.jsonl --out <prof>.jsonl
import sys, os, json, re, subprocess, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_code import run_one   # 동일 격리실행 검증

import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
CMD = {
    "claude": lambda p: ["claude", "-p", p],
    "codex":  lambda p: ["codex", "exec", "--skip-git-repo-check", p],
    "grok":   lambda p: ["grok", "-p", p],
    "gemini": lambda p: ["python3", _os.path.join(_HERE, "gemini_cli.py"), p],  # 4번째 교수(flagship, 키는 env)
}

def build_prompt(task):
    parts = ["You are an expert programming instructor. Solve the following Python task."]
    if task["category"] == "bugfix":
        parts.append("The code below has a bug. Provide the corrected function.")
    parts.append("Task: " + task["instruction"])
    if task.get("input"):
        parts.append("Code:\n```python\n" + task["input"] + "\n```")
    parts.append("Requirements: Briefly explain your reasoning in a few sentences, then provide EXACTLY ONE python code block containing the complete solution function(s). Do NOT include tests or example usage. Keep the exact function name/signature required by the task.")
    return "\n\n".join(parts)

BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)
def extract_code(text):
    blocks = BLOCK.findall(text or "")
    if not blocks:
        return ""
    # 마지막 코드블록(버그픽스에서 최종 수정본) 채택
    return blocks[-1].strip()

def call(professor, prompt, timeout=180, retries=2):
    # 빈 응답(타임아웃/CLI 불안정) 시 재시도 → 교수 간 공정성(특히 grok 배치 빈응답 방지)
    last = ""
    for attempt in range(retries + 1):
        try:
            r = subprocess.run(CMD[professor](prompt), capture_output=True, text=True,
                               timeout=timeout, stdin=subprocess.DEVNULL)
            out = (r.stdout or "") + ("\n" + r.stderr if r.returncode != 0 else "")
            last = out
            if out.strip() and "```" in out:   # 코드블록 확보 → 즉시 반환
                return out
        except subprocess.TimeoutExpired:
            last = ""
        # 빈 응답/코드없음 → 재시도
    return last

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--professor", required=True, choices=list(CMD))
    ap.add_argument("--bank", default="/mnt/cluster/sft_golden/taskbank.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()

    raw_path = a.out.replace(".jsonl", "_raw.jsonl")
    n = passed = 0
    bycat = {}
    with open(a.bank) as fb, open(a.out, "w") as fout, open(raw_path, "w") as fraw:
        for line in fb:
            line = line.strip()
            if not line: continue
            task = json.loads(line); n += 1
            cat = task["category"]; tid = task["task_id"]
            bycat.setdefault(cat, [0,0]); bycat[cat][1] += 1
            prompt = build_prompt(task)
            text = call(a.professor, prompt, a.timeout)
            code = extract_code(text)
            fraw.write(json.dumps({"task_id":tid,"professor":a.professor,"raw":text,"code":code},ensure_ascii=False)+"\n")
            ok, err = (run_one(code, task["tests"], 10, 8, 1024) if code else (False,"NO_CODE"))
            if ok:
                passed += 1; bycat[cat][0] += 1
                fout.write(json.dumps({
                    "instruction":task["instruction"],"input":task.get("input",""),
                    "output":text.strip(),"task_id":tid,"professor":a.professor,"category":cat,
                },ensure_ascii=False)+"\n")
                print(f"  PASS {tid} [{cat}]", flush=True)
            else:
                print(f"  FAIL {tid} [{cat}] :: {(err.splitlines()[-1] if err else '')[:80]}", flush=True)
    print(f"\n=== [{a.professor}] {passed}/{n} 통과 → {a.out} ===")
    for c,(p,t) in sorted(bycat.items()):
        print(f"    {c}: {p}/{t}")

if __name__ == "__main__":
    main()
