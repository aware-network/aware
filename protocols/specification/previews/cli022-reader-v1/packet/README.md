# SPEC read-only candidate: internal source and notice review

This packet carries the exact accepted 27-package filesystem reader candidate.
It is not a public selection, instruction freeze, authoring release or upgrade
to the separately installed Aware a6 client. Do not overlay environments.

Selected interfaces: aware-protocol 0.3.1 and aware-spec 0.2.2. The reader uses
SPEC SDK 0.2.0, FS SDK adapter 0.3.0 and Protocol FS adapter 0.4.0. Package
versions, protocol record versions and customer bootstrap versions are distinct.
The selected adapter extra is protocol. governed and draft are not activated.
Dormant governed exports in attached upstream source do not admit writers.

## Inspect or install for review

Verify SHA256SUMS before use. Expand payload/specification-cli022-reader-v1.tar.gz
into a fresh private directory; its retained root is
aware-specification-cli022-reader-internal-v1. Verify that root's SHA256SUMS.
On the supported Linux x86_64 platform, change into that extracted root and use
the shipped `install.sh`, selecting Python 3.12 explicitly. Choose an absolute
new environment path under a private parent, separate from a6 and every earlier
SPEC installation. Replace the example target below with your actual new path:

```sh
set -eu
spec_review_env="/absolute/path/to/new-spec-review-venv"
test ! -e "$spec_review_env"
test ! -L "$spec_review_env"
PYTHON_BIN=/usr/bin/python3.12 sh ./install.sh "$spec_review_env"
```

Run the installer only if both target-absence checks pass; do not reuse an
existing environment. If Python 3.12 is elsewhere, set PYTHON_BIN to its verified
absolute executable path. The installer checks the 3.12 minor version, creates
the environment and installs the selected roots offline from its wheelhouse.
The shipped `consumer-lock.json` records the pinned dependency inventory; it is
not a pip requirements file. No bootstrap or customer AGENTS.md is changed here.

Supported SPEC operations are observe and iteration-identity through fresh
Protocol admission. Existing Issue-governed setup previews/applies only explicit
directories and the SPEC manifest binding. It creates no SPEC documents or
iterations. Reading requires an already qualified SPEC source: this candidate
does not provide customer document creation/import or approved iteration
authoring. Never hand-author authority records to manufacture acceptance.
No approval, durable iteration-to-Issue binding, service or Goal authority is
admitted. Refused writer syntax proves absence, not approval-policy enforcement.

## Sources and notices

source/workspaces/ contains only selected neutral source. SOURCE-INDEX.json
binds attached source to the wheels and original supplier Git coordinates.
Three SPEC packages differ from the predecessor notice packet; only two wheels
changed relative to the immediate accepted reader predecessor. Retained build
recipes are provenance, not a checkout-free or universal reproducibility claim.
Package READMEs and instructions/ include historical or wider owner capabilities;
this README and REVIEW-BOUNDARIES.md define this packet's narrower selection.

notices/ retains exact upstream texts and all in-wheel legal files. The schema
notice selects BSD-3-Clause while attaching the complete upstream alternative
license file. Binary component accounts are conservative candidate lists, not
exact linkage/toolchain attestations. Historical indexes remain historical;
NOTICE-BINDINGS.json binds reuse to this exact payload.

Inner README and historical instruction versions are not current selection
instructions. This outer packet supersedes them for review only. Currentness
means observed bytes/identity/metadata, not every-write detection or continuous
confinement. Source transparency is not permission to publish: candidate-specific
notice/disclosure review, public layout/selection and delivery remain separate.
