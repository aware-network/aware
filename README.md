# Aware

Durable, bounded work for AI agents in your repository.

Aware's direction: Don't watch your agents. Watch your goals. → [https://aware.run](https://aware.run)

Give an agent an approved task. Keep its Issue, ownership, scope, evidence and
commits durable when an execution ends. Aware starts with useful filesystem
protocols—not a service prerequisite or an agent's private memory.

## Available now: agent-first Issue and commit preview

The **0.1.0a6** installable OSS preview supports **repository setup → scoped Issue → evidence
→ scoped Git commit → verified closeout or handoff**. The CLI and SDK delegate to
existing neutral owners. No generated API, ontology/ORM, service or Experience
runtime is installed.

New Issues take explicit approved problem, objective and acceptance inputs—no
placeholder authoring step. Optional `--format summary` makes receipts easier
to read while preserving publication state and reconciliation warnings; full
SDK JSON remains the default. Criteria start unchecked; verification is retained
as evidence, not manufactured acceptance. Issue closure is not Goal acceptance.
a6 corrects contract labels and clarifies evidence; the same domain owners and
22-package closure remain in use.

```sh
git clone --depth 1 https://github.com/aware-network/aware.git
cd aware
python3.12 protocols/agent/install.py --python-executable /usr/bin/python3.12 \
  --venv /tmp/aware-agent-env
/tmp/aware-agent-env/bin/aware --help
/tmp/aware-agent-env/bin/aware contract
/tmp/aware-agent-env/bin/aware init --repository-root /absolute/customer-repo
# For an explicitly approved EMPTY new target instead:
/tmp/aware-agent-env/bin/aware init --repository-root /absolute/new-project --create-repository
```

Requires Linux x86-64, Python 3.12 and Git. Existing exact Git roots, including
unborn branches, are supported. New targets require explicit creation intent,
an empty target and an existing parent. Publication requires your configured
Git author; Aware never invents one. Select your actual Python executable and a new
environment path. Installation after clone is offline and checks the exact
22-package closure. It does not need Aware's development checkout or editable imports.

- [Start an agent task: install, inputs and scope](protocols/agent/README.md)
- [Copy-and-run Issue/commit workflow](protocols/agent/quickstart.md)
- [Agent contract](protocols/agent/AGENTS.md)
- [Exact package/source inventory](protocols/agent/release.json)
- [Installed proof and limits](protocols/agent/VERIFICATION.md)

The filesystem tools check declared ownership, lifecycle, fresh record bytes
and exact publication scope; they are **not authenticated identity or a sandbox**.
Unrelated work remains preserved. Successful publication can still report pending
index reconciliation; it is not a clean-checkout claim. Missing historical result
fields mean unknown, not clean. No automatic interrupted-unborn recovery is
supported. See the workflow for handling this evidence without raw Git repair.
Issue closeout cannot manufacture Goal acceptance.

Setup creates a versioned `AGENTS.md`, modular agent/Issue/alignment docs,
`aware.protocol.toml` and bootstrap provenance when those paths are absent.
Existing customer files are preserved. Use `aware init --link-existing-agents`
only when explicitly approving an appended contract link; inspect reported
manual-integration requirements. No silent contract upgrade or overwritten instructions.
See [the authored contract and version policy](protocols/contracts/README.md).
Repository preparation creates no seed commit, remote or push. The first real
commit follows ordinary Issue scope and the existing publication owner.
See [external agent evaluation instructions](protocols/evaluations/README.md);
installation-only feedback is welcome, without invented Goal or workflow results.

## Available now: filesystem Goal reader preview

An installable, open-source **read-only preview** can discover a committed
Goal's request coordinates, observe Phase eligibility, and produce and verify
direction receipts. It uses the same neutral Goal semantics as Aware's internal
operations, through an explicitly admitted filesystem/Git provider.

```sh
python3.12 protocols/install.py --python-executable /usr/bin/python3.12 \
  --venv /tmp/aware-goal-preview-env
python3.12 protocols/demo.py --cli /tmp/aware-goal-preview-env/bin/aware-goal-native
```

Select your actual Python 3.12 executable and a **new** environment path.
The wheel bundle targets Linux x86-64; installation needs no network, Aware
development checkout, editable imports, services or ontology runtime.
The demo reads a committed **synthetic fixture**; it does not create a customer
Goal or grant an agent permission to work.

- [Install and use the reader](protocols/docs/quickstart.md)
- [Agent consumption contract](protocols/AGENTS.md)
- [Operational model and version mapping](protocols/docs/model.md)
- [Supported capabilities and limits](protocols/docs/capabilities.md)
- [Neutral source workspaces and acquisition/build inputs](workspaces/README.md)
- [Exact distribution and publication receipt](protocols/publication/receipt.json)

The preview has 13 payload distributions: seven Aware neutral packages and six
third-party packages. Source, licenses, component notices and checksums accompany
the distribution. The unchanged payload previously passed 43 Protocol and 41
Goal installed checks; see the [verification record](protocols/publication/VERIFICATION.md).

## Available now: filesystem Specification setup and read preview

A separate, Git-distributed SPEC preview provides Issue-governed manifest/directory
setup and strict reading of independently qualified existing documents. Install
its 27-package closure in a separate Linux x86-64 / Python 3.12 environment:

```sh
python3.12 protocols/specification/previews/cli022-reader-v1/install.py \
  --python-executable /usr/bin/python3.12 --venv /tmp/aware-spec-env
/tmp/aware-spec-env/bin/aware-protocol --help
/tmp/aware-spec-env/bin/aware-spec --help
```

See the [preview entrance](protocols/specification/README.md) for explicit inputs,
exact software/source/notices and capability limits. This is not an a6 upgrade:
do not overlay installations. SPEC authoring/import and approved iterations are
unavailable; without qualified documents, a new customer stops after setup.
The selected CLIs are aware-protocol 0.3.1 and aware-spec 0.2.2, with SPEC SDK
0.2.0 and filesystem SDK adapter 0.3.0. Admit dispatch
uses the existing neutral command runtime; SDK/provider/domain decisions retain
their owners. The [delivery record](protocols/specification/previews/cli022-reader-v1/PUBLICATION.md)
binds the exact software and receipts. The predecessor remains available through
its explicitly versioned entrance. Historical command sequences remain drafts;
contract 1.3.0 is unallocated. Publication is not a registry release or an a6 upgrade.

## Retained SPEC reader predecessors

The [Protocol 0.3.1 / SPEC 0.2.0 entrance](protocols/specification/previews/admit-runtime-v1/README.md)
and original setup/read preview remain available with their exact artifacts and
publication receipts. The CLI022 [historical local selection](protocols/specification/previews/cli022-reader-v1/SELECTION.md)
records adoption without upgrading a6 or authorizing SPEC writers. Use fresh,
separate installations; never overlay or silently switch an execution's command.

## Available now: governed SPEC draft preview

The reviewed **aware-spec 0.4.1** draft composition is the selected standalone
Git draft preview in a separate 26-package installation. Local selection has
independent acceptance; authorized delivery and acquisition receipts are in the
[publication record](protocols/specification/previews/cli041-draft-v1/PUBLICATION.md).
It supports Issue-governed draft creation and
reading, not SPEC approval or approved iterations. See the
[separate entrance](protocols/specification/previews/cli041-draft-v1/README.md)
and [historical local selection](protocols/specification/previews/cli041-draft-v1/SELECTION.md).
a6 remains the Issue/repository client; CLI022 remains the separately installed
setup/read preview. Never overlay environments or silently replace task commands.

## Available now: canonical filesystem collaboration preview

The selected Git preview combines the accepted operations for prepared inputs:
Issue/repository, SPEC setup and governed drafting/reading through three existing
family commands in one 31-package environment. See the
[consumer entrance](protocols/collaboration/previews/canonical-fs-v1/README.md) and
[delivery record](protocols/collaboration/previews/canonical-fs-v1/PUBLICATION.md).
Independent local selection review is accepted. This is not a
unified aware command or a repository/profile initializer. a6, existing SPEC
previews and the repository bootstrap stay unchanged; instructions remain draft.

## Locally selected unified filesystem collaboration preview

The reviewed successor is **selected locally; not publicly delivered**. One
fresh 32-package installation exposes `aware issue`, `aware protocol` and
`aware spec` through the existing SDK registrars and domain owners. See the
[prepared-input entrance](protocols/collaboration/previews/canonical-agent-fs-v1/README.md)
and [local selection record](protocols/collaboration/previews/canonical-agent-fs-v1/SELECTION.md).
Initialization and automatic guard discovery remain unavailable; instructions
remain draft. Existing published previews and the repository's a6 bootstrap
are unchanged. Do not overlay installations or silently switch retained commands.

## What comes next

Our delivery direction is **Issues → Specifications → Goals → shared map**.

Issues and scoped commits are available now; SPEC setup/read is available as the
separate preview above. Governed SPEC draft creation and reading are provided
by the distinct draft installation; command sequences remain unfrozen previews.
Approved-iteration authoring remains a separate capability cut. Supported Goal
creation/import and manifest preparation follow as separate
capability cuts, then the shared map. **These future capabilities are not in this
preview.** The separate Goal reader above remains read-only.
Goal approval, effectful pursuit, dispatch and a complete autonomous
collaboration loop remain unavailable.
Issue lifecycle and scoped publication are available separately in the agent
bundle above. Do not manually patch Goal records to bypass these gaps.

Filesystem authority is useful independently. Service/API authority can later
own selected targets, with their files becoming projections. Skills, SDKs,
CLI and Experiences compose the same operations; an interface does not create
another authority. Apps and ActorWorld build on that collaboration model, not
on an alternate implementation of it.

## Source and contribution

Aware-authored code is Apache-2.0; third-party content retains its own terms.
See [LICENSE](LICENSE), [NOTICE](NOTICE) and the legal attachments inside the
distribution. This is an early preview, not a stable API or a registry release.
Report reproducible installation and usage findings through
[GitHub Issues](https://github.com/aware-network/aware/issues), without secrets
or private customer records.

`protocols/` owns consumer profiles, workflow contracts, installation, evaluations
and distribution evidence. `workspaces/` contains only the reviewed neutral
source required by those products, organized by domain ownership—not the full
development monorepo, generated ontology/API outputs or service implementations.
See the [exact source allowlist](protocols/publication/source-layout.json).
Old Kernel/Network snapshots and `aware.repo.toml` remain retired; Git history
is unchanged. The repository itself uses the consumer
Issue profile in `aware.protocol.toml`, not an internal RepositoryRevision manifest.
Agents contributing here follow the same [versioned bootstrap](AGENTS.md) and
[modular procedures](docs/agents/README.md) that customer setup installs.

*Aware 4 Humanity.*
