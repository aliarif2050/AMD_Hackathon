# Practice Set — Evaluation Notes

Phase 6 (PRD §21) deterministic evaluation harness. **Zero API cost.**

## Files
- `eval_set.json` — 80 labeled, fresh-authored tasks (risk-weighted split, D-3).
  Never the hidden tasks; never hardcoded into `app/`.
- `evaluate.py` — standalone scorer. Runs `router.classify` (vs `expected_type`)
  + `local_solvers.try_solve` under **production routing** (`try_solve(classified, prompt)`)
  vs `expect_local`, then normalized variant-match on `gold`/`accepted` (D-4).
  Model-routed tasks → `score_generative()` returns `"deferred"` (D-6 seam). No API.
- `eval_report.json` — machine-readable output of the latest run.

## Run it
```bash
.venv/Scripts/python.exe practice/evaluate.py
```

## Risk-weighted distribution (80 tasks)
math 16 (10 fire / 6 decline), sentiment 14 (8 / 6), reasoning 12, code 12,
ner 8, summary 6, factual 6, general 6.

## Results

| Date | Ver | Class acc | Fire acc | Answer-match | Deferred | Misses |
|------|-----|-----------|----------|--------------|----------|--------|
| 2026-07-09 | baseline | 97.5% (78/80) | 96.2% (77/80) | 16/16 | 62 | 3 |
| 2026-07-09 | tuned | 100% (80/80) | 100% (80/80) | 18/18 | 62 | 0 |

### Weak spots found → fixed (baseline → tuned)
1. **Classifier gap — bare arithmetic.** `Calculate 156 + 89` and `What is 47 times 3?`
   routed to general/factual (no math keyword), starving the arithmetic solver.
   Fix: `router._ARITH_EXPR` detects `number <op> number` in `_has_math_shape`.
2. **Dangerous false-fire.** `What is 30% of 90 plus 12?` wrongly fired binary
   arithmetic on `90 plus 12` (=102). Fix: `_try_binary_arithmetic` declines when
   `%` is present.

Both fixes are additive; full pytest suite green (62 passed). Token counts N/A —
this layer is deterministic (0 Fireworks tokens). Generative scoring deferred (D-2).
