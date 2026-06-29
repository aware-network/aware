# Meta Runtime Performance Samples

This directory owns Meta-local performance samples.

Rules:

- Do not import Home proofs or Workspace proof packages.
- Keep `.aware` samples under `sample_packages/` so source/delta tests have real inputs.
- Keep Python graph builders deterministic so budget tests can fail on Meta behavior, not fixture drift.
- Use these samples before promoting a Home proof timing into a Meta performance contract.

