# Agent consumption contract

This governs using the installed filesystem preview in a customer repository,
not modifying the Aware repository itself. Follow the customer's own agent
contract and approvals too. This bundle selects filesystem authority explicitly.

1. Publish your actual stable harness identity. Codex: `codex-$CODEX_THREAD_ID`;
   Claude Code: `claude_code-$CLAUDE_CODE_SESSION_ID`. Missing or ambiguous
   identity means read-only; never reuse a previous execution's identifier.
2. Use the exact installed `aware` path. Do not import development sources,
   install service dependencies, use a different environment or fabricate an
   unsupported capability. This local actor evidence is declared, not authenticated.
3. Obtain the explicit customer repository, problem, objective, acceptance and source
   paths. Initialize through `aware init`; open exactly one scoped Issue through
   `aware issue open`. Never infer assignment from cwd, title, transcript or cache.
4. Supply repeatable `--problem`, `--objective`, `--acceptance` at open. Criteria
   start unchecked and closure does not automatically check them. Use
   `append-update` for progress/evidence. Preserve other work. Modify only approved authored sources;
   do not manually edit Issue ownership, lifecycle, scope, histories or receipts.
5. Observe through `resolve-read-projection` before every mutation. Supply the
   latest `projection.source.digest`; stale refusals require a fresh observation,
   not a digest invented to match a desired result.
6. Record actual test/evidence outcomes through tooling. Dry-run the exact
   `aware repository commit` request, inspect it, then apply unchanged. Repeat
   only the explicit owned `--path` arguments. Never raw-stage/commit as a workaround.
7. Retain the actual publication receipt. Close through `aware issue close`
   with it, the current Issue digest, resolution and actual verification. Close
   also publishes its own Issue-only closeout receipt. Do not claim Goal acceptance.
8. Hand over by block → set-owner to the exact replacement execution → fresh
   observation and resume by that execution. Record handoff evidence first.
   Caller strings and a transcript do not prove who operated the host.
9. Treat incomplete compositions and failures as retained state needing
   inspection. Do not overwrite a record, broaden scope or restore local truth
   for service-owned state to make a command pass.

Read [the copy-and-run workflow](quickstart.md). Goal creation, approval,
effectful pursuit, dispatch and Service/API are not in this bundle. Local tool
checks are neither a sandbox nor authority against arbitrary filesystem writers.

Optional `--format summary` reuses the shared owner-facing summary. Preserve its
publication state, receipts and index warnings; default SDK JSON remains available.
Missing historical fields mean unknown, not success or a clean checkout.
