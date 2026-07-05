# Compete then Collaborate — Reproducibility Release

Code, task banks, hidden tests, and the verification harness for the paper
**_"Compete then Collaborate: Frontier AI Teachers Build a Verifiable Curriculum to Improve a Coding Student Beyond Imitation."_**

![python](https://img.shields.io/badge/python-3.12-blue)
![license](https://img.shields.io/badge/code-Apache--2.0-green)
![judge](https://img.shields.io/badge/judge-code%20execution-orange)
![reproducible](https://img.shields.io/badge/reproducible-yes-brightgreen)

> **Try it yourself.** Our judge is deterministic **code execution**, not an LLM. Every number is
> recomputable from the released files or by regenerating teacher solutions under your own provider
> terms — no need to trust us. We do **not** redistribute any teacher's raw outputs (see
> [`TOS_COMPLIANCE.md`](TOS_COMPLIANCE.md)).

---

## TL;DR results (execution-verified)

**Four frontier teachers ranked head-to-head on hard competition problems** (`code_contests` d6–9, 150 problems):

| Teacher | pass@1 | extraction |
|---|---|---|
| **Gemini** | **77%** (115/150) | 100% |
| Codex | 69% (103/150) | 90% |
| Claude | 67% (82/122) | 96% |
| Grok | 50% (75/150) | 73% |

**Same collaborative curriculum, opposite directions** — imitation degrades a competent coder, verifiable-reward RL improves it:

| Method | held-out competition base → student | direction |
|---|---|---|
| SFT (union of teachers) | 5.9% → 2.9% | ↓ degrade |
| **RLVR (GRPO, 1000 steps)** | 5.9% → **8.8%** peak (7.4% @1000) | ↑ **+49% rel. at peak** |

Full numbers and the v2 learning curve: [`results/RESULTS.md`](results/RESULTS.md),
[`results/learning_curve_v2.tsv`](results/learning_curve_v2.tsv).

---

## Quickstart

```bash
git clone git@github.com:shawnkim678/compete-then-collaborate.git
cd compete-then-collaborate
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# offline sanity checks — no GPU, no internet, no API keys
python reproduce.py --check-banks   # task banks well-formed (problem + hidden tests)
python reproduce.py --selftest      # prove the execution verifier works on known code
```

## Repository layout

```
compete-then-collaborate/
├── scripts/          # execution-verified harness + pipeline
│   ├── verify_code.py         # isolated subprocess unit-test verifier (asserts)
│   ├── verify_stdio.py        # stdin/stdout verifier (competition problems)
│   ├── build_taskbank_mbpp.py # MBPP → function/bugfix task bank
│   ├── build_contests_bank.py # code_contests → stdio task bank
│   ├── prof_run.py            # run a teacher on the shared bank, keep test-passing code
│   ├── prof_run_stdio.py      # same, for competition (stdio) problems
│   ├── prof_retry.py          # self-correction (feed failing test back, retry)
│   ├── equalize_golden.py     # intersection control (problems all teachers solved)
│   ├── eval_code_students.py  # held-out pass@1 for base / student adapters
│   ├── grpo_train.py          # RLVR (GRPO) trainer, reward = fraction of tests passed
│   └── gemini_cli.py          # headless Gemini caller (key from env only)
├── data/             # task banks — problems + HIDDEN TESTS only (no teacher outputs)
│   ├── taskbank_full.jsonl              # MBPP function/bugfix (teaching split)
│   ├── taskbank_heldout.jsonl           # MBPP-test held-out (150)
│   ├── taskbank_contests.jsonl          # code_contests d6–9 (150)
│   └── taskbank_contests_heldout.jsonl  # disjoint competition held-out (68)
├── results/          # execution pass rates + RLVR learning curve (numbers, not outputs)
├── paper/            # manuscript: main.tex, refs.bib, draft, build README
├── reproduce.py      # offline bank checks + verifier self-test; entry point
├── scan_secrets.sh   # value-based secret scanner (run before any commit)
├── TOS_COMPLIANCE.md # per-provider ToS analysis + release decisions D1–D6
└── requirements.txt
```

**Not included by policy** (regenerate them yourself):
- Teacher raw outputs / verified solutions (`*_gold*.jsonl`) — **D1**. Regenerate with your own keys (below).
- SFT / teacher-distilled student weights — **D3**.
- The RLVR student LoRA adapter is teacher-output-free (**D3**) and may be published separately on the HF Hub; a link will be added here when uploaded.

## Two reproduction paths

**1. Offline (minutes, no keys):** validate the released artifacts and the judge.
```bash
python reproduce.py --check-banks   # counts + fields + tests parse for every bank
python reproduce.py --selftest      # runs correct & incorrect samples through the verifier
```

**2. Full regeneration (clean-room, your keys, your terms):** reproduce the teacher pass@1 tables.
```bash
# each teacher solves the SAME bank; only test-passing code is kept (D4 — we never redistribute outputs)
python scripts/prof_run.py       --professor claude --bank data/taskbank_full.jsonl --out /tmp/claude_gold.jsonl
python scripts/prof_run_stdio.py --professor gemini --bank data/taskbank_contests.jsonl --out /tmp/gemini_cc.jsonl --timeout 300
python scripts/prof_retry.py     --professor claude --bank data/taskbank_full.jsonl        # self-correction
```
Teacher CLIs are pluggable in `scripts/prof_run.py` (`CMD` dict). Keys are read from the environment only
(e.g. `GEMINI_API_KEY`); never hard-code them.

**3. RLVR student eval** (once the adapter is released / or after you train it):
```bash
python scripts/eval_code_students.py --base <qwen2.5-coder-7b> \
    --adapter <rlvr-adapter> --bank data/taskbank_contests_heldout.jsonl --label rlvr
```

## Which command reproduces which number

| Paper number | How to reproduce |
|---|---|
| Teacher competition pass@1 (§5.1) | path 2: `prof_run*.py` + `prof_retry.py`, then read the printed `pass@1` |
| SFT student held-out (§5.2) | train LoRA on the union golden set, then `eval_code_students.py` |
| RLVR base→student (§5.3) | `grpo_train.py`, then `eval_code_students.py --adapter <ckpt>` on `taskbank_contests_heldout.jsonl` |
| v2 learning curve | eval each checkpoint on the 68 held-out problems (see `results/learning_curve_v2.tsv`) |

## Hardware / environment

- **NVIDIA GB10 (DGX Spark)**, 128 GB unified memory.
- torch **2.11.0+cu130**, transformers **5.5.0**, trl **0.24.0**, peft **0.19.1**, unsloth **2026.6.9** (see `requirements.txt`).
- Student: Qwen2.5-Coder-7B / -32B (LoRA, bf16).
- Held-out: MBPP-test (150) + disjoint `code_contests` (68); held-out IDs are disjoint from the teaching split by construction (see `build_*` scripts).
- **Paths**: some scripts (e.g. `grpo_train.py`'s `BASE`) use absolute local paths — edit them to your model/data locations.

## Data provenance & licenses

| Source | License | Use here |
|---|---|---|
| [MBPP](https://github.com/google-research/google-research/tree/master/mbpp) | CC BY 4.0 | function/bugfix task banks |
| [`deepmind/code_contests`](https://github.com/deepmind/code_contests) | Apache-2.0 / CC BY 4.0 | competition task banks |

Task banks derived from these are released with attribution (**D6**). Code in this repo: **Apache-2.0** (`LICENSE`).

## Limitations (honest)

- RLVR gains are modest in absolute terms; the held-out set has only 68 problems, so differences within
  the RLVR plateau (±1 problem ≈ ±1.5 pp) are within sampling noise. The robust claim is the **direction**
  (SFT ↓ vs RLVR ↑), not a precise peak. Prefer checkpoint selection over training to the last step.
- Single student family (Qwen2.5-Coder), one language (Python).
- Teacher CLI reliability affects one-shot numbers; we correct infrastructure artifacts (empty responses,
  API credit depletion) by re-running affected items and report post-correction (see paper §5.1).

## Ethics / terms of service

This is **academic research** (benchmarking + methodology), not the development of a competing commercial
model. We do not redistribute teacher outputs, do not release teacher-distilled weights, and base the
headline RLVR result on public problems with an execution reward (no teacher-output distillation). Full
per-provider analysis and decisions D1–D6: [`TOS_COMPLIANCE.md`](TOS_COMPLIANCE.md).

## Cite

```bibtex
@misc{competethencollaborate2026,
  title  = {Compete then Collaborate: Frontier AI Teachers Build a Verifiable Curriculum
            to Improve a Coding Student Beyond Imitation},
  author = {Kim, Miseong Shawn},
  year   = {2026},
  note   = {Preprint. Code: https://github.com/shawnkim678/compete-then-collaborate},
}
```
