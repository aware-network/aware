# Prepared-repository workflow — draft instructions

Use all three command paths from the same fresh canonical environment described
in README.md. Require a customer-approved outcome, exact prepared Git root and
existing admitted Protocol profile. No supported repository/profile initializer
is supplied here. This is not an instruction to fabricate a Goal or approval.

## Coordinates and guards

Use an absolute repository root. Protocol manifest paths are relative to that
root or absolute. SPEC manifest paths are canonical repository-relative paths,
not relative to the Protocol manifest. Use an absolute snapshot-input path to
avoid invocation-directory ambiguity. The create-draft help explains each base.

All guard values use sha256:<hex>, but identify different exact bytes:

| Guard | Obtain from | Not interchangeable with |
| --- | --- | --- |
| Issue source | Fresh Issue owner observation | Protocol or SPEC manifest |
| Protocol source | Fresh Protocol admission source_sha256 | Normalized semantic digest or aware.spec.toml |
| Snapshot input | Reviewed draft preview input_sha256 | Snapshot semantic digest or rendered members |

Reobserve after each authorized change. Do not invent current values, refresh
stale guards automatically or replace a refused request's intent secretly.

## Issue and repository operations

Inspect aware-issue-cli ensure-snapshot --help: it accepts explicit title,
priority, problem, objective and acceptance content, plus genuine execution
context. It is the supported snapshot entrance—not an open command. Then use
start-progress and bind-scope with fresh Issue guards. Scope must cover inputs,
manifest, target package, scratch and every explicitly created ancestor.
Actor/evidence references retain the filesystem provider's actual grading;
caller strings do not become authenticated actions.

```sh
"$ISSUE" resolve-read-projection --repository-root "$REPOSITORY" \
  --protocol-source "$PROTOCOL_MANIFEST" --issue-ref "$ISSUE_REF" --format summary
"$PROTOCOL" admit --repository-root "$REPOSITORY" \
  --manifest-path "$PROTOCOL_MANIFEST" --authority-mode filesystem
```

Use the owner's returned Issue bytes/guard and Protocol source_sha256 for the
next exact operation. Default JSON retains full evidence; summary does not
authorize anything. Inspect commit-workspace --help, dry-run exact publication
before apply, retain transaction/CAS/index-reconciliation evidence, and close
the Issue only using its actual publication receipt. Refusal can retain effects.
No raw Git lifecycle shortcut or independent Markdown mutation engine.

## Configure SPEC, create a draft, observe

The existing setup command requires exact current Issue and Protocol guards.
List required directories/ancestors explicitly in effect order. Preview is
default; add --apply only after reviewing the same intended effects.

```sh
"$PROTOCOL" setup-specification --repository-root "$REPOSITORY" \
  --manifest-path "$PROTOCOL_MANIFEST" --issue-ref "$ISSUE_REF" \
  --expected-issue-sha256 "$ISSUE_DIGEST" --expected-manifest-sha256 "$MANIFEST_DIGEST" \
  --specification-root "$SPEC_ROOT" --directory-path "$SPEC_ROOT" \
  --client-intent-id "$SETUP_INTENT"
```

For nested roots add each required --directory-path explicitly. Setup creates
no document or iteration and is not a repository commit. Reobserve its changed
Protocol manifest before drafting. Prepare terms using installed public types
and the canonical codec; example-draft-input.py is the byte-pinned historical
pure input example, not approval, admission or a package writer. Save customized
inputs only within admitted scope; JSON request bytes are not a package registry.

```sh
"$SPEC" create-draft --repository-root "$REPOSITORY" \
  --protocol-manifest "$PROTOCOL_MANIFEST" --spec-manifest "$SPEC_MANIFEST" \
  --snapshot-json "$SNAPSHOT_JSON" --author-ref "$AUTHOR_REF" \
  --authoring-intent-ref "$AUTHORING_INTENT_REF" --client-intent-id "$DRAFT_INTENT" \
  --issue-ref "$ISSUE_REF" --expected-issue-sha256 "$ISSUE_DIGEST" \
  --expected-manifest-sha256 "$MANIFEST_DIGEST"
```

Inspect preview's input_sha256, proposed paths/effects and completion evidence.
Repeat the complete reviewed request with --expected-input-sha256 "$INPUT_DIGEST"
and --apply only with explicit authorization and fresh admission. This is not
a reusable permit. Exit 0 requires verified whole-context completion; late exit
2 can preserve a published package, unknown effects or cleanup evidence.
Never automatically retry known publication or delete its retained evidence.

```sh
"$SPEC" observe --repository-root "$REPOSITORY" \
  --protocol-manifest "$PROTOCOL_MANIFEST" --spec-manifest "$SPEC_MANIFEST"
```

Publish exact scoped changes and close/handoff through Issue separately. Draft
observation does not approve a SPEC or create an approved iteration. Preserve
original result/refusal evidence and durable coordinates for another execution.
This layout check is not a customer U/V/R run or proof of unassisted onboarding.
