from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import TypedDict, cast

import pytest
from aware_code_package_delta_contract import (
    CODE_PACKAGE_DELTA_CONTRACT,
    CodeLanguage,
    CodePackageDelta,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
    CodePackageDeltaProducerRef,
    CodePackageDeltaProduction,
    CodePackageOutputState,
    CodePackagePathRole,
    FrozenJsonObject,
    code_package_delta_output_digest,
)
from aware_code_semantic_contract_runtime import ContentDigest, canonical_json_bytes
from aware_file_system import (
    ConfinedFileMutationRequest,
    ConfinedFileMutationResult,
    ConfinedMutationOutcome,
    mutate_confined_file,
)
from aware_local_service_runtime import (
    InMemoryLocalOperationalStateStore,
    LocalOperationalStateConflict,
)
from aware_workspace_runtime.generated_output_apply import (
    FileWorkspaceGeneratedOutputApplyLease,
    WorkspaceGeneratedOutputApplier,
    WorkspaceGeneratedOutputApplyAuthority,
    WorkspaceGeneratedOutputApplyError,
    WorkspaceGeneratedOutputApplyRequest,
    admit_workspace_generated_output_apply,
)
from aware_workspace_runtime.semantic_materialization_publication import (
    WORKSPACE_SEMANTIC_MATERIALIZATION_AUTHORITY_GRADE,
    WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD,
    WORKSPACE_SEMANTIC_MATERIALIZATION_NON_CLAIMS,
    DirectoryWorkspaceSemanticMaterializationBodyStore,
    WorkspacePublishedSemanticCoordinate,
    WorkspaceSemanticMaterializationHead,
    WorkspaceStagedSemanticBody,
)

PACKAGE_REF = "aware.sdk.demo"
PACKAGE_NAME = "aware_sdk_demo"
OPERATION_REF = "workspace-operation:apply-generated-output"
OPERATION_DIGEST = "sha256:" + "b" * 64
SCHEMA_DIGEST = "sha256:" + "c" * 64


class _MaterializationHeadValues(TypedDict):
    package_ref: str
    package_kind: str
    manifest_digest: str
    source_authority_ref: str
    source_authority_digest: str
    request_ref: str
    request_digest: str
    operation_ref: str
    operation_digest: str
    invocation_digest: str
    profile_digest: str
    terminal_status: str
    result_digest: str
    result_body_ref: str
    result_body_digest: str
    result_body_size_bytes: int
    candidate: WorkspacePublishedSemanticCoordinate
    transition_digest: str | None
    effect_digest: str
    outputs: tuple[WorkspacePublishedSemanticCoordinate, ...]
    semantic_bodies: tuple[WorkspaceStagedSemanticBody, ...]
    output_activation: str


class _BodyStore:
    def __init__(self) -> None:
        self.bodies: dict[str, bytes] = {}

    def store_body(self, body_ref: str, canonical_body: bytes) -> None:
        self.store_bodies(((body_ref, canonical_body),))

    def store_bodies(self, bodies: tuple[tuple[str, bytes], ...]) -> None:
        for body_ref, canonical_body in bodies:
            current = self.bodies.get(body_ref)
            if current is not None and current != canonical_body:
                raise AssertionError("body identity collision")
            self.bodies[body_ref] = canonical_body

    def read_body(self, body_ref: str) -> bytes | None:
        return self.bodies.get(body_ref)


class _Authority:
    operation_ref = OPERATION_REF
    operation_digest = OPERATION_DIGEST

    def __init__(
        self,
        *,
        expected_request_digest: str,
        checkout_root: Path,
        admitted: bool = True,
    ) -> None:
        self._expected_request_digest = expected_request_digest
        self._checkout_root = checkout_root
        self._admitted = admitted
        self.admission_calls = 0
        self.root_calls = 0

    def admits(self, request: WorkspaceGeneratedOutputApplyRequest) -> bool:
        self.admission_calls += 1
        return self._admitted and request.request_digest == self._expected_request_digest

    def checkout_root_for(
        self, request: WorkspaceGeneratedOutputApplyRequest
    ) -> Path:
        self.root_calls += 1
        assert request.request_digest == self._expected_request_digest
        return self._checkout_root


class _Lease:
    def __init__(self) -> None:
        self.held = False
        self.acquire_calls = 0
        self.release_calls = 0

    def acquire(self, request: WorkspaceGeneratedOutputApplyRequest) -> bool:
        request.__post_init__()
        self.acquire_calls += 1
        if self.held:
            return False
        self.held = True
        return True

    def release(self, request: WorkspaceGeneratedOutputApplyRequest) -> None:
        request.__post_init__()
        assert self.held
        self.held = False
        self.release_calls += 1


def _digest(marker: str) -> str:
    return "sha256:" + sha256(marker.encode()).hexdigest()


def _body_ref(digest: str) -> str:
    return "cas://workspace-semantic-materialization/body/" + digest[7:]


def _delta(
    *,
    revision: str,
    movements: tuple[tuple[str, CodePackageDeltaKind, str | None, str | None], ...],
) -> CodePackageDelta:
    producer = CodePackageDeltaProducerRef(
        "test.renderer",
        "python.sdk.v1",
        "language_renderer",
        FrozenJsonObject.from_mapping({"target": PACKAGE_NAME}),
    )
    provisional_production = CodePackageDeltaProduction(producer)
    provisional_paths = tuple(
        CodePackageDeltaPath(
            relative_path=path,
            kind=kind,
            content_text=content,
            before_hash=before_hash,
            after_hash=None if content is None else _digest_bytes(content.encode()),
            size_bytes=None if content is None else len(content.encode()),
            language=CodeLanguage.python,
            is_structural=True,
            path_role=CodePackagePathRole.generated_code,
            production=provisional_production,
            metadata=FrozenJsonObject.from_mapping({}),
        )
        for path, kind, content, before_hash in sorted(movements)
    )
    source_revision_id = _digest(revision)
    output_digest = code_package_delta_output_digest(
        package_name=PACKAGE_NAME,
        authority=CodePackageDeltaAuthorityKind.code_package_delta,
        authority_kind=CodePackageDeltaAuthorityKind.code_package_delta.value,
        source_revision_id=source_revision_id,
        production=provisional_production,
        paths=provisional_paths,
    )
    production = replace(provisional_production, output_digest=output_digest)
    paths = tuple(replace(path, production=production) for path in provisional_paths)
    return CodePackageDelta(
        package_name=PACKAGE_NAME,
        authority=CodePackageDeltaAuthorityKind.code_package_delta,
        authority_kind=CodePackageDeltaAuthorityKind.code_package_delta.value,
        source_revision_id=source_revision_id,
        production=production,
        paths=paths,
    )


def _digest_bytes(body: bytes) -> str:
    return "sha256:" + sha256(body).hexdigest()


def _materialization_head(
    *,
    delta: CodePackageDelta,
    body_store: _BodyStore | DirectoryWorkspaceSemanticMaterializationBodyStore,
    revision: int,
) -> WorkspaceSemanticMaterializationHead:
    body = delta.to_json_bytes()
    body_digest = _digest_bytes(body)
    body_ref = _body_ref(body_digest)
    body_store.store_body(body_ref, body)
    output = WorkspacePublishedSemanticCoordinate(
        role="output",
        contract_key=CODE_PACKAGE_DELTA_CONTRACT,
        contract_version="1",
        contract_schema_digest=SCHEMA_DIGEST,
        value_ref=f"code-package-delta:{revision}",
        body_digest=body_digest,
        size_bytes=len(body),
    )
    staged = WorkspaceStagedSemanticBody(output, body_ref)
    values: _MaterializationHeadValues = {
        "package_ref": PACKAGE_REF,
        "package_kind": "sdk",
        "manifest_digest": _digest("manifest"),
        "source_authority_ref": f"workspace-source:revision:{revision}",
        "source_authority_digest": _digest(f"source:{revision}"),
        "request_ref": f"workspace-request:{revision}",
        "request_digest": _digest(f"request:{revision}"),
        "operation_ref": "workspace-operation:materialize",
        "operation_digest": _digest("materialize-operation"),
        "invocation_digest": _digest(f"invocation:{revision}"),
        "profile_digest": _digest("profile"),
        "terminal_status": "delta",
        "result_digest": _digest(f"result:{revision}"),
        "result_body_ref": f"result-body:{revision}",
        "result_body_digest": _digest(f"result-body:{revision}"),
        "result_body_size_bytes": 1,
        "candidate": output,
        "transition_digest": _digest(f"transition:{revision}"),
        "effect_digest": _digest(f"effect:{revision}"),
        "outputs": (output,),
        "semantic_bodies": (staged,),
        "output_activation": "staged_not_applied",
    }
    provisional = object.__new__(WorkspaceSemanticMaterializationHead)
    for field, value in values.items():
        object.__setattr__(provisional, field, value)
    object.__setattr__(provisional, "head_digest", "sha256:" + "0" * 64)
    object.__setattr__(provisional, "contract", WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD)
    object.__setattr__(
        provisional,
        "authority_grade",
        WORKSPACE_SEMANTIC_MATERIALIZATION_AUTHORITY_GRADE,
    )
    object.__setattr__(
        provisional, "non_claims", WORKSPACE_SEMANTIC_MATERIALIZATION_NON_CLAIMS
    )
    head_digest = ContentDigest.of_bytes(
        canonical_json_bytes(
            {
                "contract": WORKSPACE_SEMANTIC_MATERIALIZATION_HEAD,
                "value": provisional._payload(),
            }
        )
    ).value
    return WorkspaceSemanticMaterializationHead(
        **values,
        head_digest=head_digest,
    )


def _request(
    *,
    root: Path,
    head: WorkspaceSemanticMaterializationHead,
    materialization_revision: int,
    expected_output_revision: int,
    output_package_name: str = PACKAGE_NAME,
) -> WorkspaceGeneratedOutputApplyRequest:
    return WorkspaceGeneratedOutputApplyRequest.create(
        package_ref=PACKAGE_REF,
        output_package_name=output_package_name,
        checkout_binding_ref="workspace-checkout:test",
        checkout_binding_digest=_digest(str(root.resolve())),
        materialization_head_digest=head.head_digest,
        materialization_head_revision=materialization_revision,
        output_body_digest=head.outputs[0].body_digest,
        expected_output_head_revision=expected_output_revision,
        operation_ref=OPERATION_REF,
        operation_digest=OPERATION_DIGEST,
    )


def _admission(request: WorkspaceGeneratedOutputApplyRequest, root: Path):
    authority = _Authority(
        expected_request_digest=request.request_digest,
        checkout_root=root.resolve(),
    )
    admission = admit_workspace_generated_output_apply(
        request=request,
        operation_authority=cast(WorkspaceGeneratedOutputApplyAuthority, authority),
    )
    assert authority.admission_calls == 1
    assert authority.root_calls == 1
    return admission


def test_genesis_apply_and_current_reread_have_explicit_counters(tmp_path: Path) -> None:
    root = (tmp_path / "checkout").resolve()
    root.mkdir()
    body_store = _BodyStore()
    delta = _delta(
        revision="one",
        movements=(
            ("lib/one.py", CodePackageDeltaKind.create, "one\n", None),
            ("lib/two.py", CodePackageDeltaKind.create, "two\n", None),
        ),
    )
    head = _materialization_head(delta=delta, body_store=body_store, revision=1)
    state = InMemoryLocalOperationalStateStore()
    applier = WorkspaceGeneratedOutputApplier(
        state_store=state,
        body_store=body_store,
        apply_lease=_Lease(),
    )
    request = _request(
        root=root,
        head=head,
        materialization_revision=1,
        expected_output_revision=0,
    )
    result = applier.apply(
        admission=_admission(request, root),
        materialization=(1, head),
    )
    assert result.status == "applied"
    assert result.receipt is not None
    assert result.receipt.head_revision == 1
    assert result.metrics.preflight_count == 2
    assert result.metrics.mutation_count == 2
    assert result.metrics.reread_count == 2
    assert result.metrics.head_cas_count == 1
    assert result.metrics.head_reread_count == 1
    assert result.metrics.lease_acquire_count == 1
    assert result.metrics.lease_release_count == 1
    assert (root / "lib/one.py").read_text() == "one\n"

    current_request = _request(
        root=root,
        head=head,
        materialization_revision=1,
        expected_output_revision=1,
    )
    current = applier.apply(
        admission=_admission(current_request, root),
        materialization=(1, head),
    )
    assert current.status == "current"
    assert current.metrics.mutation_count == 0
    assert current.metrics.head_cas_count == 0
    assert current.metrics.head_reread_count == 1
    assert current.metrics.lease_acquire_count == 1
    assert current.metrics.lease_release_count == 1


def test_foreign_preflight_state_conflicts_before_any_mutation(tmp_path: Path) -> None:
    root = (tmp_path / "checkout").resolve()
    (root / "lib").mkdir(parents=True)
    (root / "lib/one.py").write_text("foreign\n")
    body_store = _BodyStore()
    delta = _delta(
        revision="one",
        movements=(("lib/one.py", CodePackageDeltaKind.create, "one\n", None),),
    )
    head = _materialization_head(delta=delta, body_store=body_store, revision=1)
    applier = WorkspaceGeneratedOutputApplier(
        state_store=InMemoryLocalOperationalStateStore(),
        body_store=body_store,
        apply_lease=_Lease(),
    )
    request = _request(
        root=root,
        head=head,
        materialization_revision=1,
        expected_output_revision=0,
    )
    result = applier.apply(
        admission=_admission(request, root), materialization=(1, head)
    )
    assert result.status == "conflicted"
    assert result.conflict_path == "lib/one.py"
    assert result.metrics.mutation_count == 0
    assert applier.read_head(
        package_ref=PACKAGE_REF,
        checkout_binding_ref="workspace-checkout:test",
    ) is None
    assert (root / "lib/one.py").read_text() == "foreign\n"


def test_partial_file_failure_recovers_without_publishing_partial_head(
    tmp_path: Path,
) -> None:
    root = (tmp_path / "checkout").resolve()
    root.mkdir()
    body_store = _BodyStore()
    delta = _delta(
        revision="one",
        movements=(
            ("lib/one.py", CodePackageDeltaKind.create, "one\n", None),
            ("lib/two.py", CodePackageDeltaKind.create, "two\n", None),
        ),
    )
    head = _materialization_head(delta=delta, body_store=body_store, revision=1)
    state = InMemoryLocalOperationalStateStore()
    calls = 0

    def fail_second(
        *, root: Path, request: ConfinedFileMutationRequest
    ) -> ConfinedFileMutationResult:
        nonlocal calls
        calls += 1
        if calls == 2:
            return ConfinedFileMutationResult(
                kind=request.kind,
                path=request.path,
                outcome=ConfinedMutationOutcome.FAILED,
                before_exists=False,
                before_content_digest=None,
                before_size_bytes=None,
                after_exists=False,
                after_content_digest=None,
                after_size_bytes=None,
                error_code="injected_failure",
            )
        return mutate_confined_file(root=root, request=request)

    request = _request(
        root=root,
        head=head,
        materialization_revision=1,
        expected_output_revision=0,
    )
    interrupted = WorkspaceGeneratedOutputApplier(
        state_store=state,
        body_store=body_store,
        apply_lease=_Lease(),
        mutate_file=fail_second,
    )
    failure = interrupted.apply(
        admission=_admission(request, root), materialization=(1, head)
    )
    assert failure.status == "failed"
    assert failure.metrics.mutation_count == 1
    assert interrupted.read_head(
        package_ref=PACKAGE_REF,
        checkout_binding_ref="workspace-checkout:test",
    ) is None

    recovered = WorkspaceGeneratedOutputApplier(
        state_store=state,
        body_store=body_store,
        apply_lease=_Lease(),
    ).apply(admission=_admission(request, root), materialization=(1, head))
    assert recovered.status == "applied"
    assert recovered.metrics.recovered_current_count == 1
    assert recovered.metrics.mutation_count == 1
    assert (root / "lib/one.py").read_text() == "one\n"
    assert (root / "lib/two.py").read_text() == "two\n"


def test_head_cas_loss_after_complete_file_effects_recovers_without_rewrite(
    tmp_path: Path,
) -> None:
    root = (tmp_path / "checkout").resolve()
    root.mkdir()
    body_store = _BodyStore()
    delta = _delta(
        revision="one",
        movements=(
            ("one.py", CodePackageDeltaKind.create, "one\n", None),
            ("two.py", CodePackageDeltaKind.create, "two\n", None),
        ),
    )
    head = _materialization_head(delta=delta, body_store=body_store, revision=1)
    request = _request(
        root=root,
        head=head,
        materialization_revision=1,
        expected_output_revision=0,
    )
    delegate = InMemoryLocalOperationalStateStore()

    class _LoseFirstCas:
        def __init__(self) -> None:
            self.lost = False

        def read(self, namespace: str, key: str, *, include_deleted: bool = False):
            return delegate.read(namespace, key, include_deleted=include_deleted)

        def compare_and_set(self, namespace: str, key: str, **kwargs):
            if not self.lost:
                self.lost = True
                raise LocalOperationalStateConflict("injected CAS loss")
            return delegate.compare_and_set(namespace, key, **kwargs)

        def delete(self, namespace: str, key: str, **kwargs):
            return delegate.delete(namespace, key, **kwargs)

    state = _LoseFirstCas()
    applier = WorkspaceGeneratedOutputApplier(
        state_store=state,
        body_store=body_store,
        apply_lease=_Lease(),
    )
    lost = applier.apply(
        admission=_admission(request, root), materialization=(1, head)
    )
    assert lost.status == "conflicted"
    assert lost.error_code == "output_head_cas_lost"
    assert lost.metrics.mutation_count == 2
    assert applier.read_head(
        package_ref=PACKAGE_REF,
        checkout_binding_ref="workspace-checkout:test",
    ) is None

    recovered = applier.apply(
        admission=_admission(request, root), materialization=(1, head)
    )
    assert recovered.status == "applied"
    assert recovered.metrics.mutation_count == 0
    assert recovered.metrics.recovered_current_count == 2
    assert recovered.metrics.head_cas_count == 1


def test_successor_update_delete_create_and_tombstone_reread(tmp_path: Path) -> None:
    root = (tmp_path / "checkout").resolve()
    root.mkdir()
    body_store = _BodyStore()
    state = InMemoryLocalOperationalStateStore()
    applier = WorkspaceGeneratedOutputApplier(
        state_store=state,
        body_store=body_store,
        apply_lease=_Lease(),
    )
    first_delta = _delta(
        revision="one",
        movements=(
            ("lib/one.py", CodePackageDeltaKind.create, "one\n", None),
            ("lib/two.py", CodePackageDeltaKind.create, "two\n", None),
        ),
    )
    first_head = _materialization_head(
        delta=first_delta, body_store=body_store, revision=1
    )
    first_request = _request(
        root=root,
        head=first_head,
        materialization_revision=1,
        expected_output_revision=0,
    )
    assert applier.apply(
        admission=_admission(first_request, root), materialization=(1, first_head)
    ).status == "applied"

    successor_delta = _delta(
        revision="two",
        movements=(
            (
                "lib/one.py",
                CodePackageDeltaKind.update,
                "one-updated\n",
                _digest_bytes(b"one\n"),
            ),
            (
                "lib/three.py",
                CodePackageDeltaKind.create,
                "three\n",
                None,
            ),
            (
                "lib/two.py",
                CodePackageDeltaKind.delete,
                None,
                _digest_bytes(b"two\n"),
            ),
        ),
    )
    successor_head = _materialization_head(
        delta=successor_delta, body_store=body_store, revision=2
    )
    successor_request = _request(
        root=root,
        head=successor_head,
        materialization_revision=2,
        expected_output_revision=1,
    )
    successor = applier.apply(
        admission=_admission(successor_request, root),
        materialization=(2, successor_head),
    )
    assert successor.status == "applied"
    assert successor.receipt is not None
    assert successor.receipt.head.absent_paths == ("lib/two.py",)
    assert not (root / "lib/two.py").exists()

    (root / "lib/two.py").write_text("foreign resurrection\n")
    current_request = _request(
        root=root,
        head=successor_head,
        materialization_revision=2,
        expected_output_revision=2,
    )
    current = applier.apply(
        admission=_admission(current_request, root),
        materialization=(2, successor_head),
    )
    assert current.status == "conflicted"
    assert current.conflict_path == "lib/two.py"
    assert current.error_code == "current_output_reread_mismatch"


def test_revision_root_authority_and_request_codec_fail_closed(tmp_path: Path) -> None:
    root = (tmp_path / "checkout").resolve()
    root.mkdir()
    foreign_root = (tmp_path / "foreign").resolve()
    foreign_root.mkdir()
    body_store = _BodyStore()
    delta = _delta(
        revision="one",
        movements=(("one.py", CodePackageDeltaKind.create, "one\n", None),),
    )
    head = _materialization_head(delta=delta, body_store=body_store, revision=1)
    request = _request(
        root=root,
        head=head,
        materialization_revision=1,
        expected_output_revision=0,
    )
    wire = request.to_json_bytes()
    assert WorkspaceGeneratedOutputApplyRequest.from_json_bytes(wire) == request
    with pytest.raises(WorkspaceGeneratedOutputApplyError, match="not canonical"):
        WorkspaceGeneratedOutputApplyRequest.from_json_bytes(wire + b" ")
    payload = json.loads(wire)
    payload["output_body_digest"] = _digest("foreign-output")
    with pytest.raises(WorkspaceGeneratedOutputApplyError, match="digest mismatched"):
        WorkspaceGeneratedOutputApplyRequest.from_json_bytes(
            canonical_json_bytes(payload)
        )

    denied = _Authority(
        expected_request_digest=request.request_digest,
        checkout_root=foreign_root,
        admitted=False,
    )
    with pytest.raises(WorkspaceGeneratedOutputApplyError, match="did not admit"):
        admit_workspace_generated_output_apply(
            request=request,
            operation_authority=cast(WorkspaceGeneratedOutputApplyAuthority, denied),
        )
    applier = WorkspaceGeneratedOutputApplier(
        state_store=InMemoryLocalOperationalStateStore(),
        body_store=body_store,
        apply_lease=_Lease(),
    )
    with pytest.raises(WorkspaceGeneratedOutputApplyError, match="differs"):
        applier.apply(
            admission=_admission(request, root), materialization=(2, head)
        )
    assert list(root.iterdir()) == []
    assert list(foreign_root.iterdir()) == []


def test_forged_admission_symlink_root_and_staged_body_substitution_fail_closed(
    tmp_path: Path,
) -> None:
    root = (tmp_path / "checkout").resolve()
    root.mkdir()
    body_store = _BodyStore()
    delta = _delta(
        revision="one",
        movements=(("one.py", CodePackageDeltaKind.create, "one\n", None),),
    )
    head = _materialization_head(delta=delta, body_store=body_store, revision=1)
    request = _request(
        root=root,
        head=head,
        materialization_revision=1,
        expected_output_revision=0,
    )
    applier = WorkspaceGeneratedOutputApplier(
        state_store=InMemoryLocalOperationalStateStore(),
        body_store=body_store,
        apply_lease=_Lease(),
    )
    from aware_workspace_runtime.generated_output_apply import (
        WorkspaceGeneratedOutputApplyAdmission,
    )

    forged = object.__new__(WorkspaceGeneratedOutputApplyAdmission)
    with pytest.raises(WorkspaceGeneratedOutputApplyError, match="not registered"):
        applier.apply(admission=forged, materialization=(1, head))

    symlink_root = tmp_path / "checkout-link"
    symlink_root.symlink_to(root, target_is_directory=True)
    symlink_authority = _Authority(
        expected_request_digest=request.request_digest,
        checkout_root=symlink_root,
    )
    with pytest.raises(WorkspaceGeneratedOutputApplyError, match="direct directory"):
        admit_workspace_generated_output_apply(
            request=request,
            operation_authority=cast(
                WorkspaceGeneratedOutputApplyAuthority, symlink_authority
            ),
        )

    output_body_ref = _body_ref(head.outputs[0].body_digest)
    body_store.bodies[output_body_ref] += b" "
    with pytest.raises(WorkspaceGeneratedOutputApplyError, match="differs"):
        applier.apply(
            admission=_admission(request, root), materialization=(1, head)
        )
    assert list(root.iterdir()) == []


def test_effect_window_lease_denies_a_second_writer_before_preflight(
    tmp_path: Path,
) -> None:
    root = (tmp_path / "checkout").resolve()
    root.mkdir()
    body_store = _BodyStore()
    delta = _delta(
        revision="one",
        movements=(("one.py", CodePackageDeltaKind.create, "one\n", None),),
    )
    head = _materialization_head(delta=delta, body_store=body_store, revision=1)
    request = _request(
        root=root,
        head=head,
        materialization_revision=1,
        expected_output_revision=0,
    )
    lease_root = (tmp_path / "lease-state").resolve()
    lease_root.mkdir()
    owner_lease = FileWorkspaceGeneratedOutputApplyLease(lease_root)
    competing_lease = FileWorkspaceGeneratedOutputApplyLease(lease_root)
    assert owner_lease.acquire(request)
    applier = WorkspaceGeneratedOutputApplier(
        state_store=InMemoryLocalOperationalStateStore(),
        body_store=body_store,
        apply_lease=competing_lease,
    )
    result = applier.apply(
        admission=_admission(request, root), materialization=(1, head)
    )
    assert result.status == "conflicted"
    assert result.error_code == "generated_output_apply_lease_unavailable"
    assert result.metrics.preflight_count == 0
    assert result.metrics.mutation_count == 0
    assert result.metrics.lease_acquire_count == 0
    assert result.metrics.lease_release_count == 0
    assert list(root.iterdir()) == []
    owner_lease.release(request)
    assert competing_lease.acquire(request)
    competing_lease.release(request)


def test_durable_body_and_output_head_reconstruct_after_restart(tmp_path: Path) -> None:
    sqlite = pytest.importorskip("aware_local_service_state_sqlite")
    root = (tmp_path / "checkout").resolve()
    root.mkdir()
    state_root = (tmp_path / "state").resolve()
    body_store = DirectoryWorkspaceSemanticMaterializationBodyStore(
        state_root, repository_binding_ref="repository:test"
    )
    state_root.chmod(0o700)
    delta = _delta(
        revision="one",
        movements=(("one.py", CodePackageDeltaKind.create, "one\n", None),),
    )
    head = _materialization_head(delta=delta, body_store=body_store, revision=1)
    state_path = state_root / "generated-output.sqlite3"
    applier = WorkspaceGeneratedOutputApplier(
        state_store=sqlite.SqliteLocalOperationalStateStore(state_path),
        body_store=body_store,
        apply_lease=_Lease(),
    )
    request = _request(
        root=root,
        head=head,
        materialization_revision=1,
        expected_output_revision=0,
    )
    applied = applier.apply(
        admission=_admission(request, root), materialization=(1, head)
    )
    assert applied.status == "applied"
    reconstructed = WorkspaceGeneratedOutputApplier(
        state_store=sqlite.SqliteLocalOperationalStateStore(state_path),
        body_store=DirectoryWorkspaceSemanticMaterializationBodyStore(
            state_root, repository_binding_ref="repository:test"
        ),
        apply_lease=_Lease(),
    )
    assert reconstructed.read_head(
        package_ref=PACKAGE_REF,
        checkout_binding_ref="workspace-checkout:test",
    ) == applier.read_head(
        package_ref=PACKAGE_REF,
        checkout_binding_ref="workspace-checkout:test",
    )


def test_real_aware_development_sdk_apply_has_visible_performance_ceiling(
    tmp_path: Path,
) -> None:
    import statistics
    import sys
    import time

    repository_root = Path(__file__).resolve().parents[7]
    for source_root in (
        repository_root
        / "workspaces/aware_kernel/modules/sdk/libs/contract_runtime/python",
        repository_root
        / "workspaces/aware_kernel/modules/sdk/libs/contract_runtime_renderer/python",
        repository_root
        / "workspaces/aware_kernel/modules/sdk/libs/contract_runtime_source/python",
        repository_root
        / "workspaces/aware_network/modules/service/libs/local_service_state_sqlite",
    ):
        sys.path.insert(0, str(source_root))

    from aware_local_service_state_sqlite import SqliteLocalOperationalStateStore
    from aware_sdk_contract_runtime import (  # pyright: ignore[reportMissingImports]
        prepare_sdk_definition_effect,
    )
    from aware_sdk_contract_runtime_renderer import (  # pyright: ignore[reportMissingImports]
        render_admitted_sdk_code_package_delta,
    )
    from aware_sdk_contract_runtime_source import (  # pyright: ignore[reportMissingImports]
        materialize_sdk_source_contract,
    )

    source_root = (
        repository_root / "workspaces/aware_dev/modules/dev/sdks/aware_dev/aware"
    )
    sources = {
        path.name: path.read_text()
        for path in sorted(source_root.glob("*.aware"))
    }
    source = materialize_sdk_source_contract(
        sdk_toml_text=(source_root / "aware.sdk.toml").read_text(),
        source_text_by_path=sources,
        selected_operation_refs=(
            "aware_dev_sdk.release_observe",
            "aware_dev_sdk.release_request",
            "aware_dev_sdk.release_rollback",
            "aware_dev_sdk.release_status",
        ),
    )
    effect = prepare_sdk_definition_effect(None, source.definition_state)
    delta = render_admitted_sdk_code_package_delta(
        effect=effect,
        source_revision_id=source.source_digest,
        prior_output_state=CodePackageOutputState.empty(
            effect.result_state.manifest.sdk_ref
        ),
    )
    assert len(delta.paths) == 6
    assert sum(path.size_bytes or 0 for path in delta.paths) > 200_000

    durations_ms: list[float] = []
    final_metrics = None
    for index in range(10):
        sample_root = (tmp_path / f"sample-{index}").resolve()
        checkout_root = sample_root / "checkout"
        state_root = sample_root / "state"
        checkout_root.mkdir(parents=True)
        state_root.mkdir()
        state_root.chmod(0o700)
        body_store = DirectoryWorkspaceSemanticMaterializationBodyStore(
            state_root, repository_binding_ref=f"repository:sample:{index}"
        )
        head = _materialization_head(
            delta=delta,
            body_store=body_store,
            revision=1,
        )
        request = _request(
            root=checkout_root,
            head=head,
            materialization_revision=1,
            expected_output_revision=0,
            output_package_name=delta.package_name,
        )
        applier = WorkspaceGeneratedOutputApplier(
            state_store=SqliteLocalOperationalStateStore(
                state_root / "generated-output.sqlite3"
            ),
            body_store=body_store,
            apply_lease=FileWorkspaceGeneratedOutputApplyLease(state_root),
        )
        started = time.perf_counter_ns()
        result = applier.apply(
            admission=_admission(request, checkout_root),
            materialization=(1, head),
        )
        durations_ms.append((time.perf_counter_ns() - started) / 1_000_000)
        assert result.status == "applied"
        final_metrics = result.metrics

    median_ms = statistics.median(durations_ms)
    p95_ms = statistics.quantiles(
        durations_ms, n=20, method="inclusive"
    )[18]
    assert median_ms < 100.0, (median_ms, durations_ms)
    assert p95_ms < 100.0, (p95_ms, durations_ms)
    assert final_metrics is not None
    assert final_metrics.preflight_count == 6
    assert final_metrics.mutation_count == 6
    assert final_metrics.reread_count == 6
    assert final_metrics.head_cas_count == 1
    assert final_metrics.head_reread_count == 1
    assert final_metrics.lease_acquire_count == 1
    assert final_metrics.lease_release_count == 1
