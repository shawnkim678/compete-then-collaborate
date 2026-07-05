#!/usr/bin/env python3
# RLVR(GRPO) 코딩 학생 — 표준 HF+PEFT (Unsloth 커스텀커널 회피, bf16 일관).
# 보상=실행검증(테스트 통과비율). vllm off(HF generate 롤아웃). 데이터=경쟁문제.
# 사용: python grpo_train.py [--steps N] [--out DIR] [--gen G]
import os, sys, re, json, argparse
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
import torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verify_stdio import run_stdio

BASE = "/home/smroot/models/qwen2.5-coder-7b"
BANK = "/mnt/cluster/sft_golden/taskbank_contests.jsonl"
BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)

def extract_code(text):
    b = BLOCK.findall(text or "")
    return b[-1].strip() if b else ""

def make_prompt(desc):
    return ("You are an expert competitive programmer. Solve in Python 3, reading stdin and writing stdout.\n\n"
            "Problem:\n" + desc[:3500] +
            "\n\nThink briefly, then give EXACTLY ONE python code block with the complete runnable program.")

def _text_of(comp):
    try:
        if isinstance(comp, str):
            return comp
        if isinstance(comp, list) and comp and isinstance(comp[0], dict):
            return comp[0].get("content", "")
        return str(comp or "")
    except Exception:
        return ""

def reward_pass(completions, tests_io=None, **kwargs):
    # 절대 None/nan 반환 금지(전 항목 float) — TRL nan-row 경고 버그 회피
    outs = []
    tio_list = tests_io if tests_io is not None else [None] * len(completions)
    for comp, tio in zip(completions, tio_list):
        try:
            code = extract_code(_text_of(comp))
            if not code or not tio:
                outs.append(0.0); continue
            tests = [(t[0], t[1]) for t in tio]
            p = sum(1 for tc in tests if run_stdio(code, [tc], timeout=6)[0])
            outs.append(float(p) / max(len(tests), 1))
        except Exception:
            outs.append(0.0)
    return outs

def reward_format(completions, **kwargs):
    outs = []
    for comp in completions:
        try:
            outs.append(0.1 if extract_code(_text_of(comp)) else 0.0)
        except Exception:
            outs.append(0.0)
    return outs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--out", default="/mnt/cluster/adapters/code-grpo-7b-v1")
    ap.add_argument("--gen", type=int, default=6)
    a = ap.parse_args()

    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig
    from datasets import Dataset
    from trl import GRPOConfig, GRPOTrainer
    # trl0.24 ↔ transformers5.5 호환 몽키패치: PreTrainedModel.warnings_issued 누락 보완
    if not hasattr(transformers.PreTrainedModel, "warnings_issued"):
        transformers.PreTrainedModel.warnings_issued = {}

    rows = [json.loads(l) for l in open(BANK) if l.strip()]
    ds = Dataset.from_list([{"prompt": make_prompt(r["instruction"]), "tests_io": r["tests_io"]}
                            for r in rows if r.get("tests_io")])
    print(f"[grpo] 데이터 {len(ds)}문제", flush=True)

    tok = AutoTokenizer.from_pretrained(BASE)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        BASE, torch_dtype=torch.bfloat16, device_map={"": 0}, attn_implementation="sdpa")
    model.config.use_cache = False

    peft_config = LoraConfig(
        r=32, lora_alpha=64, lora_dropout=0.0, bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"])

    cfg = GRPOConfig(
        output_dir=a.out, use_vllm=False,
        learning_rate=1e-5, adam_beta1=0.9, adam_beta2=0.99, weight_decay=0.1,
        warmup_ratio=0.05, lr_scheduler_type="cosine", optim="adamw_8bit",
        per_device_train_batch_size=a.gen, gradient_accumulation_steps=1,
        num_generations=a.gen, max_prompt_length=1024, max_completion_length=512,
        max_steps=a.steps, save_steps=50, logging_steps=1,
        bf16=True, fp16=False, gradient_checkpointing=True,
        report_to="none", temperature=0.8)

    trainer = GRPOTrainer(model=model, processing_class=tok,
                          reward_funcs=[reward_pass, reward_format], args=cfg,
                          train_dataset=ds, peft_config=peft_config)
    trainer.train()
    trainer.save_model(a.out); tok.save_pretrained(a.out)
    print(f"[grpo] 완료 → {a.out}", flush=True)

if __name__ == "__main__":
    main()
