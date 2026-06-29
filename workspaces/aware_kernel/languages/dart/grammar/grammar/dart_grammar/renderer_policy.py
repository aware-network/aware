from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DartRenderPolicy:
    """Render-time policy for Dart code generation (API vs ORM profiles)."""

    # Whether API barrels should export the OIG materialization extensions.
    export_oig_extensions: bool = False
    # Whether graph-ref class attributes should be emitted as hydrated object fields.
    emit_relationship_fields: bool = True
    # Whether graph-ref class attributes targeting external OCGs should be emitted.
    emit_external_relationship_fields: bool = True
    # When set, external relationship fields are emitted only if an import override
    # exists and its package root ends with this suffix.
    external_relationship_import_root_suffix: str | None = None
    # Whether private UUID linkage fields synthesized by runtime lowering should be emitted.
    emit_foreign_key_fields: bool = True

    @classmethod
    def orm_default(cls) -> "DartRenderPolicy":
        return cls(export_oig_extensions=False)

    @classmethod
    def api_default(cls) -> "DartRenderPolicy":
        return cls(export_oig_extensions=False)

    @classmethod
    def ontology_dto_default(cls) -> "DartRenderPolicy":
        return cls(
            export_oig_extensions=False,
            emit_relationship_fields=True,
            emit_external_relationship_fields=True,
            external_relationship_import_root_suffix="_ontology_dto",
            emit_foreign_key_fields=False,
        )


__all__ = ["DartRenderPolicy"]
