# Issue083 local integration

This is a local integration checkpoint, not public delivery or successor selection.
The whole source/notice envelope is required; detached-wheel acquisition is not
accepted. The six package-local legal gaps and twelve raw fixture findings remain
visible. Instructions remain draft; unassisted onboarding is unproven.

## Exact inputs and scope

- Incoming public revision: `da3ac15a5585a42c53cfc00ccaaa890416392f63`.
- Accepted producer layout: `1adca437d931073678c9ded41856eff7332fba87`;
  handoff `2f61e9109bd900287533154d6cc1107944393479`.
- Layout receipt SHA-256: `6fef470c1c99c92cdb602aa7fd6f92c1017b366ba10189ea80c0d30faedf36ed`.
- Envelope SHA-256: `a41782559bc3a2d9e02ceacc5bf458f0a77e53940b1b3bdcc8fabca6c15b53ea`.
- Payload SHA-256: `0fb3d491b4b99578b06be99894b945d27834d49ad855029de227792ade4f16f4`.
- Source revision: `1f17292b223a1b9054623b4d93589a2cab029bf9`.

The reviewed 1,148-file layout is projected through the original guarded
integration helper. The exact 68-path delta is admitted alongside four review
records: its Issue, `LAYOUT-REVIEW.json`, this report and the maintainer test.
The resulting scope is 72 exact paths. No deletion or selection is admitted.

`portable_protocols` remains the sole package selector: 26 selected Aware
packages / 1,043 sources, resolved to one installation of 40 packages.
Contributor a6, its governance files, predecessor selection and all unaffected
baseline bytes/executable modes remain unchanged.

## Proof and publication status

The producer projection/authority tests passed: 28 cases. Genuine contributor
a6 Issue admission preceded projection. Eight integrated-tree checks passed,
including one fresh offline installation of all 40 packages. These suites are
not another domain replay. Lint and formatting pass for the three producer
helper/test sources; the public maintainer test is byte-identical to its template.

Retained local receipts (SHA-256):

- Guards: `ca2c4f7161f4eed16bf809282e65173672cebadefa9747105d9d509b27bb0d42`.
- Integration: `a701caad05cd75923505e0c38398fb6566662c7f608b939050f7eef970b2d081`.
- Installed smoke: `1396804a58ce1d94eca1721edc4d09751c2bf585317c019a9d6a419f02671fed`.
- Exact projection plan: `c6ac35278e2fa1afaaf864296243b58deb60f84709fdc5b8cef766dbd060517b`.

These private execution receipts are retained by the producer handoff, not
advertised as anonymously downloadable customer inputs. Actual local commit
evidence follows after identical dry-run/apply publication. Independent review
remains pending; there is no public push authorization in this Issue.

## Reproduce the maintainer integration proof

Use an independently selected Python test environment with pytest, Python 3.12
and bubblewrap available. Create fresh private scratch and run from this pinned
checkout:

```bash
integration_scratch="$(mktemp -d /tmp/aware-issue083-integration-replay.XXXXXXXX)"
AWARE_INITIALIZER_INTEGRATION_REPLAY_ROOT="$integration_scratch" \
  PYTHONDONTWRITEBYTECODE=1 \
  python -B -m pytest -q \
  releases/canonical-issue083-fs-v1/test_local_integration.py \
  --basetemp "$integration_scratch/test-output" \
  --junitxml "$integration_scratch/integration.xml"
```

The proof reuses the byte-pinned predecessor installer smoke through an explicit
private archive-name alias. It invokes the unchanged shipped installer on the
successor envelope; it does not create another runner or modify public artifacts.
The installed subprocesses have checkout roots hidden, networking disabled and
inherited environment cleared. Five help entrances, exact versions, dependency
health, no direct URLs, missing harness identity, target reuse and private-parent
permissions are checked.

This is installation/integration proof, not another 2,187-case domain replay or
fresh unassisted customer evaluation. Repository publication uses contributor
a6 with fresh Issue-byte guards, exact paths and identical dry-run/apply inputs.
Selection, instruction freeze, transfer and push require separately governed
cuts.
