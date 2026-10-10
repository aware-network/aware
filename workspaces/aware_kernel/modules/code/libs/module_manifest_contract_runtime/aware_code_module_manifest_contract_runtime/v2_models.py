"""Immutable version-2 extension meaning; never nominal evidence."""

from dataclasses import dataclass

from .models import AwareModuleSpec


@dataclass(frozen=True, slots=True)
class DeclarationTable:
    entries: tuple[tuple[str, "DeclarationValue"], ...]


type DeclarationValue = (
    str | int | bool | None | DeclarationTable | tuple["DeclarationValue", ...]
)


@dataclass(frozen=True, slots=True)
class DeclarationTag:
    state: str
    value: DeclarationValue = None


@dataclass(frozen=True, slots=True)
class PackageOccurrenceDeclaration:
    registration: DeclarationTag
    semantic_version: DeclarationTag
    semantic_package_name: DeclarationTag
    code_package_name: DeclarationTag
    source_code_package_id: DeclarationTag
    configuration: DeclarationTag
    namespace: DeclarationTag
    owned_roots: DeclarationTag
    dependency_targets: DeclarationTag


@dataclass(frozen=True, slots=True)
class PackageDeclarationV2:
    package_id: str
    registrations: tuple[DeclarationTable, ...]
    occurrence: PackageOccurrenceDeclaration
    occurrence_declared: bool


@dataclass(frozen=True, slots=True)
class AwareModuleSpecV2(AwareModuleSpec):
    package_declarations: tuple[PackageDeclarationV2, ...] = ()
