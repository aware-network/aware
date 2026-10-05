# Agent filesystem preview verification

Consumer version: **0.1.0a1**, public Git preview dated 2026-10-05.
Exact archive: `distribution/aware-agent-fs-linux_x86_64-py312.tar.gz`.
SHA-256: `2ab8b1f087a6d2e2b4991a81b831fbd2374fa07cc17b58a251fc9c615230dc9e`.
[release.json](release.json) binds all 20 wheels, producer-source revision,
builder and source-disposition digest. This is a consumer Git overlay, not a
WorkspaceRevision, generated API publication or registry release.

## What ran

**145 checks passed, no skips:**

- **8 installed workflow tests:** initialize and open; implement/evidence/scoped
  publication/verified closeout; real scope refusal; former-owner refusal and
  durable replacement handoff; stale Issue-byte refusal; unrelated staged work
  preserved; forged publication receipt refusal; existing setup not overwritten.
- **6 candidate accounting tests:** wheel/source/hash agreement; all 20 packages
  reachable with applicable requirements satisfied; excluded surfaces physically
  absent; in-wheel Aware legal files; 103-component/185-file notice accounting;
  bounded absence of Aware private paths in shipped text.
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

## Reproduce

After the documented installation:

```sh
/tmp/aware-agent-env/bin/python -I -B protocols/agent/test_installed_workflow.py -v
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
