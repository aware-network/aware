# Neutral Agent CLI composition

Source preview **0.2.0a2** supplies one `aware` entrance over the accepted family
registrars and Kernel's command runtime. It is a composition library with a CLI
entrypoint, not a new Agent SDK, evaluator or authority provider.

```text
aware init --repo-root <absolute-root> [explicit creation/apply options]
aware issue <existing Issue leaf> [original arguments]
aware protocol admit [original arguments]
aware protocol setup-specification [original arguments]
aware spec observe [original arguments]
aware spec iteration-identity [original arguments]
aware spec create-draft [original arguments]
```

Run `aware --help`, then `aware FAMILY --help` or
`aware FAMILY LEAF --help`. Only the selected family is imported. Each original
registrar supplies its own flags, path meanings, digest guards and result format.
Publication is `aware issue commit-workspace`, the existing Issue SDK operation;
there is no new Repository commit implementation or automatic Issue selection.
SPEC setup previews by default; setup and draft effects require explicit apply
and fresh owner admission. Observation does not approve iterations or work.

This is a breaking successor to public a6's `aware-agent-cli 0.1.0a6`, retaining
the distribution, import namespace and executable identity while moving its
single current authoring home to this Agent library. The old public snapshot
remains historical and unchanged. **This is not an in-place a6 upgrade.**
It does not copy a6's `contract`, repository-create or template helpers. The
successor `init` delegates to the accepted Workspace and Protocol SDKs rather
than retaining a standalone Repository implementation.

## Initializer source command

This command is an unreleased source composition; installation and onboarding
acceptance require a newly pinned candidate. For an explicitly selected
qualified successor installation, the intended forms are:

```bash
# Validate prospective input and preview; the parent must already exist.
aware init --repo-root /absolute/customer --create-repository

# Explicitly create the empty repository and Issue-only initial profile.
aware init --repo-root /absolute/customer --create-repository --apply

# Bootstrap an existing Git root without changing HEAD, index or remote.
aware init --repo-root /absolute/existing --apply
```

`--repository-root` is an alias of `--repo-root`; both require the same canonical
absolute root. `--issue-root` selects the repository-relative Issue root and
defaults to `docs/issues`. The Protocol SDK prepares every missing ancestor
explicitly. `--no-agent-contract` omits the `AGENTS.md` and Issue protocol files;
the receipt discloses absent onboarding files. Existing targets refuse even
when their bytes match. There is no overwrite, profile upgrade or adoption.
`--dry-run` is explicit preview and cannot combine with `--apply`.

Exactly one genuine Codex or Claude harness session must be present. The command
does not accept a caller-built actor/admission, use a cached execution or change
provider identities. This is harness correlation, not authenticated actor-action
issuance. The SDKs enforce the actual process/execution and single-use authority.

Protocol prepares and validates all input before repository creation. Workspace
then admits and prepares the repository; only after its verified release does
Protocol obtain its fresh plan and admission. An absent-repository preview
reports `prospective_only`, not a live Protocol plan or result. Full success
requires both owners' results and completion. Git success followed by Protocol
failure exits 2 and retains Git creation and partial/unknown Protocol effects.
It never rolls back, automatically retries or restores spent authority.

JSON retains exact requests, attempts, effects, diagnostics and cleanup for each
owner. `--format summary` omits only rendered template bodies, keeping their
paths, byte digests and modes and every result/error field. It is not a new
approval or receipt authority. The initial profile is
`aware.collaboration.fs_v1`, with only Issue authority; SPEC, Goal, Feed and
Evidence remain unavailable until their separately governed configuration.
Init creates no Issue, seed commit, index staging, remote, user configuration,
Agent session or service.

Package membership comes from the existing `portable_protocols` checkout
profile, via Agent's module-owned `agent_cli` Code entry and ordinary dependency
metadata. It does not select the full Agent module/Workspace, import Agent
ontology or require its Service-facing SDK. `aware.protocol.toml` configures
customer records and authority; it does not select software packages.

Missing registrar exports refuse before operation dispatch, without another
environment, PATH discovery, raw writer or Service/FS fallback. Generic context
is not execution identity, Issue admission or authorization. The composition
does not refresh guards or retry a failed publication. Family diagnostics and
unknown/applied effect evidence remain unchanged.

Source tests and canonical capture are distinct from a qualified installed
bundle. Do not change a repository's Environment-selected operational CLI or
overlay an evaluated a6 environment based on this source preview. Installation,
source/notice clearance, customer onboarding and publication follow separately.
