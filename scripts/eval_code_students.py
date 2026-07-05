#!/usr/bin/env python3
# 코딩 학생 held-out 평가 — 모델이 직접 생성 → 실행검증 → pass@1.
# 베이스(무어댑터) 및 교수별 학생 어댑터를 동일 held-out으로 평가(공정).
# 사용: python eval_code_students.py --base <dir> [--adapter <dir>] --bank heldout.jsonl --label <name> --out res.jsonl
import sys, os, re, json, argparse, gc, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_code import run_one
from verify_stdio import run_stdio
from prof_run import build_prompt, extract_code
from prof_run_stdio import build_prompt as build_prompt_stdio

def gen(model, tok, prompt, max_new=320):
    msgs = [{"role": "user", "content": prompt}]
    ids = tok.apply_chat_template(msgs, tokenize=True, add_generation_prompt=True, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(ids, max_new_tokens=max_new, do_sample=False,
                             repetition_penalty=1.05, pad_token_id=tok.eos_token_id)
    txt = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
    del ids, out; gc.collect(); torch.cuda.empty_cache()
    return txt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--adapter", default="")
    ap.add_argument("--bank", default="/mnt/cluster/sft_golden/taskbank_heldout.jsonl")
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scores", default="/mnt/cluster/adapters/CODE_EVAL_SCORES.md")
    a = ap.parse_args()

    from unsloth import FastLanguageModel
    model, tok = FastLanguageModel.from_pretrained(model_name=a.base, max_seq_length=2048,
                                                   dtype=torch.bfloat16, device_map={"": 0})
    if a.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, a.adapter)
    FastLanguageModel.for_inference(model)
    print(f"[{a.label}] loaded (adapter={a.adapter or 'NONE(base)'})", flush=True)

    n = passed = 0
    bycat = {}
    with open(a.bank) as fb, open(a.out, "w") as fo:
        for line in fb:
            line = line.strip()
            if not line: continue
            task = json.loads(line); n += 1
            cat = task["category"]; bycat.setdefault(cat, [0, 0]); bycat[cat][1] += 1
            stdio = "tests_io" in task  # 경쟁문제=stdin/stdout
            prompt = build_prompt_stdio(task) if stdio else build_prompt(task)
            code = extract_code(gen(model, tok, prompt, max_new=512 if stdio else 320))
            if not code:
                ok = False
            elif stdio:
                ok, _ = run_stdio(code, [(t[0], t[1]) for t in task["tests_io"]], timeout=8)
            else:
                ok, _ = run_one(code, task["tests"], 10, 8, 1024)
            if ok:
                passed += 1; bycat[cat][0] += 1
            fo.write(json.dumps({"task_id": task["task_id"], "category": cat, "pass": bool(ok)}, ensure_ascii=False) + "\n")
            if n % 25 == 0:
                print(f"  [{a.label}] {passed}/{n}", flush=True)
    rate = 100.0 * passed / n if n else 0
    line = f"[{a.label}] pass@1 = {passed}/{n} = {rate:.1f}%"
    for c, (p, t) in sorted(bycat.items()):
        line += f" | {c} {p}/{t}"
    print(line, flush=True)
    # 요약 append
    with open(a.scores, "a") as sf:
        sf.write(f"| {a.label} | {rate:.1f}% | " + " | ".join(f"{c}:{p}/{t}" for c,(p,t) in sorted(bycat.items())) + " |\n")

if __name__ == "__main__":
    main()
