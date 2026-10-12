from __future__ import annotations

from aware_meta_type_schema import (
    FieldDefinition,
    FrozenJson,
    IdentityDefinition,
    ScalarKind,
    ShapeKind,
    TypeDefinition,
    TypeKind,
    TypeSchemaSlice,
    ValueShape,
)

from .model import (
    SDK_CONTRACT,
    SdkContractManifest,
    SdkMethodContract,
    SdkOperationContract,
    SdkTargetContract,
)


def _exact_str(value: object, field: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{field} must be exact str")


def _optional_str(value: object, field: str) -> None:
    if value is not None:
        _exact_str(value, field)


def _str_tuple(value: object, field: str) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{field} must be exact tuple")
    for index, item in enumerate(value):
        _exact_str(item, f"{field}[{index}]")


def _frozen(value: object, field: str) -> None:
    if type(value) is not FrozenJson:
        raise TypeError(f"{field} must be exact FrozenJson")
    _exact_str(value.canonical, f"{field}.canonical")


def _shape(value: object, field: str) -> None:
    if type(value) is not ValueShape:
        raise TypeError(f"{field} must be exact ValueShape")
    if type(value.kind) is not ShapeKind:
        raise TypeError(f"{field}.kind must be exact ShapeKind")
    if value.scalar_kind is not None and type(value.scalar_kind) is not ScalarKind:
        raise TypeError(f"{field}.scalar_kind must be exact ScalarKind or None")
    _optional_str(value.type_ref, f"{field}.type_ref")
    if value.element is not None:
        _shape(value.element, f"{field}.element")
    if value.map_value is not None:
        _shape(value.map_value, f"{field}.map_value")
    if type(value.variants) is not tuple:
        raise TypeError(f"{field}.variants must be exact tuple")
    for index, variant in enumerate(value.variants):
        _shape(variant, f"{field}.variants[{index}]")


def _field(value: object, field: str) -> None:
    if type(value) is not FieldDefinition:
        raise TypeError(f"{field} must be exact FieldDefinition")
    _exact_str(value.field_ref, f"{field}.field_ref")
    _exact_str(value.name, f"{field}.name")
    _shape(value.shape, f"{field}.shape")
    if type(value.required) is not bool or type(value.nullable) is not bool:
        raise TypeError(f"{field} flags must be exact bool")
    if value.default_value is not None:
        _frozen(value.default_value, f"{field}.default_value")
    _frozen(value.constraints, f"{field}.constraints")
    _str_tuple(value.aliases, f"{field}.aliases")


def _type(value: object, field: str) -> None:
    if type(value) is not TypeDefinition:
        raise TypeError(f"{field} must be exact TypeDefinition")
    _exact_str(value.type_ref, f"{field}.type_ref")
    _exact_str(value.name, f"{field}.name")
    if type(value.kind) is not TypeKind:
        raise TypeError(f"{field}.kind must be exact TypeKind")
    if type(value.fields) is not tuple:
        raise TypeError(f"{field}.fields must be exact tuple")
    for index, item in enumerate(value.fields):
        _field(item, f"{field}.fields[{index}]")
    if value.identity is not None:
        if type(value.identity) is not IdentityDefinition:
            raise TypeError(f"{field}.identity must be exact IdentityDefinition")
        _str_tuple(value.identity.field_refs, f"{field}.identity.field_refs")
    _str_tuple(value.enum_values, f"{field}.enum_values")
    if type(value.union_variants) is not tuple:
        raise TypeError(f"{field}.union_variants must be exact tuple")
    for index, variant in enumerate(value.union_variants):
        _shape(variant, f"{field}.union_variants[{index}]")
    if value.scalar_target is not None and type(value.scalar_target) is not ScalarKind:
        raise TypeError(f"{field}.scalar_target must be exact ScalarKind or None")
    _optional_str(value.discriminant_field_ref, f"{field}.discriminant_field_ref")
    _frozen(value.constraints, f"{field}.constraints")
    _str_tuple(value.aliases, f"{field}.aliases")


def _slice(value: object, field: str) -> None:
    if type(value) is not TypeSchemaSlice:
        raise TypeError(f"{field} must be exact TypeSchemaSlice")
    for name in ("bundle_digest", "namespace", "semantic_version", "slice_digest", "contract"):
        _exact_str(getattr(value, name), f"{field}.{name}")
    _str_tuple(value.root_type_refs, f"{field}.root_type_refs")
    if type(value.types) is not tuple:
        raise TypeError(f"{field}.types must be exact tuple")
    for index, item in enumerate(value.types):
        _type(item, f"{field}.types[{index}]")


def validate_sdk_contract_manifest_graph(value: object, field: str = "manifest") -> None:
    if type(value) is not SdkContractManifest:
        raise TypeError(f"{field} must be exact SdkContractManifest")
    for name in ("sdk_ref", "semantic_version", "manifest_digest", "contract"):
        _exact_str(getattr(value, name), f"{field}.{name}")
    if value.contract != SDK_CONTRACT:
        raise ValueError(f"{field}.contract is unsupported")
    for name, expected in (
        ("targets", SdkTargetContract),
        ("operations", SdkOperationContract),
        ("methods", SdkMethodContract),
    ):
        items = getattr(value, name)
        if type(items) is not tuple:
            raise TypeError(f"{field}.{name} must be exact tuple")
        for index, item in enumerate(items):
            if type(item) is not expected:
                raise TypeError(f"{field}.{name}[{index}] must be exact {expected.__name__}")
            item.__post_init__()
    if type(value.schema_slices) is not tuple:
        raise TypeError(f"{field}.schema_slices must be exact tuple")
    for index, item in enumerate(value.schema_slices):
        _slice(item, f"{field}.schema_slices[{index}]")
    expected = SdkContractManifest.create(
        sdk_ref=value.sdk_ref,
        semantic_version=value.semantic_version,
        targets=value.targets,
        schema_slices=value.schema_slices,
        operations=value.operations,
        methods=value.methods,
    )
    if value.manifest_digest != expected.manifest_digest:
        raise ValueError(f"{field}.manifest_digest differs from fresh derivation")


def validate_sdk_contract_inventory_graph(value: object, field: str = "inventory") -> None:
    from .definition import (
        SdkContractInventory,
        SdkMethodInventoryEntry,
        SdkOperationInventoryEntry,
    )

    if type(value) is not SdkContractInventory:
        raise TypeError(f"{field} must be exact SdkContractInventory")
    _exact_str(value.sdk_ref, f"{field}.sdk_ref")
    for name in ("operation_refs", "contracted_operation_refs", "legacy_operation_refs", "method_refs"):
        _str_tuple(getattr(value, name), f"{field}.{name}")
    if type(value.operations) is not tuple or any(type(item) is not SdkOperationInventoryEntry for item in value.operations):
        raise TypeError(f"{field}.operations must contain exact SdkOperationInventoryEntry")
    if type(value.methods) is not tuple or any(type(item) is not SdkMethodInventoryEntry for item in value.methods):
        raise TypeError(f"{field}.methods must contain exact SdkMethodInventoryEntry")
    value.__post_init__()


def validate_sdk_definition_state_graph(
    value: object, field: str = "definition", *, check_digest: bool = True
) -> None:
    from .definition import SDK_DEFINITION_STATE, SdkDefinitionState, _sha256

    if type(value) is not SdkDefinitionState:
        raise TypeError(f"{field} must be exact SdkDefinitionState")
    validate_sdk_contract_manifest_graph(value.manifest, f"{field}.manifest")
    validate_sdk_contract_inventory_graph(value.inventory, f"{field}.inventory")
    _exact_str(value.contract, f"{field}.contract")
    if value.contract != SDK_DEFINITION_STATE:
        raise ValueError(f"{field}.contract is unsupported")
    if check_digest:
        _sha256(value.definition_digest, f"{field}.definition_digest")
    if value.manifest.sdk_ref != value.inventory.sdk_ref:
        raise ValueError("manifest and inventory sdk_ref differ")
    manifest_operations = tuple(item.operation_ref for item in value.manifest.operations)
    contracted = set(value.inventory.contracted_operation_refs)
    if not set(manifest_operations).issubset(contracted):
        raise ValueError("manifest operations must be a contracted inventory subset")
    selected = set(manifest_operations)
    expected_methods = tuple(
        item.method_ref for item in value.inventory.methods if item.operation_ref in selected
    )
    manifest_methods = tuple(item.method_ref for item in value.manifest.methods)
    if manifest_methods != expected_methods:
        raise ValueError("manifest methods must equal methods of contracted operations")


__all__ = [
    "validate_sdk_contract_inventory_graph",
    "validate_sdk_contract_manifest_graph",
    "validate_sdk_definition_state_graph",
]
