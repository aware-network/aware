from __future__ import annotations

import asyncio
import copy
import hashlib
import json
from dataclasses import replace
from typing import cast

import pytest
from aware_code_package_delta_contract import (
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
    derive_code_package_output_state,
)
from aware_code_semantic_contract_runtime import (
    ConsumedRoleDeclaration,
    ContentDigest,
    ContractViolation,
    ExecutionPublicationSnapshot,
    PreparedSemanticEffectEnvelope,
    ProducedRoleDeclaration,
    ProfileInputDeclaration,
    ProfileStepDeclaration,
    ProviderDerivation,
    ProviderExecutionBinding,
    ProviderStepInvocation,
    RoleBinding,
    SemanticBody,
    SemanticBodyCodecBinding,
    SemanticConfigurationCoordinate,
    SemanticContractInvocation,
    SemanticContractProfileDeclaration,
    SemanticContractProviderDeclaration,
    SemanticContractRef,
    SemanticContractResult,
    SemanticContractRuntime,
    SemanticImpactCoordinate,
    SemanticImplementationCoordinate,
    SemanticOutputEnvelope,
    SemanticPackageCoordinate,
    SemanticTransitionEnvelope,
    SemanticValueCoordinate,
    TerminalStatus,
    TypedEmptyCoordinate,
    canonical_json_bytes,
)
from aware_local_service_runtime import (
    InMemoryLocalOperationalStateStore,
    LocalOperationalStateConflict,
)
from aware_workspace_runtime import semantic_materialization_publication as v5_wire
from aware_workspace_runtime.semantic_materialization_publication import (
    DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
    DirectoryWorkspaceSemanticMaterializationBodyStore,
    WorkspaceSemanticMaterializationOperationAuthority,
    WorkspaceSemanticMaterializationPublicationConflict,
    WorkspaceSemanticMaterializationPublicationError,
    WorkspaceSemanticMaterializationPublisher,
    WorkspaceMaterializationPackageOccurrenceV4,
    WorkspaceSemanticMaterializationHeadV4,
    WorkspaceSemanticMaterializationHeadRereadEvidenceV4,
    WorkspaceSemanticMaterializationOutputStateBindingV4,
    WorkspaceSemanticMaterializationPublicationReceiptV4,
    WorkspaceSemanticMaterializationRequest,
    WorkspaceSemanticMaterializationRequestV3,
    _body_ref,
    _parse_head_reread_evidence_v4_wire,
    _parse_publication_head_v4_wire,
    _parse_publication_receipt_v4_wire,
    admit_workspace_semantic_materialization,
)


def _digest(marker: str) -> ContentDigest:
    return ContentDigest(f"sha256:{marker * 64}")


SOURCE = SemanticContractRef("test.source", "1", _digest("1"))
RESULT = SemanticContractRef("test.result", "1", _digest("2"))
TRANSITION = SemanticContractRef("test.transition", "1", _digest("3"))
EFFECT = SemanticContractRef("test.effect", "1", _digest("4"))
OUTPUT = SemanticContractRef("aware.code.package-delta.v1", "1", _digest("5"))
PROVIDER = SemanticContractRef("test.provider", "1", _digest("6"))
CODEC_IMPLEMENTATION = SemanticImplementationCoordinate(
    "test-canonical-json-codec", _digest("7")
)
PROVIDER_IMPLEMENTATION = SemanticImplementationCoordinate(
    "test-semantic-provider", _digest("8")
)
PROVIDER_CONFIGURATION = SemanticConfigurationCoordinate(
    "test-semantic-provider.no-options", _digest("9")
)
MANIFEST_DIGEST = _digest("a")
OPERATION_DIGEST = _digest("b")


def _occurrence() -> WorkspaceMaterializationPackageOccurrenceV4:
    return WorkspaceMaterializationPackageOccurrenceV4(
        repository_ref="repository:test",
        workspace_ref="workspaces/test/aware.workspace.toml",
        module_ref="module:test",
        package_id="package-id:test",
        package_root="workspaces/test/modules/test/packages/sdk",
        manifest_relative_path="workspaces/test/modules/test/packages/sdk/aware.sdk.toml",
    )


class _JsonCodec:
    def __init__(self, contract: SemanticContractRef) -> None:
        self._contract = contract

    @property
    def contract(self) -> SemanticContractRef:
        return self._contract

    @property
    def implementation(self) -> SemanticImplementationCoordinate:
        return CODEC_IMPLEMENTATION

    def decode(self, canonical_body: bytes) -> object:
        value = json.loads(canonical_body)
        if canonical_json_bytes(value) != canonical_body:
            raise ContractViolation("body is not canonical JSON")
        return value

    def encode(self, value: object) -> bytes:
        return canonical_json_bytes(value)

    def decode_contextual(self, canonical_body: bytes, context) -> object:
        context.__post_init__()
        return self.decode(canonical_body)

    def encode_contextual(self, value: object, context) -> bytes:
        context.__post_init__()
        return self.encode(value)


def _coordinate(
    role: str, contract: SemanticContractRef, ref: str, body: bytes
) -> SemanticValueCoordinate:
    return SemanticValueCoordinate(
        role, contract, ref, ContentDigest.of_bytes(body), len(body)
    )


def _declaration() -> SemanticContractProviderDeclaration:
    return SemanticContractProviderDeclaration(
        provider_key="test-provider",
        provider_contract=PROVIDER,
        package_kinds=("sdk",),
        operation_kinds=("materialize",),
        consumed_roles=(ConsumedRoleDeclaration("source", (SOURCE,)),),
        result_role=ProducedRoleDeclaration("result", RESULT),
        transition_contract=TRANSITION,
        effect_role=ProducedRoleDeclaration("effect", EFFECT),
        effect_contract=EFFECT,
        output_roles=(ProducedRoleDeclaration("output", OUTPUT),),
        allows_typed_empty=True,
        counter_keys=("movements",),
    )


def _profile() -> SemanticContractProfileDeclaration:
    return SemanticContractProfileDeclaration(
        profile_ref="test-sdk-materialization",
        version="1",
        package_kinds=("sdk",),
        operation_kinds=("materialize",),
        inputs=(ProfileInputDeclaration("source", SOURCE),),
        providers=(_declaration(),),
        steps=(
            ProfileStepDeclaration(
                "test-step",
                "test-provider",
                (RoleBinding("source", "source"),),
            ),
        ),
        terminal_result_role="result",
        terminal_effect_role="effect",
        terminal_output_roles=("output",),
    )


class _Provider:
    @property
    def declaration(self) -> SemanticContractProviderDeclaration:
        return _declaration()

    async def derive(self, invocation: ProviderStepInvocation) -> ProviderDerivation:
        source = invocation.inputs[0].value
        assert type(source) is dict
        marker = source["source"]
        assert type(marker) is str
        impacts = (SemanticImpactCoordinate("test.sdk", "definition", marker),)
        if marker == "current":
            assert invocation.predecessor is not None
            candidate = invocation.predecessor.coordinate
            effect_body = canonical_json_bytes({"current": True})
            effect_coordinate = _coordinate(
                "effect", EFFECT, "effect-current", effect_body
            )
            effect = PreparedSemanticEffectEnvelope(
                provider_key="test-provider",
                effect_contract=EFFECT,
                transition_digest=ContentDigest.of_bytes(b"current"),
                base_state=invocation.invocation.predecessor,
                candidate_state=candidate,
                effect_body=effect_coordinate,
                renderer_inputs=(),
                impacts=impacts,
                work_counters=(("movements", 0),),
            )
            return ProviderDerivation(
                SemanticContractResult(
                    TerminalStatus.CURRENT,
                    invocation.invocation.digest,
                    current_result=candidate,
                    effect=effect,
                ),
                (SemanticBody(effect_coordinate, effect_body),),
            )

        result_body = canonical_json_bytes({"sdk": marker})
        transition_body = canonical_json_bytes({"movement": marker})
        effect_body = canonical_json_bytes({"render": marker})
        output_body = canonical_json_bytes({"paths": [f"{marker}.py"]})
        candidate = _coordinate("result", RESULT, f"definition-{marker}", result_body)
        transition_coordinate = _coordinate(
            "transition-body",
            TRANSITION,
            f"transition-{marker}",
            transition_body,
        )
        transition = SemanticTransitionEnvelope(
            provider_key="test-provider",
            result_contract=RESULT,
            transition_contract=TRANSITION,
            predecessor=invocation.invocation.predecessor,
            result=candidate,
            transition_body=transition_coordinate,
            impacts=impacts,
            input_closure_digest=invocation.input_closure_digest,
        )
        effect_coordinate = _coordinate(
            "effect", EFFECT, f"effect-{marker}", effect_body
        )
        effect = PreparedSemanticEffectEnvelope(
            provider_key="test-provider",
            effect_contract=EFFECT,
            transition_digest=transition.digest,
            base_state=invocation.invocation.predecessor,
            candidate_state=candidate,
            effect_body=effect_coordinate,
            renderer_inputs=(),
            impacts=impacts,
            work_counters=(("movements", 1),),
        )
        output_coordinate = _coordinate(
            "output", OUTPUT, f"output-{marker}", output_body
        )
        result = SemanticContractResult(
            TerminalStatus.DELTA,
            invocation.invocation.digest,
            transition=transition,
            effect=effect,
            outputs=(
                SemanticOutputEnvelope(
                    "test-provider", output_coordinate, effect.digest
                ),
            ),
        )
        bodies = (
            SemanticBody(candidate, result_body),
            SemanticBody(transition_coordinate, transition_body),
            SemanticBody(effect_coordinate, effect_body),
            SemanticBody(output_coordinate, output_body),
        )
        return ProviderDerivation(
            result,
            tuple(
                sorted(
                    bodies,
                    key=lambda item: canonical_json_bytes(item.coordinate.to_wire()),
                )
            ),
        )


def _runtime() -> SemanticContractRuntime:
    profile = _profile()
    codecs = {
        contract: _JsonCodec(contract)
        for contract in (SOURCE, RESULT, TRANSITION, EFFECT, OUTPUT)
    }
    return SemanticContractRuntime(profile, {"test-provider": _Provider()}, codecs)


def _invocation(
    marker: str,
    *,
    predecessor: SemanticValueCoordinate | None = None,
) -> tuple[SemanticContractInvocation, tuple[SemanticBody, ...]]:
    profile = _profile()
    source_body = canonical_json_bytes({"source": marker})
    source = _coordinate("source", SOURCE, f"source-{marker}", source_body)
    invocation = SemanticContractInvocation(
        invocation_ref=f"invocation-{marker}",
        idempotency_key=f"invocation-{marker}",
        profile_ref=profile.profile_ref,
        profile_digest=profile.digest,
        target_package=SemanticPackageCoordinate(
            "aware.sdk.demo", "sdk", MANIFEST_DIGEST
        ),
        operation_kind="materialize",
        inputs=(source,),
        predecessor=predecessor or TypedEmptyCoordinate(RESULT),
        dependencies=(),
        body_codec_bindings=tuple(
            SemanticBodyCodecBinding(contract, CODEC_IMPLEMENTATION)
            for contract in sorted(
                (SOURCE, RESULT, TRANSITION, EFFECT, OUTPUT),
                key=lambda item: canonical_json_bytes(item.to_wire()),
            )
        ),
        provider_bindings=(
            ProviderExecutionBinding(
                "test-provider", PROVIDER_IMPLEMENTATION, PROVIDER_CONFIGURATION
            ),
        ),
        requested_output_roles=() if marker == "current" else ("output",),
    )
    return invocation, (SemanticBody(source, source_body),)


async def _execute(
    runtime: SemanticContractRuntime,
    marker: str,
    *,
    predecessor: SemanticValueCoordinate | None = None,
    predecessor_body: bytes | None = None,
):
    invocation, bodies = _invocation(marker, predecessor=predecessor)
    completion = await runtime.execute(
        invocation,
        bodies,
        predecessor_body=(
            SemanticBody(predecessor, predecessor_body)
            if predecessor is not None and predecessor_body is not None
            else None
        ),
    )
    return invocation, completion


class _OperationAuthority:
    operation_ref = "workspace-operation:test-materialize"
    operation_digest = OPERATION_DIGEST.value

    def __init__(self, expected_request_digest: str) -> None:
        self.expected_request_digest = expected_request_digest
        self.calls = 0

    def admits(self, request: WorkspaceSemanticMaterializationRequest) -> bool:
        self.calls += 1
        return request.request_digest == self.expected_request_digest


class _BodyStore:
    def __init__(self) -> None:
        self.bodies: dict[str, bytes] = {}
        self.substitute_reads = False

    def store_body(self, body_ref: str, canonical_body: bytes) -> None:
        current = self.bodies.get(body_ref)
        if current is not None and current != canonical_body:
            raise AssertionError("body identity collision")
        self.bodies[body_ref] = canonical_body

    def store_bodies(self, bodies: tuple[tuple[str, bytes], ...]) -> None:
        for body_ref, canonical_body in bodies:
            self.store_body(body_ref, canonical_body)

    def read_body(self, body_ref: str) -> bytes | None:
        body = self.bodies.get(body_ref)
        if body is not None and self.substitute_reads:
            return body + b" "
        return body


def _admission(invocation: SemanticContractInvocation):
    request = WorkspaceSemanticMaterializationRequest.create(
        package_ref=invocation.target_package.package_ref,
        package_kind=invocation.target_package.package_kind,
        manifest_digest=invocation.target_package.manifest_digest.value,
        source_authority_ref=f"workspace-source:{invocation.invocation_ref}",
        source_authority_digest=ContentDigest.of_bytes(
            canonical_json_bytes([item.to_wire() for item in invocation.inputs])
        ).value,
        operation_ref=_OperationAuthority.operation_ref,
        operation_digest=_OperationAuthority.operation_digest,
        profile_ref=invocation.profile_ref,
        profile_digest=invocation.profile_digest.value,
        invocation_digest=invocation.digest.value,
    )
    authority = _OperationAuthority(request.request_digest)
    admission = admit_workspace_semantic_materialization(
        request=request, operation_authority=authority
    )
    assert authority.calls == 1
    return admission


def test_genesis_stages_exact_terminal_closure_and_rereads_one_head() -> None:
    async def prove() -> None:
        runtime = _runtime()
        invocation, completion = await _execute(runtime, "one")
        bodies = _BodyStore()
        publisher = WorkspaceSemanticMaterializationPublisher(
            runtime=runtime,
            state_store=InMemoryLocalOperationalStateStore(),
            body_store=bodies,
        )
        publication = publisher.publish(
            admission=_admission(invocation),
            invocation=invocation,
            completion=completion,
            expected_head_revision=0,
        )
        receipt = publication.receipt
        assert receipt.head_advanced
        assert receipt.head_revision == 1
        assert receipt.head.output_activation == "staged_not_applied"
        assert len(receipt.observed_semantic_bodies) == 4
        assert publication.metrics.body_write_count == 5
        assert publication.metrics.body_reread_count == 5
        assert publication.metrics.head_cas_count == 1
        assert publication.metrics.head_reread_count == 1
        assert publisher.read_head("aware.sdk.demo") == (1, receipt.head)

    asyncio.run(prove())


def test_graph_only_publisher_uses_selected_snapshot_without_global_runtime() -> None:
    _runtime, invocation, request, snapshot = _graph_v2_fixture(
        expected_revision=0, marker="8"
    )
    publisher = WorkspaceSemanticMaterializationPublisher(
        state_store=InMemoryLocalOperationalStateStore(),
        body_store=_BodyStore(),
    )
    receipt, reread = publisher._publish_graph_v2(
        request=request, snapshot=snapshot, invocation=invocation
    )
    assert receipt.head_revision == 1
    assert reread.materialization_head_revision == 1


def test_graph_only_publisher_refuses_legacy_completion_entrance() -> None:
    async def prove() -> None:
        runtime = _runtime()
        invocation, completion = await _execute(runtime, "graph-only")
        publisher = WorkspaceSemanticMaterializationPublisher(
            state_store=InMemoryLocalOperationalStateStore(),
            body_store=_BodyStore(),
        )
        with pytest.raises(
            WorkspaceSemanticMaterializationPublicationError,
            match="direct publication requires its original Code runtime",
        ):
            publisher.publish(
                admission=_admission(invocation),
                invocation=invocation,
                completion=completion,
                expected_head_revision=0,
            )

    asyncio.run(prove())


def test_successor_requires_exact_head_predecessor_and_advances_contiguously() -> None:
    async def prove() -> None:
        runtime = _runtime()
        state = InMemoryLocalOperationalStateStore()
        publisher = WorkspaceSemanticMaterializationPublisher(
            runtime=runtime, state_store=state, body_store=_BodyStore()
        )
        first_call, first_completion = await _execute(runtime, "one")
        publisher.publish(
            admission=_admission(first_call),
            invocation=first_call,
            completion=first_completion,
            expected_head_revision=0,
        )
        assert first_completion.result.transition is not None
        predecessor = first_completion.result.transition.result
        predecessor_body = first_completion.body_for(predecessor).canonical_body
        second_call, second_completion = await _execute(
            runtime,
            "two",
            predecessor=predecessor,
            predecessor_body=predecessor_body,
        )
        second = publisher.publish(
            admission=_admission(second_call),
            invocation=second_call,
            completion=second_completion,
            expected_head_revision=1,
        )
        assert second.receipt.head_revision == 2
        assert second.receipt.prior_head_revision == 1
        assert second.receipt.head.candidate.value_ref == "definition-two"

        stale_predecessor = replace(predecessor, value_ref="foreign")
        stale_call, stale_completion = await _execute(
            runtime,
            "three",
            predecessor=stale_predecessor,
            predecessor_body=predecessor_body,
        )
        with pytest.raises(
            WorkspaceSemanticMaterializationPublicationConflict,
            match="predecessor differs",
        ):
            publisher.publish(
                admission=_admission(stale_call),
                invocation=stale_call,
                completion=stale_completion,
                expected_head_revision=2,
            )

    asyncio.run(prove())


def test_genesis_and_successor_exact_retry_reconstruct_advanced_receipt() -> None:
    async def prove() -> None:
        runtime = _runtime()
        state = InMemoryLocalOperationalStateStore()
        publisher = WorkspaceSemanticMaterializationPublisher(
            runtime=runtime, state_store=state, body_store=_BodyStore()
        )
        first_invocation, first_completion = await _execute(runtime, "one")
        first_admission = _admission(first_invocation)
        first = publisher.publish(
            admission=first_admission,
            invocation=first_invocation,
            completion=first_completion,
            expected_head_revision=0,
        )
        first_retry = publisher.publish(
            admission=first_admission,
            invocation=first_invocation,
            completion=first_completion,
            expected_head_revision=0,
        )
        assert first_retry.receipt == first.receipt
        assert first_retry.receipt.head_advanced is True
        assert first_retry.metrics.head_cas_count == 0
        assert first_retry.metrics.head_reread_count == 1
        assert first_retry.metrics.body_reread_count == first.metrics.body_reread_count

        assert first_completion.result.transition is not None
        predecessor = first_completion.result.transition.result
        predecessor_body = first_completion.body_for(predecessor).canonical_body
        second_invocation, second_completion = await _execute(
            runtime,
            "two",
            predecessor=predecessor,
            predecessor_body=predecessor_body,
        )
        second_admission = _admission(second_invocation)
        second = publisher.publish(
            admission=second_admission,
            invocation=second_invocation,
            completion=second_completion,
            expected_head_revision=1,
        )
        second_retry = publisher.publish(
            admission=second_admission,
            invocation=second_invocation,
            completion=second_completion,
            expected_head_revision=1,
        )
        assert second_retry.receipt == second.receipt
        assert second_retry.receipt.prior_head_revision == 1
        assert second_retry.receipt.head_revision == 2
        assert second_retry.metrics.head_cas_count == 0
        assert publisher.read_head("aware.sdk.demo") == (
            2,
            second.receipt.head,
        )

    asyncio.run(prove())


def test_exact_retry_rejects_different_completion_request_and_predecessor() -> None:
    async def prove() -> None:
        runtime = _runtime()
        publisher = WorkspaceSemanticMaterializationPublisher(
            runtime=runtime,
            state_store=InMemoryLocalOperationalStateStore(),
            body_store=_BodyStore(),
        )
        first_invocation, first_completion = await _execute(runtime, "one")
        publisher.publish(
            admission=_admission(first_invocation),
            invocation=first_invocation,
            completion=first_completion,
            expected_head_revision=0,
        )

        different_invocation, different_completion = await _execute(runtime, "two")
        with pytest.raises(
            WorkspaceSemanticMaterializationPublicationConflict,
            match="differs from exact retry",
        ):
            publisher.publish(
                admission=_admission(different_invocation),
                invocation=different_invocation,
                completion=different_completion,
                expected_head_revision=0,
            )

        assert first_completion.result.transition is not None
        predecessor = replace(
            first_completion.result.transition.result,
            value_ref="substituted-predecessor",
        )
        predecessor_body = first_completion.body_for(
            first_completion.result.transition.result
        ).canonical_body
        substituted_invocation, substituted_completion = await _execute(
            runtime,
            "two",
            predecessor=predecessor,
            predecessor_body=predecessor_body,
        )
        with pytest.raises(
            WorkspaceSemanticMaterializationPublicationConflict,
            match="differs from exact retry",
        ):
            publisher.publish(
                admission=_admission(substituted_invocation),
                invocation=substituted_invocation,
                completion=substituted_completion,
                expected_head_revision=0,
            )

    asyncio.run(prove())


def test_current_rereads_without_advancing_head() -> None:
    async def prove() -> None:
        runtime = _runtime()
        publisher = WorkspaceSemanticMaterializationPublisher(
            runtime=runtime,
            state_store=InMemoryLocalOperationalStateStore(),
            body_store=_BodyStore(),
        )
        first_call, first_completion = await _execute(runtime, "one")
        first = publisher.publish(
            admission=_admission(first_call),
            invocation=first_call,
            completion=first_completion,
            expected_head_revision=0,
        )
        predecessor = first.receipt.head.candidate
        coordinate = first_completion.result.transition.result
        assert coordinate is not None
        current_call, current_completion = await _execute(
            runtime,
            "current",
            predecessor=coordinate,
            predecessor_body=first_completion.body_for(coordinate).canonical_body,
        )
        current = publisher.publish(
            admission=_admission(current_call),
            invocation=current_call,
            completion=current_completion,
            expected_head_revision=1,
        )
        assert current.receipt.head == first.receipt.head
        assert not current.receipt.head_advanced
        assert current.metrics.head_cas_count == 0
        assert current.metrics.head_reread_count == 1
        assert predecessor == current.receipt.head.candidate
        current_retry = publisher.publish(
            admission=_admission(current_call),
            invocation=current_call,
            completion=current_completion,
            expected_head_revision=1,
        )
        assert current_retry.receipt == current.receipt
        assert current_retry.receipt.head_advanced is False
        assert current_retry.metrics.head_cas_count == 0

    asyncio.run(prove())


def test_foreign_runtime_stale_revision_and_body_substitution_fail_closed() -> None:
    async def prove() -> None:
        runtime = _runtime()
        invocation, completion = await _execute(runtime, "one")
        body_store = _BodyStore()
        state = InMemoryLocalOperationalStateStore()
        publisher = WorkspaceSemanticMaterializationPublisher(
            runtime=runtime, state_store=state, body_store=body_store
        )
        foreign = WorkspaceSemanticMaterializationPublisher(
            runtime=_runtime(), state_store=state, body_store=body_store
        )
        with pytest.raises(
            WorkspaceSemanticMaterializationPublicationError,
            match="does not own",
        ):
            foreign.publish(
                admission=_admission(invocation),
                invocation=invocation,
                completion=completion,
                expected_head_revision=0,
            )
        body_store.substitute_reads = True
        with pytest.raises(
            WorkspaceSemanticMaterializationPublicationError,
            match="reread differs",
        ):
            publisher.publish(
                admission=_admission(invocation),
                invocation=invocation,
                completion=completion,
                expected_head_revision=0,
            )
        assert publisher.read_head("aware.sdk.demo") is None

        body_store.substitute_reads = False
        publisher.publish(
            admission=_admission(invocation),
            invocation=invocation,
            completion=completion,
            expected_head_revision=0,
        )
        with pytest.raises(
            WorkspaceSemanticMaterializationPublicationConflict,
            match="expected head revision",
        ):
            publisher.publish(
                admission=_admission(invocation),
                invocation=invocation,
                completion=completion,
                expected_head_revision=3,
            )

    asyncio.run(prove())


def test_request_and_invocation_substitution_fail_before_staging() -> None:
    async def prove() -> None:
        runtime = _runtime()
        invocation, completion = await _execute(runtime, "one")
        bodies = _BodyStore()
        publisher = WorkspaceSemanticMaterializationPublisher(
            runtime=runtime,
            state_store=InMemoryLocalOperationalStateStore(),
            body_store=bodies,
        )
        admission = _admission(invocation)
        object.__setattr__(invocation.target_package, "manifest_digest", _digest("f"))
        with pytest.raises(
            (ContractViolation, WorkspaceSemanticMaterializationPublicationError)
        ):
            publisher.publish(
                admission=admission,
                invocation=invocation,
                completion=completion,
                expected_head_revision=0,
            )
        assert bodies.bodies == {}

    asyncio.run(prove())


def test_operation_authority_is_required_and_exact() -> None:
    invocation, _ = _invocation("one")
    request = WorkspaceSemanticMaterializationRequest.create(
        package_ref=invocation.target_package.package_ref,
        package_kind=invocation.target_package.package_kind,
        manifest_digest=invocation.target_package.manifest_digest.value,
        source_authority_ref="workspace-source:test",
        source_authority_digest=_digest("c").value,
        operation_ref=_OperationAuthority.operation_ref,
        operation_digest=_OperationAuthority.operation_digest,
        profile_ref=invocation.profile_ref,
        profile_digest=invocation.profile_digest.value,
        invocation_digest=invocation.digest.value,
    )
    denied = _OperationAuthority(_digest("d").value)
    denied_authority = cast(WorkspaceSemanticMaterializationOperationAuthority, denied)
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="did not admit",
    ):
        admit_workspace_semantic_materialization(
            request=request, operation_authority=denied_authority
        )


def test_materialization_request_codec_is_strict_and_byte_canonical() -> None:
    invocation, _ = _invocation("one")
    request = WorkspaceSemanticMaterializationRequest.create(
        package_ref=invocation.target_package.package_ref,
        package_kind=invocation.target_package.package_kind,
        manifest_digest=invocation.target_package.manifest_digest.value,
        source_authority_ref="workspace-source:test",
        source_authority_digest=_digest("c").value,
        operation_ref=_OperationAuthority.operation_ref,
        operation_digest=_OperationAuthority.operation_digest,
        profile_ref=invocation.profile_ref,
        profile_digest=invocation.profile_digest.value,
        invocation_digest=invocation.digest.value,
    )
    wire = request.to_json_bytes()
    assert WorkspaceSemanticMaterializationRequest.from_json_bytes(wire) == request
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="not canonical",
    ):
        WorkspaceSemanticMaterializationRequest.from_json_bytes(wire + b" ")
    payload = json.loads(wire)
    payload["manifest_digest"] = _digest("d").value
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="digest mismatched",
    ):
        WorkspaceSemanticMaterializationRequest.from_json_bytes(
            canonical_json_bytes(payload)
        )
    payload = json.loads(wire)
    payload["unknown"] = "poison"
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="fields differ",
    ):
        WorkspaceSemanticMaterializationRequest.from_json_bytes(
            canonical_json_bytes(payload)
        )


def test_durable_sqlite_head_reconstructs_exactly(tmp_path) -> None:
    sqlite = pytest.importorskip("aware_local_service_state_sqlite")

    async def prove() -> None:
        runtime = _runtime()
        invocation, completion = await _execute(runtime, "one")
        body_store = DirectoryWorkspaceSemanticMaterializationBodyStore(
            tmp_path.resolve(), repository_binding_ref="repository:test"
        )
        state_path = tmp_path / "semantic-materialization.sqlite3"
        publisher = WorkspaceSemanticMaterializationPublisher(
            runtime=runtime,
            state_store=sqlite.SqliteLocalOperationalStateStore(state_path),
            body_store=body_store,
        )
        publication = publisher.publish(
            admission=_admission(invocation),
            invocation=invocation,
            completion=completion,
            expected_head_revision=0,
        )
        reconstructed_store = DirectoryWorkspaceSemanticMaterializationBodyStore(
            tmp_path.resolve(), repository_binding_ref="repository:test"
        )
        reconstructed = WorkspaceSemanticMaterializationPublisher(
            runtime=runtime,
            state_store=sqlite.SqliteLocalOperationalStateStore(state_path),
            body_store=reconstructed_store,
        )
        assert reconstructed.read_head("aware.sdk.demo") == (
            1,
            publication.receipt.head,
        )
        for staged in publication.receipt.observed_semantic_bodies:
            assert reconstructed_store.read_body(staged.body_ref) is not None

    asyncio.run(prove())


def _graph_v2_request(
    *,
    expected_revision: int,
    marker: str,
    snapshot: ExecutionPublicationSnapshot,
) -> WorkspaceSemanticMaterializationRequestV3:
    result = snapshot.result
    coordinate = (
        result.current_result
        if result.current_result is not None
        else None
        if result.transition is None
        else result.transition.result
    )
    assert coordinate is not None
    return WorkspaceSemanticMaterializationRequestV3.create(
        package=SemanticPackageCoordinate("aware.sdk.demo", "sdk", MANIFEST_DIGEST),
        result_coordinate=coordinate,
        source_identity_digest=_digest(marker),
        code_intent_digest=ContentDigest.of_bytes(f"intent:{marker}".encode()),
        code_match_digest=ContentDigest.of_bytes(f"match:{marker}".encode()),
        planning_input_digest=ContentDigest.of_bytes(f"planning:{marker}".encode()),
        execution_input_closure_digest=ContentDigest.of_bytes(
            f"closure:{marker}".encode()
        ),
        operation_result_digest=snapshot.result_digest,
        expected_head_revision=expected_revision,
    )


def _graph_v2_fixture(
    *, expected_revision: int, marker: str
) -> tuple[
    SemanticContractRuntime,
    SemanticContractInvocation,
    WorkspaceSemanticMaterializationRequestV3,
    ExecutionPublicationSnapshot,
]:
    runtime = _runtime()
    invocation, completion = asyncio.run(_execute(runtime, marker))
    snapshot = runtime.snapshot_completion(completion)
    return (
        runtime,
        invocation,
        _graph_v2_request(
            expected_revision=expected_revision,
            marker=marker,
            snapshot=snapshot,
        ),
        snapshot,
    )


def test_state_bound_head_v4_preserves_v3_result_and_rejects_substitution() -> None:
    _runtime_value, _invocation, request, snapshot = _graph_v2_fixture(
        expected_revision=2, marker="a"
    )
    output_coordinate = snapshot.result.outputs[0].output
    prior_body = canonical_json_bytes({"state": "prior"})
    prior_body_digest = ContentDigest.of_bytes(prior_body)
    state_body = canonical_json_bytes({"state": "retained"})
    state_body_digest = ContentDigest.of_bytes(state_body)
    binding = WorkspaceSemanticMaterializationOutputStateBindingV4(
        output_coordinate=output_coordinate,
        output_state_name="aware_dev_sdk",
        prior_state_body_ref=_body_ref(prior_body_digest.value),
        prior_state_body_digest=prior_body_digest,
        prior_state_body_size=len(prior_body),
        prior_state_digest=ContentDigest.of_bytes(b"prior CodePackageOutputState"),
        state_body_ref=_body_ref(state_body_digest.value),
        state_body_digest=state_body_digest,
        state_body_size=len(state_body),
        state_digest=ContentDigest.of_bytes(b"CodePackageOutputState"),
    )
    head = WorkspaceSemanticMaterializationHeadV4.create(
        request=request,
        package_occurrence=_occurrence(),
        predecessor_head_digest=ContentDigest.of_bytes(b"predecessor-head"),
        operation_ref="materialize:demo",
        operation_digest=OPERATION_DIGEST,
        output_state_bindings=(binding,),
    )
    assert _parse_publication_head_v4_wire(head.to_wire()) == head
    assert head.base_head.request == request
    assert head.base_head.result_coordinate == request.result_coordinate
    assert (
        head.to_wire()["contract"]
        == "aware.workspace.semantic-materialization-head.v4"
    )
    missing_predecessor = head.to_wire()
    del missing_predecessor["predecessor_head_digest"]
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        _parse_publication_head_v4_wire(missing_predecessor)

    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="body ref differs",
    ):
        replace(
            binding,
            state_body_ref=_body_ref(ContentDigest.of_bytes(b"other").value),
        )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="prior body ref differs",
    ):
        replace(binding, prior_state_body_ref=_body_ref(state_body_digest.value))
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="role-unique",
    ):
        WorkspaceSemanticMaterializationHeadV4.create(
            request=request,
            package_occurrence=_occurrence(),
            predecessor_head_digest=ContentDigest.of_bytes(b"predecessor-head"),
            operation_ref="materialize:demo",
            operation_digest=OPERATION_DIGEST,
            output_state_bindings=(binding, binding),
        )
    tampered = head.to_wire()
    tampered["operation_ref"] = "materialize:other"
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="differs from fresh derivation",
    ):
        _parse_publication_head_v4_wire(tampered)
    wrong_occurrence = head.to_wire()
    wrong_occurrence["package_occurrence"]["package_id"] = "package-id:other"
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="differs from fresh derivation",
    ):
        _parse_publication_head_v4_wire(wrong_occurrence)
    unbound_legacy = head.to_wire()
    del unbound_legacy["package_occurrence"]
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        _parse_publication_head_v4_wire(unbound_legacy)


def test_state_bound_v4_evidence_names_actual_head_and_rejects_substitution() -> None:
    _runtime, request, head, _bodies, _state, _prior, _invocation, _snapshot = (
        _state_bound_head_fixture()
    )
    receipt = WorkspaceSemanticMaterializationPublicationReceiptV4.create(
        request=request,
        head=head,
        prior_head_revision=3,
        head_revision=4,
        head_advanced=True,
    )
    reread = WorkspaceSemanticMaterializationHeadRereadEvidenceV4.create(
        observation_role="package_result",
        materialization_head_revision=4,
        head=head,
    )
    assert receipt.canonical_head_wire_digest == reread.canonical_head_wire_digest
    assert reread.materialization_head_digest == head.head_digest
    assert reread.materialization_head_digest != head.base_head.head_digest
    assert receipt.to_wire()["head"]["contract"] == head.to_wire()["contract"]
    assert reread.to_wire()["head"]["head_digest"] == head.head_digest.value
    assert _parse_publication_receipt_v4_wire(receipt.to_wire()) == receipt
    assert _parse_head_reread_evidence_v4_wire(reread.to_wire()) == reread

    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="revision is not contiguous",
    ):
        WorkspaceSemanticMaterializationPublicationReceiptV4.create(
            request=request,
            head=head,
            prior_head_revision=3,
            head_revision=5,
            head_advanced=True,
        )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="head wire digest differs",
    ):
        replace(receipt, canonical_head_wire_digest=head.base_head.head_digest)
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="differs from actual head",
    ):
        replace(reread, materialization_head_digest=head.base_head.head_digest)
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="observation role unsupported",
    ):
        WorkspaceSemanticMaterializationHeadRereadEvidenceV4.create(
            observation_role="invented",
            materialization_head_revision=4,
            head=head,
        )
    copied_receipt = receipt.to_wire()
    copied_receipt["canonical_head_wire_digest"] = head.base_head.head_digest.value
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="differs from fresh derivation",
    ):
        _parse_publication_receipt_v4_wire(copied_receipt)
    copied_reread = reread.to_wire()
    copied_reread["materialization_head_digest"] = head.base_head.head_digest.value
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="differs from fresh derivation",
    ):
        _parse_head_reread_evidence_v4_wire(copied_reread)


def _state_bound_head_fixture(*, selected_output_matches: bool = True):
    runtime, invocation, request, snapshot = _graph_v2_fixture(
        expected_revision=0, marker="a"
    )
    prior = CodePackageOutputState.empty("aware_dev_sdk")
    content = "value = 1\n"
    content_body = content.encode()
    producer = CodePackageDeltaProducerRef(
        "sdk-definition",
        "sdk-renderer-v1",
        "semantic_contract_renderer",
        FrozenJsonObject.from_mapping(
            {"prior_output_state_digest": prior.state_digest}
        ),
    )
    provisional = CodePackageDeltaProduction(
        producer=producer,
        input_digest=ContentDigest.of_bytes(b"effect").value,
    )
    provisional_path = CodePackageDeltaPath(
        "generated.py",
        CodePackageDeltaKind.create,
        content,
        None,
        ContentDigest.of_bytes(content_body).value,
        len(content_body),
        CodeLanguage.python,
        True,
        CodePackagePathRole.generated_code,
        provisional,
        FrozenJsonObject.from_mapping({}),
    )
    source_revision = ContentDigest.of_bytes(b"sdk-source").value
    output_digest = code_package_delta_output_digest(
        package_name="aware_dev_sdk",
        authority=CodePackageDeltaAuthorityKind.code_package_delta,
        authority_kind=CodePackageDeltaAuthorityKind.code_package_delta.value,
        source_revision_id=source_revision,
        production=provisional,
        paths=(provisional_path,),
    )
    production = replace(provisional, output_digest=output_digest)
    delta = CodePackageDelta(
        "aware_dev_sdk",
        CodePackageDeltaAuthorityKind.code_package_delta,
        CodePackageDeltaAuthorityKind.code_package_delta.value,
        source_revision,
        production,
        (replace(provisional_path, production=production),),
    )
    state = derive_code_package_output_state(prior, delta)
    prior_body = prior.to_json_bytes()
    state_body = state.to_json_bytes()
    delta_body = delta.to_json_bytes()
    output_coordinate = _coordinate("output", OUTPUT, "sdk-delta", delta_body)
    effect = snapshot.result.effect
    assert effect is not None
    selected_result = replace(
        snapshot.result,
        outputs=(
            SemanticOutputEnvelope(
                "test-provider",
                (
                    output_coordinate
                    if selected_output_matches
                    else snapshot.result.outputs[0].output
                ),
                effect.digest,
            ),
        ),
    )
    request = WorkspaceSemanticMaterializationRequestV3.create(
        package=request.package,
        result_coordinate=request.result_coordinate,
        source_identity_digest=request.source_identity_digest,
        code_intent_digest=request.code_intent_digest,
        code_match_digest=request.code_match_digest,
        planning_input_digest=request.planning_input_digest,
        execution_input_closure_digest=request.execution_input_closure_digest,
        operation_result_digest=selected_result.digest,
        expected_head_revision=request.expected_head_revision,
    )
    binding = WorkspaceSemanticMaterializationOutputStateBindingV4(
        output_coordinate=output_coordinate,
        output_state_name="aware_dev_sdk",
        prior_state_body_ref=_body_ref(ContentDigest.of_bytes(prior_body).value),
        prior_state_body_digest=ContentDigest.of_bytes(prior_body),
        prior_state_body_size=len(prior_body),
        prior_state_digest=ContentDigest(prior.state_digest),
        state_body_ref=_body_ref(ContentDigest.of_bytes(state_body).value),
        state_body_digest=ContentDigest.of_bytes(state_body),
        state_body_size=len(state_body),
        state_digest=ContentDigest(state.state_digest),
    )
    head = WorkspaceSemanticMaterializationHeadV4.create(
        request=request,
        package_occurrence=_occurrence(),
        operation_ref="materialize:sdk",
        operation_digest=OPERATION_DIGEST,
        output_state_bindings=(binding,),
    )
    bodies = _BodyStore()
    for body in (prior_body, state_body, delta_body):
        bodies.store_body(_body_ref(ContentDigest.of_bytes(body).value), body)
    result_body = snapshot.body_for(request.result_coordinate).canonical_body
    bodies.store_body(_body_ref(request.result_coordinate.digest.value), result_body)
    selected_wire = selected_result.to_wire()
    selected_wire.pop("digest")
    bodies.store_body(
        _body_ref(selected_result.digest.value), canonical_json_bytes(selected_wire)
    )
    invocation_wire = invocation.to_wire()
    invocation_wire.pop("digest")
    bodies.store_body(
        _body_ref(invocation.digest.value), canonical_json_bytes(invocation_wire)
    )
    prepared_bodies = tuple(
        sorted(
            (*snapshot.bodies, SemanticBody(output_coordinate, delta_body)),
            key=lambda item: canonical_json_bytes(item.coordinate.to_wire()),
        )
    )
    selected_snapshot = ExecutionPublicationSnapshot(
        invocation_digest=invocation.digest,
        profile_digest=invocation.profile_digest,
        result=selected_result,
        result_digest=selected_result.digest,
        result_wire=canonical_json_bytes(selected_result.to_wire()),
        effect_digest=snapshot.effect_digest,
        transition_digest=snapshot.transition_digest,
        bodies=prepared_bodies,
    )
    return runtime, request, head, bodies, state, prior, invocation, selected_snapshot


def test_state_bound_head_v4_rechecks_prior_delta_and_state_after_restart() -> None:
    _runtime, _request, head, bodies, state, _prior, _invocation, _snapshot = (
        _state_bound_head_fixture()
    )
    reader = WorkspaceSemanticMaterializationPublisher(
        state_store=InMemoryLocalOperationalStateStore(),
        body_store=bodies,
    )
    assert reader._read_graph_v4_output_state(
        head, output_role="output"
    ) == state
    bodies.substitute_reads = True
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="missing or changed",
    ):
        reader._read_graph_v4_output_state(
            head, output_role="output"
        )


def test_current_v4_reader_binds_selected_result_and_exact_head() -> None:
    _runtime, request, head, bodies, state, _prior, _invocation, _snapshot = (
        _state_bound_head_fixture()
    )
    store = InMemoryLocalOperationalStateStore()
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        request.package.package_ref,
        expected_revision=0,
        value=head.to_wire(),
    )
    publisher = WorkspaceSemanticMaterializationPublisher(
        state_store=store, body_store=bodies
    )
    expected = dict(
        package=request.package,
        expected_head_revision=1,
        expected_head_digest=head.head_digest,
        declaration=_declaration(),
        output_role="output",
        output_state_name="aware_dev_sdk",
    )
    assert publisher._read_graph_v4_current_output_state(**expected) == state
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="original admission",
    ):
        publisher._read_graph_v4_current_output_state(
            **{**expected, "expected_head_revision": 0}
        )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="output name differs",
    ):
        publisher._read_graph_v4_current_output_state(
            **{**expected, "output_state_name": "other_sdk"}
        )
    bodies.substitute_reads = True
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        publisher._read_graph_v4_current_output_state(**expected)

    _runtime, request, head, bodies, _state, _prior, _invocation, _snapshot = (
        _state_bound_head_fixture(selected_output_matches=False)
    )
    mismatched_store = InMemoryLocalOperationalStateStore()
    mismatched_store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        request.package.package_ref,
        expected_revision=0,
        value=head.to_wire(),
    )
    mismatched_reader = WorkspaceSemanticMaterializationPublisher(
        state_store=mismatched_store, body_store=bodies
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="selected Code result",
    ):
        mismatched_reader._read_graph_v4_current_output_state(
            **{**expected, "expected_head_digest": head.head_digest}
        )


def test_state_bound_v4_reread_checks_retained_bodies_and_actual_head() -> None:
    runtime, _request, head, bodies, _state, _prior, _invocation, _snapshot = (
        _state_bound_head_fixture()
    )
    store = InMemoryLocalOperationalStateStore()
    package_ref = head.base_head.package.package_ref
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        package_ref,
        expected_revision=0,
        value=cast(dict, head.to_wire()),
    )
    reader = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=store, body_store=bodies
    )
    evidence = reader._read_graph_v4_head_evidence(
        package_ref, observation_role="package_result"
    )
    assert evidence is not None
    assert evidence.head == head
    assert evidence.materialization_head_revision == 1
    assert evidence.materialization_head_digest == head.head_digest
    bodies.substitute_reads = True
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="missing or changed",
    ):
        reader._read_graph_v4_head_evidence(
            package_ref, observation_role="package_result"
        )


def test_package_head_occurrence_observation_revalidates_original_namespace() -> None:
    store = InMemoryLocalOperationalStateStore()
    publisher = WorkspaceSemanticMaterializationPublisher(
        state_store=store, body_store=_BodyStore()
    )
    target = _occurrence()
    _runtime, _request, head, _bodies, *_rest = _state_bound_head_fixture()
    package = head.base_head.package
    empty = publisher._observe_v4_occurrence_absence(package, target)
    publisher._validate_v4_occurrence_absence(empty, package, target)

    package_ref = head.base_head.package.package_ref
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        package_ref,
        expected_revision=0,
        value=cast(dict, head.to_wire()),
    )
    with pytest.raises(LocalOperationalStateConflict):
        publisher._validate_v4_occurrence_absence(empty, package, target)
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="lineage already exists",
    ):
        publisher._observe_v4_occurrence_absence(package, target)

    unrelated = replace(target, package_id="package-id:unrelated")
    unrelated_package = SemanticPackageCoordinate(
        "aware.sdk.unrelated", "sdk", MANIFEST_DIGEST
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="selected package head already exists",
    ):
        publisher._observe_v4_occurrence_absence(package, unrelated)
    observed = publisher._observe_v4_occurrence_absence(unrelated_package, unrelated)
    publisher._validate_v4_occurrence_absence(
        observed, unrelated_package, unrelated
    )
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        package_ref,
        expected_revision=1,
        value=cast(dict, head.to_wire()),
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="lineage history is unavailable",
    ):
        publisher._observe_v4_occurrence_absence(unrelated_package, unrelated)


def test_package_head_occurrence_observation_refuses_unbound_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = SemanticPackageCoordinate("aware.sdk.target", "sdk", MANIFEST_DIGEST)
    store = InMemoryLocalOperationalStateStore()
    publisher = WorkspaceSemanticMaterializationPublisher(
        state_store=store, body_store=_BodyStore()
    )
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        "legacy",
        expected_revision=0,
        value={"contract": "aware.workspace.semantic-materialization-head.v3"},
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="occurrence history is unavailable",
    ):
        publisher._observe_v4_occurrence_absence(package, _occurrence())
    store.delete(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        "legacy",
        expected_revision=1,
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="lineage history is unavailable",
    ):
        publisher._observe_v4_occurrence_absence(package, _occurrence())
    foreign = InMemoryLocalOperationalStateStore().read_namespace_snapshot(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE
    )
    with pytest.raises(LocalOperationalStateConflict):
        publisher._validate_v4_occurrence_absence(foreign, package, _occurrence())

    calls = 0

    def substituted_validator(self, snapshot):
        nonlocal calls
        calls += 1

    monkeypatch.setattr(
        InMemoryLocalOperationalStateStore,
        "validate_namespace_snapshot",
        substituted_validator,
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="entrance substituted",
    ):
        publisher._validate_v4_occurrence_absence(foreign, package, _occurrence())
    assert calls == 0


def test_versioned_package_head_read_preserves_v3_and_v4_identity() -> None:
    runtime, invocation, v3_request, snapshot = _graph_v2_fixture(
        expected_revision=0, marker="9"
    )
    v3_publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime,
        state_store=InMemoryLocalOperationalStateStore(),
        body_store=_BodyStore(),
    )
    _receipt, v3_observation = v3_publisher._publish_graph_v2(
        request=v3_request, snapshot=snapshot, invocation=invocation
    )
    assert v3_publisher._read_graph_package_head_evidence(
        v3_request.package.package_ref, observation_role="package_reuse"
    ).materialization_head_digest == v3_observation.materialization_head_digest

    runtime, v4_request, v4_head, bodies, _state, _prior, _invocation, _snapshot = (
        _state_bound_head_fixture()
    )
    store = InMemoryLocalOperationalStateStore()
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        v4_request.package.package_ref,
        expected_revision=0,
        value=cast(dict, v4_head.to_wire()),
    )
    v4_publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=store, body_store=bodies
    )
    observed = v4_publisher._read_graph_package_head_evidence(
        v4_request.package.package_ref, observation_role="package_reuse"
    )
    assert observed is not None
    assert observed.materialization_head_digest == v4_head.head_digest
    assert observed.materialization_head_digest != v4_head.base_head.head_digest
    bodies.substitute_reads = True
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="missing or changed",
    ):
        v4_publisher._read_graph_package_head_evidence(
            v4_request.package.package_ref, observation_role="package_reuse"
        )


def test_state_bound_v4_successor_is_derived_from_selected_code_delta() -> None:
    runtime, request, head, bodies, state, prior, invocation, snapshot = (
        _state_bound_head_fixture()
    )
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime,
        state_store=InMemoryLocalOperationalStateStore(),
        body_store=bodies,
    )
    candidate, prior_body, state_body = publisher._prepare_graph_v4_output_successor(
        request=request,
        package_occurrence=_occurrence(),
        snapshot=snapshot,
        invocation=invocation,
        operation_ref="materialize:sdk",
        operation_digest=OPERATION_DIGEST,
        output_role="output",
        prior_output_state=prior,
    )
    assert candidate == head
    assert prior_body == prior.to_json_bytes()
    assert state_body == state.to_json_bytes()
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="Code delta is invalid",
    ):
        publisher._prepare_graph_v4_output_successor(
            request=request,
            package_occurrence=_occurrence(),
            snapshot=snapshot,
            invocation=invocation,
            operation_ref="materialize:sdk",
            operation_digest=OPERATION_DIGEST,
            output_role="output",
            prior_output_state=CodePackageOutputState.empty("other_sdk"),
        )


def _existing_v4_successor_fixture():
    runtime, first_request, first_head, bodies, prior_state, _empty, _, first_snapshot = (
        _state_bound_head_fixture()
    )
    invocation, completion = asyncio.run(
        _execute(
            runtime,
            "b",
            predecessor=first_request.result_coordinate,
            predecessor_body=first_snapshot.body_for(
                first_request.result_coordinate
            ).canonical_body,
        )
    )
    original = runtime.snapshot_completion(completion)
    content = "value = 2\n"
    content_body = content.encode()
    prior_path = prior_state.paths[0]
    producer = CodePackageDeltaProducerRef(
        "sdk-definition", "sdk-renderer-v1", "semantic_contract_renderer",
        FrozenJsonObject.from_mapping(
            {"prior_output_state_digest": prior_state.state_digest}
        ),
    )
    provisional = CodePackageDeltaProduction(
        producer=producer,
        input_digest=ContentDigest.of_bytes(b"second effect").value,
    )
    provisional_path = CodePackageDeltaPath(
        "generated.py", CodePackageDeltaKind.update, content,
        prior_path.content_hash, ContentDigest.of_bytes(content_body).value,
        len(content_body), CodeLanguage.python, True,
        CodePackagePathRole.generated_code, provisional,
        FrozenJsonObject.from_mapping({}),
    )
    source_revision = ContentDigest.of_bytes(b"sdk-source-2").value
    output_digest = code_package_delta_output_digest(
        package_name="aware_dev_sdk",
        authority=CodePackageDeltaAuthorityKind.code_package_delta,
        authority_kind=CodePackageDeltaAuthorityKind.code_package_delta.value,
        source_revision_id=source_revision,
        production=provisional,
        paths=(provisional_path,),
    )
    production = replace(provisional, output_digest=output_digest)
    delta = CodePackageDelta(
        "aware_dev_sdk", CodePackageDeltaAuthorityKind.code_package_delta,
        CodePackageDeltaAuthorityKind.code_package_delta.value,
        source_revision, production,
        (replace(provisional_path, production=production),),
    )
    successor_state = derive_code_package_output_state(prior_state, delta)
    delta_body = delta.to_json_bytes()
    output = _coordinate("output", OUTPUT, "sdk-delta-2", delta_body)
    effect = original.result.effect
    assert effect is not None
    result = replace(
        original.result,
        outputs=(SemanticOutputEnvelope("test-provider", output, effect.digest),),
    )
    request = WorkspaceSemanticMaterializationRequestV3.create(
        package=first_request.package,
        result_coordinate=original.result.transition.result,
        source_identity_digest=first_request.source_identity_digest,
        code_intent_digest=first_request.code_intent_digest,
        code_match_digest=first_request.code_match_digest,
        planning_input_digest=first_request.planning_input_digest,
        execution_input_closure_digest=first_request.execution_input_closure_digest,
        operation_result_digest=result.digest,
        expected_head_revision=1,
    )
    snapshot = ExecutionPublicationSnapshot(
        invocation_digest=invocation.digest,
        profile_digest=invocation.profile_digest,
        result=result,
        result_digest=result.digest,
        result_wire=canonical_json_bytes(result.to_wire()),
        effect_digest=original.effect_digest,
        transition_digest=original.transition_digest,
        bodies=tuple(sorted(
            (
                *(item for item in original.bodies if item.coordinate.role != "output"),
                SemanticBody(output, delta_body),
            ),
            key=lambda item: canonical_json_bytes(item.coordinate.to_wire()),
        )),
    )
    return (
        runtime, first_request, first_head, bodies, prior_state,
        request, invocation, snapshot, successor_state,
    )


def test_existing_v4_successor_commits_one_state_bound_head_and_retries_exactly() -> None:
    (
        runtime, first_request, first_head, bodies, prior_state,
        request, invocation, snapshot, successor_state,
    ) = _existing_v4_successor_fixture()
    store = InMemoryLocalOperationalStateStore()
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        first_request.package.package_ref,
        expected_revision=0,
        value=cast(dict, first_head.to_wire()),
    )
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=store, body_store=bodies
    )
    kwargs = dict(
        request=request,
        snapshot=snapshot,
        invocation=invocation,
        package_occurrence=_occurrence(),
        expected_prior_head_digest=first_head.head_digest,
        prior_output_state=prior_state,
        operation_ref="materialize:sdk-2",
        operation_digest=OPERATION_DIGEST,
        output_role="output",
    )
    receipt, reread = publisher._publish_graph_v4_existing_successor(**kwargs)
    assert receipt.head_advanced
    assert receipt.prior_head_revision == 1
    assert receipt.head_revision == 2
    assert reread.head == receipt.head
    assert publisher._read_graph_v4_output_state(
        reread.head, output_role="output"
    ) == successor_state
    reconstructed = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=store, body_store=bodies
    )
    retry_receipt, retry_reread = reconstructed._publish_graph_v4_existing_successor(**kwargs)
    assert not retry_receipt.head_advanced
    assert retry_receipt.head == receipt.head
    assert retry_reread == reread
    with pytest.raises(WorkspaceSemanticMaterializationPublicationConflict):
        reconstructed._publish_graph_v4_existing_successor(
            **{**kwargs, "expected_prior_head_digest": ContentDigest.of_bytes(b"other")}
        )
    assert store.read(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        request.package.package_ref,
    ).revision == 2
    bodies.substitute_reads = True
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        reconstructed._read_graph_v4_head_evidence(
            request.package.package_ref, observation_role="package_result"
        )


def test_existing_v4_successor_rejects_wrong_predecessor_and_genesis() -> None:
    (
        runtime, first_request, first_head, bodies, prior_state,
        request, invocation, snapshot, _,
    ) = _existing_v4_successor_fixture()
    store = InMemoryLocalOperationalStateStore()
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        first_request.package.package_ref,
        expected_revision=0,
        value=cast(dict, first_head.to_wire()),
    )
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=store, body_store=bodies
    )
    kwargs = dict(
        request=request, snapshot=snapshot, invocation=invocation,
        package_occurrence=_occurrence(),
        expected_prior_head_digest=first_head.head_digest,
        prior_output_state=prior_state,
        operation_ref="materialize:sdk-2", operation_digest=OPERATION_DIGEST,
        output_role="output",
    )
    with pytest.raises(WorkspaceSemanticMaterializationPublicationConflict):
        publisher._publish_graph_v4_existing_successor(
            **{**kwargs, "expected_prior_head_digest": ContentDigest.of_bytes(b"other")}
        )
    with pytest.raises(WorkspaceSemanticMaterializationPublicationConflict):
        publisher._publish_graph_v4_existing_successor(
            **{**kwargs, "package_occurrence": replace(_occurrence(), package_id="other")}
        )
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        publisher._publish_graph_v4_existing_successor(
            **{**kwargs, "prior_output_state": CodePackageOutputState.empty("aware_dev_sdk")}
        )
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError, match="genesis"):
        publisher._publish_graph_v4_existing_successor(
            **{**kwargs, "request": first_request}
        )
    assert store.read(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        request.package.package_ref,
    ).revision == 1


def test_existing_v4_successor_losing_cas_does_not_publish_second_head(
    monkeypatch,
) -> None:
    (
        runtime, first_request, first_head, bodies, prior_state,
        request, invocation, snapshot, _,
    ) = _existing_v4_successor_fixture()
    store = InMemoryLocalOperationalStateStore()
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        first_request.package.package_ref,
        expected_revision=0,
        value=cast(dict, first_head.to_wire()),
    )
    original_cas = store.compare_and_set

    def competing_cas(namespace, key, *, expected_revision, value, updated_at=None):
        original_cas(
            namespace, key, expected_revision=expected_revision,
            value=cast(dict, first_head.to_wire()),
        )
        return original_cas(
            namespace, key, expected_revision=expected_revision,
            value=value, updated_at=updated_at,
        )

    monkeypatch.setattr(store, "compare_and_set", competing_cas)
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=store, body_store=bodies
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationConflict, match="CAS lost"
    ):
        publisher._publish_graph_v4_existing_successor(
            request=request, snapshot=snapshot, invocation=invocation,
            package_occurrence=_occurrence(),
            expected_prior_head_digest=first_head.head_digest,
            prior_output_state=prior_state,
            operation_ref="materialize:sdk-2",
            operation_digest=OPERATION_DIGEST,
            output_role="output",
        )
    current = store.read(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        request.package.package_ref,
    )
    assert current is not None and current.revision == 2
    assert current.value == first_head.to_wire()


def test_dormant_graph_v2_publication_is_contiguous_retryable_and_detached() -> None:
    state = InMemoryLocalOperationalStateStore()
    runtime, first_invocation, first_request, first_snapshot = _graph_v2_fixture(
        expected_revision=0, marker="a"
    )
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=state, body_store=_BodyStore()
    )
    first_receipt, first_reread = publisher._publish_graph_v2(
        request=first_request,
        snapshot=first_snapshot,
        invocation=first_invocation,
    )
    assert first_receipt.head_revision == 1
    assert first_reread.materialization_head_revision == 1
    assert first_reread.observation_role == "package_result"
    recovered_result, recovered_invocation = publisher._read_graph_v2_operation_result(
        first_receipt.head, declaration=_declaration()
    )
    assert recovered_result == first_snapshot.result
    assert recovered_invocation == first_invocation

    retry_receipt, retry_reread = publisher._publish_graph_v2(
        request=first_request,
        snapshot=first_snapshot,
        invocation=first_invocation,
    )
    assert retry_receipt == first_receipt
    assert retry_reread == first_reread

    _runtime_two, second_invocation, second_request, second_snapshot = (
        _graph_v2_fixture(expected_revision=1, marker="b")
    )
    second_receipt, _ = publisher._publish_graph_v2(
        request=second_request,
        snapshot=second_snapshot,
        invocation=second_invocation,
    )
    assert second_receipt.prior_head_revision == 1
    assert second_receipt.head_revision == 2
    observed = publisher._read_graph_v2_head(
        "aware.sdk.demo", observation_role="package_reuse"
    )
    assert observed is not None
    assert observed.materialization_head_revision == 2
    assert observed.observation_role == "package_reuse"

    object.__setattr__(observed.head, "code_match_digest", _digest("f"))
    restored = publisher._read_graph_v2_head(
        "aware.sdk.demo", observation_role="package_reuse"
    )
    assert restored is not None
    assert restored.head.code_match_digest == second_request.code_match_digest


def test_dormant_graph_v2_succeeds_v1_and_fences_v1_before_body_staging() -> None:
    async def prove() -> None:
        runtime = _runtime()
        state = InMemoryLocalOperationalStateStore()
        bodies = _BodyStore()
        publisher = WorkspaceSemanticMaterializationPublisher(
            runtime=runtime, state_store=state, body_store=bodies
        )
        invocation, completion = await _execute(runtime, "one")
        publisher.publish(
            admission=_admission(invocation),
            invocation=invocation,
            completion=completion,
            expected_head_revision=0,
        )
        v1_body_count = len(bodies.bodies)
        snapshot = runtime.snapshot_completion(completion)
        request = _graph_v2_request(expected_revision=1, marker="c", snapshot=snapshot)
        receipt, _ = publisher._publish_graph_v2(
            request=request, snapshot=snapshot, invocation=invocation
        )
        assert receipt.head_revision == 2
        v2_body_count = len(bodies.bodies)

        successor, successor_completion = await _execute(runtime, "two")
        with pytest.raises(
            WorkspaceSemanticMaterializationPublicationError,
            match="head contract unsupported",
        ):
            publisher.publish(
                admission=_admission(successor),
                invocation=successor,
                completion=successor_completion,
                expected_head_revision=2,
            )
        assert v2_body_count > v1_body_count
        assert len(bodies.bodies) == v2_body_count

    asyncio.run(prove())


def test_dormant_graph_v2_stored_head_poison_fails_closed() -> None:
    state = InMemoryLocalOperationalStateStore()
    runtime, invocation, request, snapshot = _graph_v2_fixture(
        expected_revision=0, marker="d"
    )
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=state, body_store=_BodyStore()
    )
    publisher._publish_graph_v2(
        request=request, snapshot=snapshot, invocation=invocation
    )
    record = state.read(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE, "aware.sdk.demo"
    )
    assert record is not None and record.value is not None
    poisoned = cast(dict[str, object], json.loads(json.dumps(record.value)))
    poisoned["code_match_digest"] = _digest("e").value
    state.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        "aware.sdk.demo",
        expected_revision=1,
        value=cast(dict, poisoned),
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="fresh derivation",
    ):
        publisher._read_graph_v2_head(
            "aware.sdk.demo", observation_role="package_reuse"
        )


def test_dormant_graph_v2_result_body_poison_fails_contextual_recovery() -> None:
    runtime, invocation, request, snapshot = _graph_v2_fixture(
        expected_revision=0, marker="1"
    )
    bodies = _BodyStore()
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime,
        state_store=InMemoryLocalOperationalStateStore(),
        body_store=bodies,
    )
    receipt, _ = publisher._publish_graph_v2(
        request=request,
        snapshot=snapshot,
        invocation=invocation,
    )
    body_ref = (
        "cas://workspace-semantic-materialization/body/"
        + snapshot.result_digest.value[7:]
    )
    digest_free_body = bodies.bodies[body_ref]
    bodies.bodies[body_ref] = snapshot.result_wire
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="body digest differs",
    ):
        publisher._read_graph_v2_operation_result(
            receipt.head, declaration=_declaration()
        )

    bodies.bodies[body_ref] = digest_free_body
    invocation_ref = (
        "cas://workspace-semantic-materialization/body/"
        + snapshot.invocation_digest.value[7:]
    )
    invocation_body = bodies.bodies.pop(invocation_ref)
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="invocation body differs",
    ):
        publisher._read_graph_v2_operation_result(
            receipt.head, declaration=_declaration()
        )
    bodies.bodies[invocation_ref] = invocation_body

    foreign_declaration = _declaration()
    object.__setattr__(foreign_declaration, "provider_key", "foreign-provider")
    with pytest.raises(
        (ContractViolation, WorkspaceSemanticMaterializationPublicationError)
    ):
        publisher._read_graph_v2_operation_result(
            receipt.head, declaration=foreign_declaration
        )


def test_dormant_graph_v2_sqlite_restart_reconstructs_exact_head(tmp_path) -> None:
    sqlite = pytest.importorskip("aware_local_service_state_sqlite")
    state_path = tmp_path / "graph-v2-publication.sqlite3"
    runtime, invocation, request, snapshot = _graph_v2_fixture(
        expected_revision=0, marker="f"
    )
    bodies = _BodyStore()
    first = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime,
        state_store=sqlite.SqliteLocalOperationalStateStore(state_path),
        body_store=bodies,
    )
    receipt, reread = first._publish_graph_v2(
        request=request, snapshot=snapshot, invocation=invocation
    )
    reconstructed = WorkspaceSemanticMaterializationPublisher(
        runtime=_runtime(),
        state_store=sqlite.SqliteLocalOperationalStateStore(state_path),
        body_store=bodies,
    )
    observed = reconstructed._read_graph_v2_head(
        "aware.sdk.demo", observation_role="package_result"
    )
    assert observed == reread
    recovered_result, recovered_invocation = (
        reconstructed._read_graph_v2_operation_result(
            observed.head, declaration=_declaration()
        )
    )
    assert recovered_result == snapshot.result
    assert recovered_invocation == invocation
    retry, _ = reconstructed._publish_graph_v2(
        request=request, snapshot=snapshot, invocation=invocation
    )
    assert retry == receipt


class _AuthorityValidator:
    def __init__(self, context, expected):
        self.context = context
        self.expected = expected
        self.calls = 0

    def validate_retained_semantic_operation_context(self, context, *, expected):
        assert context is self.context
        assert expected == self.expected
        self.calls += 1


def _authority_predecessor_fixture(publisher, package, result_contract):
    import os

    from aware_code_semantic_contract_runtime.retained_admission_interfaces import (
        RetainedSemanticAdmissionExpectation,
    )
    from aware_workspace_runtime.semantic_materialization_publication import (
        WorkspaceAuthorityPredecessorIssuerRuntime,
    )
    from test_semantic_catalog_host import admit, command_setup

    owner, parent, _, catalog, code_catalog, workspace_catalog = command_setup()
    admit(catalog, code_catalog, lambda: workspace_catalog)
    epoch_expected = catalog.read_initial_publication()
    epoch = catalog.read_initial_epoch()
    placeholder = SemanticValueCoordinate(
        "fixture",
        SemanticContractRef("fixture.bytes", "1", ContentDigest.of_bytes(b"schema")),
        "fixture:value",
        ContentDigest.of_bytes(b"value"),
        len(b"value"),
    )
    expected = RetainedSemanticAdmissionExpectation(
        runtime=_runtime(),
        generation_identity=owner.epoch_identity,
        operation_identity=object(),
        process_id=os.getpid(),
        selected_provider_registration=object(),
        stage="authority_derivation",
        profile=object(),
        provider_declaration=_declaration(),
        binding=object(),
        package=package,
        source_identity_digest=ContentDigest.of_bytes(b"source"),
        manifest_coordinate=placeholder,
        candidate_coordinate=placeholder,
        registry_package_coordinate=placeholder,
        package_context_coordinate=placeholder,
        declaration_inventory_coordinate=placeholder,
    )
    context = object()
    validator = _AuthorityValidator(context, expected)
    issuer = WorkspaceAuthorityPredecessorIssuerRuntime._assemble(
        publisher=publisher,
        command_runtime=owner,
        command_parent=parent,
        catalog_host=catalog,
        catalog_epoch=epoch,
        catalog_expected=epoch_expected,
        authority_validator=validator,
    )
    return owner, catalog, validator, issuer, context, expected, result_contract


def _authority_predecessor_call(issuer, context, expected, result_contract):
    execution = object()
    admission = issuer.issue_authority_predecessor(
        context,
        authority_expected=expected,
        execution_identity=execution,
        result_contract=result_contract,
    )
    evidence = issuer.read_authority_predecessor(
        admission,
        authority_context=context,
        authority_expected=expected,
        execution_identity=execution,
        result_contract=result_contract,
    )
    issuer.validate_authority_predecessor_admission(
        admission,
        authority_context=context,
        authority_expected=expected,
        execution_identity=execution,
        result_contract=result_contract,
    )
    return execution, admission, evidence


def test_authority_predecessor_genesis_requires_live_original_context() -> None:
    runtime, _, request, _ = _graph_v2_fixture(expected_revision=0, marker="9")
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime,
        state_store=InMemoryLocalOperationalStateStore(),
        body_store=_BodyStore(),
    )
    owner, catalog, validator, issuer, context, expected, contract = (
        _authority_predecessor_fixture(
            publisher, request.package, request.result_coordinate.contract
        )
    )
    execution, admission, evidence = _authority_predecessor_call(
        issuer, context, expected, contract
    )
    assert evidence.disposition == "genesis"
    assert type(evidence.predecessor) is TypedEmptyCoordinate
    assert evidence.predecessor.contract == contract
    assert evidence.predecessor_body is None
    assert validator.calls == 6
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="requires lineage-negative admission",
    ):
        issuer.read_authority_output_state(
            admission,
            authority_context=context,
            authority_expected=expected,
            execution_identity=execution,
            result_contract=contract,
            output_role="sdk_code_package_delta",
            output_state_name="aware_dev_sdk",
        )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError, match="replay"
    ):
        issuer.issue_authority_predecessor(
            context,
            authority_expected=expected,
            execution_identity=execution,
            result_contract=contract,
        )
    reconstructed = object.__new__(type(admission))
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError, match="context differs"
    ):
        issuer.validate_authority_predecessor_admission(
            reconstructed,
            authority_context=context,
            authority_expected=expected,
            execution_identity=execution,
            result_contract=contract,
        )
    issuer.close()
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError, match="context differs"
    ):
        issuer.validate_authority_predecessor_admission(
            admission,
            authority_context=context,
            authority_expected=expected,
            execution_identity=execution,
            result_contract=contract,
        )
    catalog.close()
    owner.close()


def test_authority_output_state_uses_original_current_v4_admission() -> None:
    runtime, request, head, bodies, output_state, _prior, _invocation, _snapshot = (
        _state_bound_head_fixture()
    )
    store = InMemoryLocalOperationalStateStore()
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        request.package.package_ref,
        expected_revision=0,
        value=head.to_wire(),
    )
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=store, body_store=bodies
    )
    owner, catalog, _, issuer, context, expected, contract = (
        _authority_predecessor_fixture(
            publisher, request.package, request.result_coordinate.contract
        )
    )
    execution, admission, evidence = _authority_predecessor_call(
        issuer, context, expected, contract
    )
    assert evidence.disposition == "current"
    assert evidence.materialization_head_digest == head.head_digest
    assert issuer.read_authority_output_state(
        admission,
        authority_context=context,
        authority_expected=expected,
        execution_identity=execution,
        result_contract=contract,
        output_role="output",
        output_state_name="aware_dev_sdk",
    ) == output_state
    issuer.validate_authority_output_state_admission(
        admission,
        authority_context=context,
        authority_expected=expected,
        execution_identity=execution,
        result_contract=contract,
        output_role="output",
        output_state_name="aware_dev_sdk",
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="original read differs",
    ):
        issuer.validate_authority_output_state_admission(
            admission,
            authority_context=context,
            authority_expected=expected,
            execution_identity=execution,
            result_contract=contract,
            output_role="output",
            output_state_name="other_sdk",
        )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="read replay",
    ):
        issuer.read_authority_output_state(
            admission,
            authority_context=context,
            authority_expected=expected,
            execution_identity=execution,
            result_contract=contract,
            output_role="output",
            output_state_name="aware_dev_sdk",
        )
    bodies.substitute_reads = True
    with pytest.raises(WorkspaceSemanticMaterializationPublicationError):
        issuer.validate_authority_output_state_admission(
            admission,
            authority_context=context,
            authority_expected=expected,
            execution_identity=execution,
            result_contract=contract,
            output_role="output",
            output_state_name="aware_dev_sdk",
        )
    bodies.substitute_reads = False
    successor_head = WorkspaceSemanticMaterializationHeadV4.create(
        request=request,
        package_occurrence=head.package_occurrence,
        operation_ref="materialize:sdk-successor",
        operation_digest=ContentDigest.of_bytes(b"successor-operation"),
        output_state_bindings=head.output_state_bindings,
    )
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        request.package.package_ref,
        expected_revision=1,
        value=successor_head.to_wire(),
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="no longer current",
    ):
        issuer.validate_authority_output_state_admission(
            admission,
            authority_context=context,
            authority_expected=expected,
            execution_identity=execution,
            result_contract=contract,
            output_role="output",
            output_state_name="aware_dev_sdk",
        )
    issuer.close()
    catalog.close()
    owner.close()


def test_authority_predecessor_refuses_v4_head_change_during_body_reread() -> None:
    runtime, request, head, initial_bodies, _state, _prior, _invocation, _snapshot = (
        _state_bound_head_fixture()
    )
    store = InMemoryLocalOperationalStateStore()
    package_ref = request.package.package_ref
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        package_ref,
        expected_revision=0,
        value=head.to_wire(),
    )
    successor = WorkspaceSemanticMaterializationHeadV4.create(
        request=request,
        package_occurrence=head.package_occurrence,
        operation_ref="materialize:changed-during-reread",
        operation_digest=ContentDigest.of_bytes(b"changed-operation"),
        output_state_bindings=head.output_state_bindings,
    )

    class _ChangingBodyStore(_BodyStore):
        changed = False

        def read_body(self, body_ref: str) -> bytes | None:
            if not self.changed:
                self.changed = True
                store.compare_and_set(
                    DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
                    package_ref,
                    expected_revision=1,
                    value=successor.to_wire(),
                )
            return super().read_body(body_ref)

    bodies = _ChangingBodyStore()
    bodies.bodies = initial_bodies.bodies.copy()
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=store, body_store=bodies
    )
    owner, catalog, _validator, issuer, context, expected, contract = (
        _authority_predecessor_fixture(
            publisher, request.package, request.result_coordinate.contract
        )
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="changed during reread",
    ):
        issuer.issue_authority_predecessor(
            context,
            authority_expected=expected,
            execution_identity=object(),
            result_contract=contract,
        )
    issuer.close()
    catalog.close()
    owner.close()


def test_authority_output_state_rejects_delta_outside_selected_code_result() -> None:
    runtime, request, head, bodies, _state, _prior, _invocation, _snapshot = (
        _state_bound_head_fixture(selected_output_matches=False)
    )
    store = InMemoryLocalOperationalStateStore()
    store.compare_and_set(
        DEFAULT_SEMANTIC_MATERIALIZATION_STATE_NAMESPACE,
        request.package.package_ref,
        expected_revision=0,
        value=head.to_wire(),
    )
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=store, body_store=bodies
    )
    owner, catalog, _, issuer, context, expected, contract = (
        _authority_predecessor_fixture(
            publisher, request.package, request.result_coordinate.contract
        )
    )
    execution, admission, _evidence = _authority_predecessor_call(
        issuer, context, expected, contract
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="differs from selected Code result",
    ):
        issuer.read_authority_output_state(
            admission,
            authority_context=context,
            authority_expected=expected,
            execution_identity=execution,
            result_contract=contract,
            output_role="output",
            output_state_name="aware_dev_sdk",
        )
    issuer.close()
    catalog.close()
    owner.close()


def test_authority_predecessor_current_retains_exact_body_and_detects_change() -> None:
    state = InMemoryLocalOperationalStateStore()
    bodies = _BodyStore()
    runtime, invocation, request, snapshot = _graph_v2_fixture(
        expected_revision=0, marker="a"
    )
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime, state_store=state, body_store=bodies
    )
    publisher._publish_graph_v2(
        request=request, snapshot=snapshot, invocation=invocation
    )
    owner, catalog, _, issuer, context, expected, contract = (
        _authority_predecessor_fixture(
            publisher, request.package, request.result_coordinate.contract
        )
    )
    execution, admission, evidence = _authority_predecessor_call(
        issuer, context, expected, contract
    )
    assert evidence.disposition == "current"
    assert evidence.predecessor == request.result_coordinate
    assert evidence.predecessor_body == publisher._read_graph_v2_body(
        request.result_coordinate
    )
    body_ref = next(
        ref
        for ref, body in bodies.bodies.items()
        if body == evidence.predecessor_body.canonical_body
    )
    retained_body = bodies.bodies.pop(body_ref)
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="body is absent",
    ):
        issuer.validate_authority_predecessor_admission(
            admission,
            authority_context=context,
            authority_expected=expected,
            execution_identity=execution,
            result_contract=contract,
        )
    bodies.bodies[body_ref] = retained_body
    issuer.validate_authority_predecessor_admission(
        admission,
        authority_context=context,
        authority_expected=expected,
        execution_identity=execution,
        result_contract=contract,
    )
    _, next_invocation, next_request, next_snapshot = _graph_v2_fixture(
        expected_revision=1, marker="b"
    )
    publisher._publish_graph_v2(
        request=next_request, snapshot=next_snapshot, invocation=next_invocation
    )
    with pytest.raises(
        WorkspaceSemanticMaterializationPublicationError,
        match="no longer current",
    ):
        issuer.validate_authority_predecessor_admission(
            admission,
            authority_context=context,
            authority_expected=expected,
            execution_identity=execution,
            result_contract=contract,
        )
    issuer.close()
    catalog.close()
    owner.close()


def test_planning_digest_persists_and_reuse_requires_exact_node_input():
    from types import SimpleNamespace

    from aware_workspace_runtime.materialization_graph_coordinator import (
        WorkspaceSemanticMaterializationGraphCoordinator,
        WorkspaceSemanticMaterializationGraphExecutionError,
    )

    runtime, invocation, request, snapshot = _graph_v2_fixture(
        expected_revision=0, marker="a"
    )
    publisher = WorkspaceSemanticMaterializationPublisher(
        runtime=runtime,
        state_store=InMemoryLocalOperationalStateStore(),
        body_store=_BodyStore(),
    )
    receipt, _ = publisher._publish_graph_v2(
        request=request, snapshot=snapshot, invocation=invocation
    )
    head = publisher._read_graph_v2_head(
        request.package.package_ref, observation_role="package_reuse"
    )
    assert head.planning_input_digest == request.planning_input_digest
    assert receipt.head.planning_input_digest == request.planning_input_digest
    assert head.head.request.planning_input_digest == request.planning_input_digest
    assert (
        head.to_wire()["planning_input_digest"]
        == request.planning_input_digest.to_wire()
    )
    binding = SimpleNamespace(
        package=request.package,
        package_entry=SimpleNamespace(
            source_identity_digest=request.source_identity_digest
        ),
        code_intent=SimpleNamespace(intent_digest=request.code_intent_digest),
        code_match=SimpleNamespace(match_digest=request.code_match_digest),
        planning_input_digest=request.planning_input_digest,
    )
    planned = SimpleNamespace(
        historical_execution_input_closure_digest=(
            request.execution_input_closure_digest
        ),
        predecessor_head_revision=head.materialization_head_revision,
        predecessor_head_digest=head.materialization_head_digest,
    )
    validate = WorkspaceSemanticMaterializationGraphCoordinator._validate_reuse_head
    validate(binding, planned, request.execution_input_closure_digest, head)
    binding.planning_input_digest = ContentDigest.of_bytes(b"different-owner-input")
    with pytest.raises(WorkspaceSemanticMaterializationGraphExecutionError):
        validate(binding, planned, request.execution_input_closure_digest, head)


@pytest.mark.parametrize("poison", ["missing", "substituted", "old_contract"])
def test_publication_planning_input_wire_cannot_be_inferred_or_restamped(poison):
    from aware_workspace_runtime.semantic_materialization_publication import (
        _parse_publication_request_v2_wire,
    )

    _, _, request, _ = _graph_v2_fixture(expected_revision=0, marker="b")
    wire = request.to_wire()
    if poison == "missing":
        del wire["planning_input_digest"]
    elif poison == "substituted":
        wire["planning_input_digest"] = ContentDigest.of_bytes(
            b"substituted"
        ).to_wire()
    else:
        wire["contract"] = "aware.workspace.semantic-materialization-request.v2"
    with pytest.raises(
        (WorkspaceSemanticMaterializationPublicationError, ContractViolation)
    ):
        _parse_publication_request_v2_wire(wire)


def _v5_wire_occurrence():
    return {
        "repository_ref": "aware-dev",
        "workspace_ref": "aware_kernel",
        "module_ref": "storage",
        "package_id": "ontology",
        "package_root": "modules/storage/ontology",
        "manifest_relative_path": "modules/storage/ontology/aware.ontology.toml",
    }


def _v5_wire_lineage():
    return {
        "contract": v5_wire._V5_LINEAGE_CONTRACT,
        "occurrence": _v5_wire_occurrence(),
        "incarnation_ref": "lineage:fixture",
    }


def _v5_wire_installation():
    value = {
        "contract": v5_wire._V5_INSTALLATION_CONTRACT,
        "namespace": v5_wire._V5_STATE_NAMESPACE,
        "store_binding_digest": "sha256:" + "1" * 64,
        "installation_ref": "installation:fixture",
        "legacy_namespace_snapshot_digest": "sha256:" + "2" * 64,
    }
    value["installation_digest"] = v5_wire._v5_digest(
        v5_wire._V5_INSTALLATION_CONTRACT, value
    )
    return value


def _v5_wire_observation():
    value = _v5_wire_installation()
    return [
        "workspace_v5_read_observation_v1",
        value["store_binding_digest"],
        value["installation_digest"],
        v5_wire._v5_occurrence_key(_v5_wire_occurrence()),
        0,
        "sha256:" + "3" * 64,
        "predecessor_read",
    ]


class _V5WireHostile:
    def __getattribute__(self, _name):
        raise AssertionError("foreign attributes invoked")

    def __eq__(self, _other):
        raise AssertionError("foreign equality invoked")

    def __hash__(self) -> int:
        raise AssertionError("foreign hashing invoked")


def test_v5_codec_published_occurrence_vector_and_domain():
    value = _v5_wire_occurrence()
    expected = "sha256:791c17dc5cfa8ff5204247de03dd7f53d017d18134b2cc15bf66fd4f4de69c55"
    assert v5_wire._v5_occurrence_key(value) == expected
    plain = "sha256:" + hashlib.sha256(v5_wire._encode_v5_occurrence(value)).hexdigest()
    assert plain != expected
    meta = (
        "sha256:"
        + hashlib.sha256(
            v5_wire._V5_OCCURRENCE_KEY_CONTRACT.encode("ascii")
            + b"\0"
            + v5_wire._encode_v5_occurrence(value)
        ).hexdigest()
    )
    assert meta != expected


@pytest.mark.parametrize("field", sorted(v5_wire._V5_OCCURRENCE_FIELDS))
def test_v5_codec_every_address_field_changes_key(field):
    value = _v5_wire_occurrence()
    before = v5_wire._v5_occurrence_key(value)
    value[field] += "-other"
    assert v5_wire._v5_occurrence_key(value) != before


def test_v5_codec_incarnation_changes_lineage_but_not_occurrence_key():
    left = _v5_wire_lineage()
    right = copy.deepcopy(left)
    right["incarnation_ref"] = "lineage:another"
    assert v5_wire._encode_v5_lineage(left) != v5_wire._encode_v5_lineage(right)
    assert v5_wire._v5_occurrence_key(left["occurrence"]) == v5_wire._v5_occurrence_key(
        right["occurrence"]
    )


@pytest.mark.parametrize(
    "value,encoder,decoder",
    (
        (_v5_wire_lineage(), v5_wire._encode_v5_lineage, v5_wire._decode_v5_lineage),
        (
            _v5_wire_installation(),
            v5_wire._encode_v5_namespace_installation,
            v5_wire._decode_v5_namespace_installation,
        ),
        (
            _v5_wire_observation(),
            v5_wire._encode_v5_read_observation,
            v5_wire._decode_v5_read_observation,
        ),
    ),
)
def test_v5_codec_canonical_roundtrip_detaches_reads(value, encoder, decoder):
    body = encoder(value)
    assert encoder(decoder(body)) == body
    assert decoder(body) == value and decoder(body) is not value
    value.clear()
    assert encoder(decoder(body)) == body


@pytest.mark.parametrize(
    "kind",
    (
        "missing",
        "extra",
        "wrong_contract",
        "wrong_namespace",
        "digest",
        "non_nfc",
        "token_bound",
        "whitespace",
        "foreign",
    ),
)
def test_v5_codec_installation_poison(kind):
    value = _v5_wire_installation()
    if kind == "missing":
        del value["installation_ref"]
    elif kind == "extra":
        value["approval"] = True
    elif kind == "wrong_contract":
        value["contract"] = (
            "aware.workspace.semantic-materialization-namespace-installation.v2"
        )
    elif kind == "wrong_namespace":
        value["namespace"] = "workspace.semantic-materialization-head.v1"
    elif kind == "digest":
        value["store_binding_digest"] = "sha256:" + "4" * 64
    elif kind == "non_nfc":
        value["installation_ref"] = "e\u0301"
    elif kind == "token_bound":
        value["installation_ref"] = "\u00e9" * 97
    elif kind == "whitespace":
        value["installation_ref"] = "two words"
    else:
        value["installation_ref"] = _V5WireHostile()
    with pytest.raises(v5_wire.WorkspaceSemanticMaterializationPublicationError):
        v5_wire._encode_v5_namespace_installation(value)


@pytest.mark.parametrize(
    "invalid", (True, False, -1, 9_223_372_036_854_775_808, 1.0, "1", None, "hostile")
)
def test_v5_codec_revision_poison(invalid):
    value = _v5_wire_observation()
    value[4] = _V5WireHostile() if invalid == "hostile" else invalid
    with pytest.raises(v5_wire.WorkspaceSemanticMaterializationPublicationError):
        v5_wire._encode_v5_read_observation(value)


@pytest.mark.parametrize(
    "invalid",
    (
        b"{}\n",
        b'{"contract":1,"contract":1}',
        b"\xff",
        b"[NaN]",
        b"[" * 1600,
        b" " * 16385,
    ),
)
def test_v5_codec_invalid_wire_refuses(invalid):
    with pytest.raises(v5_wire.WorkspaceSemanticMaterializationPublicationError):
        v5_wire._decode_v5_namespace_installation(invalid)


@pytest.mark.parametrize(
    "encoder",
    (
        v5_wire._encode_v5_lineage,
        v5_wire._encode_v5_namespace_installation,
        v5_wire._encode_v5_read_observation,
    ),
)
def test_v5_codec_foreign_container_without_behavior(encoder):
    with pytest.raises(v5_wire.WorkspaceSemanticMaterializationPublicationError):
        encoder(_V5WireHostile())


def test_v5_codec_unknown_occurrence_field_and_utf8_bound():
    value = _v5_wire_occurrence()
    value["source_digest"] = "sha256:" + "4" * 64
    with pytest.raises(v5_wire.WorkspaceSemanticMaterializationPublicationError):
        v5_wire._v5_occurrence_key(value)
    del value["source_digest"]
    value["module_ref"] = "\u00e9" * 257
    with pytest.raises(v5_wire.WorkspaceSemanticMaterializationPublicationError):
        v5_wire._v5_occurrence_key(value)


def test_v5_codec_noncanonical_bytes_and_duplicate_keys():
    value = _v5_wire_installation()
    body = v5_wire._encode_v5_namespace_installation(value)
    with pytest.raises(v5_wire.WorkspaceSemanticMaterializationPublicationError):
        v5_wire._decode_v5_namespace_installation(body + b"\n")
    repeated = (
        body[:-1] + b',"namespace":"workspace.semantic-materialization-occurrence.v5"}'
    )
    with pytest.raises(v5_wire.WorkspaceSemanticMaterializationPublicationError):
        v5_wire._decode_v5_namespace_installation(repeated)
    with pytest.raises(v5_wire.WorkspaceSemanticMaterializationPublicationError):
        v5_wire._decode_v5_namespace_installation(
            json.dumps(value, ensure_ascii=True).encode()
        )


def test_v5_codec_digest_is_self_excluded_and_schema_is_data_only():
    value = _v5_wire_installation()
    payload = {key: item for key, item in value.items() if key != "installation_digest"}
    direct = json.dumps(
        {"contract": v5_wire._V5_INSTALLATION_CONTRACT, "value": payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    assert (
        value["installation_digest"] == "sha256:" + hashlib.sha256(direct).hexdigest()
    )
    # A self-consistent foreign store still parses as data. Original store,
    # installation, fence and command checks are separate mandatory authority.
    payload["store_binding_digest"] = "sha256:" + "5" * 64
    payload["installation_digest"] = v5_wire._v5_digest(
        v5_wire._V5_INSTALLATION_CONTRACT, payload
    )
    assert (
        v5_wire._decode_v5_namespace_installation(
            v5_wire._encode_v5_namespace_installation(payload)
        )
        == payload
    )


def test_v5_codec_illformed_unicode_refuses_as_wire_error():
    value = _v5_wire_installation()
    value["installation_ref"] = "\ud800"
    with pytest.raises(v5_wire.WorkspaceSemanticMaterializationPublicationError):
        v5_wire._encode_v5_namespace_installation(value)
    body = v5_wire._encode_v5_namespace_installation(_v5_wire_installation()).replace(
        b"installation:fixture", b"\\ud800"
    )
    with pytest.raises(v5_wire.WorkspaceSemanticMaterializationPublicationError):
        v5_wire._decode_v5_namespace_installation(body)


def test_v5_codec_oversized_text_refuses_before_normalization(monkeypatch):
    def forbidden(_form, _value):
        raise AssertionError("oversized text reached normalization")

    monkeypatch.setattr(v5_wire.unicodedata, "normalize", forbidden)
    with pytest.raises(v5_wire.WorkspaceSemanticMaterializationPublicationError):
        v5_wire._v5_text("x" * 5120, 192, token=True)
