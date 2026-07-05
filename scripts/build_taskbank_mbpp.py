#!/usr/bin/env python3
# 대규모 공유 태스크뱅크 빌더 (MBPP 기반).
#  - 알고리즘: MBPP teaching split(train+validation+prompt) 임포트. MBPP 'test' split은 평가용 홀드아웃(누수방지).
#  - 버그픽스: MBPP 참조풀이에 버그 주입(mutation) → 원본테스트가 실패로 잡는 것만 채택.
# 모든 태스크는 참조풀이+히든테스트로 건전성 자동검증. 산출: taskbank_full(.jsonl/_ref.jsonl)
import os, sys, json, re, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_code import run_one
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
from datasets import load_dataset

RID = "google-research-datasets/mbpp"

def split_tests(rec):
    """예시 테스트 1개(교수에 공개) + 히든 검증테스트(나머지) 분리. 함수명 애매성 제거."""
    setup = (rec.get("test_setup_code") or "").strip()
    tl = list(rec.get("test_list") or [])
    if not tl:
        return "", ""
    example = tl[0]
    hidden_body = "\n".join(tl[1:] if len(tl) > 1 else tl)  # 테스트 1개뿐이면 그걸로 검증
    hidden = (setup + "\n" + hidden_body).strip()
    return example, hidden

# 버그 주입: 텍스트 단위 변이(한 번에 하나). 원본 테스트를 깨는 첫 변이를 채택.
MUTATIONS = [
    (r'(?<![=!<>])==', '!='), (r'!=', '=='),
    (r'<=', '<'), (r'>=', '>'), (r'(?<![<>=])<(?![=])', '<='), (r'(?<![<>=])>(?![=])', '>='),
    (r'\+ 1', '+ 0'), (r'- 1', '- 0'), (r'\+= 1', '+= 2'),
    (r'\band\b', 'or'), (r'\bor\b', 'and'),
    (r'range\(([^,()]+)\)', r'range(\1 - 1)'),
]
def make_bug(code, tests):
    for pat, rep in MUTATIONS:
        new, n = re.subn(pat, rep, code, count=1)
        if n == 0 or new == code:
            continue
        ok_orig, _ = run_one(code, tests, 8, 6, 512)
        if not ok_orig:
            return None  # 원본이 안 돌면 스킵
        ok_bug, _ = run_one(new, tests, 8, 6, 512)
        if not ok_bug:   # 변이가 테스트를 깬다 = 유효 버그
            return new
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/mnt/cluster/sft_golden/taskbank_full")
    ap.add_argument("--n-algo", type=int, default=120)
    ap.add_argument("--n-bug", type=int, default=80)
    ap.add_argument("--splits", default="train,validation,prompt",
                    help="MBPP splits (teaching=train,validation,prompt / eval=test)")
    a = ap.parse_args()

    teach = []
    for sp in a.splits.split(","):
        try:
            teach += list(load_dataset(RID, split=sp))
        except Exception as e:
            print(f"  ({sp} 스킵: {str(e)[:60]})")
    print(f"MBPP teaching 후보 {len(teach)}문항 (test split은 평가용 홀드아웃)")

    algo, bug = [], []
    skipped_setup = 0
    for rec in teach:
        # test_setup_code(외부 클래스/전역 의존, 예: class Pair) 태스크 제외 → 순수 함수 비교(공정)
        if (rec.get("test_setup_code") or "").strip():
            skipped_setup += 1
            continue
        code = (rec.get("code") or "").strip()
        example, tests = split_tests(rec)
        if not code or not tests or not example:
            continue
        # 건전성: 참조풀이가 히든테스트 통과?
        ok, _ = run_one(code, tests, 8, 6, 512)
        if not ok:
            continue
        tid = f"mbpp{rec['task_id']}"
        instr = (rec.get("text") or "").strip()
        # 함수 시그니처 명시(예시 테스트 1개) → 함수명 애매성 제거(공정)
        instr_algo = instr + "\n\n함수 시그니처는 다음 예시와 정확히 일치해야 합니다(같은 함수명·인자 순서):\n" + example
        if len(algo) < a.n_algo:
            algo.append({"task_id": f"{tid}_a", "category": "algorithm",
                         "instruction": instr_algo, "input": "", "tests": tests, "_ref": code})
        if len(bug) < a.n_bug:
            buggy = make_bug(code, tests)
            if buggy:
                bug.append({"task_id": f"{tid}_b", "category": "bugfix",
                            "instruction": "아래 파이썬 코드에는 버그가 있다. 원래 의도(문제 설명 참고)대로 동작하도록 고치시오. 문제: " + instr,
                            "input": buggy, "tests": tests, "_ref": code})
        if len(algo) >= a.n_algo and len(bug) >= a.n_bug:
            break

    T = algo + bug
    with open(a.out + ".jsonl", "w") as f, open(a.out + "_ref.jsonl", "w") as fr:
        for r in T:
            pub = {k: r[k] for k in ("task_id", "category", "instruction", "input", "tests")}
            f.write(json.dumps(pub, ensure_ascii=False) + "\n")
            fr.write(json.dumps({**pub, "professor": "_ref", "output": r["_ref"], "solution_code": r["_ref"]}, ensure_ascii=False) + "\n")
    print(f"태스크뱅크_full: 알고리즘 {len(algo)} + 버그픽스 {len(bug)} = {len(T)}문항 → {a.out}.jsonl")

if __name__ == "__main__":
    main()
