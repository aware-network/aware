# Issue protocol — filesystem v1

Record profile: `aware.issue.markdown.v1`. Authority: the admitted filesystem
Issue provider under explicit `aware.protocol.toml`. SDK operations own lifecycle
and Markdown changes; agents do not hand-edit authority records.

Reference: `fb/YYYY-MM-DD/<slug>`. Path under the admitted root:
`YYYY/MM/DD/fb-YYYY-MM-DD-<slug>.md`. Status, owner, exact scope, append-only
updates, verification and publication receipts are retained durably.

## Supported commands

- `aware issue open`: compose ensure snapshot → bind scope → start progress;
  requires explicit title, actor/evidence, unique intent and source paths.
- `aware issue resolve-read-projection`: observe status, owner, scope and source digest.
- `aware issue append-update` / `append-evidence`: retain actual request, acceptance and evidence.
- `aware issue bind-scope`: explicit customer-approved scope change, not inferred expansion.
- `aware issue block`, `set-owner`, `resume`: controlled replacement with fresh observations.
- `aware repository commit`: dry-run/apply exact owned publication through the existing owner.
- `aware issue close`: verify applied implementation receipt and publish Issue-only closeout.

Mutations require the exact latest digest, unique `--client-intent-id`,
`--actor-ref` and `--actor-evidence-ref`. Commit uses
`--expected-issue-source-sha256`; other writes use `--expected-source-sha256`.
Use `--help` for complete operation-specific inputs. Never guess a receipt.

Open is not atomic across its three operations. Retain incomplete receipts and
inspect state before recovery. Closing is not acceptance of a Goal or permission
to push. Customer authorization and filesystem permissions remain necessary.

Alignment and working notes are scoped authored documentation, not another Issue
registry. A cache, transcript, cwd or title never grants current ownership.

## Initial authored content and opt-in summary

New `aware issue open` requests require repeatable `--problem`, `--objective`
and `--acceptance`. They use the same SDK and Markdown owner; no manual record
edits or automatic acceptance. Narrative updates do not rewrite these items.
Omitted-content SDK compatibility remains available through lower-level tooling.

Use `--format summary` for concise SDK evidence; JSON remains default. Preserve
every constituent receipt on incomplete open. Publication summaries retain
`operator_ref`, `transaction_mode` and `reference_update`, including refusals.
Closeout index fields describe that operation only: pending is retained debt,
unknown is missing evidence, and neither proves a clean current Git index.
