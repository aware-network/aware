from __future__ import annotations

import pytest
from aware_meta_type_schema import (
    FieldDefinition,
    ScalarKind,
    TypeDefinition,
    TypeKind,
    TypeSchemaBundle,
    TypeSchemaSlice,
    ValueShape,
)
from aware_meta_type_schema.encoding import digest_payload
from aware_meta_type_schema.model import SLICE_CONTRACT


def _bundle() -> TypeSchemaBundle:
    leaf = TypeDefinition(
        "demo.Leaf", "Leaf", TypeKind.SCALAR_ALIAS, scalar_target=ScalarKind.STRING
    )
    child = TypeDefinition(
        "demo.Child",
        "Child",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition("demo.Child.leaf", "leaf", ValueShape.named("demo.Leaf")),
        ),
    )
    root = TypeDefinition(
        "demo.Root",
        "Root",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition(
                "demo.Root.children",
                "children",
                ValueShape.list_of(ValueShape.named("demo.Child")),
            ),
        ),
    )
    unrelated = TypeDefinition(
        "demo.Unrelated",
        "Unrelated",
        TypeKind.SCALAR_ALIAS,
        scalar_target=ScalarKind.BOOLEAN,
    )
    return TypeSchemaBundle.create(
        namespace="demo",
        semantic_version="1",
        types=(unrelated, root, leaf, child),
    )


def test_slice_is_exact_transitive_closure() -> None:
    value = TypeSchemaSlice.create(_bundle(), root_type_refs=("demo.Root",))

    assert value.root_type_refs == ("demo.Root",)
    assert [item.type_ref for item in value.types] == [
        "demo.Child",
        "demo.Leaf",
        "demo.Root",
    ]
    assert value.slice_digest.startswith("sha256:")


def test_slice_rejects_missing_root_and_extra_type() -> None:
    bundle = _bundle()
    with pytest.raises(ValueError, match="unresolved type ref"):
        TypeSchemaSlice.create(bundle, root_type_refs=("demo.Missing",))

    semantic = {
        "contract": SLICE_CONTRACT,
        "bundle_digest": bundle.schema_digest,
        "namespace": bundle.namespace,
        "semantic_version": bundle.semantic_version,
        "root_type_refs": ["demo.Root"],
        "types": [item.to_wire() for item in bundle.types],
    }
    with pytest.raises(ValueError, match="outside closure"):
        TypeSchemaSlice(
            bundle.schema_digest,
            bundle.namespace,
            bundle.semantic_version,
            ("demo.Root",),
            bundle.types,
            digest_payload(SLICE_CONTRACT, semantic),
        )


def test_nested_union_references_enter_closure() -> None:
    bundle = _bundle()
    choice = TypeDefinition(
        "demo.Choice",
        "Choice",
        TypeKind.UNION,
        union_variants=(
            ValueShape.named("demo.Root"),
            ValueShape.scalar(ScalarKind.STRING),
        ),
    )
    extended = TypeSchemaBundle.create(
        namespace="demo",
        semantic_version="2",
        types=(*bundle.types, choice),
    )

    value = TypeSchemaSlice.create(extended, root_type_refs=("demo.Choice",))

    assert {item.type_ref for item in value.types} == {
        "demo.Choice",
        "demo.Root",
        "demo.Child",
        "demo.Leaf",
    }
