from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from aware_meta.graph.projection.declarations import (
    ProjectionDeclaration,
    ProjectionObservableDeclaration,
)
from aware_meta.graph.projection.identity import (
    synthesize_object_projection_graph_identity,
)
from aware_meta.graph.projection.stable_ids import (
    stable_object_projection_graph_id,
    stable_object_projection_graph_observable_id,
)
from aware_meta.graph.config.stable_ids import (
    stable_object_projection_graph_identity_id,
)
from aware_meta_ontology.graph.config.object_config_graph_identity import (
    ObjectConfigGraphIdentity,
)
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_identity import (
    ObjectProjectionGraphIdentity,
)
from aware_meta_ontology.graph.projection.object_projection_graph_observable import (
    ObjectProjectionGraphObservable,
)


@dataclass(frozen=True, slots=True)
class ProjectionIdentityMaterializationRecord:
    projection_name: str
    object_projection_graph_id: UUID
    object_projection_graph_identity_id: UUID
    projection_hash: str | None
    is_branchable: bool


@dataclass(frozen=True, slots=True)
class ProjectionObservableMaterializationRecord:
    projection_name: str
    object_projection_graph_identity_id: UUID
    object_projection_graph_observable_id: UUID
    observable_key: str
    key: str
    kind: str
    description: str | None
    position: int
    is_default: bool


@dataclass(frozen=True, slots=True)
class ProjectionIdentityMaterializationResult:
    projection_identities: tuple[ProjectionIdentityMaterializationRecord, ...]
    observables: tuple[ProjectionObservableMaterializationRecord, ...]


def materialize_projection_identities(
    *,
    object_config_graph_identity: ObjectConfigGraphIdentity,
    object_config_graph_id: UUID,
    opgs: list[ObjectProjectionGraph],
    declarations_by_name: dict[str, ProjectionDeclaration],
) -> ProjectionIdentityMaterializationResult:
    """
    Materialize OPGI/observable identity-plane objects for full OCG builds.

    This is the semantic full-materialization rail. It is intentionally pure and
    deterministic so a later Meta-owned cache can key the resulting records by
    committed OCG package truth plus projection hashes.
    """

    ocgi = object_config_graph_identity
    can_attach_projection_identities = (
        "object_projection_graph_identities"
        in ObjectConfigGraphIdentity.model_fields
    )
    if can_attach_projection_identities:
        ocgi.object_projection_graph_identities = []

    opg_by_name = _projection_graphs_by_name(opgs)
    projection_records: list[ProjectionIdentityMaterializationRecord] = []
    observable_records: list[ProjectionObservableMaterializationRecord] = []
    for projection_name in _projection_names(
        declarations_by_name=declarations_by_name,
        opg_by_name=opg_by_name,
    ):
        decl = declarations_by_name.get(projection_name)
        opg = opg_by_name.get(projection_name)
        opgi = _materialize_projection_identity(
            ocgi=ocgi,
            object_config_graph_id=object_config_graph_id,
            projection_name=projection_name,
            declaration=decl,
            opg=opg,
        )
        if can_attach_projection_identities:
            ocgi.object_projection_graph_identities.append(opgi)

        projection_records.append(
            ProjectionIdentityMaterializationRecord(
                projection_name=projection_name,
                object_projection_graph_id=UUID(str(opgi.object_projection_graph_id)),
                object_projection_graph_identity_id=UUID(str(opgi.id)),
                projection_hash=opg.projection_hash if opg is not None else None,
                is_branchable=bool(opgi.is_branchable),
            )
        )
        observable_decls = _defaulted_observable_declarations(
            projection_name=projection_name,
            declaration=decl,
        )
        if not observable_decls:
            continue
        observables, records = _materialize_projection_observables(
            projection_name=projection_name,
            opgi=opgi,
            observable_declarations=observable_decls,
        )
        opgi.object_projection_graph_observables = observables
        observable_records.extend(records)

    return ProjectionIdentityMaterializationResult(
        projection_identities=tuple(projection_records),
        observables=tuple(observable_records),
    )


def _projection_graphs_by_name(
    opgs: list[ObjectProjectionGraph],
) -> dict[str, ObjectProjectionGraph]:
    opg_by_name: dict[str, ObjectProjectionGraph] = {}
    for opg in opgs or []:
        projection_name = (opg.name or "").strip()
        if projection_name:
            opg_by_name[projection_name] = opg
    return opg_by_name


def _projection_names(
    *,
    declarations_by_name: dict[str, ProjectionDeclaration],
    opg_by_name: dict[str, ObjectProjectionGraph],
) -> tuple[str, ...]:
    names = {
        *(name for name in declarations_by_name.keys() if (name or "").strip()),
        *(name for name in opg_by_name.keys() if (name or "").strip()),
    }
    return tuple(sorted(names))


def _materialize_projection_identity(
    *,
    ocgi: ObjectConfigGraphIdentity,
    object_config_graph_id: UUID,
    projection_name: str,
    declaration: ProjectionDeclaration | None,
    opg: ObjectProjectionGraph | None,
) -> ObjectProjectionGraphIdentity:
    label = declaration.label if declaration is not None else None
    is_branchable = bool(declaration.is_branchable) if declaration is not None else False
    object_projection_graph_id = (
        opg.id
        if opg is not None
        else stable_object_projection_graph_id(
            object_config_graph_id=object_config_graph_id,
            name=projection_name,
        )
    )

    if opg is not None:
        return synthesize_object_projection_graph_identity(
            object_config_graph_identity=ocgi,
            object_projection_graph=opg,
            label=label,
            is_branchable=is_branchable,
        )

    opgi_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=ocgi.id,
        object_projection_graph_id=object_projection_graph_id,
    )
    return ObjectProjectionGraphIdentity(
        id=opgi_id,
        object_projection_graph=None,
        object_projection_graph_id=object_projection_graph_id,
        projection_name=projection_name,
        label=label or f"opg:{projection_name}",
        is_branchable=is_branchable,
        object_config_graph_identity_id=ocgi.id,
    )


def _defaulted_observable_declarations(
    *,
    projection_name: str,
    declaration: ProjectionDeclaration | None,
) -> tuple[ProjectionObservableDeclaration, ...]:
    observable_decls = list(declaration.observables) if declaration is not None else []
    if not observable_decls:
        return ()

    default_idxs = [idx for idx, observable in enumerate(observable_decls) if observable.is_default]
    if len(default_idxs) > 1:
        keys = [observable.key for observable in observable_decls if observable.is_default]
        raise ValueError(f"Projection {projection_name!r} defines multiple default observables: {keys}")
    if len(default_idxs) == 0:
        first = observable_decls[0]
        observable_decls[0] = ProjectionObservableDeclaration(
            key=first.key,
            kind=first.kind,
            is_default=True,
            description=first.description,
            position=first.position,
        )
    return tuple(observable_decls)


def _materialize_projection_observables(
    *,
    projection_name: str,
    opgi: ObjectProjectionGraphIdentity,
    observable_declarations: tuple[ProjectionObservableDeclaration, ...],
) -> tuple[list[ObjectProjectionGraphObservable], list[ProjectionObservableMaterializationRecord]]:
    observables: list[ObjectProjectionGraphObservable] = []
    records: list[ProjectionObservableMaterializationRecord] = []
    for observable_decl in observable_declarations:
        observable_key = (observable_decl.key or "").strip()
        if not observable_key:
            continue
        observable_id = stable_object_projection_graph_observable_id(
            object_projection_graph_identity_id=opgi.id,
            observable_key=observable_key,
        )
        key = f"{projection_name}:{observable_key}"
        observables.append(
            ObjectProjectionGraphObservable(
                id=observable_id,
                object_projection_graph_identity_id=opgi.id,
                key=key,
                kind=observable_decl.kind,
                label=None,
                description=observable_decl.description,
                position=observable_decl.position,
                is_default=bool(observable_decl.is_default),
                observable_key=observable_key,
            )
        )
        records.append(
            ProjectionObservableMaterializationRecord(
                projection_name=projection_name,
                object_projection_graph_identity_id=UUID(str(opgi.id)),
                object_projection_graph_observable_id=UUID(str(observable_id)),
                observable_key=observable_key,
                key=key,
                kind=observable_decl.kind,
                description=observable_decl.description,
                position=observable_decl.position,
                is_default=bool(observable_decl.is_default),
            )
        )
    return observables, records


__all__ = [
    "ProjectionIdentityMaterializationRecord",
    "ProjectionIdentityMaterializationResult",
    "ProjectionObservableMaterializationRecord",
    "materialize_projection_identities",
]
