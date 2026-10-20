# Candidate instructions for adopting an existing repository

Agent **0.2.0a16**, with Issue CLI **0.8.4**, instructions are frozen locally pending independent review;
public delivery is not yet authorized. Use this reviewed checkout and its
whole-envelope installer, not a predecessor's acquisition path. Issue-first
useful work and optional SPEC stay independent; optional fresh Project/Goal
creates direction, not work authority. Byte pins grant no operation or retry
authority. The delivered a15 predecessor remains historical at
`5af88a6b95b928811022e5cd0255e4bb5c77bd87`. Both reviews and original guards remain.

Keep your repository layout and existing agent guidance. Aware binds Issue
records through `aware.protocol.toml`; `docs/issues` is a default, not a required
folder. This locally selected Agent 0.2.0a16 candidate retains Issue CLI 0.8.4.
Use this reviewed checkout's complete source/notice envelope, not the predecessor
installation at `b3c19b5d03229a795e8539c94f7c1cfdcc3d90d5`.
These instructions are a review candidate, not a published or unassisted
customer-adoption acceptance. The installed proof uses disposable repositories.

## Inspect and choose before initialization

Choose the actual existing Git repository, approved work and record root.
Read its instructions and record HEAD, branch, remotes, existing test results,
file modes, staged changes and unrelated untracked work. Do not clean, reset,
move or commit unrelated files to make adoption easier. Initialize neither the
downloaded Aware source nor an unapproved customer checkout.

Use one genuine harness execution identity. Missing or ambiguous identity means
stop before mutation. Set `AWARE` to the provenance-verified installed command;
do not use a contributor launcher, another environment or source overlay.
Confirm leaf inputs with installed help. Consumer Issue creation uses
`ensure-snapshot`, then explicit scope and progress operations; it is not the
contributor `issue open` workflow.

`aware.protocol.toml` binds protocol layout/profile. `aware.repo.toml` is separate
repository metadata and is not required for Issue-first adoption. Project and
Goal records are optional direction context, not filesystem configuration or
permission to write. No Project, Goal, SPEC or service is required here.

## Reuse an existing compatible configuration

If `aware.protocol.toml` exists, inspect it before choosing any initialization.
Use the original read-only admission entrance:

```bash
"$AWARE" protocol admit --repository-root "$aware_repo_root" \
  --manifest-path aware.protocol.toml
```

Require a compatible fs_v1 Issue binding and inspect its configured root and
template. Use that existing root; an `--issue-root` argument to init is not a
migration command. This workflow does not qualify arbitrary profiles or a
generic TOML merge. On incompatible configuration, retain the refusal and stop
for an explicit supported configuration decision. Do not delete the manifest,
reinitialize elsewhere, rewrite it by hand or change profile strings to bypass
the original owner.

## Add missing configuration without replacing guidance

Only use the following branch when no manifest exists. The example chooses
`coordination/issues` and preserves an existing `AGENTS.md`:

```bash
: "${aware_repo_root:?Set the approved absolute existing Git repository}"
adoption_issue_root='coordination/issues'
test ! -e "$aware_repo_root/aware.protocol.toml"
"$AWARE" init --repo-root "$aware_repo_root" \
  --issue-root "$adoption_issue_root" --no-agent-contract --format summary
```

Review both owner receipts and the proposed paths. **Review stop:** init supplies
configuration, not an Issue, approved scope or permission for later work.
Do not pass `--create-repository` when adopting an existing repository.

`--no-agent-contract` skips **both** `AGENTS.md` and the Issue-root `PROTOCOL.md`.
It does not merge guidance or install a pointer in the existing instructions.
Read the public consumer protocols explicitly. Any later in-repository pointer
edit needs customer approval and its own admitted scope. Without this opt-out,
an existing guidance-file collision refuses rather than overwriting that file.

After reviewing and explicitly authorizing the missing configuration:

```bash
"$AWARE" init --repo-root "$aware_repo_root" \
  --issue-root "$adoption_issue_root" --no-agent-contract --apply --format summary
```

Keep stdout and stderr: summary and full receipts are returned in the same
invocation. Verify the manifest's Issue root, existing guidance, staged index,
HEAD/branch, remotes and unrelated bytes/modes. Stop on non-success; known
effects and uncertainty are not rollback or retry authority.

Without existing guidance, default init may provision both onboarding files.
That is a different explicit choice; it still never overwrites an existing file.
The bootstrap manifest name and dated Issue template are fixed. Custom roots
do not mean arbitrary filenames or record formats.

## Admit useful work under the configured root

Follow the exact shipped
[first Issue guide](https://github.com/aware-network/aware/blob/b3c19b5d03229a795e8539c94f7c1cfdcc3d90d5/protocols/issues/FIRST-ISSUE.md),
substituting your approved task and configured record root, not its example
`docs/issues` path. Keep `fb/YYYY-MM-DD/<slug>` separate from the Markdown path.
After `ensure-snapshot`, obtain the actual record coordinate from
`resolve-read-projection`; do not guess the date/path or borrow an earlier guard.

Bind the exact approved paths, including the observed Issue record and any
configuration intended for first publication. Preserve unrelated staged and
untracked work. Make a fresh explicit observation for each planned lifecycle
transition. `bind-scope` and `start-progress` accept the complete original
observation through `--issue-observation-from-stdin`; do not extract/copy a
digest when using that input. Target, Issue reference and actor stay explicit.

Implement the approved task using the repository's normal tools and tests.
Existing tests may have pre-existing failures; retain and distinguish them.
Do not turn this configuration procedure into an application-correctness claim.

## Configure an optional Specification root separately

SPEC is not required for adoption. If needed, admit its exact configuration and
directory effects to the Issue, then use `protocol setup-specification` with
explicit `--specification-root`, required root/ancestor `--directory-path`
arguments, and the separately observed manifest and Issue-byte guards.
Preview, review and explicitly apply the same request without refreshing guards.

This finite operation enables an unavailable SPEC binding; it is not a general
configuration merger or root migration. An already configured different binding
refuses unsupported reconfiguration. Preserve it and stop. A specification
manifest still belongs at `<configured-root>/<spec-key>/aware.spec.toml`;
configuration and directory setup do not create a draft or approve it.

## Review local publication and closeout

Select customer-approved Git author/committer attribution before publication;
do not change global Git configuration or inject test identities. Git attribution
is metadata, not Issue authority. See the shipped
[useful task publication sequence](https://github.com/aware-network/aware/blob/b3c19b5d03229a795e8539c94f7c1cfdcc3d90d5/protocols/issues/FIRST-ISSUE.md#preview-exact-publication-and-review-it).
Only explicitly approved implementation paths belong in the request.

`issue publish-close` accepts original observation input through stdin. Retain
the exact observation and request for its separate dry-run and apply decisions.
**Review stop:** inspect code/tests, selected paths and unrelated work before
apply. The same observation is not a frozen previewed HEAD/source snapshot;
apply plans afresh. If reviewed inputs change, stop for observation and a new
decision, not silent guard refresh.

Implementation publication and closeout are two non-atomic effects. On partial
failure, retain both original receipts and do not replay the pair. Verify the
actual Issue status, publication coordinates, staging and foreign bytes/modes.
Do not claim a clean tree merely because unrelated files remain intentionally
untracked. Resource closes do not complete a ledger or resolve historical
unknowns. Remote push, external evaluation transfer and Project/Goal elevation
require separate authorization.
