#!/usr/bin/env python3
# 경쟁문제(stdin/stdout) 채점 — 프로그램을 각 테스트 input으로 실행해 output 일치 검사.
# run_stdio(code, tests) : tests=[(input_str, expected_out), ...] → (ok, detail)
import sys, os, subprocess, tempfile

def _norm(s):
    # 줄별 trailing 공백 제거 + 마지막 개행 무시
    return "\n".join(line.rstrip() for line in s.replace("\r\n", "\n").split("\n")).rstrip("\n")

def run_stdio(code, tests, timeout=8, per_case=True):
    if not code.strip():
        return False, "NO_CODE"
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "sol.py")
        with open(f, "w") as fh:
            fh.write(code)
        passed = 0
        for i, (inp, exp) in enumerate(tests):
            try:
                r = subprocess.run([sys.executable, f], input=inp, capture_output=True,
                                   text=True, timeout=timeout, cwd=d)
            except subprocess.TimeoutExpired:
                return False, f"TIMEOUT@case{i}"
            except Exception as e:
                return False, f"ERR@case{i}:{e}"
            if r.returncode != 0:
                return False, f"RUNTIME@case{i}:{(r.stderr or '')[-120:]}"
            if _norm(r.stdout) == _norm(exp):
                passed += 1
            else:
                return False, f"WRONG@case{i}"
        return (passed == len(tests)), f"{passed}/{len(tests)}"

if __name__ == "__main__":
    import json
    # 자체 테스트
    code = "n=int(input())\nfor _ in range(n):\n s=input().strip()\n bal=0;ok=True\n for c in s:\n  bal+= 1 if c=='(' else -1\n  if bal<0: ok=False;break\n print('YES' if ok and bal==0 else 'NO')"
    tests = [("3\n((()))\n(())()\n()((", "YES\nYES\nNO")]
    print(run_stdio(code, tests))
