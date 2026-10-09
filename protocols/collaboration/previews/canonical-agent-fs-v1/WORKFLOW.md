# One installed entrance, existing owners — draft workflow

Use AWARE from this preview's single fresh installation. Require the prepared
repository/profile and customer-approved outcome described in README.md. No
initializer is supplied. Do not copy raw Markdown, use another environment's
bootstrap, or borrow a provider execution to hide missing admission.

## Coordinates and guards

Set REPOSITORY to the exact absolute Git root. PROTOCOL_MANIFEST is relative to
that root or an accepted absolute path. SPEC_MANIFEST must be canonical
repository-relative, not relative to the Protocol file. SNAPSHOT_JSON should be
absolute: relative input paths are based on the invoking process directory.
These are arguments, not proof of authority; owners revalidate concrete targets.

| Guard | Owner observation | Never substitute |
| --- | --- | --- |
| ISSUE_DIGEST | Exact current Issue source bytes | Protocol or SPEC bytes |
| MANIFEST_DIGEST | Protocol admission source_sha256, exact manifest bytes | ProtocolManifest.digest (normalized semantics) or SPEC digest |
| INPUT_DIGEST | Reviewed draft preview input_sha256 | Snapshot semantics or rendered members |

All use sha256:<hex>, but each identifies a different byte source. Retain labeled
coordinates and original receipts. Reobserve after an authorized change; a stale
guard requires review, not automatic refresh-and-retry. Guard discovery is not
automated here. Never infer execution, owner, Issue or acceptance from cwd or cache.

## Issue → setup → draft → observe → publication/closeout

Inspect the original command's help before supplying inputs:

```sh
"$AWARE" issue ensure-snapshot --help
"$AWARE" issue start-progress --help
"$AWARE" issue bind-scope --help
```

ensure-snapshot is the supported content entrance, not an open command. Supply
approved title, problem, objective, acceptance, priority and genuine execution.
Admit an In Progress Issue with fresh guards and scope covering intended inputs,
manifest, package, scratch and explicitly created ancestors. Existing policy
allows exact-or-directory-prefix scope; this document is not another checker.

```sh
"$AWARE" issue resolve-read-projection --repository-root "$REPOSITORY" \
  --protocol-source "$PROTOCOL_MANIFEST" --issue-ref "$ISSUE_REF" --format summary
"$AWARE" protocol admit --repository-root "$REPOSITORY" \
  --manifest-path "$PROTOCOL_MANIFEST" --authority-mode filesystem
```

Read the original Issue guard and Protocol source_sha256. This is still explicit
bookkeeping, not an automatic authorization token or authenticated actor action.

```sh
"$AWARE" protocol setup-specification --repository-root "$REPOSITORY" \
  --manifest-path "$PROTOCOL_MANIFEST" --issue-ref "$ISSUE_REF" \
  --expected-issue-sha256 "$ISSUE_DIGEST" --expected-manifest-sha256 "$MANIFEST_DIGEST" \
  --specification-root "$SPEC_ROOT" --directory-path "$SPEC_ROOT" \
  --client-intent-id "$SETUP_INTENT"
```

Preview is default. For nested roots list every required ancestor/directory in
effect order. Explicit apply repeats the reviewed request with --apply and fresh
Issue admission. Setup creates no SPEC documents or iterations and is not a
commit. Reobserve the changed Protocol bytes before drafting.

Prepare inputs with the installed public SPEC types and canonical codec.
example-draft-input.py is an unchanged pure input example: customize approved
content within scope. It is not an authority/approval record or package writer.
The snapshot JSON is request data, not a software manifest or registry.

```sh
"$AWARE" spec create-draft --repository-root "$REPOSITORY" \
  --protocol-manifest "$PROTOCOL_MANIFEST" --spec-manifest "$SPEC_MANIFEST" \
  --snapshot-json "$SNAPSHOT_JSON" --author-ref "$AUTHOR_REF" \
  --authoring-intent-ref "$AUTHORING_INTENT_REF" --client-intent-id "$DRAFT_INTENT" \
  --issue-ref "$ISSUE_REF" --expected-issue-sha256 "$ISSUE_DIGEST" \
  --expected-manifest-sha256 "$MANIFEST_DIGEST"
```

Review preview's input_sha256, proposed effects and completion evidence. Explicit
apply repeats the complete request with --expected-input-sha256 "$INPUT_DIGEST"
and --apply. Preview does not renew write authority. Exit 0 requires verified
whole-context completion; exit 2 can retain publication or unknown cleanup.
Preserve that evidence; never automatically retry known publication or delete it.

```sh
"$AWARE" spec observe --repository-root "$REPOSITORY" \
  --protocol-manifest "$PROTOCOL_MANIFEST" --spec-manifest "$SPEC_MANIFEST"
"$AWARE" issue commit-workspace --help
"$AWARE" issue close --help
```

Dry-run exact Issue publication before apply. Retain operator_ref,
transaction_mode, reference_update, index reconciliation and observed effect
evidence; missing historical fields mean unknown. Close only with an actual
publication receipt. Draft observation is not approval or an approved iteration.
No raw Git lifecycle repair, hand-written authority or separate workflow state.

Another genuine execution resumes through fresh owner admission using durable
Issue/source records and original operation refs—not transcripts or restored
serialized capabilities. Preserve former-owner and partial-effect history.
This instruction proposal is not an unassisted U/V/R or recovery proof.
