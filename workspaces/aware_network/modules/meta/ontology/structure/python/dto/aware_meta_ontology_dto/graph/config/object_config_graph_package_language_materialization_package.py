from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Code Ontology Dto
from aware_code_ontology_dto.code.code_enums import CodeLanguage

if TYPE_CHECKING:
    from aware_code_ontology_dto.package.code_package import CodePackage
    from aware_meta_ontology_dto.graph.config.object_config_graph_package_language_materialization import (
        ObjectConfigGraphPackageLanguageMaterialization,
    )


class ObjectConfigGraphPackageLanguageMaterializationPackage(BaseModel):
    """
    Generated CodePackage output produced by one OCG package language target.
    This is materialized output truth, not declaration intent. The parent
    `ObjectConfigGraphPackageLanguageMaterialization` declares what should be
    produced; this child points at the actual generated `CodePackage` committed
    from that materialization.
    """

    # Relationships
    code_package: CodePackage | None = Field(
        default=None, description="Generated CodePackage containing materialized files for this target."
    )
    object_config_graph_package_language_materialization: ObjectConfigGraphPackageLanguageMaterialization | None = (
        Field(
            default=None,
            description="Reverse view for ObjectConfigGraphPackageLanguageMaterialization.materialized_packages",
        )
    )

    # Attributes
    package_output_key: str = Field(
        default="language_package", description="Output key from the semantic materialization artifact contract."
    )
    package_name: str = Field(description="Generated language package/distribution name.")
    language: CodeLanguage = Field(description="Target language plugin used to produce the package.")
    output_dir: str = Field(description="Package-root-relative output directory declared by the target.")
    package_root: str = Field(description="Materialized package root relative to the workspace root.")
    sources_root: str | None = Field(
        default=None, description="Generated source root relative to the CodePackage package root."
    )
    import_root: str | None = Field(default=None, description="Import root / SQL namespace exposed by this package.")
    materialization_source: str = Field(
        default="ontology", description='Materialization source profile, e.g. "ontology" or "ontology_orm_models".'
    )
    renderer_kind: str | None = Field(
        default=None, description='Optional renderer implementation selector, e.g. "sqlite".'
    )
    renderer_profile: str | None = Field(default=None, description='Optional renderer profile, e.g. "orm_models".')
    object_config_graph_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Historical OIG commit for the source OCG used to render this package."
    )
    code_package_object_instance_graph_commit_id: UUID | None = Field(
        default=None, description="Historical OIG commit for the generated CodePackage snapshot."
    )
    status: str = Field(
        default="materialized", description="Materialization status from the language plugin/package writer."
    )
