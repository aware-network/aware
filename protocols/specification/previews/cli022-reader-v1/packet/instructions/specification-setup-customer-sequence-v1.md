# SPEC setup customer sequence — unreleased command proposal

Status: installed-command-aligned draft for review, not current public support.
Issue: `fb/2026-10-06/protocol-specification-customer-command-v0`.

Public a6 remains Issue/repository-only. The independently accepted 26-package
archive `955e423c82e4…` ships the exact `aware-protocol` 0.3.0 setup command and
`aware-spec` 0.2.0 reader. Its bounded qualification is recorded in
[the installed report](../REVIEW-BOUNDARIES.md).
The previous `7faa6f6a46b0…` archive does not qualify the command. Neither archive
ships the `aware` agent/bootstrap client. There is no `aware spec` wrapper,
combined installer or public download route for this SPEC command yet.

Use [the draft bootstrap addendum](specification-consumer-bootstrap-addendum-v1.md)
only under explicit preparer/customer selection. Keep a6's existing 1.2.1 contract
intact; future template integration needs its own reviewed version and artifact.
Never overlay the two environments to manufacture a combined client.

## Inputs and authority

A customer supplies the exact Git repository and approved setup outcome, the
installed Issue command, the qualified Protocol/SPEC commands, and the SPEC
record root. Commands may live in explicitly identified separate environments;
none may import Aware's development checkout. Do not use an unpinned current
development CLI as a substitute. Only filesystem authority is supported.

The repository must already have a canonical `aware.protocol.toml` declaring
Issue authority and SPEC `specification_fs_v1` as unavailable, or the identical
desired SPEC authority binding. Public `aware init` creates the Issue-only
manifest through tooling; its existing repository/create intent rules still
apply. Setup does not create or overwrite the bootstrap, reconfigure another
root/profile, or migrate a foreign manifest. Preserve customer `AGENTS.md`.

Use the customer's own genuine, unambiguous harness execution. The setup
command resolves it through the owning Issue provider, not an actor flag.
Missing/ambiguous execution refuses. It is harness-observed filesystem identity,
not authenticated actor-action issuance or hostile-process confinement.

## Establish the setup Issue through the existing Issue tooling

Use an exact new Issue reference, customer-approved content and explicit scope.
For example, with `AWARE` set to the exact qualified existing Issue client:

```sh
"$AWARE" issue open --repository-root /absolute/customer-repo \
  --issue-ref fb/2026-10-06/enable-spec \
  --title 'Enable Specification records' \
  --problem 'The repository has no admitted Specification root' \
  --objective 'Configure agreements/specs without changing existing work' \
  --acceptance 'Observe the configured profile and preserve unrelated files' \
  --scope-path aware.protocol.toml \
  --scope-path agreements \
  --client-intent-id enable-spec-issue-1 \
  --actor-ref '<this genuine provider execution>' \
  --actor-evidence-ref '<actual customer execution evidence>'
```

Issue opening has its own composed effects and receipts; inspect them before
continuing. Require that exact Issue to be In Progress, owned by the invoking
execution and scoped to the manifest and all requested directory paths. Scope
uses the existing exact-or-directory-prefix policy, not a new exact-only rule.
An existing admitted Issue may be used instead; do not infer it from recency.

Observe it through the same installed Issue client:

```sh
"$AWARE" issue resolve-read-projection \
  --repository-root /absolute/customer-repo \
  --issue-ref fb/2026-10-06/enable-spec
```

Retain the returned `projection.source.digest` as `ISSUE_DIGEST` and verify the
owner/status/scope. This projection is an input observation, not the admission
that setup will obtain. Observe the manifest with the qualified Protocol command:

```sh
"$PROTOCOL" admit --repository-root /absolute/customer-repo \
  --manifest-path aware.protocol.toml
```

Require canonical filesystem admission and retain `admission.source_sha256` as
`MANIFEST_DIGEST`. Both digests must be `sha256:<hex>` and identify different
exact source bytes. The normalized semantic manifest digest is **not** a
substitute. Do not auto-refresh stale digests or manually rewrite authority.

## Preview, inspect, then explicitly apply

For a missing `agreements/specs` root, list both missing ancestors explicitly,
in parent-first order. If ancestors already exist, select the actual intended
directory effects; do not let a helper recursively create undeclared paths.
Set `PROTOCOL` to the exact newly qualified command, not public a6's `aware`.

```sh
"$PROTOCOL" setup-specification \
  --repository-root /absolute/customer-repo \
  --manifest-path aware.protocol.toml \
  --expected-manifest-sha256 "$MANIFEST_DIGEST" \
  --issue-ref fb/2026-10-06/enable-spec \
  --expected-issue-sha256 "$ISSUE_DIGEST" \
  --specification-root agreements/specs \
  --directory-path agreements \
  --directory-path agreements/specs \
  --client-intent-id enable-spec-setup-1 \
  --dry-run
```

Require `status=planned`, `effect=none`, the exact effect order and expected
preimage/postimage. After customer review, repeat the same request with `--apply`
instead of `--dry-run`. Apply obtains a **fresh** genuine Issue admission;
preview JSON never grants permission. A changed source/Issue/topology requires
fresh observation and evaluation, not blind retry. The intent id correlates
effects; it is not an authorization token or durable replay guarantee.

On completion preserve the complete JSON, including exact postimage digest,
effects, modes, durability, identities and harness authority grade. On refusal
preserve `code`, `effect`, every effect and residual scratch path. Applied or
unknown effects can exist despite exit 2. Do not label refusal success, assume
rollback, erase scratch evidence or reset unrelated work. Currentness is observed
state, not every-write detection; continuous confinement is unsupported.

## Read only independently qualified SPEC packages

Setup creates directories and the manifest binding only. It creates **no SPEC
documents or iterations**. A new customer without a qualified package stops
here; there is no supported document/approved-iteration creation or import in
this slice, and no hand-authored authority substitute is recommended.

If the customer already supplied independently qualified canonical SPEC packages
under the admitted root, select their exact manifests (and required closure)
explicitly. Set `SPEC` to the qualified installed reader; carry setup's actual
`manifest_postimage_sha256` as `POSTIMAGE_DIGEST`:

```sh
"$SPEC" observe --repository-root /absolute/customer-repo \
  --protocol-manifest aware.protocol.toml \
  --expected-manifest-sha256 "$POSTIMAGE_DIGEST" \
  --spec-manifest agreements/specs/example/aware.spec.toml
```

For an existing exact iteration, use `iteration-identity` with the same source
selection plus its actual `--iteration-ref`. Do not infer it from a folder,
draft or Issue. Reading/identity never grants Phase acceptance, Issue binding,
approval or work execution. Service/API, Goal and Experience are not prerequisites.

## Publication and completion remain separate

Use the existing Issue/Workspace publication workflow to preview/apply exact
changed source paths and retain the real publication receipt before closeout.
Setup does not stage, commit, push, close the Issue, accept a SPEC, or implement
SPEC-guarded publication. Git does not commit empty directories; do not add a
placeholder file just to manufacture a setup artifact. Document that distinction
in the setup evidence. Preserve the current public agent bootstrap until a
separately versioned consumer-contract update is accepted.

This sequence prepares customer setup and qualified-input reading, **not
self-serve SPEC authoring or SPEC-driven approved execution**. Exact command
installation has bounded acceptance; bootstrap integration, candidate-specific
notices/public presentation, external evaluation and release selection remain
independent proofs/decisions. This document is not a frozen customer brief.
