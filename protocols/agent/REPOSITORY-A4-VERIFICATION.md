# a4 candidate proof — consumer promotion held

Source coordinate: `cb8c93594783cfdd56f392b6e65aea0d9f07ced0` in
`aware-network/aware`, currently a local commit, not yet pushed.
This follows independently accepted source adoption `e34a662ac4eb`.

## Exact candidate

Archive: `distribution/aware-agent-fs-0.1.0a4-linux_x86_64-py312.tar.gz`.
SHA-256: `52109f772692071681570e59a161ced33ac6606ff2effdff4fa2094cd4c58cbe`.

- [Candidate release manifest](release-a4-candidate.json), SHA-256
  `a3e57d5e430cbc37194b9a16a264961e07e17781493703e8fd4ca5b44415a6c0`.
- [Source/owner binding](repository-a4-candidate-binding.json), SHA-256
  `7e09caaac0b2a0d0439dc9e3f6e2e8f2308091f04a19c29b55e8c656cfd5cdd0`.
- Active builder SHA-256
  `0a7eacd4752dad4c1bac06c0e20ac6256283ed7b1aaeaff7e2a8e004a11119cb`.

395 archive members, all 394 checksums verified, 22 reachable wheels and clean
installed dependency checks. Seventeen wheel files remain byte-identical to
a3. Five have the declared new public versions. The three domain owner files
match accepted internal committed bytes; no second engine is introduced.
Agent contract remains 1.1.0. No generated Service/API/DTO, ontology/ORM or
Experience surface is introduced.

At this candidate checkpoint, `release.json` and the ordinary installer selected
a3. The candidate record is deliberately separate. README/quickstart did not
yet advertise a4. Subsequent [reviewed local promotion](A4-CONSUMER-PROMOTION.md)
selects these same accepted archive bytes without rebuilding. Historical
a3 archive, builder and receipts remain unchanged.

## Executed proof

Fresh Python 3.12 installation under Bubblewrap: networking disabled, environment
cleared, development checkouts and candidate source/workspaces/.git hidden,
private temporary directory, no inherited PYTHONPATH or editable/direct-URL
product installations. The installed CLI reports `aware-agent-cli 0.1.0a4`.

**161 installed tests passed, zero skipped**:

- 40 installed bootstrap/setup/workflow/repair cases. Includes absent/empty
  initial index, clean first commit and closeout, foreign staging preservation,
  exact installed owner bytes, and successful publication with explicit pending
  reconciliation under owned staging conflict or foreign native index lock.
- 121 retained owner baseline tests, supplied separately. Pytest tooling was
  separately mounted and added to the test runner only, not the product closure.

Retained JUnit SHA-256:
`01da80189842017cd9b8828e5c7406c599019757c8cfdb01f5c61adf8a15a0e3`.
Producer receipt is retained outside the distribution; independent replay should
generate its own result rather than depend on the producer's private path.

**18 source/accounting tests passed**: eight bundle and ten source-layout tests.
The overwrite-refusal test now exercises the existing immutable a4 archive,
not its earlier source-preparation branch. Tests confirm source/wheel bindings,
dependency closure, contract assets, legal-file presence and bounded privacy/
excluded-surface accounting. These observations do not establish comprehensive
rights/disclosure clearance or reproducible builds.

## Replay without changing the default release

Copy the pinned public source coordinate into a disposable replay directory.
Verify the archive and both candidate-record hashes. For the unchanged installer
in that disposable directory only, supply the exact candidate-manifest bytes
as `release.json`; do not edit the public checkout's selected release record.
Use a new explicit Python 3.12 venv target under the isolation described above.
Run `protocols/agent/test_bundle.py` against the disposable candidate manifest,
and `protocols/publication/test_source_layout.py` with the new archive present.

For installed tests, supply separately:

- `AWARE_REPAIR_TEST_SUPPORT`: the pinned `protocols/agent` test-support directory;
- `AWARE_REPAIR_BINDING`: exact `repository-a4-candidate-binding.json`;
- a separate pytest 9.0.2 tool directory, with no Aware packages.

Run installed Python with `-I`; add only the pytest tool directory to its test
runner, then run pytest on `owner-tests`, `test_installed_bootstrap.py`,
`test_installed_repository_setup.py`, `test_installed_workflow.py` and
`test_installed_repository_repair.py`. Use normal pytest import mode: the retained
state suite imports its adjacent `conftest`; an initial importlib-mode attempt
failed collection and is not counted as passing proof. No product source
directory is added to imports.

## Intermediate observations and limits

An earlier scratch archive `c4706a3e…` is unselected: the builder dropped the
top-level adoption record, causing one source inventory failure. The builder
correction at `cb8c935…` preserves that record without changing domain bytes.
This final archive was rebuilt and tested afterward.

One overlapping verification attempt read the scratch a3 release manifest
before final builder completion and installed a3. It is excluded entirely.
Final proof explicitly checked a4 and used a separate fresh installation.

Independent exact-candidate review and candidate-specific public contents/
instructions acceptance remain pending. This does not establish full SDK
unification, live resident acceptance, interrupted-unborn debt recovery,
external evaluation or a remotely accessible source publication. No push or
consumer promotion is authorized by this technical packet.
