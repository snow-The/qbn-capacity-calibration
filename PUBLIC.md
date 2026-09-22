# What this repository publishes — and what it deliberately does not

This repository is the **public companion to the paper**. It carries the paper source, the code,
and the verification artefacts — the things a reader needs to check or reproduce the work.

## Published

| Path | What it contains |
|---|---|
| `paper/` | Paper source (Typst is the single source of content), the generated LaTeX, and `submission.zip` |
| `theory/` | The theorem write-ups (T1–T6) and their numerical verification scripts |
| `formal/` | Lean 4 formalisation of the core theorems, with the axiom audit |
| `hardware/` | Real-hardware protocol for Quantum Inspire / Tuna-17: submitter, analysers, and diagnostics |
| `results/` | Compact result summaries and the **raw hardware counts** |
| `c1/` | Cross-framework reproduction study |
| `ml/` | Model specification and training code |
| `tools/` | Pre-release check |

## Deliberately NOT published

| Excluded | Why |
|---|---|
| `docs/` | The **internal document set**. It contains a defence script, an ownership map that states who answers which question and how to hand off, self-assessments against academic standards, and candid status and decision notes. These are working documents for the authors, not part of the scientific record. |
| `ml/_verify/*_README.md` | **Third-party model cards** downloaded from HuggingFace while selecting embedding models. We hold no rights to them. |

## How this is enforced

`tools/verify_repo.py` fails the release check when any excluded path reappears, so a later sync
from the working repository cannot leak them by accident. Run it before every push:

```bash
python tools/verify_repo.py
```

## Changing the policy

Edit the `FORBIDDEN` list in `tools/verify_repo.py` **and** the tables above together. If something
currently internal should become public, the honest order is: decide, then move it, then update both
places — not the other way round.
