# Issue083 customer instruction freeze

Instructions are frozen locally, pending independent review. Public delivery is
not authorized. The [instruction record](INSTRUCTIONS.json) binds twelve exact
guidance/example files, including the first-Issue reference and guarded admission
example. It does not select software, admit operations or freeze historical source
READMEs. Workspace's `portable_protocols` remains the sole package selector.

Baseline: selection closeout `5d35a566b0d7e565e3c7b33cb7e6d5632ffdcee8`.
The ten-path cut changes six existing status/guidance records and adds four
Issue/evidence/test records. All other baseline bytes and executable modes remain
exact. Contributor a6, predecessor history and customer guidance templates are
unchanged. Root install/init command blocks retain their exact selected bytes;
the workflow now directs installation through the same whole-envelope wrapper.

Envelope SHA-256:
`a41782559bc3a2d9e02ceacc5bf458f0a77e53940b1b3bdcc8fabca6c15b53ea`.
Payload SHA-256:
`0fb3d491b4b99578b06be99894b945d27834d49ad855029de227792ade4f16f4`.
Source-index SHA-256:
`3ae51d3c2a8238adb31335f2b2941a30495066d81f048ef8848b593249025fb0`.
Whole-envelope carriage remains required; six detached-wheel legal gaps remain
unrepaired and twelve audit findings remain visible. No artifact is normalized.

## Maintainer replay

Use Python 3.12, bubblewrap and an independently selected pytest environment.
From this pinned checkout, create fresh private scratch:

```sh
freeze_scratch="$(mktemp -d /tmp/aware-issue083-freeze-replay.XXXXXXXX)"
AWARE_INITIALIZER_INTEGRATION_REPLAY_ROOT="$freeze_scratch" \
  PYTHONDONTWRITEBYTECODE=1 \
  python -B -m pytest -q -p no:cacheprovider \
  releases/canonical-issue083-fs-v1/test_instruction_freeze.py \
  --basetemp "$freeze_scratch/test-output" \
  --junitxml "$freeze_scratch/instructions.xml"
```

The proof reuses the existing, byte-pinned installer smoke. It checks exact
instruction pins and tamper refusals, unaffected bytes/modes, installer commands,
local links and shell syntax. Harmless guard probes distinguish an absent target
from existing files, directories and symlinks. Installed help checks use the same
forty-package offline environment with checkouts hidden and inherited environment
cleared. No participant runner or copied installer is introduced.

These are instruction/install checks, not a new domain matrix, first-Issue task,
SPEC publication or unassisted customer evaluation. Preview's prospective inputs
are not admitted plans. Issue, manifest and input guards identify different bytes;
no silent refresh or mutation retry is supplied. Paired publication/closeout is
non-atomic and saved receipts do not recreate live authority.

Next: independent bounded freeze review, then explicitly authorized publication
and revision-pinned acquisition proof. Fresh unassisted evaluation follows
qualified delivery.

## Local proof receipts

Seven checks passed, zero skipped, including a fresh offline installation of all
forty packages with inherited environment cleared and checkouts hidden. Ten
installed operation help entrances activate. Root/workflow installation guards
refuse existing files, directories and valid/dangling symlinks before a harmless
installer marker; absent targets proceed. All 1,149 unaffected baseline files and
all 1,155 baseline executable modes remain exact.

The byte-pinned typed example executes through the installed environment and
round-trips exactly through its decoder without creating documents or authority.
It is an illustrative snapshot, not an admitted draft or approval. These two
additional subprocess probes are separate from the seven-case XML.

Retained SHA-256 values:

- Seven-case XML: `a4af0765053fa91b3ff7ae4e495239ae6d1ca5b916a206987319a61bbae90d90`.
- Installed receipt: `24c4574565441c33679873e92ca618ed240ac9788abe8b512deba5afb7346591`.
- Instruction record: `dd08097a34302e2326c7be4d1c6de393209a5aca27cbbff95919514fa0383728`.
- Maintainer test: `923567558b58407951dfbea66b64d135f2a5ce1d12839e447b05b9e1fc02bfa6`.
- Typed example snapshot: `f1fefc5183183277d1fd32e9bf00776e982bf0989be83fc7fb5175f815a55409`.
- Decoder receipt: `6580a9fb9f9b0816f0e4d51854ede6685ae80d9bdd40362d4cefa77ce18b3e42`.

The initial accounting replay had five passes, one failed literal prose assertion
and one installer deselection. The phrase was split by Markdown wrapping; only
the assertion's whitespace treatment changed. Its failed XML remains retained,
SHA-256 `483cd922fb54d377e1d380083b270832fa6ac60badef9a369727a4fdf7c2b35a`.
That correction changes no customer instruction bytes or runtime behavior.

## Original local publication evidence

Implementation: `df6320206e761665ecf7246959138e20eed6ed43`. Its actual delta is
exactly the ten admitted paths. Original contributor a6 dry-run/apply share the
same paths, message and Issue-byte guard
`sha256:7651952c90322ea500bc2a107f112b3c029f24061a18bbac21f9e764bcd4adba`.
The applied receipt reports `reference_update=cas_applied`,
`transaction_mode=isolated_index_atomic_ref_v1`, `shared_index_projection=applied`
and `index_reconciliation_pending=false`. The Workspace publication owner is
unchanged. No instruction review, transfer or push follows from this local commit.

Original receipt SHA-256 values:

- Read: `7a270f137418c242811546073e9008698d6806dbafa8e933918a4886e7b5cb25`.
- Dry-run: `e97cb37e6d6ae9bf31e14fa4abd55fd1a29ae1e9839b524b72f055e45759e497`.
- Apply: `ae974212a8817e49563068e682628687f781628e7a3fac9aaaa1d9f01b989684`.
- Final overlapping accounting, six passed / one installation deselected:
  `8579d4ff2b2f477ddcca57c00b54dd722102329c81cfdf15ae8efe8693d99f63`.

The governing Issue remains In Progress for independent freeze review. Its
authored acceptance criteria are preserved; evidence does not hand-check them.
