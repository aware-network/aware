# Neutral workspaces publication checkpoint

## Scope and immutable product identity

Baseline public revision: `701e3b5b2ff2b160eb489d2e6a63a7e9715d6de5`.
Consumer remains `aware-agent-cli 0.1.0a3`, contract `aware.agent.fs.v1 / 1.1.0`.
Archive SHA-256 remains
`4af072afaea666480009c03721c9846d122f61d7160fb1511329463762222a1c`.
The root repository's accepted bootstrap remains 1.0.0.

[The source inventory](source-layout.json) maps **187 relocated files**:
181 byte-identical, six README provenance-link corrections only. All runtime,
SDK, FS provider, CLI, template, build-input and legal bytes are unchanged.
There are **16 explicitly admitted neutral source projects**, not 16 interfaces:
seven Goal/Protocol and nine agent/Issue/repository. The installed agent payload
remains 22 reachable packages; the separate Goal payload remains 13.

`protocols/` owns contracts, profile/workflow instructions, installers, tests,
evaluation, distribution and provenance. `workspaces/` owns only their reviewed
neutral source, organized by existing domain coordinates. Original Goal capsule
metadata lives under `protocols/publication/goal-source-capsule/`; source paths
map into workspaces and the original attachment remains unchanged.
No retired Kernel/Network outputs, internal repository/workspace manifests,
generated API/DTO, ontology/ORM, services or Experience implementation is restored.

The original a3 builder was retained **byte-for-byte** at
`protocols/publication/builders/agent-0.1.0a3.py`; the immutable release manifest
still pins that historical builder. The active builder now reads public
workspace projects by default. Owner-source regeneration requires explicit
`--refresh-owner-sources` and a pinned source repository; it is not a normal
consumer build dependency. A current-version build refuses before source
mutation rather than overwriting the accepted candidate. Future builds record
public workspace input hashes and source amendments separately from owner
provenance. The changed active assembly path has **not** produced or accepted a
new consumer archive in this cut.

## External evidence intake

[The bounded intake](../evaluations/admissions/a3-onboarding-20261005.md) cites
private archive commit `5d9f4dfc07f6d2d5642665cb20d77dc2ba5b70fd`.
Fetched archive HEAD matched. V2 validation reproduced **7 artifacts, 3 findings,
4 interactions**; candidate, version and archive hash match a3.
I reports successful installation, explicit unborn-repository creation and
actionable missing-intent refusal. U/V/R, Issue commits and closeout were not
run. Development checkout visibility and supplied choreography remain disclosed.
No private submission was republished or modified; validation is byte/shape
accounting, not authorship or general workflow acceptance.

## Producer validation

A new environment installed the exact a3 archive with Bubblewrap, networking
disabled, the development checkout hidden and inherited environment cleared.
Dependency checks passed. Installed APIs resolve from wheels, not workspaces.

**198 passed, zero skipped**:

- 10 repository preparation, 15 bootstrap, 8 Issue/publication workflow;
- 8 bundle, 16 evaluation, 10 retained Goal/publication accounting;
- 10 source-layout inventory/immutability/neutral-boundary checks;
- 121 pinned owner tests, with separately supplied pytest tools.

Owner-test JUnit SHA-256:
`c882545bb4f60ce61d60faaf4bc5049d8a112bfdecf1c35217809cc59e54ba8d`.

Separately, all **16 public source projects rebuilt** with
`uv build --wheel --no-sources` to a disposable output. Every entire wheel hash
matched its accepted distribution: nine agent/Issue/repository wheels and seven
Goal/Protocol wheels. This is one same-host rebuild observation, not cross-host
reproducibility, independently reacquired build-backend proof or a new release.
No rebuilt wheel replaced a distribution member.

### Replay

Install using `protocols/agent/install.py` into a new Python 3.12 environment.
Run its interpreter with `-I -B` over:

```text
protocols/agent/test_installed_repository_setup.py
protocols/agent/test_installed_bootstrap.py
protocols/agent/test_installed_workflow.py
protocols/agent/test_bundle.py
protocols/evaluations/v2/test_validate.py
protocols/publication/test_preview.py
protocols/publication/test_source_layout.py
```

Supply pytest separately for the 121 exported `protocols/agent/owner-tests`;
do not install test tools into the claimed consumer closure. Retain the same
checkout-hidden/network-disabled boundary. The original build/source pins and
qualification remain intact; no Goal approval, service authority, authenticated
actor policy, hostile-process isolation or external U/V/R pass is implied.

## Next outcome

Publish this exact neutral-only tree through the governed Issue and bounded
non-force Git delivery. Then ask a fresh client execution to complete a real
approved Issue outcome on unchanged a3, followed separately by V and R.
Additional source enters only after an explicit value/dependency/notice review.
