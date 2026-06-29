from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from python_grammar.import_grouping import public_label_from_import_root


DEFAULT_BASE_CLASS_MODULE = "aware_orm.models.orm_model"
DEFAULT_BASE_CLASS_NAME = "ORMModel"
DEFAULT_PYTHON_SUPPORT_IMPORT_ROOTS = {
    "aware_types": public_label_from_import_root("aware_types"),
}
DEFAULT_ORM_SUPPORT_IMPORT_ROOTS = {
    **DEFAULT_PYTHON_SUPPORT_IMPORT_ROOTS,
    "aware_orm": public_label_from_import_root("aware_orm"),
}


def _default_python_support_import_roots() -> dict[str, str]:
    return dict(DEFAULT_PYTHON_SUPPORT_IMPORT_ROOTS)


def _default_orm_support_import_roots() -> dict[str, str]:
    return dict(DEFAULT_ORM_SUPPORT_IMPORT_ROOTS)


@dataclass(frozen=True)
class PythonRenderPolicy:
    """
    Render-time policy for Python code generation.

    This is the SSOT for "what we emit" vs "what we skip", so DTO evolution can
    be expressed as policy changes rather than forking the renderer.
    """

    # Base class for rendered *model* classes (not IO models).
    base_class_module: str = DEFAULT_BASE_CLASS_MODULE
    base_class_name: str = DEFAULT_BASE_CLASS_NAME
    support_import_roots: Mapping[str, str] = field(default_factory=_default_orm_support_import_roots)

    # Feature flags (ORM defaults preserve existing behavior).
    emit_relationship_fields: bool = True
    emit_external_relationship_fields: bool = True
    external_relationship_import_root_suffix: str | None = None
    emit_foreign_key_fields: bool = True
    emit_edge_fields: bool = True
    emit_edge_backed_properties: bool = True

    emit_function_facades: bool = True
    emit_function_io_models: bool = True
    emit_function_registry: bool = True
    honor_exclude_serialization: bool = True

    # DTO/wire contract policy:
    # - When True, top-level items in an emitted file (enums, classes) are rendered
    #   in the same order they appear in the source `.aware` file(s) when code
    #   section bindings are present.
    # - This is important for human readability and for treating `.aware` as the SSOT.
    respect_source_order: bool = False

    # When True, DTO discriminators with constant string defaults (e.g. `operation`)
    # are emitted as raw Python literals (e.g. `operation: str = "tag"`) rather than
    # always wrapping the default in `Field(default=...)`.
    emit_discriminator_literals: bool = False

    # When True, discriminator *tag* fields in union variants are typed as
    # `Literal["tag"]` to prevent accidental tag drift (e.g. `operation="typo"`).
    #
    # Note: This may trigger "incompatible override" warnings in static type checkers
    # because variants narrow a mutable attribute type from `str` to `Literal[...]`.
    emit_discriminator_literal_types: bool = False

    # When True, DTO wrapper envelopes that store a discriminator *base* type
    # (e.g. `EnvironmentOperationRequest`) will:
    # - preserve subclass payloads during serialization (via SerializeAsAny)
    # - parse raw dict payloads into the correct subclass (via field validators)
    #
    # SSOT for discriminator tags/keys remains compiled OCG annotations (DISCRIMINATE).
    emit_discriminated_union_parsers: bool = False

    # When True, model-typed fields that point at external dependency graphs are
    # imported at runtime. API DTO packages need this because they are plain
    # Pydantic BaseModel packages and do not run ORM package bootstrap rebuild.
    runtime_import_external_model_fields: bool = False

    @classmethod
    def orm_default(cls) -> "PythonRenderPolicy":
        return cls()

    @classmethod
    def orm_models_default(cls) -> "PythonRenderPolicy":
        return cls(
            emit_function_facades=False,
            emit_function_io_models=False,
            emit_function_registry=False,
        )

    @classmethod
    def api_default(cls) -> "PythonRenderPolicy":
        # API profile: no ORM runtime sugar (FKs/edges/call-chain facades/registry).
        return cls(
            base_class_module="pydantic",
            base_class_name="BaseModel",
            support_import_roots=_default_python_support_import_roots(),
            emit_relationship_fields=True,
            emit_foreign_key_fields=False,
            emit_edge_fields=False,
            emit_edge_backed_properties=False,
            emit_function_facades=False,
            emit_function_io_models=False,
            emit_function_registry=False,
            honor_exclude_serialization=False,
            respect_source_order=True,
            emit_discriminator_literals=True,
            emit_discriminator_literal_types=True,
            emit_discriminated_union_parsers=True,
            runtime_import_external_model_fields=True,
        )

    @classmethod
    def ontology_dto_default(cls) -> "PythonRenderPolicy":
        # Ontology DTO profile: latest ontology data only. Internal aggregate relationships
        # remain nested DTO payloads; external graph relationships are allowed only through
        # generated dependency DTO packages. Runtime helpers stay out.
        return cls(
            base_class_module="pydantic",
            base_class_name="BaseModel",
            support_import_roots=_default_python_support_import_roots(),
            emit_relationship_fields=True,
            emit_external_relationship_fields=True,
            external_relationship_import_root_suffix="_ontology_dto",
            emit_foreign_key_fields=False,
            emit_edge_fields=False,
            emit_edge_backed_properties=False,
            emit_function_facades=False,
            emit_function_io_models=False,
            emit_function_registry=False,
            honor_exclude_serialization=False,
            respect_source_order=True,
            emit_discriminator_literals=True,
            emit_discriminator_literal_types=True,
            emit_discriminated_union_parsers=True,
        )


__all__ = [
    "DEFAULT_BASE_CLASS_MODULE",
    "DEFAULT_BASE_CLASS_NAME",
    "DEFAULT_ORM_SUPPORT_IMPORT_ROOTS",
    "DEFAULT_PYTHON_SUPPORT_IMPORT_ROOTS",
    "PythonRenderPolicy",
]
