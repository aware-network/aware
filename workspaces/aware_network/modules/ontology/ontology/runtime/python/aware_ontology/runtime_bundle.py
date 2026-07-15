from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence
from uuid import UUID

import msgpack

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_meta.attribute.config.type_descriptor_helpers import resolve_type_info
from aware_meta.graph.config.runtime_derivation.service import (
    build_namespace_by_code_id_from_graph,
)
from aware_meta.orm_artifacts.binding import (
    dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph,
)
from aware_meta.orm_artifacts.graphsql import (
    compile_plan_cache_from_object_config_graph,
)
from aware_meta.orm_artifacts.projection_plans import (
    compile_projection_plan_cache_from_object_config_graph,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_orm.db.schema_registry import (
    DBSchemaRegistry,
    build_db_schema_registry_entry,
    write_db_schema_registry,
)
from aware_orm.graph.serialization import serialize_plans
from aware_orm.projection.serialization import serialize_projection_plans
from aware_orm.runtime.package_artifacts import ORM_GRAPH_BINDING_FILENAME
from aware_utils.hashing import calculate_sha256
from aware_utils.io import ensure_directory
from aware_utils.string_transform import to_snake_case


ONTOLOGY_RUNTIME_BUNDLE_RELATIVE_PATH = (
    ".aware/ontology/runtime/ontology.runtime.manifest.json"
)
_OCG_SNAPSHOT_FILENAME = "ocg.snapshot.msgpack"
_OPG_INDEX_FILENAME = "opg.index.json"
_BINDINGS_FILENAME = "bindings.manifest.json"
_HANDLERS_FILENAME = "handlers.manifest.json"
_DB_SCHEMA_REGISTRY_FILENAME = "db.schema.registry.json"
_BUNDLE_CONTRACT_FILENAME = "bundle.contract.json"


@dataclass(frozen=True, slots=True)
class OntologyRuntimeBundleResult:
    manifest_path: Path
    contract_path: Path
    db_schema_registry_path: Path | None
    artifact_count: int


@dataclass(frozen=True, slots=True)
class _SerializedArtifact:
    path: Path
    relative_path: str
    sha256: str


def write_ontology_runtime_bundle(
    *,
    output_dir: Path,
    env_id: UUID,
    env_title: str,
    env_canonical_language: CodeLanguage,
    aware_root: Path,
    canonical_graph: ObjectConfigGraph,
    graphsql_graph: ObjectConfigGraph | None = None,
    external_graphs: Sequence[ObjectConfigGraph] | None = None,
    overlay_payloads: Mapping[str, object] | None = None,
    binding_graph: ObjectConfigGraph | None = None,
    handlers: Sequence[Mapping[str, object]] | None = None,
    environment_service_provider_modules: Sequence[str] | None = None,
    function_impl_policy: object | None = None,
) -> OntologyRuntimeBundleResult:
    """Write an ontology-owned runtime artifact bundle.

    This is the physical producer for ontology runtime artifacts. It intentionally
    does not import Structure runtime/composition writers: Structure may forward
    the resulting OntologyRuntimeArtifactSet receipt, but it does not own or
    compose these artifacts.
    """

    root = ensure_directory(Path(output_dir).expanduser().resolve())
    aware_root = Path(aware_root).expanduser().resolve()
    overlays = dict(overlay_payloads or {})
    binding_object_config_graph = binding_graph or canonical_graph
    sql_graph = graphsql_graph or _ontology_runtime_sql_graph(
        canonical_graph,
        external_graphs=external_graphs or (),
    )

    graphsql_plans = _build_graphsql_plans(sql_graph)
    projection_plans = _build_projection_plans(sql_graph)

    ocg_artifact = _export_ocg_snapshot(canonical_graph, root)
    binding_snapshot_artifact = _export_orm_graph_binding_snapshot(
        binding_object_config_graph,
        root,
    )
    overlay_artifacts = _export_overlays(overlays, root)
    opg_index_artifact, _opg_artifacts, opg_entries = _export_opg_index(
        getattr(canonical_graph, "object_projection_graphs", ()) or (),
        root,
        allow_empty=True,
    )
    graphsql_artifact = _export_binary_artifact(
        payload=graphsql_plans,
        destination=root / "graphsql",
        filename="graphsql.plans.msgpack",
    )
    projection_artifact = _export_binary_artifact(
        payload=projection_plans,
        destination=root / "projection",
        filename="projection.plans.msgpack",
    )

    class_fqn_by_class_config_id = _load_python_models_manifest_mapping(
        aware_root=aware_root,
        strict=True,
    )
    python_modules = _python_modules_from_class_fqns(
        class_fqn_by_class_config_id.values()
    )
    bindings_artifact = _export_bindings_manifest(
        destination=root,
        class_config_ids=tuple(
            UUID(value) for value in class_fqn_by_class_config_id.keys()
        ),
        class_fqn_by_class_config_id=class_fqn_by_class_config_id,
        sql_mapping_by_class_config_id=_derive_sql_mapping_by_class_config_id(
            object_config_graph=sql_graph,
            sql_overlay_payload=overlays.get("sql"),
        ),
    )
    handlers_artifact = (
        _export_handlers_manifest(destination=root, handlers=handlers)
        if handlers
        else None
    )

    db_schema_registry_path = _write_db_schema_registry(
        output_dir=root,
        env_id=env_id,
        aware_root=aware_root,
    )
    db_schema_registry_artifact = _artifact(
        path=db_schema_registry_path,
        relative_path=_DB_SCHEMA_REGISTRY_FILENAME,
    )
    manifest_payload = _manifest_payload(
        env_id=env_id,
        env_title=env_title,
        env_canonical_language=env_canonical_language,
        canonical_graph=canonical_graph,
        ocg_artifact=ocg_artifact,
        binding_snapshot_artifact=binding_snapshot_artifact,
        overlay_artifacts=overlay_artifacts,
        opg_index_artifact=opg_index_artifact,
        opg_entries=opg_entries,
        graphsql_artifact=graphsql_artifact,
        projection_artifact=projection_artifact,
        bindings_artifact=bindings_artifact,
        db_schema_registry_artifact=db_schema_registry_artifact,
        handlers_artifact=handlers_artifact,
        python_modules=python_modules,
        environment_service_provider_modules=environment_service_provider_modules,
        function_impl_policy=function_impl_policy,
    )
    manifest_path = root / "ontology.runtime.manifest.json"
    manifest_path.write_text(
        json.dumps(manifest_payload, indent=2, sort_keys=False),
        encoding="utf-8",
    )
    contract_path = _write_bundle_contract(
        manifest_path=manifest_path,
        environment_config_id=env_id,
        provider_modules=environment_service_provider_modules or (),
    )
    artifact_count = (
        5
        + len(overlay_artifacts)
        + len(opg_entries)
        + (1 if handlers_artifact is not None else 0)
        + (1 if db_schema_registry_path is not None else 0)
        + 1
    )
    return OntologyRuntimeBundleResult(
        manifest_path=manifest_path,
        contract_path=contract_path,
        db_schema_registry_path=db_schema_registry_path,
        artifact_count=artifact_count,
    )


def _build_graphsql_plans(graph: ObjectConfigGraph) -> bytes:
    plan_cache = compile_plan_cache_from_object_config_graph(object_config_graph=graph)
    return serialize_plans(plan_cache.all())


def _build_projection_plans(graph: ObjectConfigGraph) -> bytes:
    plans = []
    for dialect in ("postgres", "sqlite"):
        cache = compile_projection_plan_cache_from_object_config_graph(
            object_config_graph=graph,
            dialect=dialect,
        )
        plans.extend(list(cache.all()))
    return serialize_projection_plans(plans)


def _ontology_runtime_sql_graph(
    graph: ObjectConfigGraph,
    *,
    external_graphs: Sequence[ObjectConfigGraph] = (),
) -> ObjectConfigGraph:
    from sql_grammar.transformers.runtime_to_sql_transformer import (
        RuntimeToSQLTransformer,
    )

    graph_for_sql = _clone_object_config_graph_public_fields(graph)
    external_graphs_by_id = {
        external_graph.id: external_graph for external_graph in external_graphs
    }
    transformer = RuntimeToSQLTransformer(
        namespace_by_code_id=build_namespace_by_code_id_from_graph(graph_for_sql),
        external_graphs_by_id=external_graphs_by_id or None,
    )
    sql_graph = transformer.transform(graph_for_sql, code_primitive_type=None)
    return sql_graph


def _clone_object_config_graph_public_fields(
    graph: ObjectConfigGraph,
) -> ObjectConfigGraph:
    """Clone OCG public fields without copying runtime private/session state."""

    return ObjectConfigGraph.model_validate(
        graph.model_dump(mode="python", by_alias=False, round_trip=True)
    )


def _export_ocg_snapshot(
    graph: ObjectConfigGraph,
    destination: Path,
) -> _SerializedArtifact:
    ensure_directory(destination)
    path = destination / _OCG_SNAPSHOT_FILENAME
    path.write_bytes(msgpack.packb(_dump_model(graph), use_bin_type=True))
    return _artifact(path=path, relative_path=_OCG_SNAPSHOT_FILENAME)


def _export_orm_graph_binding_snapshot(
    graph: ObjectConfigGraph,
    destination: Path,
) -> _SerializedArtifact:
    ensure_directory(destination)
    path = destination / ORM_GRAPH_BINDING_FILENAME
    path.write_bytes(
        dump_orm_graph_binding_snapshot_msgpack_from_object_config_graph(
            object_config_graph=graph,
        )
    )
    return _artifact(path=path, relative_path=ORM_GRAPH_BINDING_FILENAME)


def _export_overlays(
    overlays: Mapping[str, object],
    destination: Path,
) -> dict[str, _SerializedArtifact]:
    overlay_dir = ensure_directory(destination / "overlay_payloads")
    artifacts: dict[str, _SerializedArtifact] = {}
    for language, payload in sorted(overlays.items(), key=lambda item: str(item[0])):
        filename = f"overlay_payloads.{language}.msgpack"
        path = overlay_dir / filename
        path.write_bytes(msgpack.packb(_dump_model(payload), use_bin_type=True))
        artifacts[str(language)] = _artifact(
            path=path,
            relative_path=str(Path("overlay_payloads") / filename),
        )
    return artifacts


def _export_opg_index(
    opgs: Iterable[object],
    destination: Path,
    *,
    allow_empty: bool,
) -> tuple[_SerializedArtifact, dict[str, _SerializedArtifact], list[dict[str, str]]]:
    opg_dir = ensure_directory(destination / "opgs")
    entries: list[dict[str, str]] = []
    artifacts: dict[str, _SerializedArtifact] = {}
    for opg in opgs:
        projection_hash = str(getattr(opg, "projection_hash", "") or "").strip()
        if not projection_hash:
            raise ValueError("ObjectProjectionGraph missing projection_hash.")
        model_name = str(getattr(opg, "name", "") or "").strip()
        if not model_name:
            raise ValueError(f"ObjectProjectionGraph {projection_hash} missing name.")
        filename = f"{projection_hash}.json"
        path = opg_dir / filename
        path.write_text(
            json.dumps(_dump_model(opg), indent=2, sort_keys=False),
            encoding="utf-8",
        )
        relative_path = str(Path("opgs") / filename)
        artifacts[projection_hash] = _artifact(path=path, relative_path=relative_path)
        entries.append(
            {
                "model": model_name,
                "projection_hash": projection_hash,
                "file": relative_path,
            }
        )
    if not entries and not allow_empty:
        raise ValueError("No ObjectProjectionGraphs provided for serialization.")
    index_path = destination / _OPG_INDEX_FILENAME
    index_path.write_text(
        json.dumps({"entries": entries}, indent=2),
        encoding="utf-8",
    )
    return (
        _artifact(path=index_path, relative_path=_OPG_INDEX_FILENAME),
        artifacts,
        entries,
    )


def _export_binary_artifact(
    *,
    payload: bytes,
    destination: Path,
    filename: str,
) -> _SerializedArtifact:
    if not payload:
        raise ValueError(f"Runtime bundle artifact {filename} cannot be empty.")
    directory = ensure_directory(destination)
    path = directory / filename
    path.write_bytes(payload)
    return _artifact(path=path, relative_path=str(Path(destination.name) / filename))


def _export_bindings_manifest(
    *,
    destination: Path,
    class_config_ids: Iterable[UUID],
    class_fqn_by_class_config_id: Mapping[str, str],
    sql_mapping_by_class_config_id: Mapping[str, list[dict[str, object]]],
) -> _SerializedArtifact:
    manifest_dir = ensure_directory(destination)
    out_path = manifest_dir / _BINDINGS_FILENAME
    bindings: list[dict[str, object]] = []
    for class_config_id in class_config_ids:
        class_config_id_token = str(class_config_id)
        class_fqn = class_fqn_by_class_config_id.get(class_config_id_token)
        if not class_fqn:
            continue
        sql_mapping = sql_mapping_by_class_config_id.get(class_config_id_token)
        if not sql_mapping:
            continue
        bindings.append(
            {
                "class_fqn": class_fqn,
                "canonical_entity_id": class_config_id_token,
                "sql_mapping": sql_mapping,
            }
        )
    out_path.write_text(
        json.dumps(
            {
                "version": "1.0.0",
                "planner_version": "1.0.0",
                "bindings": bindings,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return _artifact(path=out_path, relative_path=_BINDINGS_FILENAME)


def _export_handlers_manifest(
    *,
    destination: Path,
    handlers: Sequence[Mapping[str, object]] | None,
) -> _SerializedArtifact:
    out_path = ensure_directory(destination) / _HANDLERS_FILENAME
    items = [dict(handler) for handler in handlers or ()]
    items.sort(
        key=lambda handler: (
            str(handler.get("class_fqn") or ""),
            str(handler.get("function_name") or ""),
            str(handler.get("call_target") or ""),
            str(handler.get("handler_fqn") or ""),
        )
    )
    out_path.write_text(
        json.dumps({"version": "1.0", "handlers": items}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return _artifact(path=out_path, relative_path=_HANDLERS_FILENAME)


def _manifest_payload(
    *,
    env_id: UUID,
    env_title: str,
    env_canonical_language: CodeLanguage,
    canonical_graph: ObjectConfigGraph,
    ocg_artifact: _SerializedArtifact,
    binding_snapshot_artifact: _SerializedArtifact,
    overlay_artifacts: Mapping[str, _SerializedArtifact],
    opg_index_artifact: _SerializedArtifact,
    opg_entries: Sequence[Mapping[str, str]],
    graphsql_artifact: _SerializedArtifact,
    projection_artifact: _SerializedArtifact,
    bindings_artifact: _SerializedArtifact,
    db_schema_registry_artifact: _SerializedArtifact,
    handlers_artifact: _SerializedArtifact | None,
    python_modules: Sequence[str],
    environment_service_provider_modules: Sequence[str] | None,
    function_impl_policy: object | None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "version": "1.0",
        "built_at": datetime.now(tz=UTC).isoformat(),
        "environment": {
            "id": str(env_id),
            "title": env_title,
            "canonical_language": env_canonical_language.value,
        },
        "ocg": {
            "canonical_id": str(env_id),
            "hash": ocg_artifact.sha256,
            "semantic_hash": str(getattr(canonical_graph, "hash", "") or "") or None,
            "snapshot": ocg_artifact.relative_path,
        },
        "ocg_binding_snapshot": {
            "file": binding_snapshot_artifact.relative_path,
            "hash": binding_snapshot_artifact.sha256,
        },
        "overlays": {
            language: {
                "language": language,
                "file": artifact.relative_path,
                "hash": artifact.sha256,
            }
            for language, artifact in overlay_artifacts.items()
        },
        "opg_index": {
            "file": opg_index_artifact.relative_path,
            "entries": [dict(entry) for entry in opg_entries],
        },
        "graphsql": {
            "file": graphsql_artifact.relative_path,
            "hash": graphsql_artifact.sha256,
            "status": "ready",
        },
        "projection_plans": {
            "file": projection_artifact.relative_path,
            "hash": projection_artifact.sha256,
        },
        "bindings": {
            "file": bindings_artifact.relative_path,
            "hash": bindings_artifact.sha256,
        },
        "db_schema_registry": {
            "file": db_schema_registry_artifact.relative_path,
            "hash": db_schema_registry_artifact.sha256,
            "status": "ready",
        },
    }
    provider_modules = [
        str(module).strip()
        for module in environment_service_provider_modules or ()
        if str(module).strip()
    ]
    if provider_modules:
        payload["environment_service_provider_modules"] = provider_modules
    if python_modules:
        payload["loader"] = {"python_modules": list(python_modules)}
    if handlers_artifact is not None:
        payload["handlers"] = {
            "file": handlers_artifact.relative_path,
            "hash": handlers_artifact.sha256,
        }
    function_impl_payload = _dump_model(function_impl_policy)
    if function_impl_payload:
        payload["function_impl_policy"] = function_impl_payload
    return _without_none(payload)


def _python_modules_from_class_fqns(class_fqns: Iterable[str]) -> tuple[str, ...]:
    modules: list[str] = []
    seen: set[str] = set()
    for class_fqn in class_fqns:
        module = str(class_fqn or "").strip().split(".", maxsplit=1)[0].strip()
        if not module or module in seen:
            continue
        seen.add(module)
        modules.append(module)
    return tuple(modules)


def _write_db_schema_registry(
    *,
    output_dir: Path,
    env_id: UUID,
    aware_root: Path,
) -> Path:
    sql_root = aware_root / "sql"
    if not sql_root.is_dir():
        raise ValueError(
            "Ontology runtime bundle requires generated SQL root beside the "
            f"ontology package: {sql_root}"
        )
    registry_path = output_dir / _DB_SCHEMA_REGISTRY_FILENAME
    _ = write_db_schema_registry(
        path=registry_path,
        registry=DBSchemaRegistry(
            environment_id=env_id,
            entries=[
                build_db_schema_registry_entry(
                    package_kind="ontology",
                    backend_targets=("postgres",),
                    sql_root=sql_root,
                    source_label=aware_root.name,
                    relative_to=registry_path.parent,
                )
            ],
        ),
    )
    return registry_path


def _write_bundle_contract(
    *,
    manifest_path: Path,
    environment_config_id: UUID,
    provider_modules: Sequence[str],
) -> Path:
    digest = _sha256_hex(manifest_path)
    payload = {
        "schema_version": 1,
        "environment_config_id": str(environment_config_id),
        "bundle_manifest_sha256": digest,
        "bundle_manifest_size_bytes": manifest_path.stat().st_size,
        "bundle_head_id": hashlib.sha256(
            json.dumps(
                {
                    "schema_version": 1,
                    "manifest_sha256": digest,
                    "producer": "aware_ontology.runtime_bundle",
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest(),
        "release_identity": {
            "producer": "aware_ontology.runtime_bundle",
            "manifest_path": manifest_path.name,
        },
        "environment_service_provider_modules": [
            str(module).strip() for module in provider_modules if str(module).strip()
        ],
        "environment_module_service_provider_vector": [],
    }
    out_path = manifest_path.parent / _BUNDLE_CONTRACT_FILENAME
    out_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return out_path


def _load_python_models_manifest_mapping(
    *,
    aware_root: Path,
    strict: bool,
) -> dict[str, str]:
    path = _resolve_python_models_manifest_path(aware_root=aware_root)
    if not path.is_file():
        if strict:
            candidates = ", ".join(
                candidate.as_posix()
                for candidate in _python_models_manifest_candidates(
                    aware_root=aware_root
                )
            )
            raise FileNotFoundError(
                "Ontology runtime bundle requires Python models manifest. "
                f"Checked: {candidates}"
            )
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    classes = payload.get("classes") if isinstance(payload, Mapping) else None
    if not isinstance(classes, list):
        return {}
    return {
        str(entry["class_config_id"]): f"{entry['module']}.{entry['name']}"
        for entry in classes
        if isinstance(entry, Mapping)
        and str(entry.get("class_config_id") or "").strip()
        and str(entry.get("module") or "").strip()
        and str(entry.get("name") or "").strip()
    }


def _resolve_python_models_manifest_path(*, aware_root: Path) -> Path:
    for candidate in _python_models_manifest_candidates(aware_root=aware_root):
        if candidate.is_file():
            return candidate
    return aware_root / ".aware" / "materializations" / "python.models.json"


def _python_models_manifest_candidates(*, aware_root: Path) -> tuple[Path, ...]:
    return (
        aware_root / ".aware" / "materializations" / "python.models.json",
        aware_root
        / "python"
        / "orm_runtime"
        / ".aware"
        / "materializations"
        / "python.models.json",
        aware_root / "python" / ".aware" / "materializations" / "python.models.json",
    )


def _derive_sql_mapping_by_class_config_id(
    *,
    object_config_graph: ObjectConfigGraph,
    sql_overlay_payload: object | None = None,
) -> dict[str, list[dict[str, object]]]:
    class_by_id: dict[UUID, ClassConfig] = {}
    table_schema_by_class_id: dict[UUID, str] = {}
    for node in getattr(object_config_graph, "object_config_graph_nodes", ()) or ():
        if getattr(node, "type", None) != ObjectConfigGraphNodeType.class_:
            continue
        class_config = getattr(node, "class_config", None)
        if class_config is None:
            continue
        class_by_id[class_config.id] = class_config
        table_schema_by_class_id[class_config.id] = _table_schema_from_class_fqn(
            object_config_graph=object_config_graph,
            class_config=class_config,
        )

    out: dict[str, list[dict[str, object]]] = {}
    for class_config_id, class_config in class_by_id.items():
        table_schema = table_schema_by_class_id.get(class_config_id, "default")
        table_name = _overlay_rendered_name(
            sql_overlay_payload,
            section="class_overlays",
            key=str(class_config_id),
        ) or to_snake_case(getattr(class_config, "name", "object"))
        entries: list[dict[str, object]] = []
        seen_attr_names: set[str] = set()
        for link in getattr(class_config, "class_config_attribute_configs", ()) or ():
            attr = getattr(link, "attribute_config", None)
            if attr is None or not getattr(attr, "name", None):
                continue
            info = resolve_type_info(attr)
            if info.kind not in {
                AttributeTypeDescriptorKind.primitive,
                AttributeTypeDescriptorKind.enum,
            }:
                continue
            if getattr(attr, "is_virtual", False):
                continue
            attr_name = str(attr.name)
            entries.append(
                {
                    "attribute_name": attr_name,
                    "persisted": True,
                    "table_schema": table_schema,
                    "table_name": table_name,
                    "column_name": _overlay_rendered_name(
                        sql_overlay_payload,
                        section="attribute_overlays",
                        key=str(attr.id),
                    )
                    or to_snake_case(attr_name),
                    "fk_owner": None,
                    "fk_columns": [],
                    "join_chain": [],
                }
            )
            seen_attr_names.add(attr_name)
        if "id" not in seen_attr_names:
            entries.append(
                {
                    "attribute_name": "id",
                    "persisted": True,
                    "table_schema": table_schema,
                    "table_name": table_name,
                    "column_name": "id",
                    "fk_owner": None,
                    "fk_columns": [],
                    "join_chain": [],
                }
            )
        entries.sort(
            key=lambda entry: (
                0 if entry.get("attribute_name") == "id" else 1,
                str(entry.get("attribute_name") or ""),
            )
        )
        out[str(class_config_id)] = entries
    return out


def _table_schema_from_class_fqn(
    *,
    object_config_graph: ObjectConfigGraph,
    class_config: ClassConfig,
) -> str:
    fqn_prefix = (getattr(object_config_graph, "fqn_prefix", None) or "").strip()
    class_fqn = (getattr(class_config, "class_fqn", None) or "").strip()
    namespace = ""
    if fqn_prefix and class_fqn.startswith(fqn_prefix + "."):
        relative_fqn = class_fqn[len(fqn_prefix) + 1 :]
        parts = [part for part in relative_fqn.split(".") if part]
        namespace = ".".join(parts[:-1])
    if not namespace:
        return "default"
    segments = [to_snake_case(segment) for segment in namespace.split(".") if segment]
    return "_".join(segments) or "default"


def _overlay_rendered_name(
    payload: object | None,
    *,
    section: str,
    key: str,
) -> str | None:
    if payload is None:
        return None
    mapping = getattr(payload, section, None)
    if not isinstance(mapping, Mapping):
        return None
    overlay = mapping.get(key)
    value = getattr(overlay, "rendered_name", None)
    text = str(value or "").strip()
    return text or None


def _dump_model(value: object | None) -> object:
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json", exclude_none=True, by_alias=True)
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, Mapping):
        dumped: dict[str, object] = {}
        for key, item in value.items():
            dumped_item = _dump_model(item)
            if dumped_item is not None:
                dumped[str(key)] = dumped_item
        return dumped
    if isinstance(value, (list, tuple)):
        return [_dump_model(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (str, int, float, bool)):
        return value
    return None


def _without_none(payload: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in payload.items() if value is not None}


def _artifact(*, path: Path, relative_path: str) -> _SerializedArtifact:
    return _SerializedArtifact(
        path=path,
        relative_path=relative_path,
        sha256=calculate_sha256(path),
    )


def _sha256_hex(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


__all__ = [
    "ONTOLOGY_RUNTIME_BUNDLE_RELATIVE_PATH",
    "OntologyRuntimeBundleResult",
    "write_ontology_runtime_bundle",
]
