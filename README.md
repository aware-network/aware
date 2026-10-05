# Aware

Durable, bounded work for AI agents in your existing repository.

Give an agent an approved task. Keep its Issue, ownership, scope, evidence and
commits durable when an execution ends. Aware starts with useful filesystem
protocols—not a service prerequisite or an agent's private memory.

## Available now: agent-first Issue and commit preview

An installable OSS preview supports **repository setup → scoped Issue → evidence
→ scoped Git commit → verified closeout or handoff**. The CLI and SDK delegate to
existing neutral owners. No generated API, ontology/ORM, service or Experience
runtime is installed.

```sh
git clone https://github.com/aware-network/aware.git
cd aware
python3.12 protocols/agent/install.py --python-executable /usr/bin/python3.12 \
  --venv /tmp/aware-agent-env
/tmp/aware-agent-env/bin/aware --help
/tmp/aware-agent-env/bin/aware init --repository-root /absolute/customer-repo
```

Requires Linux x86-64, Python 3.12 and an existing Git repository with committed
HEAD and configured Git author. Select your actual Python executable and a new
environment path. Installation after clone is offline and checks the exact
20-package closure. It does not need Aware's development checkout or editable imports.

- [Start an agent task: install, inputs and scope](protocols/agent/README.md)
- [Copy-and-run Issue/commit workflow](protocols/agent/quickstart.md)
- [Agent contract](protocols/agent/AGENTS.md)
- [Exact package/source inventory](protocols/agent/release.json)
- [Installed proof and limits](protocols/agent/VERIFICATION.md)

The filesystem tools check declared ownership, lifecycle, fresh record bytes
and exact publication scope; they are **not authenticated identity or a sandbox**.
Unrelated work remains preserved. Issue closeout cannot manufacture Goal acceptance.

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
- [Inspectable source and acquisition/build inputs](protocols/source/README.md)
- [Exact distribution and publication receipt](protocols/publication/receipt.json)

The preview has 13 payload distributions: seven Aware neutral packages and six
third-party packages. Source, licenses, component notices and checksums accompany
the distribution. The unchanged payload previously passed 43 Protocol and 41
Goal installed checks; see the [verification record](protocols/publication/VERIFICATION.md).

## What comes next

Supported Goal creation/import and manifest preparation are the next useful
product boundary. **They are not in this preview.** Neither are Goal approval,
effectful pursuit, dispatch or a complete autonomous collaboration loop.
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

The existing [Kernel](workspaces/aware_kernel) and
[Network](workspaces/aware_network) trees remain an earlier infrastructure
snapshot. They are **not dependencies of this preview**. Their retained
RepositoryRevision manifests describe that base snapshot, not this new
Git-published consumer overlay. The previous infrastructure introduction is
[preserved here](protocols/publication/infrastructure-readme.md).

*Aware 4 Humanity.*
