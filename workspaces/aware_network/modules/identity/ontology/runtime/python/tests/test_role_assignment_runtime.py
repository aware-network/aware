from __future__ import annotations

from pathlib import Path
import re
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pytest

from aware_code.semantic_materialization import SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA
from aware_identity_ontology_orm_models.actor.actor import Actor as ActorReplicaModel
from aware_identity_ontology_orm_models.role.role_config import (
    RoleConfig as RoleConfigReplicaModel,
)
from aware_identity_ontology_orm_models.role.role_config_class_config import (
    RoleConfigClassConfig as RoleConfigClassConfigReplicaModel,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.runtime.testing import IsolatedMetaAwareRoot as IsolatedAwareRoot
from aware_meta_ontology_orm_models.class_.class_instance import (
    ClassInstance as ClassInstanceReplicaModel,
)
from aware_meta_ontology_orm_models.class_.class_instance_identity import (
    ClassInstanceIdentity as ClassInstanceIdentityReplicaModel,
)
from aware_meta_ontology_orm_models.graph.instance.object_instance_graph_branch import (
    ObjectInstanceGraphBranch as ObjectInstanceGraphBranchReplicaModel,
)
from aware_orm.filters import EqFilter
from aware_orm.models.base_model import BaseORMModel
from aware_orm.query_spec import Predicate, PredicateGroup, QuerySpec
from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata, register_sql_metadata
from aware_orm.session.session import Session

from ._paths import IDENTITY_RUNTIME_SOURCE_ROOT, REPO_ROOT

_ROLE_ASSIGNMENT_RUNTIME_ONTOLOGY_PACKAGE_NAMES: tuple[str, ...] = (
    "history-ontology",
    "identity-ontology",
    "environment-ontology",
)

_SEMANTIC_ONTOLOGY_CATALOG_ENTRY_SPECS: tuple[
    tuple[str, str, str, str, str, tuple[str, ...], str],
    ...,
] = (
    (
        "storage",
        "storage-ontology",
        "aware_storage",
        "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        "workspaces/aware_kernel",
        (),
        "aware_storage",
    ),
    (
        "content",
        "content-ontology",
        "aware_content",
        "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        "workspaces/aware_kernel",
        ("storage-ontology",),
        "aware_content",
    ),
    (
        "code",
        "code-ontology",
        "aware_code",
        "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        "workspaces/aware_kernel",
        ("content-ontology",),
        "aware_code",
    ),
    (
        "history",
        "history-ontology",
        "aware_history",
        "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        "workspaces/aware_kernel",
        ("code-ontology",),
        "aware_history",
    ),
    (
        "meta",
        "meta-ontology",
        "aware_meta",
        "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        "workspaces/aware_kernel",
        ("code-ontology", "content-ontology", "history-ontology"),
        "aware_meta",
    ),
    (
        "ontology",
        "ontology-ontology",
        "aware_ontology",
        "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        "workspaces/aware_kernel",
        ("meta-ontology", "code-ontology"),
        "aware_ontology",
    ),
    (
        "api",
        "api-ontology",
        "aware_api",
        "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        "workspaces/aware_kernel",
        ("meta-ontology", "code-ontology"),
        "aware_api",
    ),
    (
        "reactivity",
        "reactivity-ontology",
        "aware_reactivity",
        "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        "workspaces/aware_kernel",
        ("meta-ontology", "api-ontology", "content-ontology"),
        "aware_reactivity",
    ),
    (
        "attention",
        "attention-ontology",
        "aware_attention",
        "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        "workspaces/aware_network",
        ("meta-ontology", "code-ontology", "identity-ontology"),
        "aware_attention",
    ),
    (
        "identity",
        "identity-ontology",
        "aware_identity",
        "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        "workspaces/aware_network",
        (
            "meta-ontology",
            "reactivity-ontology",
            "storage-ontology",
            "content-ontology",
            "history-ontology",
        ),
        "aware_identity",
    ),
    (
        "environment",
        "environment-ontology",
        "aware_environment",
        "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        ".",
        (
            "meta-ontology",
            "ontology-ontology",
            "content-ontology",
            "storage-ontology",
            "history-ontology",
            "identity-ontology",
            "code-ontology",
            "attention-ontology",
            "reactivity-ontology",
        ),
        "aware_environment",
    ),
)


def _semantic_ontology_package_catalog() -> dict[str, object]:
    return {
        "schema": SEMANTIC_ONTOLOGY_PACKAGE_CATALOG_SCHEMA,
        "entries": [
            _semantic_ontology_catalog_entry(
                module_id=module_id,
                package_name=package_name,
                fqn_prefix=fqn_prefix,
                manifest_path=manifest_path,
                owner_root=owner_root,
                dependency_package_names=dependency_package_names,
                runtime_handler_provider_import_root=(
                    runtime_handler_provider_import_root
                ),
            )
            for (
                module_id,
                package_name,
                fqn_prefix,
                manifest_path,
                owner_root,
                dependency_package_names,
                runtime_handler_provider_import_root,
            ) in _SEMANTIC_ONTOLOGY_CATALOG_ENTRY_SPECS
        ],
    }


def _semantic_ontology_catalog_entry(
    *,
    module_id: str,
    package_name: str,
    fqn_prefix: str,
    manifest_path: str,
    owner_root: str,
    dependency_package_names: tuple[str, ...],
    runtime_handler_provider_import_root: str,
) -> dict[str, object]:
    resolved_owner_root = REPO_ROOT if owner_root == "." else REPO_ROOT / owner_root
    return {
        "module_id": module_id,
        "package_name": package_name,
        "fqn_prefix": fqn_prefix,
        "manifest_path": (REPO_ROOT / manifest_path).resolve().as_posix(),
        "owner_root": resolved_owner_root.resolve().as_posix(),
        "dependency_package_names": dependency_package_names,
        "projection_names": (),
        "runtime_handler_provider_import_root": runtime_handler_provider_import_root,
    }


class _RoleAssignmentReplicaSession(Session):
    def __init__(self, *, index: object | None = None) -> None:
        self._index = index
        self._rows_by_class_config_id: dict[UUID, dict[UUID, dict[str, object]]] = {}
        backend = _RoleAssignmentReplicaBackend(rows=self._rows_by_class_config_id)
        super().__init__(branch_id=uuid4(), skip_db=False, backend=backend)
        for model_type in (
            ActorReplicaModel,
            ClassInstanceReplicaModel,
            ClassInstanceIdentityReplicaModel,
            ObjectInstanceGraphBranchReplicaModel,
            RoleConfigReplicaModel,
            RoleConfigClassConfigReplicaModel,
        ):
            _install_replica_sql_metadata(model_type=model_type, index=self._index)

    async def __aenter__(self) -> "_RoleAssignmentReplicaSession":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        return None

    def add_model_row(self, *, model_type: type, row: dict[str, object]) -> None:
        _install_replica_sql_metadata(
            model_type=model_type,
            index=self._index,
            persisted_attributes=set(row),
        )
        row_id = row.get("id")
        if row_id is None:
            raise ValueError(
                f"Missing id for seeded replica row: {_model_fqn(model_type)}"
            )
        metadata = model_type.get_sql_runtime_metadata()
        if metadata is None:
            raise RuntimeError(
                f"Missing replica SQL metadata for {_model_fqn(model_type)}"
            )
        self._rows_by_class_config_id.setdefault(metadata.class_config_id, {})[
            UUID(str(row_id))
        ] = dict(row)

    def require_model_row(
        self,
        *,
        model_type: type,
        row_id: UUID,
    ) -> dict[str, object]:
        metadata = model_type.get_sql_runtime_metadata()
        if metadata is None:
            raise RuntimeError(
                f"Missing replica SQL metadata for {_model_fqn(model_type)}"
            )
        row = self._rows_by_class_config_id.get(metadata.class_config_id, {}).get(
            row_id
        )
        if row is None:
            raise RuntimeError(
                f"Missing seeded replica row: {_model_fqn(model_type)} id={row_id}"
            )
        return dict(row)

    def _deserialize_to_model(self, model_class: type, row_data: dict[str, Any]) -> Any:
        processed_data: dict[str, object] = {}
        for key, value in self._map_sql_columns_to_attributes(
            model_class, row_data
        ).items():
            if (
                (key == "id" or key.endswith("_id"))
                and isinstance(value, str)
                and value
            ):
                try:
                    processed_data[key] = UUID(value)
                    continue
                except (TypeError, ValueError):
                    pass
            processed_data[key] = value
        instance = model_class.model_construct(**processed_data)
        instance._branch_id = self.branch_id
        instance._is_new = False
        instance._bound_session = self
        return instance


class _RoleAssignmentReplicaBackend:
    name = "role_assignment_replica"

    def __init__(
        self,
        *,
        rows: dict[UUID, dict[UUID, dict[str, object]]],
    ) -> None:
        self._rows = rows

    def enqueue_insert(self, sql: str, params: tuple[Any, ...]) -> None:
        _ = sql, params
        raise _read_only_replica_error()

    def enqueue_update(self, sql: str, params: tuple[Any, ...]) -> None:
        _ = sql, params
        raise _read_only_replica_error()

    def enqueue_delete(self, sql: str, params: tuple[Any, ...]) -> None:
        _ = sql, params
        raise _read_only_replica_error()

    def has_pending_operations(self) -> bool:
        return False

    def get_pending_counts(self) -> dict[str, int]:
        return {"inserts": 0, "updates": 0, "deletes": 0}

    def clear_pending(self) -> None:
        return None

    async def execute_query_spec(
        self,
        *,
        sql_metadata: SQLRuntimeMetadata,
        query_spec: QuerySpec,
        source_class_fqn: str | None,
        count: bool = False,
    ) -> list[dict[str, object]]:
        _ = source_class_fqn
        rows = tuple(
            row
            for row in self._rows.get(sql_metadata.class_config_id, {}).values()
            if _query_predicate_matches(row=row, predicate=query_spec.where)
        )
        if count:
            return [{"count": len(rows)}]
        return [dict(row) for row in rows]

    async def execute_read(
        self,
        sql: str,
        params: tuple[Any, ...],
    ) -> list[dict[str, object]]:
        _ = sql, params
        raise AssertionError("RoleAssignment replica reads must use execute_query_spec")

    async def commit(self) -> None:
        raise _read_only_replica_error()

    async def rollback(self) -> None:
        return None


def _query_predicate_matches(
    *,
    row: dict[str, object],
    predicate: Predicate | None,
) -> bool:
    if predicate is None:
        return True
    if isinstance(predicate, EqFilter):
        return row.get(predicate.column) == predicate.value
    if isinstance(predicate, PredicateGroup):
        if predicate.op == "and":
            return all(
                _query_predicate_matches(row=row, predicate=child)
                for child in predicate.predicates
            )
        if predicate.op == "or":
            return any(
                _query_predicate_matches(row=row, predicate=child)
                for child in predicate.predicates
            )
    raise AssertionError(
        f"Unsupported RoleAssignment test QuerySpec predicate: {predicate!r}"
    )


def _install_replica_sql_metadata(
    *,
    model_type: type,
    index: object | None = None,
    persisted_attributes: set[str] | None = None,
) -> None:
    if not issubclass(model_type, BaseORMModel):
        raise TypeError(f"Expected generated ORM model type, got {model_type!r}")
    class_config_id = _class_config_id_for_replica_model(
        model_type=model_type,
        index=index,
    )
    if class_config_id is None:
        raise RuntimeError(
            "RoleAssignment replica test requires generated ClassConfig binding: "
            f"{_model_fqn(model_type)}"
        )
    attributes = {"id"}
    existing = model_type.get_sql_runtime_metadata()
    if existing is not None and existing.table_schema == "role_assignment_replica_test":
        attributes.update(existing.persisted_attributes)
    attributes.update(
        attribute
        for attribute in (persisted_attributes or set())
        if isinstance(attribute, str) and attribute.strip()
    )
    metadata = SQLRuntimeMetadata(
        class_config_id=class_config_id,
        table_schema="role_assignment_replica_test",
        table_name=_replica_virtual_table_name(class_fqn=_model_fqn(model_type)),
        column_by_attribute={attribute: attribute for attribute in sorted(attributes)},
        persisted_attributes=frozenset(attributes),
        fk_owner_by_attribute={},
        fk_columns_by_attribute={},
        join_chain_by_attribute={},
    )
    setattr(model_type, "_sql_runtime_metadata", metadata)
    register_sql_metadata(metadata, class_fqn=_model_fqn(model_type))


def _class_config_id_for_replica_model(
    *,
    model_type: type,
    index: object | None,
) -> UUID | None:
    class_config = model_type.get_class_config()
    class_config_id = getattr(class_config, "id", None)
    if isinstance(class_config_id, UUID):
        return class_config_id
    class_configs_by_id = getattr(index, "class_configs_by_id", None)
    if not isinstance(class_configs_by_id, dict):
        return None
    model_fqn = _model_fqn(model_type)
    for candidate in class_configs_by_id.values():
        if getattr(candidate, "class_fqn", None) == model_fqn:
            candidate_id = getattr(candidate, "id", None)
            return candidate_id if isinstance(candidate_id, UUID) else None
    return None


def _replica_virtual_table_name(*, class_fqn: str) -> str:
    table_name = re.sub(r"[^A-Za-z0-9_]+", "_", class_fqn).strip("_").lower()
    if not table_name:
        raise RuntimeError(
            "RoleAssignment replica test could not derive table name from "
            f"class FQN: {class_fqn!r}"
        )
    return table_name


def _model_fqn(model_type: type) -> str:
    semantic_fqn = _semantic_fqn_from_orm_model_type(model_type)
    if semantic_fqn is not None:
        return semantic_fqn
    get_registry_key = getattr(model_type, "get_registry_key", None)
    if callable(get_registry_key):
        value = get_registry_key()
        if isinstance(value, str) and value.strip():
            return value
    return f"{model_type.__module__}.{model_type.__name__}"


def _semantic_fqn_from_orm_model_type(model_type: type) -> str | None:
    module_name = model_type.__module__
    prefixes = {
        "aware_identity_ontology_orm_models.": "aware_identity",
        "aware_meta_ontology_orm_models.": "aware_meta",
    }
    semantic_prefix: str | None = None
    tail: str | None = None
    for physical_prefix, candidate_semantic_prefix in prefixes.items():
        if module_name.startswith(physical_prefix):
            semantic_prefix = candidate_semantic_prefix
            tail = module_name.removeprefix(physical_prefix)
            break
    if semantic_prefix is None or tail is None:
        return None
    tokens = [token.removesuffix("_") for token in tail.split(".") if token]
    class_module_token = _camel_to_snake(model_type.__name__)
    if tokens and tokens[-1] == class_module_token:
        tokens = tokens[:-1]
    return ".".join((semantic_prefix, *tokens, model_type.__name__))


def _camel_to_snake(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()


def _read_only_replica_error() -> RuntimeError:
    return RuntimeError("RoleAssignment test replica session is read-only")


def test_role_assignment_uses_meta_runtime_readback_boundary() -> None:
    source = (
        IDENTITY_RUNTIME_SOURCE_ROOT / "ontology" / "materialization" / "assignment.py"
    ).read_text(encoding="utf-8")

    assert "from aware_runtime.index" not in source
    assert "AwareRuntimeIndex" not in source
    assert "hydrate_orm_graph_from_oig" not in source
    assert "SQLGenerator" not in source
    assert "SELECT * FROM" not in source
    assert (
        "from aware_runtime.materialization import MaterializationRuntimeContext"
        not in source
    )


async def _seed_oigi_row(
    rows: _RoleAssignmentReplicaSession,
) -> tuple[UUID, UUID, UUID]:
    object_instance_graph_identity_id = uuid4()
    object_instance_graph_id = uuid4()
    class_instance_id = uuid4()
    class_config_id = uuid4()
    class_instance_identity_id = uuid4()
    rows.add_model_row(
        model_type=ClassInstanceReplicaModel,
        row={
            "id": class_instance_id,
            "object_instance_graph_id": object_instance_graph_id,
            "class_config_id": class_config_id,
            "source_object_id": uuid4(),
        },
    )
    rows.add_model_row(
        model_type=ClassInstanceIdentityReplicaModel,
        row={
            "id": class_instance_identity_id,
            "object_instance_graph_identity_id": object_instance_graph_identity_id,
            "class_instance_id": class_instance_id,
            "label": "root",
        },
    )
    return (
        object_instance_graph_identity_id,
        class_config_id,
        class_instance_identity_id,
    )


async def _seed_additional_class_instance_identity(
    *,
    rows: _RoleAssignmentReplicaSession,
    existing_class_instance_identity_id: UUID,
    object_instance_graph_identity_id: UUID,
    class_config_id: UUID,
) -> UUID:
    class_instance_identity_row = rows.require_model_row(
        model_type=ClassInstanceIdentityReplicaModel,
        row_id=existing_class_instance_identity_id,
    )
    existing_class_instance_id = UUID(
        str(class_instance_identity_row["class_instance_id"])
    )
    class_instance_row = rows.require_model_row(
        model_type=ClassInstanceReplicaModel,
        row_id=existing_class_instance_id,
    )
    object_instance_graph_id = UUID(str(class_instance_row["object_instance_graph_id"]))
    class_instance_id = uuid4()
    class_instance_identity_id = uuid4()
    rows.add_model_row(
        model_type=ClassInstanceReplicaModel,
        row={
            "id": class_instance_id,
            "object_instance_graph_id": object_instance_graph_id,
            "class_config_id": class_config_id,
            "source_object_id": uuid4(),
        },
    )
    rows.add_model_row(
        model_type=ClassInstanceIdentityReplicaModel,
        row={
            "id": class_instance_identity_id,
            "object_instance_graph_identity_id": object_instance_graph_identity_id,
            "class_instance_id": class_instance_id,
            "label": "secondary",
        },
    )
    return class_instance_identity_id


async def _seed_assignment_prereqs(
    *,
    rows: _RoleAssignmentReplicaSession,
    actor_id: UUID,
    identity_id: UUID,
    public_key: str,
    role_config_name: str | None,
    role_config_id: UUID | None,
    class_config_id: UUID | None,
) -> None:
    from aware_identity_ontology.stable_ids import stable_role_config_class_config_id

    _ = public_key
    rows.add_model_row(
        model_type=ActorReplicaModel,
        row={
            "id": actor_id,
            "identity_id": identity_id,
            "key": "default",
            "type": "human",
        },
    )
    if role_config_id is not None and role_config_name is not None:
        rows.add_model_row(
            model_type=RoleConfigReplicaModel,
            row={
                "id": role_config_id,
                "name": role_config_name,
                "description": "Role assignment runtime proof policy.",
            },
        )
        if class_config_id is not None:
            rows.add_model_row(
                model_type=RoleConfigClassConfigReplicaModel,
                row={
                    "id": stable_role_config_class_config_id(
                        role_config_id=role_config_id,
                        class_config_id=class_config_id,
                    ),
                    "role_config_id": role_config_id,
                    "class_config_id": class_config_id,
                    "access_level": "admin",
                },
            )


async def _seed_identity_lane(*, context, public_key: str) -> None:
    from aware_identity_ontology.identity.identity import Identity
    from aware_identity_ontology.identity.identity_enums import IdentityType
    from aware_identity_ontology.stable_ids import stable_identity_id

    identity_id = stable_identity_id(public_key=public_key, type="human")
    identity_lane = context.bind_lane(
        projection="Identity",
        branch_id=identity_id,
    )
    with identity_lane.activate(commit=True, publish=False):
        await Identity.signup(public_key=public_key, type=IdentityType.human)


async def _build_role_assignment_materialization_context(
    *,
    actor_id: UUID,
) -> object:
    from aware_identity.materialization.bootstrap import (
        build_identity_materialization_context,
    )

    return await build_identity_materialization_context(
        repo_root=REPO_ROOT,
        runtime_ontology_package_names=(
            _ROLE_ASSIGNMENT_RUNTIME_ONTOLOGY_PACKAGE_NAMES
        ),
        semantic_ontology_package_catalog=_semantic_ontology_package_catalog(),
        actor_id=actor_id,
        environment_id=uuid5(
            NAMESPACE_URL, "aware://tests/identity/role-assignment/environment"
        ),
    )


@pytest.mark.asyncio
async def test_issue_assignee_role_assignment_reports_created_then_existing(
    tmp_path: Path,
    monkeypatch,
) -> None:

    import aware_identity_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_identity.role.assignment import (
        ensure_role_assignment,
        resolve_role_assignments,
    )
    from aware_identity_service_dto.role.assignment import (
        RoleAssignmentRequest,
        RoleAssignmentResolveRequest,
    )
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_actor_role_id,
        stable_identity_id,
        stable_role_class_instance_id,
        stable_role_config_class_config_id,
        stable_role_config_id,
        stable_role_id,
    )

    public_key = f"ed25519:{'55' * 32}"
    identity_id = stable_identity_id(public_key=public_key, type="human")
    actor_id = stable_actor_id(identity_id=identity_id, key="default")
    role_config_name = "issue_assignee"
    role_config_id = stable_role_config_id(name=role_config_name)

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        context = await _build_role_assignment_materialization_context(
            actor_id=actor_id,
        )
        rows = _RoleAssignmentReplicaSession(index=context.index)
        await _seed_identity_lane(context=context, public_key=public_key)
        oigi_id, class_config_id, class_instance_identity_id = await _seed_oigi_row(
            rows
        )
        expected_role_config_class_config_id = stable_role_config_class_config_id(
            role_config_id=role_config_id,
            class_config_id=class_config_id,
        )
        expected_role_id = stable_role_id(
            role_config_id=role_config_id,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_branch_key="all",
        )
        expected_actor_role_id = stable_actor_role_id(
            actor_id=actor_id, role_id=expected_role_id
        )
        expected_role_class_instance_id = stable_role_class_instance_id(
            role_id=expected_role_id,
            class_instance_identity_id=class_instance_identity_id,
            role_config_class_config_id=expected_role_config_class_config_id,
        )
        await _seed_assignment_prereqs(
            rows=rows,
            actor_id=actor_id,
            identity_id=identity_id,
            public_key=public_key,
            role_config_name=role_config_name,
            role_config_id=role_config_id,
            class_config_id=class_config_id,
        )

        request = RoleAssignmentRequest(
            actor_id=actor_id,
            role_config_name=role_config_name,
            class_instance_identity_id=class_instance_identity_id,
            request_id=uuid4(),
            source_service="issue",
            reason="issue.assign",
        )

        async with rows as session:
            first = await ensure_role_assignment(
                session=session,
                request=request,
                context=context,
            )
        assert first.request_id == request.request_id
        assert first.role_created is True
        assert first.actor_role_created is True
        assert first.binding.role_id == expected_role_id
        assert first.binding.actor_role_id == expected_actor_role_id
        assert first.binding.role_class_instance_id == expected_role_class_instance_id
        assert first.binding.class_instance_identity_id == class_instance_identity_id
        assert (
            first.binding.role_config_class_config_id
            == expected_role_config_class_config_id
        )
        assert first.binding.role_config_id == role_config_id
        assert first.binding.object_instance_graph_identity_id == oigi_id
        assert first.role_class_instance_created is True

        async with rows as session:
            second = await ensure_role_assignment(
                session=session,
                request=request,
                context=context,
            )
        assert second.role_created is False
        assert second.actor_role_created is False
        assert second.role_class_instance_created is False
        assert second.binding == first.binding

        async with rows as session:
            resolved = await resolve_role_assignments(
                request=RoleAssignmentResolveRequest(
                    actor_id=actor_id,
                    role_config_name=role_config_name,
                    class_instance_identity_id=class_instance_identity_id,
                    request_id=request.request_id,
                ),
                session=session,
                context=context,
            )
        role_head = await FSCommitStore().head(
            branch_id=expected_role_id,
            projection_hash=_projection_hash_by_name(context=context, name="Role"),
        )
        identity_head = await FSCommitStore().head(
            branch_id=identity_id,
            projection_hash=_projection_hash_by_name(context=context, name="Identity"),
        )

        assert [binding.actor_role_id for binding in resolved.bindings] == [
            expected_actor_role_id
        ]
        assert resolved.bindings[0].role_id == expected_role_id
        assert resolved.request_id == request.request_id
        assert role_head is not None
        assert identity_head is not None


@pytest.mark.asyncio
async def test_ensure_role_assignment_requires_existing_role_config(
    tmp_path: Path, monkeypatch
) -> None:

    import aware_identity_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_identity.role.assignment import (
        ensure_role_assignment,
    )
    from aware_identity_service_dto.role.assignment import RoleAssignmentRequest
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_identity_id,
    )

    public_key = f"ed25519:{'66' * 32}"
    identity_id = stable_identity_id(public_key=public_key, type="human")
    actor_id = stable_actor_id(identity_id=identity_id, key="default")

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        context = await _build_role_assignment_materialization_context(
            actor_id=actor_id,
        )
        rows = _RoleAssignmentReplicaSession(index=context.index)
        _, class_config_id, class_instance_identity_id = await _seed_oigi_row(rows)
        await _seed_assignment_prereqs(
            rows=rows,
            actor_id=actor_id,
            identity_id=identity_id,
            public_key=public_key,
            role_config_name=None,
            role_config_id=None,
            class_config_id=class_config_id,
        )

        async with rows as session:
            with pytest.raises(ValueError, match="missing role_config_id"):
                await ensure_role_assignment(
                    session=session,
                    request=RoleAssignmentRequest(
                        actor_id=actor_id,
                        role_config_name="aware.identity.role-assignment.missing-policy",
                        class_instance_identity_id=class_instance_identity_id,
                    ),
                    context=context,
                )


@pytest.mark.asyncio
async def test_issue_assignee_role_unassignment_removes_binding_and_cleans_role_lane(
    tmp_path: Path,
    monkeypatch,
) -> None:

    import aware_identity_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_identity.role.assignment import (
        ensure_role_assignment,
        resolve_role_assignments,
        unassign_role,
    )
    from aware_identity_service_dto.role.assignment import (
        RoleAssignmentRequest,
        RoleAssignmentResolveRequest,
        RoleUnassignmentRequest,
    )
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_identity_id,
        stable_role_config_id,
    )

    public_key = f"ed25519:{'77' * 32}"
    identity_id = stable_identity_id(public_key=public_key, type="human")
    actor_id = stable_actor_id(identity_id=identity_id, key="default")
    role_config_name = "issue_assignee"
    role_config_id = stable_role_config_id(name=role_config_name)

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        context = await _build_role_assignment_materialization_context(
            actor_id=actor_id,
        )
        rows = _RoleAssignmentReplicaSession(index=context.index)
        await _seed_identity_lane(context=context, public_key=public_key)
        oigi_id, class_config_id, class_instance_identity_id = await _seed_oigi_row(
            rows
        )
        await _seed_assignment_prereqs(
            rows=rows,
            actor_id=actor_id,
            identity_id=identity_id,
            public_key=public_key,
            role_config_name=role_config_name,
            role_config_id=role_config_id,
            class_config_id=class_config_id,
        )
        assign_request = RoleAssignmentRequest(
            actor_id=actor_id,
            role_config_name=role_config_name,
            class_instance_identity_id=class_instance_identity_id,
            request_id=uuid4(),
            source_service="issue",
            reason="issue.assign",
        )
        unassign_request = RoleUnassignmentRequest(
            actor_id=actor_id,
            role_config_name=role_config_name,
            class_instance_identity_id=class_instance_identity_id,
            request_id=uuid4(),
            source_service="issue",
            reason="issue.unassign",
        )

        async with rows as session:
            first = await ensure_role_assignment(
                session=session,
                request=assign_request,
                context=context,
            )
        assert first.binding.object_instance_graph_identity_id == oigi_id

        async with rows as session:
            removed = await unassign_role(
                session=session,
                request=unassign_request,
                context=context,
            )
        assert removed.binding == first.binding
        assert removed.actor_role_removed is True
        assert removed.role_class_instance_removed is True
        assert removed.role_removed is True

        async with rows as session:
            resolved = await resolve_role_assignments(
                request=RoleAssignmentResolveRequest(
                    actor_id=actor_id,
                    role_config_name=role_config_name,
                    class_instance_identity_id=class_instance_identity_id,
                    request_id=uuid4(),
                ),
                session=session,
                context=context,
            )
        assert resolved.bindings == []


@pytest.mark.asyncio
async def test_unassign_role_refuses_multi_class_instance_role_envelope(
    tmp_path: Path,
    monkeypatch,
) -> None:

    import aware_identity_ontology  # noqa: F401
    import aware_meta_ontology  # noqa: F401
    from aware_identity.role.assignment import (
        ensure_role_assignment,
        unassign_role,
    )
    from aware_identity_service_dto.role.assignment import (
        RoleAssignmentRequest,
        RoleUnassignmentRequest,
    )
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_identity_id,
        stable_role_config_id,
    )

    public_key = f"ed25519:{'88' * 32}"
    identity_id = stable_identity_id(public_key=public_key, type="human")
    actor_id = stable_actor_id(identity_id=identity_id, key="default")
    role_config_name = "issue_assignee"
    role_config_id = stable_role_config_id(name=role_config_name)

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        context = await _build_role_assignment_materialization_context(
            actor_id=actor_id,
        )
        rows = _RoleAssignmentReplicaSession(index=context.index)
        await _seed_identity_lane(context=context, public_key=public_key)
        oigi_id, class_config_id, first_class_instance_identity_id = (
            await _seed_oigi_row(rows)
        )
        second_class_instance_identity_id = (
            await _seed_additional_class_instance_identity(
                rows=rows,
                existing_class_instance_identity_id=first_class_instance_identity_id,
                object_instance_graph_identity_id=oigi_id,
                class_config_id=class_config_id,
            )
        )
        await _seed_assignment_prereqs(
            rows=rows,
            actor_id=actor_id,
            identity_id=identity_id,
            public_key=public_key,
            role_config_name=role_config_name,
            role_config_id=role_config_id,
            class_config_id=class_config_id,
        )

        async with rows as session:
            await ensure_role_assignment(
                session=session,
                request=RoleAssignmentRequest(
                    actor_id=actor_id,
                    role_config_name=role_config_name,
                    class_instance_identity_id=first_class_instance_identity_id,
                    request_id=uuid4(),
                    source_service="issue",
                    reason="issue.assign",
                ),
                context=context,
            )
        async with rows as session:
            await ensure_role_assignment(
                session=session,
                request=RoleAssignmentRequest(
                    actor_id=actor_id,
                    role_config_name=role_config_name,
                    class_instance_identity_id=second_class_instance_identity_id,
                    request_id=uuid4(),
                    source_service="issue",
                    reason="issue.assign",
                ),
                context=context,
            )

        async with rows as session:
            with pytest.raises(
                ValueError, match="ambiguous multi-class-instance role envelope"
            ):
                await unassign_role(
                    session=session,
                    request=RoleUnassignmentRequest(
                        actor_id=actor_id,
                        role_config_name=role_config_name,
                        class_instance_identity_id=first_class_instance_identity_id,
                        request_id=uuid4(),
                        source_service="issue",
                        reason="issue.unassign",
                    ),
                    context=context,
                )


def _projection_hash_by_name(*, context, name: str) -> str:
    matches = sorted(
        {
            opg.projection_hash
            for opg in context.index.ocg.object_projection_graphs
            if (opg.name or "").strip() == name.strip()
        }
    )
    if len(matches) != 1:
        raise RuntimeError(f"Expected one projection hash for {name!r}, got {matches}")
    return matches[0]
