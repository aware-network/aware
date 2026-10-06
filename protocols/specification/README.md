# Filesystem Specification setup and read preview

Status: public-layout proposal for review; not published or selected by a6.
This separate Linux x86-64 / Python 3.12 preview configures a SPEC binding through
an approved Issue and reads independently qualified Specification packages.
It does not supply SPEC authoring/import or approved iterations. New users can
configure the root, but without a qualified package they stop after setup.

## Install separately

From this checkout, select your actual Python 3.12 executable and a new environment
under an existing parent. Never install over a6 or combine wheelhouses.

```sh
python3.12 protocols/specification/install.py \
  --python-executable /usr/bin/python3.12 --venv /tmp/aware-spec-env
/tmp/aware-spec-env/bin/aware-protocol --help
/tmp/aware-spec-env/bin/aware-spec --help
```

The wrapper verifies the exact accepted packet and its payload, retains source
and notices, then delegates to the existing offline installer. No network or
development checkout is needed after acquisition. Requires Git for customer
repositories. It changes no customer records or bootstrap. A failed installation
can leave a partial environment and retained evidence; it is not rolled back.

Supported interfaces: `aware-protocol` 0.3.0 (`admit`, `setup-specification`) and
`aware-spec` 0.2.0 (`observe`, `iteration-identity`). Other package entrypoints are
not admitted interfaces. The 26-package closure is not a combined agent client.
Use separately selected a6 `aware` for repository/Issue operations; retain its
1.2.1 bootstrap. No `aware spec` wrapper or automatic contract upgrade exists.

## Inputs and sequence

The preparer supplies an approved outcome, exact Git root, real harness execution,
an a6-owned In Progress Issue and exact manifest/Issue byte digests. Setup must own
the manifest and every requested directory. Preview defaults to no effects; apply
requires explicit review and fresh Issue admission. Preserve all refusal/effect
JSON, even after exit 2. Setup neither stages nor publishes nor closes an Issue.

Follow the [draft command sequence](packet/instructions/specification-setup-customer-sequence-v1.md)
and [draft interface addendum](packet/instructions/specification-consumer-bootstrap-addendum-v1.md)
only after explicit preparer selection. These remain drafts, not installed or
frozen AGENTS instructions. Contract 1.3.0 remains unallocated.

Setup creates only directories and `aware.protocol.toml` binding. Reading needs
exact existing manifest selections and iteration coordinates. No hand-authored
authority substitute, approval, durable Issue binding, protected SPEC publication,
Goal coordination, Service/API or Experience capability is supplied.
Currentness means observed state, not every-write detection; confinement is
cooperative, not continuous or hostile-process isolation.

## Exact software, source and notices

- [Review packet](distribution/aware-specification-fs-review-packet-v1.tar.gz),
  SHA-256 `865c57be501818dc380c9019a0fc710658d67242375a080b563258d6365a97a0`.
- [Delivery accounting](delivery.json) maps each carried packet member to this tree.
- [Neutral source snapshot](../../workspaces/previews/specification-setup-read-v1/README.md)
  preserves all 137 source/build/legal files without overwriting a6 sources.
- [Source index](packet/SOURCE-INDEX.json), [notice bindings](packet/NOTICE-BINDINGS.json),
  [installed boundaries](packet/REVIEW-BOUNDARIES.md), and [packet checksums](packet/SHA256SUMS).

The packet expands to `aware-specification-fs-review-packet-v1`; its inner payload
expands to `aware-specification-setup-read-internal-v3`. These retained names do
not imply a different semantic profile. Its original README's 'no setup CLI'
and historical nonclaims are construction evidence, explained by the attached
installed boundaries. This page supplies the current proposed entrance.

Source indices retain original supplier revisions and packet-relative paths;
delivery.json maps them to accessible paths here. The neutral snapshot is composite,
not a full workspace revision or editable install. Build recipes are inspectable
under packet/build-inputs; reproducible wheel builds are not claimed.
The preserved packet/SHA256SUMS is archive-relative: verify it after extracting
the unchanged distribution, not against this source-remapped tree. Use delivery.json
for the actual tree coordinates and their exact hashes.
Aware-authored work follows the existing Apache-2.0 policy; upstream terms stay
separate. Conservative native-component notices do not prove exact linkage or
publisher toolchain identity. Historical notice indices remain unchanged.

Exact packet notice/disclosure coverage has bounded acceptance; this new layout
and wrapper require their own review. No exhaustive secret/legal warranty is
made. Public coordinate, publication authorization and evaluation admission
remain separate. Report findings via the existing [evaluation protocol](../evaluations/README.md).
