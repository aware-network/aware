# a5 Issue-usability candidate checkpoint

Status: producer technical checkpoint, pending independent candidate review.
This is not consumer acceptance, promotion, external evaluation or publication.
The selected public `release.json` and a4 archive remain unchanged.

Input: independently accepted Issue owner source
`c112eeb065f414f810e3d4d221e20bcb9df38487`, with content/closeout acceptance
at `5d005d4a1dd702226cadc32548a796fa5521132c`. Owner-source closeout is
`c8c193f7f16e39fb66cc7970183b3a0447ffdab8` in the producer repository.
The consumer includes the neutral owner bytes; it does not depend on access to
that repository or the private evaluation archive.

The `prepare_issue_a5.py` generator adopts exactly five committed source files
and four pinned test files. Runtime content, lifecycle and publication decisions
stay with existing owners. The CLI summary is reused directly, not duplicated.
The thin open composition requires explicit initial problem/objective/acceptance
and retains partial receipts on a later request-construction failure.

Built versions: `aware-agent-cli 0.1.0a5`, `aware-issue-sdk 0.7.0a3`,
`aware-issue-fs-adapter 0.6.0a3`, `aware-issue-cli 0.6.0a3` and customer contract
`aware.agent.fs.v1 1.2.0`. No dependencies or authority profiles are added.
SDK omitted-content compatibility and full JSON remain supported. The existing
repository owner and other payload dependencies are not redesigned.

## Exact candidate

The unchanged builder ran from disposable committed public source
`084c021b0db0e24d80681631d21adf6d05c821a9`. The local preparation commit is
not a remotely published source coordinate. The candidate's source and notice
attachments are included in its archive; no private checkout is an installation
dependency.

| Record | SHA-256 |
| --- | --- |
| `distribution/aware-agent-fs-0.1.0a5-linux_x86_64-py312.tar.gz` (3,573,305 bytes) | `0e6a2c98a0d8c691b7078ab48194363971d547689514b5c8fa3a3d2f7ccc9184` |
| `release-a5-candidate.json` | `dea4c561c37f557dbb9012838522f4e96d076b323e220e164eba7e24c3442bc0` |
| `issue-a5-candidate-binding.json` | `db92c19afccf083aab6f566191ed1b4cc3708cf7cbfa006b9e5379f105dd90d6` |
| `source-provenance.json` | `afb8f89aaf556a728f90558e29f0a9e4f553bdbff6a6ce0ec8957ddd269d9dd7` |
| Unchanged `build_bundle.py` | `0a7eacd4752dad4c1bac06c0e20ac6256283ed7b1aaeaff7e2a8e004a11119cb` |

The archive has 396 members / 395 checksum entries and 22 payload packages.
All 22 are reachable through 35 active dependency requirements. Exactly four
wheels changed; the other 18 match a4 byte-for-byte. The workspace publication
operator remains the accepted a4 owner bytes and version, not a replacement
commit engine. Owner bindings identify the installed module explicitly rather
than guessing authority from a basename such as `main.py`.

The manifest's historical `source_revision` (`728831f6636a611a8baac61dbc258ed563a0e466`)
is the original extraction coordinate, not this complete build source. Actual
build source is recorded separately in the candidate binding and embedded
provenance; row-specific owner revisions identify later exact-byte adoptions.
No historical field or old artifact has been silently relabeled.

## Producer proof

- 80 focused owner-source tests passed before building; 10 source-layout checks
  passed. These are source proofs, not substitutes for installed execution.
- Candidate-bound accounting replay: 28 passed, zero skipped. This comprises
  8 retained a4 accounting cases, 10 a5 accounting cases and 10 source-layout
  cases. All declared wheel/source/contract/notice bytes match; excluded
  Service/API/DTO, ontology/ORM, Experience and benchmark surfaces are absent.
- Installed replay: 222 passed, zero skipped. These comprise 175 pinned owner
  cases (43 SDK, 20 provider, 17 CLI, 9 state, 86 shared commit owner) and 47
  installed workflow/bootstrap/repository/usability cases. Pytest 9.0.2 and
  its helper modules were supplied separately, not added to the payload.
- Linux x86-64, Python 3.12.3: offline installation, cleared environment,
  hidden producer checkouts and older installations, non-editable contained
  imports, no direct-URL installations, clean dependency checks.
- New usability cases exercise required and malformed authored content before
  creation, real typed open/commit/close, partial creation receipts after a
  refused scope, out-of-scope refusal, shared summary identity, actual index
  fields and foreign-work preservation. Authored acceptance remains unchecked.
  Typed-response `cas_failed` summary tests do not claim a live CAS race.

The first installed collection attempt failed because a pinned state fixture
imports `conftest` by name. Adding only that fixture directory to the proof
runner fixed collection; no product module path or candidate byte changed.
The failed receipt is retained. A replay of the initial installation passed;
a separate clean installation-and-test replay then also passed all 222 cases,
zero skipped. The two runs are not counted as 444 distinct tests. Its 22 payload
packages plus installer-provided `pip` are contained in the fresh environment.

Clean installation-and-test JUnit:
`/tmp/aware-a5-candidate.CIusBO/clean-proof/installed.xml`,
SHA-256 `46cb0f4795f42484365b479601b0084604e65cbe5e9ae354f94c48c0c88ca7c5`.

Retained initial replay JUnit:
`/tmp/aware-a5-candidate.CIusBO/proof/installed.xml`,
SHA-256 `aef42d5ee1815f9695598329e3e0f42ea401d5035d4a9f3b955cd5285b5a16c9`.
Failed collection JUnit:
`/tmp/aware-a5-candidate.CIusBO/proof/initial-collection-failure.xml`,
SHA-256 `5352563ebdda14c28d9b4b628a72daad698a79f6909ef02ee1908ff813d3f1f8`.
Accounting JUnit: `/tmp/aware-a5-candidate.CIusBO/accounting.xml`,
SHA-256 `e39b17963c9300ab80ab3996c4e01036df7800c43ee38d19b2e0179f3d2ffc58`.

## Independent replay

Use a fresh disposable qualification packet, **not** an edit to this checkout's
live `release.json`: copy the unchanged `protocols/install.py`, agent installer,
exact a5 archive, candidate binding, pinned owner tests, five installed test
files and authored contracts. Copy `release-a5-candidate.json` into the packet
as `release.json` solely to select the candidate for the existing installer.
Provide pytest and its helpers separately, with no Aware product modules.

The retained producer packet and runner are at
`/tmp/aware-a5-candidate.CIusBO/clean-proof`. Runner SHA-256:
`e18d699abb848115b044073d874d378bc48a3f1a84a713c2f2020bc11254c948`.
For another run, copy only `packet`, `test-tools` and `run_installed.py` to a
new scratch directory, create its empty `tmp` directory, and do not copy `env`.
Set `proof_root` to that absolute new directory:

```sh
bwrap --die-with-parent --new-session --unshare-net \
  --ro-bind / / --dev /dev --proc /proc \
  --tmpfs /home --tmpfs /root --tmpfs /tmp \
  --bind "$proof_root" "$proof_root" --clearenv \
  --setenv PATH /usr/bin:/bin --setenv HOME "$proof_root" \
  --setenv LANG C.UTF-8 --setenv TMPDIR "$proof_root/tmp" \
  --chdir "$proof_root" \
  /usr/bin/python3.12 -I -B "$proof_root/run_installed.py"
```

The runner refuses an existing environment, installs through the unchanged
installer, and tests the installed product with isolated Python. Its only
added import roots are separate test tools, the harness and the pinned state
fixture directory. Neither `workspaces/` nor extracted product source is
available as an import fallback. The explicit `--reuse-installed-for-tests`
option denotes only a replay, never a new installation claim.

Tested installed harness hashes:

| File | SHA-256 |
| --- | --- |
| `test_installed_a5_usability.py` | `8b1ffafa3af1e2db0da54ed300ae7a635964a8354d1eff30849f6b80f6e3e39c` |
| `test_installed_bootstrap.py` | `1b6d8c8f99923ef48cc2738f1160258eadc267a19af70919916d1b2c7a722c29` |
| `test_installed_repository_repair.py` | `6c48406b7432a135739a129d4188ca0284a66b10c05dafc448d9f79a32c5b1a1` |
| `test_installed_repository_setup.py` | `e543d0fbd8a0dc06423d778eb0a14d1057d290b0decf2d671b4b35bb98e28c65` |
| `test_installed_workflow.py` | `63291bd0173367b164aa631b3ec2a3efe0fd7f12e294488e90a126cfbf79c146` |

## Limits and next decision

These are synthetic producer qualifications, not another external client's
U/V/R evidence or independent acceptance. Genuine crash/interrupted-unborn
recovery, authenticated actor admission, Goal writers and Service/API remain
unsupported. Index reconciliation evidence remains operation-specific; a
successful publication with pending debt is not a clean index. No hostile
process isolation, exhaustive public-safety audit or reproducible whole-bundle
build is claimed.

In-wheel legal files and unchanged third-party attachments were accounted for;
this is not a new rights certification. Existing contracts and consumer
bootstrap are not automatically upgraded. Independent candidate review precedes
any consumer selection, root documentation/bootstrap alignment or publication.

See [the candidate workflow](quickstart-a5-candidate.md). External evaluation,
consumer promotion and public Git publication remain separate. No push.
