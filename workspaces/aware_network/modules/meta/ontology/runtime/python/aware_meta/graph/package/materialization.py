from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_code_ontology.projection.code_section_projection import CodeSectionProjection
from aware_meta.fqn_resolver import FqnResolver
from aware_meta.graph.config.materialization import (
    ObjectConfigGraphIdentityMaterializationRecord,
    materialize_object_config_graph_identity,
)
from aware_meta.graph.projection.declarations import ProjectionDeclaration
from aware_meta.graph.projection.compiler import (
    compile_object_config_graph_projections,
)
from aware_meta.graph.projection.materialization import (
    ProjectionIdentityMaterializationRecord,
    ProjectionObservableMaterializationRecord,
    materialize_projection_identities,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.projection.object_projection_graph_declaration import (
    ObjectProjectionGraphDeclaration,
)


@dataclass(frozen=True, slots=True)
class MetaObjectConfigGraphPackageProjectionCompilation:
    declarations: tuple[ObjectProjectionGraphDeclaration, ...]
    declarations_by_name: dict[str, ProjectionDeclaration]
    projection_names: frozenset[str]


@dataclass(frozen=True, slots=True)
class MetaObjectConfigGraphPackageMaterializationReceipt:
    object_config_graph_id: UUID
    object_config_graph_hash: str
    layout_hash: str | None
    object_config_graph_identity: ObjectConfigGraphIdentityMaterializationRecord | None
    projection_identities: tuple[ProjectionIdentityMaterializationRecord, ...]
    observables: tuple[ProjectionObservableMaterializationRecord, ...]


def compile_object_config_graph_package_projections(
    *,
    code_section_projections: list[CodeSectionProjection],
    fqn_resolver: FqnResolver,
    object_config_graph_id: UUID,
    ocg_fqn_prefix: str,
) -> MetaObjectConfigGraphPackageProjectionCompilation:
    declarations, declarations_by_name = compile_object_config_graph_projections(
        code_section_projections,
        fqn_resolver,
        object_config_graph_id=object_config_graph_id,
        ocg_fqn_prefix=ocg_fqn_prefix,
    )
    return MetaObjectConfigGraphPackageProjectionCompilation(
        declarations=tuple(declarations),
        declarations_by_name=declarations_by_name,
        projection_names=frozenset(declarations_by_name),
    )


def materialize_object_config_graph_package_identity_plane(
    *,
    graph: ObjectConfigGraph,
    projection_declarations_by_name: dict[str, ProjectionDeclaration],
) -> MetaObjectConfigGraphPackageMaterializationReceipt:
    """
    Attach package-level identity-plane materialization to a full OCG payload.

    This package boundary composes the OCG-owned OCGI materializer with the
    projection-owned OPGI/observable materializer and emits a deterministic
    receipt suitable for the future Meta materialization/index cache.
    """

    if not projection_declarations_by_name:
        return MetaObjectConfigGraphPackageMaterializationReceipt(
            object_config_graph_id=graph.id,
            object_config_graph_hash=str(graph.hash or ""),
            layout_hash=graph.layout_hash,
            object_config_graph_identity=None,
            projection_identities=(),
            observables=(),
        )

    ocgi_result = materialize_object_config_graph_identity(
        ocg_fqn_prefix=graph.fqn_prefix,
    )
    projection_result = materialize_projection_identities(
        object_config_graph_identity=ocgi_result.object_config_graph_identity,
        object_config_graph_id=graph.id,
        opgs=graph.object_projection_graphs,
        declarations_by_name=projection_declarations_by_name,
    )
    graph.object_config_graph_identity = ocgi_result.object_config_graph_identity
    graph.object_config_graph_identity_id = ocgi_result.object_config_graph_identity.id

    return MetaObjectConfigGraphPackageMaterializationReceipt(
        object_config_graph_id=graph.id,
        object_config_graph_hash=str(graph.hash or ""),
        layout_hash=graph.layout_hash,
        object_config_graph_identity=ocgi_result.record,
        projection_identities=projection_result.projection_identities,
        observables=projection_result.observables,
    )


__all__ = [
    "MetaObjectConfigGraphPackageMaterializationReceipt",
    "MetaObjectConfigGraphPackageProjectionCompilation",
    "compile_object_config_graph_package_projections",
    "materialize_object_config_graph_package_identity_plane",
]
