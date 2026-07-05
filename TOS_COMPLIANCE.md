# ToS Compliance & Data Release Policy

> Read carefully before publishing. Based on verbatim review of each provider's terms (2026-07-04).
## 0. Academic-research purpose (governing framing)
This work is **academic research** — a benchmarking and methodology study — **not** the development, deployment, or distillation of a commercial model that competes with any provider. No model trained here is offered as a product or service. This framing is decisive for the providers whose restrictions are **competition-scoped**:
- **Anthropic** restricts building a *competing product* / training *competing AI models* — a non-commercial research student is not a competing product → not applicable.
- **OpenAI** restricts using Output to *develop models that compete with OpenAI* — a research, non-deployed model does not compete → not applicable.
- **xAI**'s clause is **act-scoped** ("distilling Outputs"), so academic intent alone does not fully exempt the SFT arm; we therefore add conservative mitigations (D1–D4): no raw-output redistribution, no release of teacher-distilled weights, and the headline RLVR result uses public problems + execution reward (no teacher-output distillation).

> **Principle: we do NOT redistribute any teacher's raw outputs; the headline RLVR result uses public problems + execution reward (no teacher-output distillation).**

## 1. Per-provider terms (as reviewed 2026-07-04)
| Provider | Output ownership | Train models on Output | Redistribute Output |
|---|---|---|---|
| **Anthropic (Claude)** | Customer owns Outputs | Prohibits building **competing** product / training **competing** AI models (Commercial Terms §D.4) | No explicit prohibition |
| **OpenAI (Codex/GPT)** | User owns Output | Prohibits using Output to **develop models that compete with OpenAI** (binds original generator only) | No explicit prohibition; downstream recipients not bound |
| **Google (Gemini)** | User retains output rights | Generative-AI terms restrict using the service/output to develop **competing** ML models/services | No explicit blanket redistribution ban; verify current API terms |
| **xAI (Grok)** | User owns User Content | Prohibits using Output to **develop competing** models AND **"distilling model data or Outputs"** (AUP) | Prohibits **"distributing / distilling Outputs"** ⚠️ strictest |

## 2. Compliance decisions
- **D1 — Do NOT publish raw teacher outputs.** xAI explicitly prohibits distributing Outputs; we apply this conservatively to all three. `data/teacher_outputs/` is **excluded** from the public release.
- **D2 — Headline result (RLVR) is distillation-free.** RLVR reward = execution of the *student's own* code on `deepmind/code_contests` public tests. Teacher answers are **not** in RLVR training. This is the paper's central positive claim and is ToS-clean w.r.t. teacher outputs.
- **D3 — SFT is a research baseline showing imitation *fails*.** Teacher outputs were used only for internal research comparison, not to build a commercial competing product, and are not redistributed. We do **not** release the SFT/union student weights that were trained on teacher outputs (esp. any Grok-derived weights) to avoid "distilling Outputs" concerns; we release the **RLVR student** (teacher-output-free).
- **D4 — Reproduction by regeneration.** We release tasks, prompts, hidden tests, and the verification harness. Users regenerate teacher outputs **with their own API keys under their own ToS** — we never redistribute. This preserves "try it yourself" without violating any provider's terms.
- **D5 — Benchmarking framing.** Reporting execution pass rates of named models is standard benchmarking (permitted). The judge is deterministic code execution, not an LLM, so no self-preference bias and no LLM-judge licensing entanglement.
- **D6 — Upstream dataset licenses.** MBPP (cc-by-4.0) and `deepmind/code_contests` (Apache-2.0/CC BY 4.0) are redistributed with attribution per their licenses; task banks derived from them are released with provenance.

## 3. What is / isn't in the public release
| Included | Excluded |
|---|---|
| scripts (harness, builders, train/eval, GRPO) | raw teacher outputs (`cc_*_gold_raw`, `code_*_gold_raw`) |
| task banks + hidden tests (public-dataset-derived) | SFT/union student weights trained on teacher outputs |
| RLVR student LoRA adapter (teacher-output-free) | provider API keys / credentials |
| result logs, learning curve, reward curves, eval scores | — |
| `reproduce.py` (recompute paper numbers from released files) | — |

## 4. Paper ethics statement (drop-in)
> "Teacher outputs were used solely for internal research evaluation and are not redistributed. Our primary result (RLVR) uses public competition problems with an execution-based reward and does not distill teacher outputs. The SFT baseline, which uses teacher outputs, serves only to demonstrate that imitation fails; we do not release models trained on teacher outputs. We report execution-verified pass rates (a deterministic judge), and we release tasks, tests, and harness so that any party may reproduce every number either by re-running the released verifier on our artifacts or by regenerating teacher solutions under their own provider agreements."

*Reviewed against Anthropic Commercial Terms, OpenAI Terms of Use, xAI Consumer ToS + AUP — 2026-07-04. Re-verify before public push (terms change).*
