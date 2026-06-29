from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import Field

# Code Ontology Orm Models
from aware_code_ontology_orm_models.code.code_enums import CodeLanguage

# Orm
from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology_orm_models.graph.config.object_config_graph_package import ObjectConfigGraphPackage
    from aware_meta_ontology_orm_models.graph.config.object_config_graph_package_language_materialization_package import (
        ObjectConfigGraphPackageLanguageMaterializationPackage,
    )


class ObjectConfigGraphPackageLanguageMaterialization(ORMModel):
    """
    One language materialization target declared by an ObjectConfigGraphPackage.
    This is semantic package intent, not renderer output. Language plugins still
    own artifact-level receipts; this child only declares which language
    CodePackage surfaces the OCG package requires.
    """

    # Relationships
    materialized_packages: list[ObjectConfigGraphPackageLanguageMaterializationPackage] = Field(
        default_factory=list, description="Generated CodePackage outputs produced for this target."
    )
    object_config_graph_package: ObjectConfigGraphPackage | None = Field(
        default=None, exclude=True, description="Reverse view for ObjectConfigGraphPackage.language_materializations"
    )

    # Attributes
    target_key: str = Field(description="Globally stable target identity, expected to include package and role.")
    role: str = Field(description='Human/stable role inside the owning OCG package, e.g. "local_state_sqlite".')
    language: CodeLanguage = Field(description="Target language plugin.")
    output_dir: str = Field(description="Package-root-relative output directory for generated files.")
    import_root: str = Field(description="Import root / SQL namespace expected by the generated target.")
    package_name: str = Field(description="Language package/distribution name emitted for this target.")
    materialization_source: str = Field(
        default="ontology", description='Materialization source profile, e.g. "ontology" or "ontology_orm_models".'
    )
    renderer_kind: str | None = Field(
        default=None, description='Optional renderer implementation selector, e.g. "sqlite".'
    )
    renderer_profile: str | None = Field(default=None, description='Optional renderer profile, e.g. "orm_models".')
    stable_ids_import_root: str | None = Field(
        default=None, description="Optional stable-id import root override for generated source."
    )
    source_is_runtime: bool = Field(
        default=False, description="True when this target materializes runtime handler surfaces."
    )

    # Foreign Keys
    object_config_graph_package_id: UUID = Field(
        description="Foreign key for ObjectConfigGraphPackage.language_materializations"
    )
