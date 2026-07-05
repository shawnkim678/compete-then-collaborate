#!/usr/bin/env python3
"""reproduce.py — try-it-yourself entry point.

Offline (no GPU / no internet / no API keys):
  --check-banks   validate every released task bank (counts, fields, tests parse)
  --selftest      prove the execution verifier itself works (correct code passes, wrong code fails)

Full pass@1 reproduction needs either (a) regenerating teacher solutions with your own API keys
(scripts/prof_run*.py) or (b) the released RLVR student adapter + scripts/eval_code_students.py.
We do not redistribute teacher outputs (see TOS_COMPLIANCE.md), so those numbers are reproduced,
not shipped.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "scripts"))
DATA = os.path.join(HERE, "data")

FUNCTION_BANKS = ["taskbank_full.jsonl", "taskbank_heldout.jsonl"]
STDIO_BANKS = ["taskbank_contests.jsonl", "taskbank_contests_heldout.jsonl"]


def _load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def check_banks():
    print("=== task-bank integrity (offline) ===")
    ok = True
    for b in FUNCTION_BANKS:
        p = os.path.join(DATA, b)
        if not os.path.exists(p):
            print(f"  MISSING {b}"); ok = False; continue
        rows = _load(p)
        bad = [r["task_id"] for r in rows if "tests" not in r or "instruction" not in r]
        leak = [r["task_id"] for r in rows if any(k in r for k in ("output", "professor", "teacher"))]
        print(f"  {b}: {len(rows)} tasks | missing-fields {len(bad)} | teacher-output-fields {len(leak)}")
        ok &= not bad and not leak
    for b in STDIO_BANKS:
        p = os.path.join(DATA, b)
        if not os.path.exists(p):
            print(f"  MISSING {b}"); ok = False; continue
        rows = _load(p)
        bad = [r["task_id"] for r in rows if "tests_io" not in r or not r["tests_io"]]
        leak = [r["task_id"] for r in rows if any(k in r for k in ("output", "professor", "teacher"))]
        print(f"  {b}: {len(rows)} tasks | missing-tests {len(bad)} | teacher-output-fields {len(leak)}")
        ok &= not bad and not leak
    print("RESULT:", "OK — banks are well-formed and contain no teacher outputs" if ok else "PROBLEMS FOUND")
    return ok


def selftest():
    """Prove the deterministic judge works: a correct solution passes, a wrong one fails."""
    print("=== verifier self-test (offline) ===")
    from verify_code import run_one
    from verify_stdio import run_stdio

    good = "def add(a, b):\n    return a + b\n"
    bad = "def add(a, b):\n    return a - b\n"
    tests = "assert add(2, 3) == 5\nassert add(0, 0) == 0\n"
    ok_good, _ = run_one(good, tests, 10, 8, 1024)
    ok_bad, _ = run_one(bad, tests, 10, 8, 1024)
    print(f"  unit-test judge : correct->{ok_good} (expect True) | wrong->{ok_bad} (expect False)")

    s_good = "print(int(input()) + int(input()))\n"
    s_bad = "print(0)\n"
    io = [("2\n3\n", "5\n")]
    sg, _ = run_stdio(s_good, io, timeout=8)
    sb, _ = run_stdio(s_bad, io, timeout=8)
    print(f"  stdio judge     : correct->{sg} (expect True) | wrong->{sb} (expect False)")

    passed = ok_good and not ok_bad and sg and not sb
    print("RESULT:", "OK — judge accepts correct code and rejects wrong code" if passed else "JUDGE MISBEHAVED")
    return passed


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check-banks", action="store_true", help="validate released task banks")
    ap.add_argument("--selftest", action="store_true", help="prove the execution verifier works")
    a = ap.parse_args()
    if not (a.check_banks or a.selftest):
        ap.print_help(); sys.exit(0)
    allok = True
    if a.check_banks:
        allok &= check_banks()
    if a.selftest:
        allok &= selftest()
    sys.exit(0 if allok else 1)
