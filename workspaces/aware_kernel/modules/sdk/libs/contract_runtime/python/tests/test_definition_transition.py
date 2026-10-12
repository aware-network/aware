from __future__ import annotations

from dataclasses import replace

import pytest
from aware_meta_type_schema import (
    FieldDefinition,
    FrozenJson,
    ScalarKind,
    TypeDefinition,
    TypeKind,
    TypeSchemaBundle,
    TypeSchemaSlice,
    ValueShape,
)
from aware_sdk_contract_runtime import (
    SdkContractInventory,
    SdkContractManifest,
    SdkDefinitionMovementOperation,
    SdkDefinitionPredecessorKind,
    SdkDefinitionSemanticKind,
    SdkDefinitionState,
    SdkMethodContract,
    SdkMethodInventoryEntry,
    SdkOperationContract,
    SdkOperationInventoryEntry,
    SdkTargetContract,
    derive_sdk_definition_transition,
    prepare_sdk_definition_effect,
)


def _slice(type_ref: str) -> TypeSchemaSlice:
    name = type_ref.rsplit(".", 1)[-1]
    bundle = TypeSchemaBundle.create(
        namespace="proof",
        semantic_version="1",
        types=(
            TypeDefinition(
                type_ref,
                name,
                TypeKind.VALUE_OBJECT,
                fields=(
                    FieldDefinition(
                        f"{type_ref}.enabled",
                        "enabled",
                        ValueShape.scalar(ScalarKind.BOOLEAN),
                        default_value=FrozenJson.from_value(False),
                    ),
                ),
            ),
        ),
    )
    return TypeSchemaSlice.create(bundle, root_type_refs=(type_ref,))


def _state(*, legacy_mode: str = "sync") -> SdkDefinitionState:
    request = _slice("proof.Request")
    result = _slice("proof.Result")
    error = _slice("proof.Error")
    manifest = SdkContractManifest.create(
        sdk_ref="proof_sdk",
        semantic_version="1",
        targets=(SdkTargetContract("python", "python", "proof_sdk"),),
        schema_slices=(request, result, error),
        operations=(
            SdkOperationContract(
                "proof_sdk.current",
                request.slice_digest,
                result.slice_digest,
                (error.slice_digest,),
                "proof.current",
            ),
        ),
        methods=(
            SdkMethodContract(
                "proof_sdk.client.current",
                "proof_sdk.current",
                "query",
                "read",
                "none",
                "none",
                "sync",
            ),
        ),
    )
    operations = (
        SdkOperationInventoryEntry(
            "proof_sdk.current",
            "contracted",
            "proof.Request",
            "proof.Result",
            ("proof.Error",),
            "proof.current",
            (),
            (),
            ("proof_sdk.client.current",),
        ),
        SdkOperationInventoryEntry(
            "proof_sdk.legacy",
            "legacy",
            None,
            None,
            (),
            None,
            (),
            (),
            ("proof_sdk.client.legacy",),
        ),
    )
    methods = (
        SdkMethodInventoryEntry(
            "proof_sdk.client.current",
            "proof_sdk.current",
            "query",
            "read",
            "none",
            "none",
            "sync",
            "provider",
        ),
        SdkMethodInventoryEntry(
            "proof_sdk.client.legacy",
            "proof_sdk.legacy",
            "command",
            "write",
            "workspace",
            "required",
            legacy_mode,
            "legacy",
        ),
    )
    inventory = SdkContractInventory(
        "proof_sdk",
        tuple(item.operation_ref for item in operations),
        ("proof_sdk.current",),
        ("proof_sdk.legacy",),
        tuple(item.method_ref for item in methods),
        operations,
        methods,
    )
    return SdkDefinitionState.create(manifest, inventory)


def test_typed_empty_transition_has_complete_semantic_closure_and_effect() -> None:
    state = _state()
    transition = derive_sdk_definition_transition(None, state)
    effect = prepare_sdk_definition_effect(None, state)

    assert transition.predecessor_kind is SdkDefinitionPredecessorKind.TYPED_EMPTY
    assert transition.predecessor_definition_digest is None
    assert all(
        movement.operation is SdkDefinitionMovementOperation.ADD
        for movement in transition.movements
    )
    assert {movement.coordinate.kind for movement in transition.movements} == {
        SdkDefinitionSemanticKind.MANIFEST_METADATA,
        SdkDefinitionSemanticKind.TARGET,
        SdkDefinitionSemanticKind.SCHEMA_SLICE,
        SdkDefinitionSemanticKind.SCHEMA,
        SdkDefinitionSemanticKind.OPERATION,
        SdkDefinitionSemanticKind.METHOD,
        SdkDefinitionSemanticKind.INVENTORY_OPERATION,
        SdkDefinitionSemanticKind.INVENTORY_METHOD,
    }
    assert effect.transition_digest == transition.transition_digest
    assert effect.result_state == state
    assert effect.movements == transition.movements
    assert "source_path" not in str(state.to_wire())


def test_legacy_only_change_advances_definition_without_changing_manifest() -> None:
    before = _state(legacy_mode="sync")
    after = _state(legacy_mode="async")
    transition = derive_sdk_definition_transition(before, after)

    assert before.manifest.manifest_digest == after.manifest.manifest_digest
    assert before.definition_digest != after.definition_digest
    assert len(transition.movements) == 1
    movement = transition.movements[0]
    assert movement.coordinate.kind is SdkDefinitionSemanticKind.INVENTORY_METHOD
    assert movement.coordinate.parts == ("proof_sdk.client.legacy",)
    assert movement.operation is SdkDefinitionMovementOperation.CHANGE


def test_transition_rejects_cross_sdk_predecessor() -> None:
    before = _state()
    after = _state()
    object.__setattr__(after.manifest, "sdk_ref", "other_sdk")
    with pytest.raises((TypeError, ValueError)):
        derive_sdk_definition_transition(before, after)


def test_foreign_nested_schema_method_is_never_executed() -> None:
    calls: list[str] = []

    class ForeignField(FieldDefinition):
        def to_wire(self) -> dict[str, object]:
            calls.append("foreign_to_wire")
            return super().to_wire()

    state = _state()
    schema = state.manifest.schema_slices[0]
    definition = schema.types[0]
    original = definition.fields[0]
    foreign = ForeignField(
        original.field_ref,
        original.name,
        original.shape,
        original.required,
        original.nullable,
        original.default_value,
        original.constraints,
        original.aliases,
    )
    object.__setattr__(definition, "fields", (foreign,))

    with pytest.raises(TypeError, match="exact FieldDefinition"):
        derive_sdk_definition_transition(None, state)
    assert calls == []


def test_definition_digest_rejects_coherent_object_restamping() -> None:
    state = _state()
    object.__setattr__(state, "definition_digest", "sha256:" + "9" * 64)
    with pytest.raises(ValueError, match="definition_digest mismatch"):
        state.to_wire()


def test_inventory_relation_rejects_missing_contracted_method() -> None:
    state = _state()
    inventory = replace(
        state.inventory,
        method_refs=("proof_sdk.client.legacy",),
        methods=(state.inventory.methods[1],),
        operations=(
            replace(state.inventory.operations[0], method_refs=()),
            state.inventory.operations[1],
        ),
    )
    with pytest.raises(ValueError, match="manifest methods"):
        SdkDefinitionState.create(state.manifest, inventory)
