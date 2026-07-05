#!/usr/bin/env python3
# reproduce.py — 공개 아티팩트로 논문 수치 재계산 (try-it-yourself).
#   --verify : 릴리스된 골든셋/학생출력을 히든테스트로 재실행 → pass@1 재현 (오프라인).
# (전체 구현은 scripts/의 verify_code.run_one / verify_stdio.run_stdio 재사용)
import argparse, json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

def verify_bank(bank, kind):
    from verify_code import run_one
    from verify_stdio import run_stdio
    n = p = 0
    for line in open(bank):
        line = line.strip()
        if not line: continue
        r = json.loads(line); n += 1
        code = r.get("solution_code") or r.get("_ref") or ""
        if kind == "stdio":
            ok, _ = run_stdio(code, [(t[0], t[1]) for t in r.get("tests_io", [])])
        else:
            ok, _ = run_one(code, r.get("tests", ""), 10, 8, 1024)
        p += 1 if ok else 0
    print(f"  {os.path.basename(bank)}: {p}/{n} pass ({100*p/max(n,1):.1f}%)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    print("=== Static re-verification (paper numbers recomputed from released files) ===")
    # 예: task-bank soundness + released student outputs. 릴리스 시 실제 경로로 채움.
    print("(fill in released bank/output paths at release time)")
