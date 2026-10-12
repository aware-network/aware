"""Content-addressed semantic definitions and exact source attribution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from .encoding import digest_payload
from .model import TypeDefinition
from .persistent_index import PersistentBodyAuthority, PersistentBodyCoordinate

TYPE_DEFINITION_FRAGMENT_CONTRACT = "aware.meta.type-schema.definition-fragment.v1"
SOURCE_ATTRIBUTION_FRAGMENT_CONTRACT = (
    "aware.meta.type-schema.source-attribution-fragment.v1"
)


class TypeSchemaFragmentError(ValueError):
    """Raised when semantic fragment or ownership attribution is inexact."""


def _token(value: str, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value.strip() != value
        or any(character.isspace() for character in value)
    ):
        raise TypeSchemaFragmentError(f"{field} must be a nonempty token")
    return value


def _source_path(value: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise TypeSchemaFragmentError("source_path must be normalized text")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise TypeSchemaFragmentError("source_path must be normalized and relative")
    if path.suffix != ".aware":
        raise TypeSchemaFragmentError("source_path must identify .aware source")
    return value


@dataclass(frozen=True, slots=True)
class TypeDefinitionFragment:
    definition: TypeDefinition
    referenced_type_refs: tuple[str, ...]
    fragment_ref: str
    contract: str = TYPE_DEFINITION_FRAGMENT_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != TYPE_DEFINITION_FRAGMENT_CONTRACT:
            raise TypeSchemaFragmentError("definition fragment contract unsupported")
        if not isinstance(self.definition, TypeDefinition):
            raise TypeError("definition must be TypeDefinition")
        if type(self.referenced_type_refs) is not tuple:
            raise TypeSchemaFragmentError("referenced_type_refs must be tuple")
        refs = tuple(
            sorted(
                _token(value, "referenced_type_ref")
                for value in self.referenced_type_refs
            )
        )
        if refs != self.referenced_type_refs or len(refs) != len(set(refs)):
            raise TypeSchemaFragmentError(
                "referenced_type_refs must be sorted and unique"
            )
        if refs != tuple(sorted(self.definition.referenced_type_refs())):
            raise TypeSchemaFragmentError(
                "referenced_type_refs do not match definition"
            )
        expected = digest_payload(self.contract, self.semantic_wire())
        if self.fragment_ref != expected:
            raise TypeSchemaFragmentError(f"fragment_ref mismatch; expected {expected}")

    @classmethod
    def create(cls, definition: TypeDefinition) -> TypeDefinitionFragment:
        if not isinstance(definition, TypeDefinition):
            raise TypeError("definition must be TypeDefinition")
        refs = tuple(sorted(definition.referenced_type_refs()))
        semantic = {
            "contract": TYPE_DEFINITION_FRAGMENT_CONTRACT,
            "definition": definition.to_wire(),
            "referenced_type_refs": list(refs),
        }
        return cls(
            definition,
            refs,
            digest_payload(TYPE_DEFINITION_FRAGMENT_CONTRACT, semantic),
        )

    @property
    def type_ref(self) -> str:
        return self.definition.type_ref

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "definition": self.definition.to_wire(),
            "referenced_type_refs": list(self.referenced_type_refs),
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "fragment_ref": self.fragment_ref}

    def to_body(self) -> PersistentBodyAuthority:
        return PersistentBodyAuthority.from_wire(
            schema=self.contract,
            ref_field="fragment_ref",
            authority_ref=self.fragment_ref,
            wire=self.to_wire(),
        )


@dataclass(frozen=True, slots=True)
class SourceDefinitionBinding:
    type_ref: str
    definition: PersistentBodyCoordinate

    def __post_init__(self) -> None:
        object.__setattr__(self, "type_ref", _token(self.type_ref, "type_ref"))
        if not isinstance(self.definition, PersistentBodyCoordinate):
            raise TypeError("definition must be PersistentBodyCoordinate")
        if self.definition.schema != TYPE_DEFINITION_FRAGMENT_CONTRACT:
            raise TypeSchemaFragmentError(
                "source binding must reference definition fragment"
            )

    def to_wire(self) -> dict[str, object]:
        return {"type_ref": self.type_ref, "definition": self.definition.to_wire()}


@dataclass(frozen=True, slots=True)
class TypeSchemaSourceAttributionFragment:
    package_ref: str
    source_path: str
    document_coordinate_ref: str
    bindings: tuple[SourceDefinitionBinding, ...]
    attribution_ref: str
    contract: str = SOURCE_ATTRIBUTION_FRAGMENT_CONTRACT

    def __post_init__(self) -> None:
        if self.contract != SOURCE_ATTRIBUTION_FRAGMENT_CONTRACT:
            raise TypeSchemaFragmentError("source attribution contract unsupported")
        object.__setattr__(self, "package_ref", _token(self.package_ref, "package_ref"))
        object.__setattr__(self, "source_path", _source_path(self.source_path))
        object.__setattr__(
            self,
            "document_coordinate_ref",
            _token(self.document_coordinate_ref, "document_coordinate_ref"),
        )
        if type(self.bindings) is not tuple:
            raise TypeSchemaFragmentError("source bindings must be immutable tuple")
        bindings = tuple(sorted(self.bindings, key=lambda item: item.type_ref))
        if bindings != self.bindings or any(
            not isinstance(item, SourceDefinitionBinding) for item in bindings
        ):
            raise TypeSchemaFragmentError("source bindings must be typed and sorted")
        refs = tuple(item.type_ref for item in bindings)
        if len(refs) != len(set(refs)):
            raise TypeSchemaFragmentError("source bindings contain duplicate type_ref")
        expected = digest_payload(self.contract, self.semantic_wire())
        if self.attribution_ref != expected:
            raise TypeSchemaFragmentError(
                f"attribution_ref mismatch; expected {expected}"
            )

    @classmethod
    def create(
        cls,
        *,
        package_ref: str,
        source_path: str,
        document_coordinate_ref: str,
        bindings: tuple[SourceDefinitionBinding, ...],
    ) -> TypeSchemaSourceAttributionFragment:
        bindings = tuple(sorted(bindings, key=lambda item: item.type_ref))
        normalized_package_ref = _token(package_ref, "package_ref")
        normalized_source_path = _source_path(source_path)
        normalized_coordinate_ref = _token(
            document_coordinate_ref, "document_coordinate_ref"
        )
        semantic = {
            "contract": SOURCE_ATTRIBUTION_FRAGMENT_CONTRACT,
            "package_ref": normalized_package_ref,
            "source_path": normalized_source_path,
            "document_coordinate_ref": normalized_coordinate_ref,
            "bindings": [item.to_wire() for item in bindings],
        }
        return cls(
            normalized_package_ref,
            normalized_source_path,
            normalized_coordinate_ref,
            bindings,
            digest_payload(SOURCE_ATTRIBUTION_FRAGMENT_CONTRACT, semantic),
        )

    def semantic_wire(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "package_ref": self.package_ref,
            "source_path": self.source_path,
            "document_coordinate_ref": self.document_coordinate_ref,
            "bindings": [item.to_wire() for item in self.bindings],
        }

    def to_wire(self) -> dict[str, object]:
        return {**self.semantic_wire(), "attribution_ref": self.attribution_ref}

    def to_body(self) -> PersistentBodyAuthority:
        return PersistentBodyAuthority.from_wire(
            schema=self.contract,
            ref_field="attribution_ref",
            authority_ref=self.attribution_ref,
            wire=self.to_wire(),
        )


__all__ = [
    "SOURCE_ATTRIBUTION_FRAGMENT_CONTRACT",
    "TYPE_DEFINITION_FRAGMENT_CONTRACT",
    "SourceDefinitionBinding",
    "TypeDefinitionFragment",
    "TypeSchemaFragmentError",
    "TypeSchemaSourceAttributionFragment",
]
