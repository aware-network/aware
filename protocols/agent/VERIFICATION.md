# Agent filesystem preview verification

Consumer version: **0.1.0a2**, public Git preview dated 2026-10-05.
Exact archive: `distribution/aware-agent-fs-0.1.0a2-linux_x86_64-py312.tar.gz`.
SHA-256: `62085974eb99889aaf43275c7b6a635ebd6ed191513e563c812a556472c48dd6`.
[release.json](release.json) binds all 20 wheels, producer-source revision,
builder and source-disposition digest. This is a consumer Git overlay, not a
WorkspaceRevision, generated API publication or registry release.

## What ran

**161 checks passed, no skips:**

- **8 installed workflow tests:** initialize and open; implement/evidence/scoped
  publication/verified closeout; real scope refusal; former-owner refusal and
  durable replacement handoff; stale Issue-byte refusal; unrelated staged work
  preserved; forged publication receipt refusal; existing setup not overwritten.
- **15 installed bootstrap tests:** complete rendered scaffold/hash provenance;
  installed/authored template equivalence; read-only contract observation;
  existing AGENTS/docs preservation; explicit managed link with original CRLF
  retained; symlink/outside-root refusals before writes; stale/partial bootstrap
  refusal; no silent upgrade; valid links, actual admission and shell quoting.
- **7 candidate accounting tests:** wheel/source/hash agreement; all 20 packages
  reachable with applicable requirements satisfied; excluded surfaces physically
  absent; in-wheel Aware legal files; 103-component/185-file notice accounting;
  bounded absence of Aware private paths in shipped text; packaged contract bytes
  equal authored templates and root requirement/version agrees with its wheel.
- **10 retained Goal publication tests:** exact old archive/source/export hashes
  and acquisition refusal boundaries. These check the separate unchanged Goal
  preview and refreshed root README receipt, not new Goal semantics.
- **121 pinned original owner tests:** Issue SDK, provider, CLI, operational state
  machine and Workspace commit. [The manifest](owner-tests/manifest.json) pins
  each test's source bytes at `728831f6636a611a8baac61dbc258ed563a0e466`.

The final archive installed into a **fresh** Python 3.12 environment under
Bubblewrap with network disabled, the development checkout hidden, and inherited
environment cleared. All 20 payload packages resolved offline; dependency check
and CLI activation passed. Test tools were supplied separately, not added to the
consumer environment. No editable or direct-URL installed dependencies.
The eight operation proofs and 121 owner tests ran against that installation.
No runtime domain source was imported from the test directory or development checkout.

One test-runner collection attempt needed its existing test-only `conftest`
directory supplied explicitly. One archive-test attempt tried to open a generated
wheelhouse `.gitignore` as a ZIP; the harness was corrected to select `.whl`
members. Neither correction changed a domain operation or refusal rule.

The first unpublished a2 assembly mistakenly reused a registry-loop version in
its root requirement. Offline installation refused it. The builder now keeps
consumer version separate and a regression assertion pins requirement/version
to the actual CLI wheel. That failed internal archive was quarantined and is
not public; this report binds the corrected, freshly installed candidate above.

## Reproduce

After the documented installation:

```sh
/tmp/aware-agent-env/bin/python -I -B protocols/agent/test_installed_workflow.py -v
/tmp/aware-agent-env/bin/python -I -B protocols/agent/test_installed_bootstrap.py -v
/tmp/aware-agent-env/bin/python -I -B protocols/agent/test_bundle.py -v
python3.12 -B protocols/publication/test_preview.py -v
```

The operation tests create disposable Git fixtures. Raw Git is used solely to
seed fixture history and inject staged customer work; all tested agent work,
scope publication and closeout go through the installed owners.
Their fixture actor strings are **not authenticated people or genuine harness sessions**.

For the owner replay, provide pytest 9.0.2 and its dependencies in a separate
test-tools directory, then run the installed interpreter with `-I`, explicitly
adding that directory and `owner-tests/state` to the **test-only** search path.
Use `pytest.main(["protocols/agent/owner-tests", "--import-mode=importlib", "-q"])`.
The original tests are exported unchanged by `prepare_owner_tests.py`; runtime
imports must still resolve only from the selected installed environment.

## Source/build disposition

All 33 selected owner files are accounted for: **30 byte-identical files and
three curated export facades**. The facade/version/dependency changes exclude
service/view/participant and broad Workspace bootstrap interfaces. The new
agent command composes/delegates; it owns no Issue lifecycle or commit engine.
The seven new Aware wheels carry in-wheel Apache-2.0 license and scoped NOTICE.
Nine previous neutral/schema wheels and four hash-qualified publisher wheels
complete the closure. Component notices are conservative inputs, not linkage proof.

Public rebuild inputs are in [source](source) and the prior
[schema/Protocol source capsule](../source/README.md). Each new source project is
standalone Hatchling packaging; it can be built without the development checkout:
`python3.12 -m pip wheel --no-deps --wheel-dir /absolute/new-wheelhouse <project-path>`.
Supply the declared build tools separately; this is not a consumer installation step.
`build_bundle.py` is the producer's source-pinned extraction/assembly rail;
re-extracting original owner blobs requires their source repository, whereas
building the already exported public projects does not.
No cross-host reproducible-build claim is made.

## Limits

This is installed producer evidence, **not external client acceptance**. It
does not prove adversarial filesystem isolation, authenticated actor identity,
service authority, hosted approval policy, or support for arbitrary platforms.
The local owner accepts declared identity evidence under this filesystem profile.
No Goal creation, approval, effectful pursuit, dispatch or resident service is
advertised. The prior native Goal matrix does not accept this Issue bundle.
Current-epoch rejection remains unsupported in the independent Goal preview.

The bounded source/text scan found no Aware-private paths or selected credential
patterns; deliberate scanner test literals and upstream attribution are not
private provenance. This is not exhaustive privacy, authorship or legal certification.
User-delegated OSS preparation chooses the conservative notice treatment in
[NOTICES.md](NOTICES.md); source transparency and honest limits remain visible.

## Public delivery receipt

The **prior 0.1.0a1** implementation was non-force pushed to `aware-network/aware/main` at
`44bf1a9060aa760312ff3a73ab5b3a30517910d7`. An unauthenticated, revision-pinned
GitHub download returned its digest `2ab8b1f0…` (3,533,294 bytes),
and the public README leads with the installed Issue/commit workflow.
This is actual public Git delivery—not a registry release or external client evaluation.

The follow-up Git attributes preserve upstream legal CRLF/EOF bytes unchanged,
rather than reformatting hash-qualified notices to suppress whitespace findings.
No wheel or bundle bytes change with this preservation rule.

The **0.1.0a2** implementation was non-force pushed at
`7c32154df3923610cce831ca10c0574a7065c3cf`. An anonymous, revision-pinned
GitHub archive download reproduced the full SHA-256 above. A fresh shallow public
clone at that revision contained no old `workspaces`, `aware.repo.toml` or
internal publication manifests. Its exact bundle installed into another new
environment with networking disabled, development checkout hidden and inherited
environment cleared. All **161 checks passed again, zero skipped**: 40 consumer,
bootstrap, accounting and publication checks plus 121 pinned owner tests.
Test-only pytest tools remained separately supplied; no consumer dependency changed.

One replay attempt omitted the sandbox's `/dev` mount, so Git fixture setup
refused access to `/dev/null` before any tested operation ran. Supplying the
standard sandbox device mount resolved that runner error; no source or candidate
bytes changed. This is producer public-delivery replay, not independent client
acceptance, a registry release or a claim of authenticated identity/isolation.

The [a2 publication Issue](../../docs/issues/2026/10/05/fb-2026-10-05-protocols-only-versioned-agent-experience-v0.md)
records publication and closeout. The previous a1 receipt does not accept a2.
Only the agent-interface wheel changes; the other 19 wheel identities/bytes
remain equal to a1. Domain-owner source and the optional Goal distribution are
unchanged. Contract `aware.agent.fs.v1` / 1.0.0 is separately versioned.
