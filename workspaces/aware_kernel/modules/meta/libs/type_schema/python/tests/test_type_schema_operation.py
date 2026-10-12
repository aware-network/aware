from __future__ import annotations

import gc
import weakref

import aware_meta_type_schema.type_schema_operation as _operation_module
import pytest
from aware_meta_type_schema.composed_slice_advancement import (
    _slice_admission_context,
)
from aware_meta_type_schema.composition import (
    TypeOwnerBinding,
    resolve_composed_slice,
)
from aware_meta_type_schema.composition_codec import encode_composition_value
from aware_meta_type_schema.composition_transition import (
    DefinitionFragmentMovement,
    PackageRootMovement,
    SourceAttributionFragmentMovement,
    TypeOwnerBindingMovement,
    create_typed_empty_catalog,
    create_typed_empty_package,
    transition_catalog,
    transition_package,
)
from aware_meta_type_schema.definition_fragment import (
    SourceDefinitionBinding,
    TypeDefinitionFragment,
    TypeSchemaSourceAttributionFragment,
)
from aware_meta_type_schema.model import ScalarKind, TypeDefinition, TypeKind
from aware_meta_type_schema.persistent_index import PersistentBodyAuthority
from aware_meta_type_schema.positive_reader import (
    PositiveBodyRead,
    TypeSchemaPositiveReaderCapability,
)
from aware_meta_type_schema.type_schema_operation import (
    _consume_type_schema_operation_witness,
    _discard_type_schema_operation,
    _discard_type_schema_operation_witness,
    _finish_type_schema_operation,
    _open_type_schema_operation,
)


class _Store:
    def __init__(self) -> None:
        self.bodies: dict[str, PersistentBodyAuthority] = {}

    def ingest(self, values: tuple[PersistentBodyAuthority, ...]) -> None:
        self.bodies.update((value.coordinate.body_ref, value) for value in values)

    def reader(self, request_ref: str) -> TypeSchemaPositiveReaderCapability:
        def read(expected):
            body = self.bodies[expected.body_ref]
            return PositiveBodyRead(
                body.coordinate.body_ref,
                body.coordinate.body_digest,
                body.coordinate.size_bytes,
                body.coordinate.schema,
                body.canonical_bytes,
            )

        return TypeSchemaPositiveReaderCapability(
            request_ref=request_ref,
            read_body=read,
        )


def _bootstrap_operation():
    store = _Store()
    package_ref = "package:demo@1.0.0"
    fragment = TypeDefinitionFragment.create(
        TypeDefinition(
            type_ref="demo.Text",
            name="Text",
            kind=TypeKind.SCALAR_ALIAS,
            scalar_target=ScalarKind.STRING,
        )
    )
    empty_package, package_bodies = create_typed_empty_package(
        package_ref=package_ref,
        package_name="demo",
        namespace="demo",
        semantic_version="1.0.0",
        dependency_package_refs=(),
    )
    store.ingest(package_bodies)
    attribution = TypeSchemaSourceAttributionFragment.create(
        package_ref=package_ref,
        source_path="demo/demo.aware",
        document_coordinate_ref="coordinate:demo",
        bindings=(
            SourceDefinitionBinding(fragment.type_ref, fragment.to_body().coordinate),
        ),
    )
    operation = _open_type_schema_operation()
    package = transition_package(
        empty_package,
        definition_movements=(
            DefinitionFragmentMovement(fragment.type_ref, None, fragment),
        ),
        attribution_movements=(
            SourceAttributionFragmentMovement(
                attribution.source_path, None, attribution
            ),
        ),
        reader=store.reader("request:package"),
        request_ref="request:package",
        _operation_context=operation,
    )
    store.ingest(package.emitted_bodies)
    empty_catalog, catalog_bodies = create_typed_empty_catalog(
        target_package_ref=package_ref
    )
    store.ingest(catalog_bodies)
    owner = TypeOwnerBinding.create(
        type_ref=fragment.type_ref,
        package_ref=package_ref,
    )
    catalog = transition_catalog(
        empty_catalog,
        package_movements=(
            PackageRootMovement(package_ref, None, package.successor, package),
        ),
        owner_movements=(TypeOwnerBindingMovement(fragment.type_ref, None, owner),),
        reader=store.reader("request:catalog"),
        request_ref="request:catalog",
        _operation_context=operation,
    )
    store.ingest(catalog.emitted_bodies)
    composed = resolve_composed_slice(
        catalog.successor,
        root_type_refs=(fragment.type_ref,),
        reader=store.reader("request:composed"),
        request_ref="request:composed",
        _operation_context=operation,
    ).slice
    return operation, package, catalog, composed


def test_operation_witness_is_exact_single_use_and_byte_bound() -> None:
    operation, package, catalog, composed = _bootstrap_operation()
    witness = _finish_type_schema_operation(operation, composed)
    admission, canonical_bytes, _, _, _, _ = _consume_type_schema_operation_witness(
        witness,
        package_transition=package,
        catalog_transition=catalog,
        composed_slice=composed,
    )

    assert canonical_bytes == encode_composition_value(composed)
    retained = _slice_admission_context(admission)
    assert retained.slice is composed
    assert retained.canonical_bytes == canonical_bytes
    with pytest.raises(ValueError, match="not active"):
        _consume_type_schema_operation_witness(
            witness,
            package_transition=package,
            catalog_transition=catalog,
            composed_slice=composed,
        )


def test_operation_failure_cleanup_and_admission_weak_lifetime() -> None:
    operation, package, catalog, composed = _bootstrap_operation()
    witness = _finish_type_schema_operation(operation, composed)
    admission, _, _, _, _, _ = _consume_type_schema_operation_witness(
        witness,
        package_transition=package,
        catalog_transition=catalog,
        composed_slice=composed,
    )
    admission_ref = weakref.ref(admission)
    del admission
    gc.collect()
    assert admission_ref() is None

    abandoned = _open_type_schema_operation()
    _discard_type_schema_operation(abandoned)
    with pytest.raises(ValueError, match="not active"):
        _finish_type_schema_operation(abandoned, composed)
    _discard_type_schema_operation_witness(witness)


def test_current_operation_reuses_only_the_exact_predecessor_admission() -> None:
    operation, package, catalog, composed = _bootstrap_operation()
    witness = _finish_type_schema_operation(operation, composed)
    admission, _, _, _, _, _ = _consume_type_schema_operation_witness(
        witness,
        package_transition=package,
        catalog_transition=catalog,
        composed_slice=composed,
    )

    current_operation = _open_type_schema_operation()
    current_package = transition_package(
        package.successor,
        definition_movements=(),
        attribution_movements=(),
        reader=_Store().reader("request:current-package"),
        request_ref="request:current-package",
        _operation_context=current_operation,
    )
    current_catalog = transition_catalog(
        catalog.successor,
        package_movements=(),
        owner_movements=(),
        reader=_Store().reader("request:current-catalog"),
        request_ref="request:current-catalog",
        _operation_context=current_operation,
    )
    current_witness = _finish_type_schema_operation(
        current_operation,
        composed,
        predecessor_admission=admission,
    )
    current_admission, current_bytes, _, _, _, _ = (
        _consume_type_schema_operation_witness(
        current_witness,
        package_transition=current_package,
        catalog_transition=current_catalog,
        composed_slice=composed,
        )
    )

    assert current_admission is admission
    assert current_bytes == encode_composition_value(composed)


def test_operation_rejects_result_mutation_before_witness_issuance() -> None:
    operation, package, _, composed = _bootstrap_operation()
    object.__setattr__(package, "transition_ref", "sha256:" + "0" * 64)

    with pytest.raises(ValueError, match="changed after owner admission"):
        _finish_type_schema_operation(operation, composed)
    with pytest.raises(ValueError, match="not active"):
        _finish_type_schema_operation(operation, composed)


def test_witness_rejects_result_mutation_before_consumption() -> None:
    operation, package, catalog, composed = _bootstrap_operation()
    witness = _finish_type_schema_operation(operation, composed)
    object.__setattr__(catalog, "transition_ref", "sha256:" + "0" * 64)

    with pytest.raises(ValueError, match="changed after owner admission"):
        _consume_type_schema_operation_witness(
            witness,
            package_transition=package,
            catalog_transition=catalog,
            composed_slice=composed,
        )
    with pytest.raises(ValueError, match="not active"):
        _consume_type_schema_operation_witness(
            witness,
            package_transition=package,
            catalog_transition=catalog,
            composed_slice=composed,
        )


def test_operation_guard_matcher_binding_is_behavior_free_and_terminal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def hostile_matcher(value: object, guard: object) -> bool:
        del value, guard
        calls.append("called")
        return True

    operation, _, _, composed = _bootstrap_operation()
    with monkeypatch.context() as changed:
        changed.setattr(
            _operation_module,
            "_matches_protected_operand_guard",
            hostile_matcher,
        )
        with pytest.raises(ValueError, match="verification primitive changed"):
            _finish_type_schema_operation(operation, composed)
    assert calls == []
    with pytest.raises(ValueError, match="not active"):
        _finish_type_schema_operation(operation, composed)

    operation, package, catalog, composed = _bootstrap_operation()
    witness = _finish_type_schema_operation(operation, composed)
    with monkeypatch.context() as changed:
        changed.setattr(
            _operation_module,
            "_matches_protected_operand_guard",
            hostile_matcher,
        )
        with pytest.raises(ValueError, match="verification primitive changed"):
            _consume_type_schema_operation_witness(
                witness,
                package_transition=package,
                catalog_transition=catalog,
                composed_slice=composed,
            )
    assert calls == []
    with pytest.raises(ValueError, match="not active"):
        _consume_type_schema_operation_witness(
            witness,
            package_transition=package,
            catalog_transition=catalog,
            composed_slice=composed,
        )


@pytest.mark.parametrize("builtin_name", ("type", "object", "list", "len"))
def test_operation_verifier_rejects_builtin_shadow_without_behavior(
    monkeypatch: pytest.MonkeyPatch,
    builtin_name: str,
) -> None:
    calls: list[str] = []

    def hostile_type(value: object) -> type[object]:
        calls.append("called")
        return type(value)

    operation, _, _, composed = _bootstrap_operation()
    with monkeypatch.context() as changed:
        changed.setattr(
            _operation_module, builtin_name, hostile_type, raising=False
        )
        with pytest.raises(ValueError, match="verification primitive changed"):
            _finish_type_schema_operation(operation, composed)
    assert calls == []
    with pytest.raises(ValueError, match="not active"):
        _finish_type_schema_operation(operation, composed)

    operation, package, catalog, composed = _bootstrap_operation()
    witness = _finish_type_schema_operation(operation, composed)
    with monkeypatch.context() as changed:
        changed.setattr(
            _operation_module, builtin_name, hostile_type, raising=False
        )
        with pytest.raises(ValueError, match="verification primitive changed"):
            _consume_type_schema_operation_witness(
                witness,
                package_transition=package,
                catalog_transition=catalog,
                composed_slice=composed,
            )
    assert calls == []
    with pytest.raises(ValueError, match="not active"):
        _consume_type_schema_operation_witness(
            witness,
            package_transition=package,
            catalog_transition=catalog,
            composed_slice=composed,
        )


def test_operation_verifier_rejects_paired_matcher_restamp_without_behavior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def hostile_matcher(value: object, guard: object) -> bool:
        del value, guard
        calls.append("called")
        return True

    operation, _, _, composed = _bootstrap_operation()
    with monkeypatch.context() as changed:
        changed.setattr(
            _operation_module, "_matches_protected_operand_guard", hostile_matcher
        )
        changed.setattr(_operation_module, "_RETAINED_GUARD_MATCHER", hostile_matcher)
        with pytest.raises(ValueError, match="verification primitive changed"):
            _finish_type_schema_operation(operation, composed)
    assert calls == []
    with pytest.raises(ValueError, match="not active"):
        _finish_type_schema_operation(operation, composed)

    for name in ("_RETAINED_DICT_CONTAINS", "_RETAINED_DICT_GETITEM"):
        operation, _, _, composed = _bootstrap_operation()
        with monkeypatch.context() as changed:
            changed.setattr(_operation_module, name, hostile_matcher)
            with pytest.raises(ValueError, match="verification primitive changed"):
                _finish_type_schema_operation(operation, composed)
        assert calls == []
        with pytest.raises(ValueError, match="not active"):
            _finish_type_schema_operation(operation, composed)
