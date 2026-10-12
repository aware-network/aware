from __future__ import annotations

from enum import StrEnum

import pytest
from aware_meta_type_schema import (
    FieldDefinition,
    FrozenJson,
    IdentityDefinition,
    ScalarKind,
    ShapeKind,
    TypeDefinition,
    TypeKind,
    TypeSchemaBundle,
    ValueShape,
)
from aware_meta_type_schema.model import _token


def test_exact_string_token_fast_path_preserves_unicode_and_identity() -> None:
    token = "sha256:" + "a" * 64

    assert _token(token, "token") is token
    with pytest.raises(TypeError, match="token must be str"):
        _token(1, "token")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="token must be a non-empty token"):
        _token("", "token")

    unicode_whitespace = tuple(
        chr(codepoint)
        for codepoint in range(0x110000)
        if chr(codepoint).isspace()
    )
    assert unicode_whitespace
    assert all(not value.split() for value in unicode_whitespace)
    for whitespace in unicode_whitespace:
        for value in (
            whitespace + "token",
            "token" + whitespace,
            "left" + whitespace + "right",
        ):
            with pytest.raises(ValueError, match="token must be a non-empty token"):
                _token(value, "token")


def test_string_subclass_token_retains_legacy_hook_order() -> None:
    calls: list[str] = []

    class ObservedString(str):
        def __bool__(self) -> bool:
            calls.append("bool")
            return len(self) != 0

        def strip(self, chars: str | None = None) -> str:
            calls.append("strip")
            return super().strip(chars)

        def __iter__(self):  # type: ignore[no-untyped-def]
            calls.append("iter")
            return super().__iter__()

    value = ObservedString("token")
    assert _token(value, "token") is value
    assert calls == ["bool", "strip", "iter"]

    class RaisingEquality(str):
        def strip(self, chars: str | None = None) -> str:
            return self

        def __ne__(self, other: object) -> bool:
            raise RuntimeError("subclass equality")

    with pytest.raises(RuntimeError, match="subclass equality"):
        _token(RaisingEquality("token"), "token")

    class RaisingStrip(str):
        def strip(self, chars: str | None = None) -> str:
            raise RuntimeError("subclass strip")

    with pytest.raises(RuntimeError, match="subclass strip"):
        _token(RaisingStrip("token"), "token")

    class TokenEnum(StrEnum):
        VALUE = "token"

    assert _token(TokenEnum.VALUE, "token") is TokenEnum.VALUE


def test_identity_free_nested_api_value_and_graph_identity_share_bundle() -> None:
    address = TypeDefinition(
        type_ref="demo.Address",
        name="Address",
        kind=TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition(
                "demo.Address.city",
                "city",
                ValueShape.scalar(ScalarKind.STRING),
                required=True,
            ),
        ),
    )
    request = TypeDefinition(
        type_ref="demo.CreateRequest",
        name="CreateRequest",
        kind=TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition(
                "demo.CreateRequest.addresses",
                "addresses",
                ValueShape.list_of(ValueShape.named("demo.Address")),
                required=True,
            ),
            FieldDefinition(
                "demo.CreateRequest.labels",
                "labels",
                ValueShape.map_of(ValueShape.scalar(ScalarKind.STRING)),
            ),
        ),
    )
    account = TypeDefinition(
        type_ref="demo.Account",
        name="Account",
        kind=TypeKind.GRAPH_OBJECT,
        fields=(
            FieldDefinition(
                "demo.Account.id",
                "id",
                ValueShape.scalar(ScalarKind.UUID),
                required=True,
            ),
        ),
        identity=IdentityDefinition(("demo.Account.id",)),
    )

    bundle = TypeSchemaBundle.create(
        namespace="demo", semantic_version="1.0.0", types=(request, account, address)
    )

    assert [value.type_ref for value in bundle.types] == [
        "demo.Account",
        "demo.Address",
        "demo.CreateRequest",
    ]
    assert bundle.types[0].identity is not None
    assert bundle.types[1].identity is None
    assert bundle.schema_digest.startswith("sha256:")


def test_missing_default_and_explicit_null_default_are_distinct() -> None:
    missing = FieldDefinition(
        "demo.Value.missing",
        "missing",
        ValueShape.scalar(ScalarKind.STRING),
        nullable=True,
    )
    explicit_null = FieldDefinition(
        "demo.Value.explicit_null",
        "explicit_null",
        ValueShape.scalar(ScalarKind.STRING),
        nullable=True,
        default_value=FrozenJson.from_value(None),
    )

    assert missing.to_wire()["has_default"] is False
    assert explicit_null.to_wire()["has_default"] is True
    assert missing.to_wire() != explicit_null.to_wire()


def test_bundle_digest_is_independent_of_type_input_order() -> None:
    first = TypeDefinition(
        "demo.A", "A", TypeKind.SCALAR_ALIAS, scalar_target=ScalarKind.STRING
    )
    second = TypeDefinition(
        "demo.B", "B", TypeKind.SCALAR_ALIAS, scalar_target=ScalarKind.INTEGER
    )

    left = TypeSchemaBundle.create(
        namespace="demo", semantic_version="1", types=(first, second)
    )
    right = TypeSchemaBundle.create(
        namespace="demo", semantic_version="1", types=(second, first)
    )

    assert left == right
    assert left.schema_digest == right.schema_digest


def test_local_kind_shape_and_reference_failures_are_closed() -> None:
    with pytest.raises(ValueError, match="shape payload"):
        ValueShape(kind=ShapeKind.SCALAR, type_ref="demo.Other")
    with pytest.raises(ValueError, match="identity field refs"):
        TypeDefinition(
            "demo.Bad",
            "Bad",
            TypeKind.GRAPH_OBJECT,
            identity=IdentityDefinition(("demo.Bad.id",)),
        )
    broken = TypeDefinition(
        "demo.Broken",
        "Broken",
        TypeKind.VALUE_OBJECT,
        fields=(
            FieldDefinition(
                "demo.Broken.other", "other", ValueShape.named("demo.Missing")
            ),
        ),
    )
    with pytest.raises(ValueError, match="unresolved type ref"):
        TypeSchemaBundle.create(namespace="demo", semantic_version="1", types=(broken,))


@pytest.mark.parametrize(
    "value",
    (
        TypeDefinition(
            "demo.Choice",
            "Choice",
            TypeKind.UNION,
            union_variants=(
                ValueShape.scalar(ScalarKind.STRING),
                ValueShape.scalar(ScalarKind.INTEGER),
            ),
            discriminant_field_ref="demo.Choice.kind",
        ),
    ),
)
def test_only_union_types_accept_discriminants(value: TypeDefinition) -> None:
    assert value.discriminant_field_ref == "demo.Choice.kind"

    with pytest.raises(ValueError, match="enum types require only enum_values"):
        TypeDefinition(
            "demo.Enum",
            "Enum",
            TypeKind.ENUM,
            enum_values=("one",),
            discriminant_field_ref="demo.Enum.kind",
        )
    with pytest.raises(ValueError, match="scalar aliases require only scalar_target"):
        TypeDefinition(
            "demo.Text",
            "Text",
            TypeKind.SCALAR_ALIAS,
            scalar_target=ScalarKind.STRING,
            discriminant_field_ref="demo.Text.kind",
        )
