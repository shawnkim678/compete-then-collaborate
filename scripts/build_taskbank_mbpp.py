#!/usr/bin/env python3
# Large shared task-bank builder (MBPP-based).
#  - algorithm: import the MBPP teaching split (train+validation+prompt). The MBPP 'test' split is the eval held-out (no leakage).
#  - bugfix   : inject a bug (mutation) into the MBPP reference solution -> keep only mutations the original tests catch.
# Every task is auto-validated for soundness with reference solution + hidden tests. Output: taskbank_full(.jsonl/_ref.jsonl)
import os, sys, json, re, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_code import run_one
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
from datasets import load_dataset

RID = "google-research-datasets/mbpp"

def split_tests(rec):
    """Split one example test (shown to the teacher) from the hidden verification tests (the rest). Removes function-name ambiguity."""
    setup = (rec.get("test_setup_code") or "").strip()
    tl = list(rec.get("test_list") or [])
    if not tl:
        return "", ""
    example = tl[0]
    hidden_body = "\n".join(tl[1:] if len(tl) > 1 else tl)  # if there is only one test, verify with it
    hidden = (setup + "\n" + hidden_body).strip()
    return example, hidden

# Bug injection: text-level mutation (one at a time). Keep the first mutation that breaks the original tests.
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
            return None  # skip if the original does not run
        ok_bug, _ = run_one(new, tests, 8, 6, 512)
        if not ok_bug:   # the mutation breaks the tests = a valid bug
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
            print(f"  (skip {sp}: {str(e)[:60]})")
    print(f"MBPP teaching candidates: {len(teach)} tasks (the test split is the eval held-out)")

    algo, bug = [], []
    skipped_setup = 0
    for rec in teach:
        # exclude tasks with test_setup_code (external class / global deps, e.g. class Pair) -> pure-function comparison (fair)
        if (rec.get("test_setup_code") or "").strip():
            skipped_setup += 1
            continue
        code = (rec.get("code") or "").strip()
        example, tests = split_tests(rec)
        if not code or not tests or not example:
            continue
        # soundness: does the reference solution pass the hidden tests?
        ok, _ = run_one(code, tests, 8, 6, 512)
        if not ok:
            continue
        tid = f"mbpp{rec['task_id']}"
        instr = (rec.get("text") or "").strip()
        # state the function signature (one example test) -> removes function-name ambiguity (fair)
        instr_algo = instr + "\n\nThe function signature must exactly match the following example (same function name and argument order):\n" + example
        if len(algo) < a.n_algo:
            algo.append({"task_id": f"{tid}_a", "category": "algorithm",
                         "instruction": instr_algo, "input": "", "tests": tests, "_ref": code})
        if len(bug) < a.n_bug:
            buggy = make_bug(code, tests)
            if buggy:
                bug.append({"task_id": f"{tid}_b", "category": "bugfix",
                            "instruction": "The Python code below has a bug. Fix it so it behaves as intended (see the problem description). Problem: " + instr,
                            "input": buggy, "tests": tests, "_ref": code})
        if len(algo) >= a.n_algo and len(bug) >= a.n_bug:
            break

    T = algo + bug
    with open(a.out + ".jsonl", "w") as f, open(a.out + "_ref.jsonl", "w") as fr:
        for r in T:
            pub = {k: r[k] for k in ("task_id", "category", "instruction", "input", "tests")}
            f.write(json.dumps(pub, ensure_ascii=False) + "\n")
            fr.write(json.dumps({**pub, "professor": "_ref", "output": r["_ref"], "solution_code": r["_ref"]}, ensure_ascii=False) + "\n")
    print(f"taskbank_full: algorithm {len(algo)} + bugfix {len(bug)} = {len(T)} tasks -> {a.out}.jsonl")

if __name__ == "__main__":
    main()
