# Compete then Collaborate — Reproducibility Release

Code, tasks, tests, harness, and the RLVR student for the paper
*"Compete then Collaborate: Frontier AI Teachers Build a Verifiable Curriculum to Improve a Coding Student Beyond Imitation."*

> **Try it yourself.** Our judge is deterministic **code execution**, so every number is recomputable from the released files — no need to trust us or re-query any teacher.

## Contents
- `scripts/` — verification harness (`verify_code.py`, `verify_stdio.py`), task-bank builders, teacher runners, self-correction, intersection, evaluation, and GRPO (RLVR) trainer.
- `data/` — task banks + **hidden tests** (derived from public MBPP & code_contests, with provenance). **Raw teacher outputs are NOT included** (see `TOS_COMPLIANCE.md`).
- `results/` — eval scores, RLVR learning curve, reward curves, training logs.
- `models/` — RLVR student LoRA adapter (teacher-output-free) [HF Hub link].
- `patches/` — framework patches to run GRPO on NVIDIA GB10 (transformers 5.5 / torch 2.11 / cu130).
- `reproduce.py` — recompute the paper's tables from the released artifacts.

## Two reproduction paths
1. **Static re-verification (offline, minutes):** run `python reproduce.py --verify` to re-execute the released solutions/students against the hidden tests and reproduce every pass@1 in the paper. No internet, no API keys.
2. **Full regeneration (clean-room):** run `scripts/prof_run*.py` with **your own** provider API keys to regenerate teacher solutions under **your own** terms, then re-verify. We never redistribute teacher outputs.

## Hardware / environment
- NVIDIA GB10 (DGX Spark), 128GB unified memory. torch 2.11.0+cu130, transformers 5.5, trl 0.24 (+ patches in `patches/`).
- Student: Qwen2.5-Coder-7B/-32B (LoRA). Held-out: MBPP-test (150) + disjoint code_contests (68), leakage-checked.

## License & terms
- Code: [choose e.g. Apache-2.0]. Upstream data (MBPP, code_contests) redistributed under their licenses with attribution.
- **Teacher outputs are not redistributed** — see `TOS_COMPLIANCE.md` for the per-provider (Anthropic/OpenAI/xAI) analysis and our compliance decisions.

## Cite
[bib entry — to be finalized with venue]
