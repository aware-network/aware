from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, TypeAlias, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from aware_code_ontology.code.code_enums import CodeLanguage
from aware_experience.compiler.models import (
    ProjectionOwnedClassTruth,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph

_TModel = TypeVar("_TModel", bound=BaseModel)
_EMPTY_FROZEN_STR: frozenset[str] = frozenset()
_ClassBinding: TypeAlias = tuple[
    str,
    str,
    frozenset[str],
    frozenset[str],
    tuple[tuple[str, str], ...],
]


@dataclass(frozen=True, slots=True)
class _ClassConfigTruth:
    attributes: frozenset[str]
    identity_key_attributes: frozenset[str]
    relationship_targets: dict[str, str]


class _BindingsSqlMappingRow(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    attribute_name: str | None = None


class _BindingsRow(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    class_fqn: str | None = None
    canonical_class_config_id: str | None = None
    canonical_entity_id: str | None = None
    sql_mapping: tuple[_BindingsSqlMappingRow, ...] = ()


class _BindingsManifest(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    bindings: tuple[_BindingsRow, ...] = ()


class _OPGIndexEntry(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    model: str | None = None
    file: str | None = None


class _OPGIndexFile(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    entries: tuple[_OPGIndexEntry, ...] = ()


class _OPGNodeCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    class_config_id: UUID | str | None = None
    is_root: bool = False


class _OPGObservableCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    observable_key: str | None = None
    key: str | None = None


class _OPGIdentityCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    object_projection_graph_observables: tuple[_OPGObservableCompat, ...] = ()


class _OPGFileCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    object_projection_graph_identity: _OPGIdentityCompat | None = None
    object_projection_graph_nodes: tuple[_OPGNodeCompat, ...] = ()


class _EnvironmentManifestArtifact(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    file: str
    hash: str | None = None


class _EnvironmentManifestCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    opg_index: _EnvironmentManifestArtifact
    bindings: _EnvironmentManifestArtifact | None = None


class _CompilerEnvironmentObservableCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    observable_key: str | None = None
    key: str | None = None


class _CompilerProjectionIdentityCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    projection_name: str | None = None
    object_projection_graph_observables: tuple[
        _CompilerEnvironmentObservableCompat, ...
    ] = ()


class _CompilerObjectConfigGraphIdentityCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    object_projection_graph_identities: tuple[
        _CompilerProjectionIdentityCompat, ...
    ] = ()


class _CompilerAttributeConfigCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    id: UUID | str | None = None
    name: str = ""
    is_primary: bool = False


class _CompilerClassConfigAttributeEdgeCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    attribute_config_id: UUID | str | None = None
    attribute_config: _CompilerAttributeConfigCompat | None = None
    is_identity_key: bool = False


class _CompilerClassConfigRelationshipAttributeCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    attribute_config_id: UUID | str | None = None


class _CompilerClassConfigRelationshipCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    target_class_config_id: UUID | str | None = None
    class_config_relationship_attributes: tuple[
        _CompilerClassConfigRelationshipAttributeCompat, ...
    ] = ()


class _CompilerClassConfigCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    id: UUID | str | None = None
    class_config_attribute_configs: tuple[
        _CompilerClassConfigAttributeEdgeCompat, ...
    ] = ()
    class_config_relationships: tuple[_CompilerClassConfigRelationshipCompat, ...] = ()


class _CompilerObjectConfigGraphNodeCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    class_config_id: UUID | str | None = None
    class_config: _CompilerClassConfigCompat | None = None


class _CompilerObjectConfigGraphCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    language: CodeLanguage | str | None = None
    object_config_graph_identity: _CompilerObjectConfigGraphIdentityCompat | None = None
    object_config_graph_nodes: tuple[_CompilerObjectConfigGraphNodeCompat, ...] = ()


class _CompilerEnvironmentCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    canonical_language: CodeLanguage | str | None = None
    object_config_graphs: tuple[_CompilerObjectConfigGraphCompat, ...] = ()


class _CompositionModuleRow(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    manifest_path: str


class _CompositionManifestCompat(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore")

    modules: tuple[_CompositionModuleRow, ...] = ()


def load_environment_projection_truth(
    *, composition_manifest_path: Path, repo_root: Path
) -> dict[str, dict[str, ProjectionOwnedClassTruth]]:
    return load_environment_projection_truth_from_runtime_manifests(
        environment_runtime_manifest_paths=_manifest_paths_from_composition_manifest(
            composition_manifest_path=composition_manifest_path,
            repo_root=repo_root,
        ),
        repo_root=repo_root,
    )


def load_environment_projection_truth_from_runtime_manifests(
    *,
    environment_runtime_manifest_paths: Sequence[Path],
    repo_root: Path,
) -> dict[str, dict[str, ProjectionOwnedClassTruth]]:
    repo_root = repo_root.resolve()
    if not environment_runtime_manifest_paths:
        return {}

    projection_truth_by_name: dict[str, dict[str, ProjectionOwnedClassTruth]] = {}
    projection_alias_candidates: dict[str, set[str]] = {}
    for idx, module_manifest_path in enumerate(environment_runtime_manifest_paths):
        module_manifest_path = _resolve_runtime_manifest_path(
            module_manifest_path=module_manifest_path,
            repo_root=repo_root,
            module_idx=idx,
        )
        module_manifest = _load_json_model(
            module_manifest_path, _EnvironmentManifestCompat
        )
        module_runtime_dir = module_manifest_path.parent
        class_truth_by_config_id = _load_class_attribute_truth_from_environment_json(
            module_manifest_path=module_manifest_path
        )

        opg_index_relpath = module_manifest.opg_index.file.strip()
        if not opg_index_relpath:
            raise ValueError(
                f"Invalid module manifest {module_manifest_path}: missing opg_index.file"
            )
        opg_index_path = (module_runtime_dir / opg_index_relpath).resolve()
        _assert_within(
            base=module_runtime_dir, candidate=opg_index_path, label="opg index path"
        )
        if not opg_index_path.exists():
            raise FileNotFoundError(f"OPG index not found: {opg_index_path}")
        opg_index = _load_json_model(opg_index_path, _OPGIndexFile)

        class_binding_by_config_id = _load_module_class_bindings(
            module_manifest=module_manifest,
            module_runtime_dir=module_runtime_dir,
            class_truth_by_config_id=class_truth_by_config_id,
        )

        for entry in opg_index.entries:
            model = _normalize_projection_token(entry.model or "")
            if not model:
                continue
            if model in projection_truth_by_name:
                raise ValueError(
                    f"Ambiguous projection model {model!r} across composed module manifests; expected one owner"
                )
            file_relpath = (entry.file or "").strip()
            if not file_relpath:
                raise ValueError(
                    f"Invalid OPG index entry for model {model!r} at {opg_index_path}: missing file"
                )
            opg_path = (module_runtime_dir / file_relpath).resolve()
            _assert_within(
                base=module_runtime_dir, candidate=opg_path, label="opg file path"
            )
            if not opg_path.exists():
                raise FileNotFoundError(f"OPG file not found: {opg_path}")
            opg_payload = _load_json_model(opg_path, _OPGFileCompat)

            projection_catalog: dict[str, ProjectionOwnedClassTruth] = {}
            for node in opg_payload.object_projection_graph_nodes:
                class_config_id = _uuid_to_key(node.class_config_id)
                if not class_config_id:
                    continue
                if class_config_id not in class_binding_by_config_id:
                    continue
                binding = class_binding_by_config_id[class_config_id]
                (
                    class_token,
                    class_fqn,
                    class_attributes,
                    identity_key_attributes,
                    relationship_targets,
                ) = binding

                relationship_targets_resolved: dict[str, str] = {}
                for (
                    relationship_attribute,
                    target_class_config_id,
                ) in relationship_targets:
                    if target_class_config_id not in class_binding_by_config_id:
                        continue
                    target_binding = class_binding_by_config_id[target_class_config_id]
                    relationship_targets_resolved[relationship_attribute] = (
                        target_binding[0]
                    )

                current_truth = ProjectionOwnedClassTruth(
                    class_fqn=class_fqn,
                    attributes=class_attributes,
                    identity_key_attributes=identity_key_attributes,
                    relationship_targets=tuple(
                        sorted(relationship_targets_resolved.items())
                    ),
                )
                if (
                    class_token in projection_catalog
                    and projection_catalog[class_token] != current_truth
                ):
                    prior_truth = projection_catalog[class_token]
                    raise ValueError(
                        f"Ambiguous class token mapping {class_token!r} for projection {model!r}: {prior_truth!r} vs {current_truth!r}"
                    )
                projection_catalog[class_token] = current_truth

            projection_truth_by_name[model] = projection_catalog
            projection_alias = _resolve_projection_root_alias(
                opg_payload=opg_payload,
                class_binding_by_config_id=class_binding_by_config_id,
            )
            if projection_alias:
                projection_alias_candidates.setdefault(projection_alias, set()).add(
                    model
                )

    _publish_unique_projection_aliases(
        truth_by_name=projection_truth_by_name,
        alias_candidates=projection_alias_candidates,
    )
    _publish_casefold_projection_aliases(truth_by_name=projection_truth_by_name)
    return projection_truth_by_name


def load_environment_projection_observable_truth(
    *, composition_manifest_path: Path, repo_root: Path
) -> dict[str, frozenset[str]]:
    return load_environment_projection_observable_truth_from_runtime_manifests(
        environment_runtime_manifest_paths=_manifest_paths_from_composition_manifest(
            composition_manifest_path=composition_manifest_path,
            repo_root=repo_root,
        ),
        repo_root=repo_root,
    )


def load_environment_projection_observable_truth_from_runtime_manifests(
    *,
    environment_runtime_manifest_paths: Sequence[Path],
    repo_root: Path,
) -> dict[str, frozenset[str]]:
    repo_root = repo_root.resolve()
    if not environment_runtime_manifest_paths:
        return {}

    observable_truth_by_name: dict[str, frozenset[str]] = {}
    projection_alias_candidates: dict[str, set[str]] = {}
    for idx, module_manifest_path in enumerate(environment_runtime_manifest_paths):
        module_manifest_path = _resolve_runtime_manifest_path(
            module_manifest_path=module_manifest_path,
            repo_root=repo_root,
            module_idx=idx,
        )
        module_manifest = _load_json_model(
            module_manifest_path, _EnvironmentManifestCompat
        )
        module_runtime_dir = module_manifest_path.parent
        compiler_observable_truth_by_name = (
            _load_projection_observable_truth_from_compiler_environment_json(
                module_manifest_path=module_manifest_path
            )
        )
        class_truth_by_config_id = _load_class_attribute_truth_from_environment_json(
            module_manifest_path=module_manifest_path
        )

        opg_index_relpath = module_manifest.opg_index.file.strip()
        if not opg_index_relpath:
            raise ValueError(
                f"Invalid module manifest {module_manifest_path}: missing opg_index.file"
            )
        opg_index_path = (module_runtime_dir / opg_index_relpath).resolve()
        _assert_within(
            base=module_runtime_dir, candidate=opg_index_path, label="opg index path"
        )
        if not opg_index_path.exists():
            raise FileNotFoundError(f"OPG index not found: {opg_index_path}")
        opg_index = _load_json_model(opg_index_path, _OPGIndexFile)
        class_binding_by_config_id = _load_module_class_bindings(
            module_manifest=module_manifest,
            module_runtime_dir=module_runtime_dir,
            class_truth_by_config_id=class_truth_by_config_id,
        )

        for entry in opg_index.entries:
            model = _normalize_projection_token(entry.model or "")
            if not model:
                continue
            if model in observable_truth_by_name:
                raise ValueError(
                    f"Ambiguous projection model {model!r} across composed module manifests; expected one owner"
                )
            file_relpath = (entry.file or "").strip()
            if not file_relpath:
                raise ValueError(
                    f"Invalid OPG index entry for model {model!r} at {opg_index_path}: missing file"
                )
            opg_path = (module_runtime_dir / file_relpath).resolve()
            _assert_within(
                base=module_runtime_dir, candidate=opg_path, label="opg file path"
            )
            if not opg_path.exists():
                raise FileNotFoundError(f"OPG file not found: {opg_path}")
            opg_payload = _load_json_model(opg_path, _OPGFileCompat)
            projection_alias = _resolve_projection_root_alias(
                opg_payload=opg_payload,
                class_binding_by_config_id=class_binding_by_config_id,
            )
            if projection_alias:
                projection_alias_candidates.setdefault(projection_alias, set()).add(
                    model
                )
            compiler_observable_truth = _resolve_compiler_observable_truth(
                compiler_observable_truth_by_name=compiler_observable_truth_by_name,
                model=model,
            )
            if compiler_observable_truth is not None:
                observable_truth_by_name[model] = compiler_observable_truth
                continue
            identity = opg_payload.object_projection_graph_identity
            if identity is None:
                observable_truth_by_name[model] = frozenset()
                continue
            observables_raw = identity.object_projection_graph_observables
            observable_keys: set[str] = set()
            for observable_row in observables_raw:
                observable_key = _extract_observable_group_key(
                    observable_key=observable_row.observable_key or "",
                    key=observable_row.key or "",
                )
                if observable_key:
                    observable_keys.add(observable_key)
            observable_truth_by_name[model] = frozenset(observable_keys)

    _publish_unique_projection_aliases(
        truth_by_name=observable_truth_by_name,
        alias_candidates=projection_alias_candidates,
    )
    _publish_casefold_projection_aliases(truth_by_name=observable_truth_by_name)
    return observable_truth_by_name


def _load_module_class_bindings(
    *,
    module_manifest: _EnvironmentManifestCompat,
    module_runtime_dir: Path,
    class_truth_by_config_id: dict[str, _ClassConfigTruth],
) -> dict[str, _ClassBinding]:
    class_binding_by_config_id: dict[str, _ClassBinding] = {}

    bindings_artifact = module_manifest.bindings
    if bindings_artifact is None:
        return class_binding_by_config_id
    bindings_relpath = bindings_artifact.file.strip()
    if not bindings_relpath:
        return class_binding_by_config_id
    bindings_path = (module_runtime_dir / bindings_relpath).resolve()
    _assert_within(
        base=module_runtime_dir, candidate=bindings_path, label="bindings path"
    )
    if not bindings_path.exists():
        return class_binding_by_config_id

    bindings_payload = _load_json_model(bindings_path, _BindingsManifest)
    for row in bindings_payload.bindings:
        class_fqn = (row.class_fqn or "").strip()
        class_config_id = (row.canonical_class_config_id or "").strip() or (
            row.canonical_entity_id or ""
        ).strip()
        if not class_fqn or not class_config_id:
            continue

        attribute_names: set[str] = set()
        for mapping in row.sql_mapping:
            attribute_name = (mapping.attribute_name or "").strip()
            if attribute_name:
                attribute_names.add(attribute_name)

        class_truth: _ClassConfigTruth | None = None
        if class_config_id in class_truth_by_config_id:
            class_truth = class_truth_by_config_id[class_config_id]
        has_ocg_truth = class_truth is not None
        ocg_attribute_names: frozenset[str] = (
            class_truth.attributes if class_truth is not None else _EMPTY_FROZEN_STR
        )
        identity_key_attributes: frozenset[str] = (
            class_truth.identity_key_attributes
            if class_truth is not None
            else _EMPTY_FROZEN_STR
        )
        relationship_targets: tuple[tuple[str, str], ...] = (
            tuple(sorted(class_truth.relationship_targets.items()))
            if class_truth is not None
            else tuple()
        )

        class_name = class_fqn.rsplit(".", 1)[-1].strip()
        if not class_name:
            continue
        current = (
            class_name,
            class_fqn,
            (ocg_attribute_names if has_ocg_truth else frozenset(attribute_names)),
            identity_key_attributes,
            relationship_targets,
        )
        if (
            class_config_id in class_binding_by_config_id
            and class_binding_by_config_id[class_config_id] != current
        ):
            prior = class_binding_by_config_id[class_config_id]
            raise ValueError(
                f"Ambiguous class config binding {class_config_id!r} in {bindings_path}: {prior!r} vs {current!r}"
            )
        class_binding_by_config_id[class_config_id] = current

    return class_binding_by_config_id


def _load_class_attribute_truth_from_environment_json(
    *, module_manifest_path: Path
) -> dict[str, _ClassConfigTruth]:
    environment_json_path = _resolve_compiler_environment_json_path(
        module_manifest_path=module_manifest_path
    )
    _assert_within(
        base=environment_json_path.parent.parent,
        candidate=environment_json_path,
        label="compiler environment.json path",
    )
    if not environment_json_path.exists():
        return {}

    environment_config = _load_json_model(
        environment_json_path, _CompilerEnvironmentCompat
    )
    object_config_graphs = environment_config.object_config_graphs
    if not object_config_graphs:
        return {}

    canonical_language = _normalize_language_token(
        environment_config.canonical_language
    )
    canonical_graph = _select_canonical_graph(
        object_config_graphs=object_config_graphs,
        canonical_language=canonical_language,
    )
    if canonical_graph is None:
        return {}

    nodes = canonical_graph.object_config_graph_nodes
    attributes_by_class_config_id: dict[str, _ClassConfigTruth] = {}
    for node in nodes:
        class_config = node.class_config
        if class_config is None:
            continue
        class_config_id = _uuid_to_key(class_config.id)
        if not class_config_id:
            continue

        attribute_edges = class_config.class_config_attribute_configs
        if not attribute_edges:
            attributes_by_class_config_id[class_config_id] = _ClassConfigTruth(
                attributes=frozenset(),
                identity_key_attributes=frozenset(),
                relationship_targets={},
            )
            continue

        attribute_names: set[str] = set()
        identity_key_attribute_names: set[str] = set()
        attribute_name_by_config_id: dict[str, str] = {}
        for edge in attribute_edges:
            attribute_config = edge.attribute_config
            if attribute_config is None:
                continue
            attribute_name = attribute_config.name.strip()
            if not attribute_name:
                continue
            attribute_names.add(attribute_name)

            edge_attribute_config_id = _uuid_to_key(edge.attribute_config_id)
            if edge_attribute_config_id:
                attribute_name_by_config_id[edge_attribute_config_id] = attribute_name
            fallback_attribute_config_id = _uuid_to_key(attribute_config.id)
            if fallback_attribute_config_id:
                attribute_name_by_config_id[fallback_attribute_config_id] = (
                    attribute_name
                )

            is_identity_key = edge.is_identity_key
            if not is_identity_key:
                is_identity_key = bool(attribute_config.is_primary)
            if is_identity_key:
                identity_key_attribute_names.add(attribute_name)

        relationship_targets: dict[str, str] = {}
        for relationship_row in class_config.class_config_relationships:
            target_class_config_id = _uuid_to_key(
                relationship_row.target_class_config_id
            )
            if not target_class_config_id:
                continue
            for (
                relationship_attribute_row
            ) in relationship_row.class_config_relationship_attributes:
                attribute_config_id = _uuid_to_key(
                    relationship_attribute_row.attribute_config_id
                )
                if not attribute_config_id:
                    continue
                if attribute_config_id not in attribute_name_by_config_id:
                    continue
                attribute_name = attribute_name_by_config_id[attribute_config_id]
                relationship_targets[attribute_name] = target_class_config_id

        attributes_by_class_config_id[class_config_id] = _ClassConfigTruth(
            attributes=frozenset(attribute_names),
            identity_key_attributes=frozenset(identity_key_attribute_names),
            relationship_targets=relationship_targets,
        )
    return attributes_by_class_config_id


def _load_projection_observable_truth_from_compiler_environment_json(
    *, module_manifest_path: Path
) -> dict[str, frozenset[str]]:
    environment_json_path = _resolve_compiler_environment_json_path(
        module_manifest_path=module_manifest_path
    )
    if not environment_json_path.exists():
        return {}

    environment_config = _load_json_model(
        environment_json_path, _CompilerEnvironmentCompat
    )
    canonical_language = _normalize_language_token(
        environment_config.canonical_language or ""
    )
    canonical_graph = _select_canonical_compiler_graph(
        object_config_graphs=environment_config.object_config_graphs,
        canonical_language=canonical_language,
    )
    if canonical_graph is None:
        return {}

    graph_identity = canonical_graph.object_config_graph_identity
    if graph_identity is None:
        return {}

    observable_truth_by_name: dict[str, frozenset[str]] = {}
    for projection_identity in graph_identity.object_projection_graph_identities:
        projection_name = _normalize_projection_token(
            projection_identity.projection_name or ""
        )
        if not projection_name:
            continue
        observable_keys = frozenset(
            observable_key
            for observable_row in projection_identity.object_projection_graph_observables
            if (
                observable_key := _extract_observable_key(
                    observable_key=observable_row.observable_key or "",
                    key=observable_row.key or "",
                )
            )
        )
        observable_truth_by_name[projection_name] = observable_keys
    return observable_truth_by_name


def _resolve_compiler_observable_truth(
    *,
    compiler_observable_truth_by_name: dict[str, frozenset[str]],
    model: str,
) -> frozenset[str] | None:
    if model in compiler_observable_truth_by_name:
        return _collapse_observable_group_truth(
            compiler_observable_truth_by_name[model]
        )

    model_casefolded = model.casefold()
    matches = [
        truth
        for projection_name, truth in compiler_observable_truth_by_name.items()
        if projection_name.casefold() == model_casefolded
    ]
    if not matches:
        return None
    if len(matches) > 1:
        raise ValueError(
            f"Ambiguous compiler projection observable truth for projection {model!r}"
        )
    return _collapse_observable_group_truth(matches[0])


def _resolve_compiler_environment_json_path(*, module_manifest_path: Path) -> Path:
    runtime_dir = module_manifest_path.parent
    aware_dir = runtime_dir.parent.parent
    environment_json_path = (aware_dir / "compiler" / "environment.json").resolve()
    _assert_within(
        base=aware_dir,
        candidate=environment_json_path,
        label="compiler environment.json path",
    )
    return environment_json_path


def _select_canonical_graph(
    *,
    object_config_graphs: list[ObjectConfigGraph],
    canonical_language: str,
) -> ObjectConfigGraph | None:
    for graph in object_config_graphs:
        graph_language = _normalize_language_token(graph.language)
        if canonical_language and graph_language == canonical_language:
            return graph
    if object_config_graphs:
        return object_config_graphs[0]
    return None


def _select_canonical_compiler_graph(
    *,
    object_config_graphs: tuple[_CompilerObjectConfigGraphCompat, ...],
    canonical_language: str,
) -> _CompilerObjectConfigGraphCompat | None:
    for graph in object_config_graphs:
        graph_language = _normalize_language_token(graph.language or "")
        if canonical_language and graph_language == canonical_language:
            return graph
    if object_config_graphs:
        return object_config_graphs[0]
    return None


def _resolve_manifest_path(
    *,
    manifest_path_raw: str,
    repo_root: Path,
    composition_path: Path,
    module_idx: int,
) -> Path:
    module_manifest_path = Path(manifest_path_raw)
    if not module_manifest_path.is_absolute():
        module_manifest_path = (repo_root / module_manifest_path).resolve()
    else:
        module_manifest_path = module_manifest_path.resolve()
    _assert_within(
        base=repo_root, candidate=module_manifest_path, label="module manifest path"
    )
    if not module_manifest_path.exists():
        raise FileNotFoundError(
            "Environment module manifest not found: "
            + f"{module_manifest_path} (composition={composition_path} modules[{module_idx}])"
        )
    return module_manifest_path


def _manifest_paths_from_composition_manifest(
    *,
    composition_manifest_path: Path,
    repo_root: Path,
) -> tuple[Path, ...]:
    composition_path = composition_manifest_path.resolve()
    repo_root = repo_root.resolve()
    if not composition_path.exists():
        raise FileNotFoundError(
            f"Environment composition manifest not found: {composition_path}"
        )
    composition = _load_json_model(composition_path, _CompositionManifestCompat)
    if not composition.modules:
        return ()

    manifest_paths: list[Path] = []
    for idx, module_row in enumerate(composition.modules):
        manifest_path_raw = module_row.manifest_path.strip()
        if not manifest_path_raw:
            raise ValueError(
                f"Invalid module entry at {composition_path} modules[{idx}]: "
                "manifest_path must be non-empty string"
            )
        manifest_paths.append(
            _resolve_manifest_path(
                manifest_path_raw=manifest_path_raw,
                repo_root=repo_root,
                composition_path=composition_path,
                module_idx=idx,
            )
        )
    return tuple(manifest_paths)


def _resolve_runtime_manifest_path(
    *, module_manifest_path: Path, repo_root: Path, module_idx: int
) -> Path:
    if not module_manifest_path.is_absolute():
        resolved = (repo_root / module_manifest_path).resolve()
    else:
        resolved = module_manifest_path.resolve()
    _assert_within(base=repo_root, candidate=resolved, label="module manifest path")
    if not resolved.exists():
        raise FileNotFoundError(
            "Environment module manifest not found: "
            + f"{resolved} (runtime_manifests[{module_idx}])"
        )
    return resolved


def _load_json_model(path: Path, model_type: type[_TModel]) -> _TModel:
    raw_text = path.read_text(encoding="utf-8")
    try:
        return model_type.model_validate_json(raw_text)
    except Exception as exc:
        raise ValueError(
            f"Invalid {model_type.__name__} payload at {path}: {exc}"
        ) from exc


def _normalize_projection_token(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    if "." in token:
        token = token.split(".")[-1]
    return token.strip()


def _normalize_observable_token(raw: str) -> str:
    return (raw or "").strip().casefold()


def _extract_observable_key(*, observable_key: str, key: str) -> str:
    observable_key_token = observable_key.strip()
    if observable_key_token:
        return _normalize_observable_token(observable_key_token)
    key_token = key.strip()
    if key_token:
        if ":" in key_token:
            key_token = key_token.rsplit(":", 1)[-1]
        return _normalize_observable_token(key_token)
    return ""


def _extract_observable_group_key(*, observable_key: str, key: str) -> str:
    full_key = _extract_observable_key(observable_key=observable_key, key=key)
    if not full_key:
        return ""
    return _normalize_observable_group_token(full_key)


def _normalize_observable_group_token(raw: str) -> str:
    token = _normalize_observable_token(raw)
    if "." in token:
        token = token.rsplit(".", 1)[0]
    return token


def _collapse_observable_group_truth(observable_keys: frozenset[str]) -> frozenset[str]:
    return frozenset(
        observable_group
        for observable_key in observable_keys
        if (observable_group := _normalize_observable_group_token(observable_key))
    )


def _resolve_projection_root_alias(
    *,
    opg_payload: _OPGFileCompat,
    class_binding_by_config_id: dict[str, _ClassBinding],
) -> str | None:
    root_class_tokens: set[str] = set()
    for node in opg_payload.object_projection_graph_nodes:
        if not node.is_root:
            continue
        class_config_id = _uuid_to_key(node.class_config_id)
        if not class_config_id:
            continue
        binding = class_binding_by_config_id.get(class_config_id)
        if binding is None:
            continue
        class_token = _normalize_projection_token(binding[0])
        if class_token:
            root_class_tokens.add(class_token)
    if len(root_class_tokens) != 1:
        return None
    return next(iter(root_class_tokens))


def _publish_unique_projection_aliases(
    *,
    truth_by_name: dict[str, object],
    alias_candidates: dict[str, set[str]],
) -> None:
    for alias, models in alias_candidates.items():
        if alias in truth_by_name:
            continue
        if len(models) != 1:
            continue
        model = next(iter(models))
        if model not in truth_by_name:
            continue
        truth_by_name[alias] = truth_by_name[model]


def _publish_casefold_projection_aliases(*, truth_by_name: dict[str, object]) -> None:
    by_casefolded: dict[str, list[str]] = {}
    for projection_name in truth_by_name:
        by_casefolded.setdefault(projection_name.casefold(), []).append(projection_name)
    for casefolded_name, projection_names in by_casefolded.items():
        if casefolded_name in truth_by_name:
            continue
        if len(projection_names) != 1:
            continue
        truth_by_name[casefolded_name] = truth_by_name[projection_names[0]]


def _normalize_language_token(raw: CodeLanguage | str) -> str:
    if isinstance(raw, CodeLanguage):
        return raw.value.strip().lower()
    return raw.strip().lower()


def _uuid_to_key(raw: UUID | str | None) -> str:
    if raw is None:
        return ""
    if isinstance(raw, UUID):
        return str(raw)
    return raw.strip()


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}"
    )


__all__ = [
    "load_environment_projection_observable_truth",
    "load_environment_projection_observable_truth_from_runtime_manifests",
    "load_environment_projection_truth",
    "load_environment_projection_truth_from_runtime_manifests",
]
