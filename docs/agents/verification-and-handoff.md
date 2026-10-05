# Verification and handoff

Before close, record changed paths, actual test commands/results, evidence,
limitations and the real `publication_receipt_ref` from an applied scoped commit.
Call `aware issue close` with current digest, actor/evidence, unique intent,
resolution, `--verified-by` and `--publication-receipt-ref`. The owner validates
that receipt and publishes the Issue-only closeout; no Goal acceptance is implied.

For a replacement execution:

1. Current owner appends evidence, remaining work and known blockers.
2. Current owner invokes `issue block`, then `issue set-owner --new-owner-ref`
   with the replacement's actual harness execution id and fresh digest each time.
3. Replacement observes the durable projection and verifies owner/status/scope.
4. Replacement invokes `issue resume` with its own actor/evidence and current digest.

A transcript is explanatory, not authority. Current local actor strings are
declared rather than authenticated. Refusals and incomplete results remain
evidence; do not convert absence of an operation into an enforcement pass.

Authored acceptance remains unchecked unless separately evidenced; Issue
closeout does not evaluate it or grant Goal acceptance. Retain actual index
warnings: unknown is not clean. Summaries preserve publication owner and
reference-update state; default JSON remains available.
