"""Source integration with genuine owners. Git writes only build test fixtures."""

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from aware_issue_fs_adapter import FilesystemIssueOperationProvider
from aware_issue_fs_adapter import specification_iteration as pairing_module
from aware_issue_fs_adapter.specification_iteration import (
    FilesystemSpecificationIterationBindingProvider,
)
from aware_issue_sdk import (
    IssueSdkOperationClient,
    IssueSpecificationIterationBindingError,
    IssueSpecificationIterationBindingObserveRequest,
    SpecificationIterationBindingOutcome,
)
from aware_specification_fs_sdk_adapter import SpecificationIterationAdmission
from aware_specification_sdk import (
    SpecificationDraftRequest,
    SpecificationObserveRequest,
)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_root = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
_spec_fixture = _load(
    "workflow_spec_pairing_fixtures",
    _root
    / "workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter/tests/test_provider.py",
)
_issue_fixture = _load(
    "workflow_issue_pairing_fixtures", Path(__file__).with_name("test_provider.py")
)
canonical_tree = _spec_fixture.canonical_tree
ITERATION = "specification:example.spec/phase:foundation/iteration:proof"
ISSUE = _issue_fixture.ISSUE_REF
SPEC_ROOT = "customer/contracts/example"
ISSUE_PATH = "docs/issues/2026/09/20/fb-2026-09-20-example.md"


def git(base, *args):
    return subprocess.check_output(
        ["git", "-C", str(base), *args], stderr=subprocess.PIPE
    )


def sha(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def repository(canonical_tree):
    base, root = canonical_tree
    (base / SPEC_ROOT).parent.mkdir(parents=True)
    (base / root).rename(base / SPEC_ROOT)
    _issue_fixture._repository(base)
    path = base / "aware.protocol.toml"
    path.write_text(
        path.read_text().replace('root = "docs/specs"', 'root = "customer/contracts"')
    )
    git(base, "init", "-b", "main")
    git(base, "config", "user.email", "fixture@example.invalid")
    git(base, "config", "user.name", "Fixture")
    git(base, "add", SPEC_ROOT)
    git(base, "commit", "-m", "Committed SPEC fixture; Issue remains uncommitted")
    return base


@pytest.fixture
def context(repository):
    spec = _spec_fixture.open_provider(repository, (SPEC_ROOT,))
    admission = spec.admit_iteration(SpecificationObserveRequest(), ITERATION)
    pairing = FilesystemSpecificationIterationBindingProvider(
        repository_root=repository, iteration_admission=admission
    )
    request = IssueSpecificationIterationBindingObserveRequest(
        ISSUE,
        ITERATION,
        admission.identity.plan.plan_revision,
        admission.identity.plan_digest,
        admission.observation.source_digest,
        sha(repository / ISSUE_PATH),
        pairing.manifest_sha256,
        git(repository, "rev-parse", "HEAD").decode().strip(),
    )
    try:
        yield repository, spec, admission, pairing, request
    finally:
        pairing.close()
        spec.close()


def observe(pairing, request):
    return IssueSdkOperationClient(pairing).observe_specification_iteration_binding(
        request
    )


def refused(result, diagnostic):
    assert result.outcome is SpecificationIterationBindingOutcome.REFUSED
    assert diagnostic in result.diagnostics
    assert result.committed_members == ()
    assert result.issue_projection is None
    assert (
        result.binding_persisted
        is result.approval_verified
        is result.work_authorized
        is False
    )


def test_custom_root_real_admission_committed_bytes_and_uncommitted_issue(context):
    base, _, admission, pairing, request = context
    result = observe(pairing, request)
    assert result.outcome is SpecificationIterationBindingOutcome.VERIFIED
    assert result.roots == (SPEC_ROOT,)
    assert result.head == request.expected_head
    assert result.phase_ref == admission.identity.phase_ref
    assert result.issue_projection.issue_ref == ISSUE
    assert result.issue_projection.owner_ref == "codex-example"
    for member in result.committed_members:
        assert (
            git(base, "cat-file", "blob", member.blob_oid)
            == (base / member.path).read_bytes()
        )
        assert member.body_digest == sha(base / member.path)
    assert result.to_wire()["approval_verified"] is False
    assert result.to_wire()["binding_persisted"] is False
    assert result.to_wire()["work_authorized"] is False


@pytest.mark.parametrize(
    "field,value,diagnostic",
    [
        ("iteration_ref", ITERATION + "-other", "pairing_iteration_identity_mismatch"),
        ("plan_revision", 2, "pairing_iteration_identity_mismatch"),
        ("plan_digest", "sha256:" + "0" * 64, "pairing_iteration_identity_mismatch"),
        (
            "expected_specification_source_digest",
            "sha256:" + "0" * 64,
            "pairing_specification_source_mismatch",
        ),
        ("expected_issue_source_sha256", "sha256:" + "0" * 64, "pairing_issue_changed"),
        (
            "expected_manifest_sha256",
            "sha256:" + "0" * 64,
            "pairing_expected_manifest_mismatch",
        ),
        ("expected_head", "0" * 40, "pairing_head_changed"),
    ],
)
def test_exact_request_coordinates_refuse(context, field, value, diagnostic):
    _, _, _, pairing, request = context
    refused(observe(pairing, replace(request, **{field: value})), diagnostic)


@pytest.mark.parametrize("kind", ["object", "dto", "observation", "evidence", "forged"])
def test_data_cannot_replace_original_admission(context, kind):
    base, spec, admission, _, _ = context
    if kind == "forged":
        value = object.__new__(SpecificationIterationAdmission)
        value._provider = spec
        value._identity = admission.identity
        value._observation = admission.observation
    else:
        value = {
            "object": object(),
            "dto": {"iteration_ref": ITERATION},
            "observation": admission.observation,
            "evidence": pairing_module.revalidate_specification_iteration_source_evidence(
                admission
            ),
        }[kind]
    with pytest.raises(
        IssueSpecificationIterationBindingError,
        match="pairing_specification_admission_refused",
    ):
        FilesystemSpecificationIterationBindingProvider(
            repository_root=base, iteration_admission=value
        )


@pytest.mark.parametrize("action", ["released", "closed", "restamped"])
def test_retired_and_cross_provider_admission_refuse(context, action):
    base, spec, admission, pairing, request = context
    second = None
    try:
        if action == "released":
            spec.release_iteration(admission)
        elif action == "closed":
            spec.close()
        else:
            second = _spec_fixture.open_provider(base, (SPEC_ROOT,))
            admission._provider = second
        refused(observe(pairing, request), "pairing_specification_admission_refused")
    finally:
        if second:
            second.close()


def test_equal_bytes_in_another_repository_are_not_same_source(context, tmp_path):
    base, _, admission, _, _ = context
    clone = tmp_path / "clone"
    shutil.copytree(base, clone)
    with pytest.raises(
        IssueSpecificationIterationBindingError,
        match="pairing_source_repository_mismatch",
    ):
        FilesystemSpecificationIterationBindingProvider(
            repository_root=clone, iteration_admission=admission
        )


def test_manifest_change_and_root_substitution_refuse(context):
    base, _, _, pairing, request = context
    manifest = base / "aware.protocol.toml"
    manifest.write_text(
        manifest.read_text().replace(
            'root = "customer/contracts"', 'root = "elsewhere"'
        )
    )
    refused(observe(pairing, request), "pairing_manifest_changed")


def test_original_admission_outside_declared_spec_root_refuses(repository):
    spec = _spec_fixture.open_provider(repository, (SPEC_ROOT,))
    try:
        admission = spec.admit_iteration(SpecificationObserveRequest(), ITERATION)
        path = repository / "aware.protocol.toml"
        path.write_text(
            path.read_text().replace(
                'root = "customer/contracts"', 'root = "other/contracts"'
            )
        )
        with pytest.raises(
            IssueSpecificationIterationBindingError,
            match="pairing_specification_outside_binding",
        ):
            FilesystemSpecificationIterationBindingProvider(
                repository_root=repository, iteration_admission=admission
            )
    finally:
        spec.close()


def test_dirty_administrative_bytes_retire_admission_without_semantic_bypass(context):
    base, _, _, pairing, request = context
    path = base / SPEC_ROOT / "SPEC.md"
    path.write_text(path.read_text().replace("Owner: `fixture`", "Owner: `other`"))
    refused(observe(pairing, request), "pairing_specification_admission_refused")
    refused(observe(pairing, request), "pairing_specification_admission_refused")


@pytest.mark.parametrize("change", ["untracked", "different", "symlink"])
def test_committed_file_and_exact_byte_identity(repository, change):
    path = repository / SPEC_ROOT / "SPEC.md"
    if change == "untracked":
        git(repository, "rm", "--cached", str(path.relative_to(repository)))
    elif change == "different":
        path.write_text(path.read_text().replace("Owner: `fixture`", "Owner: `other`"))
        git(repository, "add", SPEC_ROOT)
    else:
        source = path.read_bytes()
        path.unlink()
        path.symlink_to("../../../../foreign.md")
        git(repository, "add", SPEC_ROOT)
        git(repository, "commit", "-m", "Symlink tree fixture")
        path.unlink()
        path.write_bytes(source)
    if change != "symlink":
        git(repository, "commit", "-m", "Changed tree fixture")
    if change == "different":
        path.write_text(path.read_text().replace("Owner: `other`", "Owner: `fixture`"))
    spec = _spec_fixture.open_provider(repository, (SPEC_ROOT,))
    try:
        admission = spec.admit_iteration(SpecificationObserveRequest(), ITERATION)
        with FilesystemSpecificationIterationBindingProvider(
            repository_root=repository, iteration_admission=admission
        ) as pairing:
            request = IssueSpecificationIterationBindingObserveRequest(
                ISSUE,
                ITERATION,
                1,
                admission.identity.plan_digest,
                admission.observation.source_digest,
                sha(repository / ISSUE_PATH),
                pairing.manifest_sha256,
                git(repository, "rev-parse", "HEAD").decode().strip(),
            )
            refused(
                observe(pairing, request),
                "pairing_committed_source_mismatch"
                if change == "different"
                else "pairing_specification_not_committed_regular",
            )
    finally:
        spec.close()


@pytest.mark.parametrize("when", ["during_sources", "before_return"])
def test_actual_head_race_refuses(context, monkeypatch, when):
    base, _, _, pairing, request = context
    original = pairing._committed_sources if when == "during_sources" else pairing._head
    count = 0

    def race(*args):
        nonlocal count
        count += 1
        if when == "during_sources" or count == 2:
            (base / "race.txt").write_text("separate actor epoch\n")
            git(base, "add", "race.txt")
            git(base, "commit", "-m", "Independent epoch movement fixture")
        return original(*args)

    monkeypatch.setattr(
        pairing, "_committed_sources" if when == "during_sources" else "_head", race
    )
    refused(observe(pairing, request), "pairing_head_changed")


@pytest.mark.parametrize("target", ["issue", "manifest", "spec"])
def test_return_boundary_currentness_refuses(context, monkeypatch, target):
    base, _, _, pairing, request = context
    original = pairing._issue
    count = 0

    def race(*args):
        nonlocal count
        count += 1
        result = original(*args)
        if count == 1:
            path = (
                base
                / {
                    "issue": ISSUE_PATH,
                    "manifest": "aware.protocol.toml",
                    "spec": f"{SPEC_ROOT}/SPEC.md",
                }[target]
            )
            body = path.read_text()
            path.write_text(
                body.replace("Example", "Updated")
                if target == "issue"
                else body + "# epoch changed\n"
            )
        return result

    monkeypatch.setattr(pairing, "_issue", race)
    diagnostic = {
        "issue": "pairing_issue_changed",
        "manifest": "pairing_manifest_changed",
        "spec": "pairing_specification_admission_refused",
    }[target]
    refused(observe(pairing, request), diagnostic)


@pytest.mark.parametrize(
    "status,owner",
    [("Closed", "codex-other"), ("Open", "TBD"), ("In Progress", "codex-other")],
)
def test_observed_lifecycle_and_owner_never_admit_work(context, status, owner):
    base, _, _, pairing, request = context
    path = base / ISSUE_PATH
    path.write_text(
        _issue_fixture._issue(status=status).replace("codex-example", owner)
    )
    result = observe(pairing, replace(request, expected_issue_source_sha256=sha(path)))
    assert result.outcome is SpecificationIterationBindingOutcome.VERIFIED
    assert result.issue_projection.status.lower().replace(
        " ", "_"
    ) == status.lower().replace(" ", "_")
    assert result.work_authorized is result.approval_verified is False


def test_independent_contexts_preserve_work_index_and_refs_and_write_no_binding(
    context,
):
    base, _, admission, pairing, request = context
    (base / "foreign-staged.txt").write_text("foreign staged work\n")
    git(base, "add", "foreign-staged.txt")
    (base / "foreign-dirty.txt").write_text("foreign dirty work\n")
    before = {
        str(p.relative_to(base)): p.read_bytes() for p in base.rglob("*") if p.is_file()
    }
    assert (
        observe(pairing, request).outcome
        is SpecificationIterationBindingOutcome.VERIFIED
    )
    with FilesystemSpecificationIterationBindingProvider(
        repository_root=base, iteration_admission=admission
    ) as second:
        assert (
            observe(second, request).outcome
            is SpecificationIterationBindingOutcome.VERIFIED
        )
    after = {
        str(p.relative_to(base)): p.read_bytes() for p in base.rglob("*") if p.is_file()
    }
    assert after == before


def test_two_proposed_issues_do_not_persist_or_occupy_a_cardinality_slot(context):
    base, _, _, pairing, request = context
    second_ref = "fb/2026-09-20/second"
    second_path = base / "docs/issues/2026/09/20/fb-2026-09-20-second.md"
    second_path.write_text(_issue_fixture._issue(issue_ref=second_ref))
    assert (
        observe(pairing, request).outcome
        is SpecificationIterationBindingOutcome.VERIFIED
    )
    second = replace(
        request, issue_ref=second_ref, expected_issue_source_sha256=sha(second_path)
    )
    assert (
        observe(pairing, second).outcome
        is SpecificationIterationBindingOutcome.VERIFIED
    )
    assert "specification:" not in second_path.read_text()


def test_unborn_repository_has_no_spec_epoch_but_unbound_issue_is_readable(repository):
    fresh = repository.parent / "unborn"
    shutil.copytree(repository, fresh, ignore=shutil.ignore_patterns(".git"))
    git(fresh, "init", "-b", "main")
    assert (
        FilesystemIssueOperationProvider(repository_root=fresh)
        .resolve_read_projection(
            pairing_module.IssueReadProjectionResolveRequest(ISSUE)
        )
        .outcome.value
        == "found"
    )
    spec = _spec_fixture.open_provider(fresh, (SPEC_ROOT,))
    try:
        admission = spec.admit_iteration(SpecificationObserveRequest(), ITERATION)
        with FilesystemSpecificationIterationBindingProvider(
            repository_root=fresh, iteration_admission=admission
        ) as pairing:
            request = IssueSpecificationIterationBindingObserveRequest(
                ISSUE,
                ITERATION,
                1,
                admission.identity.plan_digest,
                admission.observation.source_digest,
                sha(fresh / ISSUE_PATH),
                pairing.manifest_sha256,
                "0" * 40,
            )
            refused(observe(pairing, request), "pairing_git_epoch_unavailable")
    finally:
        spec.close()


def test_malformed_owner_result_is_typed_non_authorizing_refusal(context, monkeypatch):
    _, _, _, pairing, request = context
    monkeypatch.setattr(pairing, "resolve_read_projection", lambda request: object())
    refused(observe(pairing, request), "pairing_issue_result_invalid")


def test_replaced_repository_refuses(context):
    base, _, _, pairing, request = context
    moved = base.with_name("original-moved")
    base.rename(moved)
    shutil.copytree(moved, base)
    refused(observe(pairing, request), "pairing_repository_changed")


def test_closed_pairing_context_refuses(context):
    _, _, _, pairing, request = context
    pairing.close()
    refused(observe(pairing, request), "pairing_context_closed")


@pytest.mark.parametrize("change", ["missing", "symlink", "iteration_plan"])
def test_real_source_owner_refusals_are_preserved(context, change):
    base, _, _, pairing, request = context
    path = base / SPEC_ROOT / "SPEC.md"
    if change == "missing":
        path.unlink()
    elif change == "symlink":
        other = base / "foreign-spec.md"
        other.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(other)
    else:
        path = (
            base
            / SPEC_ROOT
            / "phases/00-foundation/iterations/00-2026-09-06-proof/README.md"
        )
        path.write_text(
            path.read_text().replace(
                "Prove exact filesystem", "Change exact filesystem"
            )
        )
        # Regardless of a fixture's wording, a real administrative byte change
        # invalidates source admission even when the plan remains the same.
        path.write_text(path.read_text().replace("fixture", "other-fixture"))
    refused(observe(pairing, request), "pairing_specification_admission_refused")


def test_duplicate_specification_identity_refuses_through_real_owner(repository):
    other = "customer/contracts/duplicate"
    shutil.copytree(repository / SPEC_ROOT, repository / other)
    spec = _spec_fixture.open_provider(repository, tuple(sorted((SPEC_ROOT, other))))
    try:
        with pytest.raises(pairing_module.SpecificationOperationError):
            spec.admit_iteration(SpecificationObserveRequest(), ITERATION)
    finally:
        spec.close()


def test_duplicate_issue_identity_refuses_through_existing_issue_owner(context):
    base, _, _, pairing, request = context
    (base / "docs/issues/fb-duplicate.md").write_text(_issue_fixture._issue())
    refused(observe(pairing, request), "pairing_issue_unavailable")


def test_changed_issue_identity_refuses_without_scope_or_work_admission(context):
    base, _, _, pairing, request = context
    path = base / ISSUE_PATH
    path.write_text(path.read_text().replace(ISSUE, "fb/2026-09-20/other"))
    refused(
        observe(pairing, replace(request, expected_issue_source_sha256=sha(path))),
        "pairing_issue_unavailable",
    )


@pytest.mark.parametrize("owner", ["spec_evidence", "issue_projection"])
def test_incomplete_typed_owner_result_refuses(context, monkeypatch, owner):
    _, _, _, pairing, request = context
    if owner == "spec_evidence":
        value = object.__new__(pairing_module.SpecificationIterationSourceEvidence)
        monkeypatch.setattr(
            pairing_module,
            "revalidate_specification_iteration_source_evidence",
            lambda token: value,
        )
        diagnostic = "pairing_specification_admission_refused"
    else:
        original = pairing.resolve_read_projection

        def malformed(req):
            value = original(req)
            projection = object.__new__(type(value.projection))
            object.__setattr__(projection, "issue_ref", req.issue_ref)
            object.__setattr__(
                projection, "source_digest", request.expected_issue_source_sha256
            )
            return replace(value, projection=projection)

        monkeypatch.setattr(pairing, "resolve_read_projection", malformed)
        diagnostic = "pairing_observation_failed"
    refused(observe(pairing, request), diagnostic)


def test_git_environment_cannot_substitute_other_repository_or_index(
    context, tmp_path, monkeypatch
):
    _, _, _, pairing, request = context
    other = tmp_path / "unrelated"
    other.mkdir()
    git(other, "init", "-b", "main")
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))
    monkeypatch.setenv("GIT_INDEX_FILE", str(tmp_path / "foreign.index"))
    assert (
        observe(pairing, request).outcome
        is SpecificationIterationBindingOutcome.VERIFIED
    )
    assert not (tmp_path / "foreign.index").exists()


def test_all_selected_closures_require_committed_identity(repository):
    second = "customer/contracts/second"
    definition = _spec_fixture.definition()
    phase = definition.phases[0]
    definition = replace(
        definition,
        key="second.spec",
        phases=(
            replace(
                phase,
                gate=replace(
                    phase.gate,
                    invariant_refs=("specification:second.spec/invariant:safe",),
                ),
            ),
        ),
    )
    writer = _spec_fixture.open_provider(repository, (second,))
    try:
        writer.create_draft(SpecificationDraftRequest(definition, "fixture", "intent"))
    finally:
        writer.close()
    spec = _spec_fixture.open_provider(repository, tuple(sorted((SPEC_ROOT, second))))
    try:
        admission = spec.admit_iteration(SpecificationObserveRequest(), ITERATION)
        with FilesystemSpecificationIterationBindingProvider(
            repository_root=repository, iteration_admission=admission
        ) as pairing:
            request = IssueSpecificationIterationBindingObserveRequest(
                ISSUE,
                ITERATION,
                1,
                admission.identity.plan_digest,
                admission.observation.source_digest,
                sha(repository / ISSUE_PATH),
                pairing.manifest_sha256,
                git(repository, "rev-parse", "HEAD").decode().strip(),
            )
            refused(
                observe(pairing, request), "pairing_specification_not_committed_regular"
            )
    finally:
        spec.close()


def test_fresh_processes_issue_their_own_admissions_and_preserve_all_bytes(context):
    base, _, _, _, request = context
    source_projects = (
        _root / "workspaces/aware_coordination/modules/workflow/sdks/issue/python",
        _root
        / "workspaces/aware_coordination/modules/workflow/sdks/issue/filesystem_adapter/python",
        _root
        / "workspaces/aware_kernel/modules/specification/sdks/specification/python/public",
        _root
        / "workspaces/aware_kernel/modules/specification/sdks/specification/python/fs_adapter",
    )
    script = """
import json, os, sys
for path in json.loads(sys.argv[1]):
    sys.path.insert(0, path)
from aware_specification_fs_sdk_adapter import SpecificationFsSdkProvider
from aware_specification_sdk import SpecificationObserveRequest
from aware_issue_fs_adapter.specification_iteration import FilesystemSpecificationIterationBindingProvider
from aware_issue_sdk import IssueSdkOperationClient, IssueSpecificationIterationBindingObserveRequest
data = json.loads(sys.argv[4])
data.pop('contract')
request = IssueSpecificationIterationBindingObserveRequest(**data)
fd = os.open(sys.argv[2], os.O_RDONLY | os.O_DIRECTORY)
try:
    spec = SpecificationFsSdkProvider(fd, (sys.argv[3],))
finally:
    os.close(fd)
try:
    admission = spec.admit_iteration(SpecificationObserveRequest(), request.iteration_ref)
    with FilesystemSpecificationIterationBindingProvider(repository_root=sys.argv[2], iteration_admission=admission) as provider:
        result = IssueSdkOperationClient(provider).observe_specification_iteration_binding(request)
        assert result.outcome.value == 'verified_proposed_pairing', result.diagnostics
        print(json.dumps(result.to_wire(), sort_keys=True))
finally:
    spec.close()
"""
    before = {
        str(p.relative_to(base)): p.read_bytes() for p in base.rglob("*") if p.is_file()
    }
    results = [
        subprocess.check_output(
            [
                sys.executable,
                "-B",
                "-c",
                script,
                json.dumps(list(map(str, source_projects))),
                str(base),
                SPEC_ROOT,
                json.dumps(request.to_wire()),
            ]
        )
        for _ in range(2)
    ]
    assert results[0] == results[1]
    assert {
        str(p.relative_to(base)): p.read_bytes() for p in base.rglob("*") if p.is_file()
    } == before
