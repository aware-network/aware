# Aware unified filesystem installation review

This internal review envelope carries the accepted shared installation with
its exact neutral sources and notice inputs. Candidate-specific notice and
public-content acceptance, public layout, instruction freeze, selection and
delivery remain separate. This is not a registry release.

## Install once for technical review

Target: Linux x86-64 / Python 3.12. Create a private scratch directory with
`mktemp -d` and verify this envelope's SHA256SUMS. Expand
payload/aware-canonical-neutral-fs-internal-v1.tar.gz into that scratch directory.
It expands into aware-canonical-neutral-fs-internal-v1; `internal` identifies
the retained candidate, not an additional authority mode. Enter that directory,
verify its SHA256SUMS and run the shipped installer:

```bash
set -eu
spec_review_parent="$(mktemp -d)"
spec_review_env="$spec_review_parent/env"
test ! -e "$spec_review_env"
test ! -L "$spec_review_env"
PYTHON_BIN=/usr/bin/python3.12 /bin/sh ./install.sh "$spec_review_env"
"$spec_review_env/bin/aware" --help
```

Use a fresh installation. Do not overlay a6 or an older SPEC environment.
All operations below use this same installation:

```text
aware issue <existing leaf>
aware protocol admit | setup-specification
aware spec observe | iteration-identity | create-draft
```

Inspect installed `--help` for exact arguments. The original aware-issue-cli,
aware-protocol and aware-spec commands remain parity/diagnostic entrances in
this same environment, not additional toolchains. No transitive entrypoint is
automatically supported. Kernel owns command execution; Agent's neutral CLI
library composes the original registrars, SDKs and filesystem providers.

## Prepared inputs and authority

This candidate does not provide `aware init` or repository creation. Bring an
existing Git repository and tooling-managed Issue authority, an admitted
aware.protocol.toml configuration, exact target paths and authored inputs.
Do not fabricate lifecycle or approval evidence to fill an onboarding gap.
Automatic initialization and guard discovery remain unfinished; this envelope
does not establish unassisted self-service onboarding.

Issue, exact Protocol manifest bytes, SPEC source closure and draft inputs have
separate guards even when all use sha256:<hex>. ProtocolManifest.digest describes
normalized semantics and cannot replace the manifest-byte guard. SPEC selection
locators are repository-relative; draft snapshot paths follow the invoking
working directory, so explicit absolute input paths avoid ambiguity. Apply must
revalidate original guards, never silently refresh or retry a known publication.

Preview is non-authorizing. Issue publication/closeout, governed SPEC setup and
draft preview/apply/read reuse their original owners. Approval, approved-iteration
authoring, Goal operations, Service/API and Experience authority are unavailable.
Retain applied/unknown effects, cleanup and index reconciliation evidence.
Observed-state currentness is not every-write detection; cooperative descriptor
confinement is not continuous confinement. No a6 compatibility migration layer
is required for this breaking pre-distribution foundation. Historical a6 bytes
and this repository's selected operational command are not changed by installing.

## Source and notices

SOURCE-INDEX.json binds `source/` to the original portable_protocols capture and
committed neutral bytes, not a new software catalog. Customer aware.protocol.toml
selects record/authority bindings, not packages. Full producer discovery inventory
is not included. Some selected README/assets describe historical resident, seed
or broad-workspace behavior; they are source history, not consumer instructions.
Use this draft entrance and the shipped installer, not historical `uv sync` or
seed/resident examples. No public coordinate is claimed for this new envelope yet.

Preserve LICENSE, NOTICE, notices, source archives and indexes with the payload.
Aware Apache-2.0 does not replace upstream terms. NOTICE-BINDINGS.json correlates
all current wheels/resources with their original notices. The older packet indexes
and new-dependency draft are historical: current bindings supersede their old
candidate coordinates and unresolved-input wording without rewriting those bytes.
Root NOTICE's repository-wide reference is carried as source/THIRD_PARTY_NOTICES.md.

The 20 schema resources retain scoped MIT/BSD attribution and documented
adaptations. BSD-3-Clause is selected; the complete upstream file also retains
its alternative AFL text without electing it. Pathspec's MPL-2.0 terms and
corresponding source are attached. Source-derived jsonschema keeps its distinct
version, modification notice, recipe, constraints and original source URL/hash;
the original source archive is not attached. This is not a reproducible-build claim.

The rpds and pydantic-core crate accounts are conservative notice coverage, not
exact binary linkage or publisher-toolchain proof. Cython input is correlated
to msgpack, not PyYAML. LibYAML input remains precautionary from configurable CI.
CONTENT-AUDIT.json preserves unsuppressed bounded findings, including binaries;
it is not exhaustive secret detection, authorship certification or legal clearance.
