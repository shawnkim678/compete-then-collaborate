# LaTeX build — Compete then Collaborate (v0.2)

## Files
- `main.tex` — arXiv-neutral article (single-column, `article` class).
- `refs.bib` — bibliography, all entries filled with verified citations
  (jang1999ola; multiteacherkd = Jin et al., ICLR 2026, arXiv:2602.01064;
  rlhfbook = Lambert 2025, Manning/arXiv:2504.12501; minillm = Gu et al., ICLR 2024,
  arXiv:2306.08543; distillm2 = Ko et al., 2025, arXiv:2503.07067).

## Compile
```bash
latexmk -pdf main.tex          # preferred
# or:
pdflatex main && bibtex main && pdflatex main && pdflatex main
```
No local TeX here — use Overleaf (upload `main.tex` + `refs.bib`) or a machine with
`texlive-latex-extra` (needs `pgfplots`, `booktabs`, `natbib`, `hyperref`).

## Status — results complete (all `\pending{}` removed)
- ✅ **Gemini (4th teacher)** folded into the §5.1 competition tables (MBPP + hard).
- ✅ **v2 1000-step RLVR learning curve** — §5.3 figure uses logged reward + per-checkpoint
  held-out pass@1 (real coordinates, twin-axis pgfplots).
- ✅ **Bibliography** — all entries verified (no placeholders).

## Optional before submission
1. **Workshop-template variant**: once a venue is chosen, wrap the same body in that venue's
   class (e.g. `acl`, `neurips_2026`); keep `main.tex` as the neutral master.

## Copyright / secrets safety
- No teacher raw outputs, no API keys, no third-party copyrighted PDFs are included here.
- The Jang (1999) dissertation is cited bibliographically only; the PDF stays in
  `references/` (git-ignored) and is never redistributed.
