# Aware for repository agents

Install once. Give an agent a customer-approved task. Keep ownership, scope,
evidence and publication durable across executions—not trapped in chat history.

This **0.1.0a2 filesystem preview** exposes existing Aware Issue and repository
owners through a thin `aware` interface. No service, generated API, ontology/ORM,
Experience runtime or Aware development environment is required.

## Install

Requires Linux x86-64, Python **3.12** with `venv`/`ensurepip`, and Git. Work in
an existing Git repository with a committed HEAD and configured author name/email.
The installer does not create a repository, configure Git, install Python or
overwrite an existing environment.

```sh
git clone --depth 1 https://github.com/aware-network/aware.git
cd aware
python3.12 protocols/agent/install.py --python-executable /usr/bin/python3.12 \
  --venv /tmp/aware-agent-env
/tmp/aware-agent-env/bin/aware --help
/tmp/aware-agent-env/bin/aware contract
```

Choose your actual Python 3.12 executable and a new environment path. After the
clone, installation is offline, verifies the pinned archive and every member,
and checks dependencies. Preserve the accompanying source and notices.
The installer prints the retained source/notice location. The exact 20-package
closure is in [release.json](release.json); it is not Aware's development closure.

## Give the agent these inputs

- Absolute customer Git root and installed command path.
- Customer-approved objective, acceptance checks and exact authored source paths.
- Its own real, stable harness execution identity—not another agent's identifier.
- [The consumer contract](AGENTS.md) and [the workflow below](quickstart.md).

Initialize the **Issue-only** profile through tooling:

```sh
/tmp/aware-agent-env/bin/aware init --repository-root /absolute/customer-repo
```

This creates `aware.protocol.toml`, versioned `AGENTS.md` and missing modular
agent/Issue/alignment docs, `.aware/agent-protocol.md` and `.aware/agent-bootstrap.json`.
It does not overwrite existing files or a customer `AGENTS.md`. To explicitly
append a managed link to an existing regular `AGENTS.md`, select
`--link-existing-agents`. Original instructions are retained; conflicts require
customer review, not automatic precedence. Inspect `preserved` and
`manual_integration_required` in the setup result. Initialization and the
three-operation `issue open` composition are not multi-file transactions.
An interrupted operation must be inspected; do not erase durable receipts and retry blindly.

The authored [contract](../contracts/README.md) is `aware.agent.fs.v1` / 1.0.0.
The public repository, shipped CLI resources and customer scaffolds are rendered
from those same templates. Contract versioning is independent of the CLI version
and record/profile version; upgrades are explicit, never ordinary bootstrap side effects.
`aware contract` observes installed template identities/hashes, not actor authority.

The useful loop is:

**Initialize → open scoped Issue → implement and verify → append evidence →
dry-run/apply scoped commit → close with the real publication receipt.**

For replacement, the owner blocks and transfers the Issue; the new execution
observes its durable state and resumes. Neither a transcript nor a cache assigns work.

## Supported boundary

`aware` and `aware-issue-cli` are the supported commands for this bundle.
`aware issue --help` lists the typed operations. `aware repository commit`
routes to the same Issue provider and Workspace publication owner; it does not
copy commit enforcement. Unsupported transitive entrypoints are not collectively
admitted interfaces. This is not a flag-compatible replacement for development `aware-cli`.

The SDK export facades have explicitly new alpha versions. Service/view,
participant, bootstrap/grammar and generated interfaces are excluded rather than
silently emulated. [Source dispositions](source-provenance.json) pin the selected
owner files; business implementation bytes are unchanged. No checkout imports,
editable dependencies or alternate domain engines are installed.

Local tooling checks **declared** ownership, lifecycle, fresh Issue bytes and
scope. It is not authenticated identity, a hostile-process sandbox, automatic
approval-policy enforcement, or permanent filesystem authorization. A process
with filesystem access can bypass the tools. Use customer permissions and review.
No service-owned target may fall back to these local files.

Goal creation/import, Goal approval, effectful pursuit, dispatch, hosted service
and ActorWorld are unavailable here. The separate [Goal reader](../docs/quickstart.md)
remains a read-only qualified-input preview; it is not required for Issue work.
Closing an Issue cannot create Goal acceptance.

## Verify and report

See [verification](VERIFICATION.md), [notice treatment](NOTICES.md) and the
[launch summary](LAUNCH.md). Report reproducible findings through
[GitHub Issues](https://github.com/aware-network/aware/issues), including the
Git revision, archive digest, command/version, Python/platform, expected and
observed result. Redact customer records, credentials and private paths.

This is an early OSS preview, not a stable API, registry release or a universal
platform installer. No external customer acceptance or reproducible-build claim
is inferred from the installed fixture proofs.
