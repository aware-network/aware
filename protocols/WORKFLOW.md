# Aware filesystem initializer review

Draft instructions for one installed `aware` entrance: initialize a repository,
read its protocol guidance, and begin Issue-governed work. This internal envelope
includes the exact accepted 40-package payload, selected source snapshot and
candidate-bound notice inputs. Public-content acceptance, instruction freeze,
selection and delivery remain separate; this is not a registry release or an
unassisted-onboarding claim.

## Install once

Qualified target: Linux x86-64 with `/usr/bin/python3.12`. Verify the outer
`SHA256SUMS`, then expand
`payload/aware-canonical-neutral-fs-internal-v1.tar.gz` into a fresh private
scratch directory. It expands into `aware-canonical-neutral-fs-internal-v1`.
The `internal` name identifies the retained artifact, not an authority mode.
Enter that directory and verify its `SHA256SUMS` before running the shipped
installer:

```bash
set -eu
sha256sum -c SHA256SUMS
aware_init_parent="$(mktemp -d)"
aware_init_env="$aware_init_parent/env"
test ! -e "$aware_init_env"
test ! -L "$aware_init_env"
PYTHON_BIN=/usr/bin/python3.12 /bin/sh ./install.sh "$aware_init_env"
"$aware_init_env/bin/aware" --help
```

The environment must be absent; its private parent must exist. Never overlay
a6, an older SPEC preview or a resident development environment. All supported
commands below use this same installation. The original family entrypoints
remain parity/diagnostic entrances, not three separate toolchains. Do not infer
support from other transitive executables.

The inner README's older statement that this candidate does not supply init is
superseded by these candidate-bound draft instructions. Its bytes stay unchanged
with the accepted archive and checksums. Selected source READMEs containing seed,
resident or broad-workspace recipes are source history, not customer directions.

## Required harness context

Run initialization in your actual supported agent harness. It must provide one
unambiguous, nonblank stable session identity: `CODEX_THREAD_ID` for Codex or
`CLAUDE_CODE_SESSION_ID` for Claude Code. Do not export fabricated values, copy
another execution's id or reuse an evaluator fixture id to bypass refusal.
Missing or ambiguous context refuses; installing wheels cannot create it.
Keep the same harness execution for preview and apply. A new execution uses its
own identity and must obtain fresh admission rather than replay another's plan.

These filesystem receipts identify the invoking execution; they are not a
cryptographic authentication or resident-session admission claim. Test-only
harness exports in qualification recipes are not customer setup instructions.

## Initialize explicitly

Select `aware_repo_root` as an explicit absolute target path under an existing
parent directory. For a new repository, the target must be absent or empty:

```bash
"$aware_init_env/bin/aware" init --help
"$aware_init_env/bin/aware" init --repo-root "$aware_repo_root" \
  --create-repository --format summary
```

Preview is the default and has no source effects. For a new repository, review
the Workspace preparation preview (`outcome=planned`) and the prospective
Protocol inputs separately (`status=prospective_only`). These inputs are not an
admitted Protocol plan: `completion_verified=false` and `effect=none`.
Apply obtains fresh Protocol admission after Workspace prepares the repository.
To request those effects in the same genuine execution:

```bash
"$aware_init_env/bin/aware" init --repo-root "$aware_repo_root" \
  --create-repository --apply --format json
```

For an existing Git repository, omit `--create-repository`; retain the explicit
target and preview before apply. Existing configuration/guidance refuses rather
than being overwritten. This is not a repair or migration command. Inspect
installed help for `--issue-root` and `--no-agent-contract`; do not infer a
documentation-only or resident-service startup operation.

Init composes Workspace repository preparation followed by Protocol bootstrap.
It retains both receipts, does not undo known effects if the second owner
refuses, and does not silently retry. Success requires verified completion from
both owners. Preserve error, effect, cleanup and retry fields even when a command
returns nonzero: a refusal can follow known creation. Inspect existing effects
before deciding a fresh request; never treat exit status as automatic rollback.

By default this prepares the Issue directories, an `aware.protocol.toml` binding
and `AGENTS.md` guidance. It does not create a seed commit, stage work, add a
remote, open an Issue, fabricate approval or start a service. Read the generated
guidance to understand coordination rules before choosing an operation.
Tool installation, readable guidance, repository preparation, operational
configuration and future service startup are distinct steps.

## Begin Issue-governed work

Use the installed Issue SDK commands, not handwritten lifecycle evidence:

```bash
"$aware_init_env/bin/aware" issue ensure-snapshot --help
"$aware_init_env/bin/aware" issue bind-scope --help
"$aware_init_env/bin/aware" issue start-progress --help
"$aware_init_env/bin/aware" issue publish-close --help
```

Before `ensure-snapshot`, explicitly choose the Issue reference, title, problem,
objective, acceptance and creation intent. Its owner/actor references must name
the current execution reported by init; its actor-evidence reference must point
to your retained execution evidence, not a synthetic `fixture:` coordinate.
Follow the installed help for the exact flags. Scope binding, In Progress
admission and publication are separate operations; init does not authorize them.
Preview publication with `--dry-run` before requesting it. Repository author
configuration for a local Git commit is also separate from init.

The accepted installed cases demonstrate init followed by first-Issue publication
and closeout, including foreign-work preservation. They are synthetic tooling
proofs, not evidence that a new participant can finish without guidance.
Automatic guard discovery and a fully unassisted onboarding loop remain unproved.

## SPEC and guard meanings

The same installation also exposes:

```text
aware protocol admit | setup-specification
aware spec observe | iteration-identity | create-draft
```

SPEC setup remains separately Issue-governed. Init does not configure SPEC
documents or create drafts, approved iterations, bindings or Goals. Draft input
preparation uses the supported typed tooling; do not fabricate approved records
or a package-selection JSON to fill a missing entrance.

Issue bytes, exact Protocol manifest bytes and draft input bytes have distinct
guards, even when all are spelled `sha256:<hex>`. `ProtocolManifest.digest` is
normalized semantic identity, not a manifest-byte currentness substitute.
Protocol/SPEC selection locators are repository-relative; draft snapshot paths
follow the invoking working directory, so explicit absolute input paths avoid
ambiguity. No silent guard refresh or mutation retry is supported. Runtime
currentness observes state, not every write; cooperative descriptor confinement
does not claim continuous confinement.

## Source and notices

`SOURCE-INDEX.json` binds `source/` to the original committed `portable_protocols`
capture and the unchanged wheels. It is evidence, not a second package selector.
Full producer discovery inventory stays producer-side. Customer
`aware.protocol.toml` selects records/authority, not software packages.

Keep the payload, LICENSE, NOTICE, indexes, source archives and all notice texts
together. Aware's Apache-2.0 policy does not replace upstream terms. The root
NOTICE's repository-wide reference is supplied as `source/THIRD_PARTY_NOTICES.md`.
`NOTICE-BINDINGS.json` binds current wheel/resource identities to the inherited
and additional attachments. Earlier indexes and held-input wording remain exact
history; they are not this envelope's customer authority.

Six selected Code/Workspace wheels declare Apache-2.0 metadata but have no
package-local legal attachment. Their exact absence is visible in
`aware_package_legal_inventory`; the repository LICENSE and NOTICE accompany
the whole envelope. This is carriage accounting, not acceptance of orphan-wheel
redistribution. Review the envelope's sufficiency before any public delivery;
do not detach wheels from their source/legal envelope.

The schema resources keep scoped MIT/BSD attribution and documented adaptations.
BSD-3-Clause is selected while the complete upstream file retains its alternative
AFL text without selecting it. Pathspec's MPL terms and corresponding source are
attached. Packaging's three original license documents and two license-index
Python modules are attached as detected license-path inputs, not five separate
legal obligations. Its upstream alternatives are preserved without relabelling
them Aware Apache or silently selecting one. The source-derived jsonschema recipe,
constraints and original
publisher source URL/hash are carried; its original source archive is not attached.

rpds and pydantic-core component accounts are conservative, not exact linkage or
publisher-toolchain proof. Cython is correlated to msgpack, not silently assigned
to PyYAML; LibYAML remains precautionary input from a configurable CI default.
`CONTENT-AUDIT.json` preserves unsuppressed bounded findings, including binaries
and carried source archives; it is not exhaustive disclosure or legal clearance.

This FS installation does not admit Service/API, object operations, materialization,
native receiving or Experience authority. No a6 compatibility migration layer,
public coordinate or change to aware-dev's selected operational CLI is claimed.
