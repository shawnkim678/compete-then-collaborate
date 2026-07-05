#!/usr/bin/env python3
# 코딩 골든셋 실행검증 하네스 (교수진 비교연구용, stdlib 전용)
# 각 샘플: solution_code + tests 를 격리 서브프로세스로 실행 → 통과분만 골든셋 채택.
# 사용: python verify_code.py <in.jsonl> <out_golden.jsonl> [--timeout 10]
#
# 입력 레코드 스키마(교수가 생성):
#   {task_id, professor, category, instruction, input, output, solution_code, tests}
#     - output       : SFT 학습 타깃(추론+코드, 사람이 읽는 교습답)
#     - solution_code: 실행가능 코드(함수정의 등)
#     - tests        : assert 기반 검증코드 (solution_code 뒤에 붙여 실행)
# 통과 기준: (solution_code + tests) 서브프로세스 실행이 예외 없이 종료.
import sys, os, json, subprocess, tempfile, argparse, textwrap

RUNNER = textwrap.dedent('''
    import resource, sys
    # 리소스 제한: CPU {cpu}s, 메모리 {mem}MB
    try:
        resource.setrlimit(resource.RLIMIT_CPU, ({cpu}, {cpu}))
        resource.setrlimit(resource.RLIMIT_AS, ({mem}*1024*1024, {mem}*1024*1024))
    except Exception:
        pass
''')

def run_one(sol, tests, timeout, cpu, mem):
    src = RUNNER.format(cpu=cpu, mem=mem) + "\n" + sol + "\n\n" + tests + "\nprint('__OK__')\n"
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "t.py")
        with open(f, "w") as fh:
            fh.write(src)
        try:
            r = subprocess.run([sys.executable, f], capture_output=True, text=True,
                               timeout=timeout, cwd=d)
            ok = (r.returncode == 0) and ("__OK__" in r.stdout)
            err = "" if ok else (r.stderr or r.stdout)[-500:]
            return ok, err
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT"
        except Exception as e:
            return False, f"RUNNER_ERR:{e}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--timeout", type=int, default=10)
    ap.add_argument("--cpu", type=int, default=8)
    ap.add_argument("--mem", type=int, default=1024)
    a = ap.parse_args()

    n = passed = 0
    bycat = {}
    with open(a.inp) as fin, open(a.out, "w") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            n += 1
            r = json.loads(line)
            sol = r.get("solution_code", "")
            tests = r.get("tests", "")
            ok, err = run_one(sol, tests, a.timeout, a.cpu, a.mem)
            cat = r.get("category", "?")
            bycat.setdefault(cat, [0, 0])
            bycat[cat][1] += 1
            tid = r.get("task_id", f"#{n}")
            if ok:
                passed += 1
                bycat[cat][0] += 1
                # 학습용 필드만 저장
                fout.write(json.dumps({
                    "instruction": r["instruction"],
                    "input": r.get("input", ""),
                    "output": r["output"],
                    "task_id": tid, "professor": r.get("professor", "?"), "category": cat,
                }, ensure_ascii=False) + "\n")
                print(f"  PASS {tid} [{cat}]")
            else:
                print(f"  FAIL {tid} [{cat}] :: {err.splitlines()[-1] if err else ''}")

    print(f"\n=== 검증결과: {passed}/{n} 통과 → {a.out} ===")
    for c, (p, t) in sorted(bycat.items()):
        print(f"    {c}: {p}/{t}")

if __name__ == "__main__":
    main()
