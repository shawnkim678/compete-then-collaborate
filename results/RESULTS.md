# Results (execution-verified, deterministic)

All numbers come from executing code against hidden tests — no LLM judge, no teacher raw outputs.

## Teacher competition — pass@1 (four labs)

### Easy (MBPP, 200 shared problems) — saturated
| Teacher | one-shot | after self-correction |
|---|---|---|
| Claude | 96.5% | 100% |
| Grok | 89.5% | 99.5% |
| Codex | 90.0% | 99.0% |
| Gemini | 85.0% | 99.5% |

### Hard (code_contests d6–9, 150 problems) — the informative signal
| Teacher | pass@1 | code-extraction |
|---|---|---|
| Gemini | 77% (115/150) | 100% |
| Codex | 69% (103/150) | 90% |
| Claude | 67% (82/122) | 96% |
| Grok | 50% (75/150) | 73% |

Fairness notes: Grok's and Gemini's first runs hit infrastructure artifacts (empty CLI
responses / API credit depletion) that were corrected by re-running the affected items;
reported numbers are post-correction. See paper §5.1.

## Collaboration: imitation (SFT) vs verifiable-reward RL (RLVR)

| Method | competition base→student | direction |
|---|---|---|
| SFT (union) | 5.9% → 2.9% | down (degrade) |
| RLVR (GRPO, 1000 steps) | 5.9% → 8.8% peak (7.4% @1000) | up (+49% rel. at peak) |

## RLVR v2 learning curve (held-out 68 competition problems)
See `learning_curve_v2.tsv`. base 5.9% → 8.8% plateau (steps 250–750) → 7.4% at step 1000.
Differences within the plateau are within ±1 problem (sampling noise); robust signal is base→RLVR.

*No teacher raw outputs are included (ToS D1). Reproduce by regenerating teacher solutions with
your own API keys (D4), or re-run the released verifier on the released task banks.*
