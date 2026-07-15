from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, cast
from uuid import UUID

from aware_code.types import JsonObject
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionCallTarget,
    ResolveRuntimeRefsRequest,
    ResolveRuntimeRefsResponse,
    ResolvedRuntimeClassRef,
    ResolvedRuntimeFunctionTarget,
)


class EnvironmentRuntimeRefResolver(Protocol):
    async def get_runtime(self, *, environment_id: UUID) -> object: ...


async def resolve_runtime_refs(
    resolver: EnvironmentRuntimeRefResolver,
    request: ResolveRuntimeRefsRequest,
) -> ResolveRuntimeRefsResponse:
    runtime = await resolver.get_runtime(environment_id=request.environment_id)
    index = runtime.invoker.get_index()

    function_targets = tuple(
        _resolve_function_target(index=index, query=query)
        for query in request.function_targets
    )
    class_refs = tuple(
        _resolve_class_ref(index=index, query=query) for query in request.class_refs
    )
    result_statuses = tuple(
        result.status for result in (*function_targets, *class_refs)
    )
    return ResolveRuntimeRefsResponse(
        operation="resolve_runtime_refs",
        actor_id=request.actor_id,
        environment_id=request.environment_id,
        process_id=request.process_id,
        thread_id=request.thread_id,
        branch_id=request.branch_id,
        projection_hash=request.projection_hash,
        status=(
            "succeeded"
            if all(status == "resolved" for status in result_statuses)
            else "partial"
        ),
        error=None,
        function_targets=list(function_targets),
        class_refs=list(class_refs),
        evidence=JsonObject(
            {
                "resolver": "environment.runtime_ref",
                "function_target_count": len(function_targets),
                "class_ref_count": len(class_refs),
            }
        ),
    )


def resolve_runtime_refs_from_artifact_refs(
    *,
    artifact_refs: Sequence[object],
    request: ResolveRuntimeRefsRequest,
) -> ResolveRuntimeRefsResponse:
    catalog = _ArtifactRuntimeCatalog.from_artifact_refs(artifact_refs)
    function_targets = tuple(
        _resolve_artifact_function_target(catalog=catalog, query=query)
        for query in request.function_targets
    )
    class_refs = tuple(
        _resolve_artifact_class_ref(catalog=catalog, query=query)
        for query in request.class_refs
    )
    result_statuses = tuple(
        result.status for result in (*function_targets, *class_refs)
    )
    return ResolveRuntimeRefsResponse(
        operation="resolve_runtime_refs",
        actor_id=request.actor_id,
        environment_id=request.environment_id,
        process_id=request.process_id,
        thread_id=request.thread_id,
        branch_id=request.branch_id,
        projection_hash=request.projection_hash,
        status=(
            "succeeded"
            if all(status == "resolved" for status in result_statuses)
            else "partial"
        ),
        error=None,
        function_targets=list(function_targets),
        class_refs=list(class_refs),
        evidence=JsonObject(
            {
                "resolver": "environment.runtime_ref.artifact_registry",
                "artifact_set_count": catalog.artifact_set_count,
                "descriptor_count": len(catalog.descriptors),
                "function_target_count": len(function_targets),
                "class_ref_count": len(class_refs),
            }
        ),
    )


@dataclass(frozen=True, slots=True)
class _ArtifactClassEntry:
    class_config_id: UUID | None
    class_name: str | None
    class_fqn: str | None
    projection_name: str
    projection_hash: str | None
    object_projection_graph_id: UUID | None
    object_projection_graph_identity_id: UUID | None
    constructor_function_id: UUID | None
    function_entries: tuple[Mapping[str, object], ...]


@dataclass(frozen=True, slots=True)
class _ArtifactRuntimeCatalog:
    descriptors: tuple[_ArtifactClassEntry, ...]
    artifact_set_count: int

    @classmethod
    def from_artifact_refs(
        cls, artifact_refs: Sequence[object]
    ) -> "_ArtifactRuntimeCatalog":
        artifact_sets: list[Mapping[str, object]] = []
        descriptors: list[_ArtifactClassEntry] = []
        for artifact_ref in artifact_refs:
            artifact_set = _artifact_set_payload_from_ref(artifact_ref)
            if artifact_set is None:
                continue
            artifact_sets.append(artifact_set)
            for descriptor in _mapping_sequence(
                artifact_set.get("runtime_projection_descriptors")
            ):
                entry = _artifact_class_entry_from_descriptor(descriptor)
                if entry is not None:
                    descriptors.append(entry)
        return cls(
            descriptors=tuple(descriptors),
            artifact_set_count=len(artifact_sets),
        )

    def class_matches(self, class_ref: str) -> tuple[_ArtifactClassEntry, ...]:
        return tuple(
            entry
            for entry in self.descriptors
            if _artifact_class_matches(entry=entry, class_ref=class_ref)
        )


def _artifact_class_entry_from_descriptor(
    descriptor: Mapping[str, object],
) -> _ArtifactClassEntry | None:
    projection_name = _optional_text(descriptor.get("projection_name"))
    if projection_name is None:
        return None
    metadata = _mapping_payload(descriptor.get("metadata"))
    functions = _mapping_sequence(metadata.get("capability_functions"))
    class_config_id = _uuid_or_none(metadata.get("root_class_config_id"))
    class_name = _optional_text(metadata.get("root_class_name")) or projection_name
    class_fqn = _optional_text(metadata.get("root_class_fqn"))
    for function in functions:
        class_config_id = class_config_id or _uuid_or_none(
            function.get("owner_class_config_id")
        )
        class_name = _optional_text(function.get("owner_class_name")) or class_name
        class_fqn = _optional_text(function.get("owner_class_fqn")) or class_fqn
    return _ArtifactClassEntry(
        class_config_id=class_config_id,
        class_name=class_name,
        class_fqn=class_fqn,
        projection_name=projection_name,
        projection_hash=_optional_text(descriptor.get("projection_hash")),
        object_projection_graph_id=_uuid_or_none(
            descriptor.get("object_projection_graph_id")
        ),
        object_projection_graph_identity_id=_uuid_or_none(
            descriptor.get("object_projection_graph_identity_id")
        ),
        constructor_function_id=_uuid_or_none(
            descriptor.get("constructor_function_id")
        ),
        function_entries=functions,
    )


def _resolve_artifact_function_target(
    *,
    catalog: _ArtifactRuntimeCatalog,
    query: object,
) -> ResolvedRuntimeFunctionTarget:
    query_key = _optional_text(getattr(query, "query_key", None))
    function_ref = _optional_text(getattr(query, "function_ref", None)) or ""
    call_target = _call_target(getattr(query, "call_target", None))
    projection_hash_hint = _optional_text(getattr(query, "projection_hash_hint", None))
    class_ref, separator, function_name = function_ref.rpartition(".")
    if not class_ref or not separator or not function_name:
        return _function_target_result(
            query_key=query_key,
            function_ref=function_ref,
            call_target=call_target,
            status="invalid_ref",
            error="function_ref must be a qualified '<class_fqn>.<function_name>' value.",
        )
    class_matches = catalog.class_matches(class_ref)
    if projection_hash_hint is not None:
        hinted = tuple(
            entry
            for entry in class_matches
            if entry.projection_hash == projection_hash_hint
        )
        if hinted:
            class_matches = hinted
    if len(class_matches) != 1:
        return _artifact_function_target_result(
            query_key=query_key,
            function_ref=function_ref,
            call_target=call_target,
            status=("class_not_found" if not class_matches else "ambiguous_class_ref"),
            error=f"class_ref {class_ref!r} matched {len(class_matches)} artifact descriptors.",
            entry=class_matches[0] if len(class_matches) == 1 else None,
            evidence={
                "class_ref": class_ref,
                "match_count": len(class_matches),
                "projection_hash_hint": projection_hash_hint,
            },
        )
    entry = class_matches[0]
    function_matches = tuple(
        function
        for function in entry.function_entries
        if _optional_text(function.get("name")) == function_name
    )
    if len(function_matches) != 1:
        return _artifact_function_target_result(
            query_key=query_key,
            function_ref=function_ref,
            call_target=call_target,
            status=(
                "function_not_found" if not function_matches else "ambiguous_function"
            ),
            error=(
                f"function_name {function_name!r} matched {len(function_matches)} "
                f"artifact functions on {class_ref!r}."
            ),
            entry=entry,
            evidence={"class_ref": class_ref, "function_name": function_name},
        )
    function = function_matches[0]
    return _artifact_function_target_result(
        query_key=query_key,
        function_ref=function_ref,
        call_target=call_target,
        status="resolved",
        entry=entry,
        function=function,
        evidence={
            "resolver": "environment.runtime_ref.artifact_registry",
            "class_ref": class_ref,
            "function_name": function_name,
            "projection_hash_hint": projection_hash_hint,
        },
    )


def _resolve_artifact_class_ref(
    *,
    catalog: _ArtifactRuntimeCatalog,
    query: object,
) -> ResolvedRuntimeClassRef:
    query_key = _optional_text(getattr(query, "query_key", None))
    class_ref = _optional_text(getattr(query, "class_ref", None)) or ""
    if not class_ref:
        return ResolvedRuntimeClassRef(
            query_key=query_key,
            status="invalid_ref",
            error="class_ref is required.",
            class_ref=class_ref,
        )
    matches = catalog.class_matches(class_ref)
    if len(matches) != 1:
        return ResolvedRuntimeClassRef(
            query_key=query_key,
            status=("class_not_found" if not matches else "ambiguous_class_ref"),
            error=f"class_ref {class_ref!r} matched {len(matches)} artifact descriptors.",
            class_ref=class_ref,
            evidence=JsonObject({"match_count": len(matches)}),
        )
    entry = matches[0]
    return ResolvedRuntimeClassRef(
        query_key=query_key,
        status="resolved",
        error=None,
        class_ref=class_ref,
        class_config_id=entry.class_config_id,
        class_name=entry.class_name,
        class_fqn=entry.class_fqn,
        evidence=JsonObject({"resolver": "environment.runtime_ref.artifact_registry"}),
    )


def _artifact_function_target_result(
    *,
    query_key: str | None,
    function_ref: str,
    call_target: InvokeFunctionCallTarget,
    status: str,
    error: str | None = None,
    entry: _ArtifactClassEntry | None = None,
    function: Mapping[str, object] | None = None,
    evidence: dict[str, object] | None = None,
) -> ResolvedRuntimeFunctionTarget:
    return ResolvedRuntimeFunctionTarget(
        query_key=query_key,
        status=status,
        error=error,
        function_ref=function_ref,
        call_target=call_target,
        class_config_id=entry.class_config_id if entry is not None else None,
        class_name=entry.class_name if entry is not None else None,
        class_fqn=entry.class_fqn if entry is not None else None,
        class_config_function_config_id=_uuid_or_none(
            function.get("link_id") if function is not None else None
        ),
        function_id=_uuid_or_none(function.get("id") if function is not None else None),
        function_name=_optional_text(
            function.get("name") if function is not None else None
        ),
        projection_hash=entry.projection_hash if entry is not None else None,
        object_projection_graph_id=(
            entry.object_projection_graph_id if entry is not None else None
        ),
        object_projection_graph_identity_id=(
            entry.object_projection_graph_identity_id if entry is not None else None
        ),
        candidate_projection_hashes=(
            [entry.projection_hash]
            if entry is not None and entry.projection_hash is not None
            else []
        ),
        evidence=cast(JsonObject, dict(evidence or {})),
    )


def _artifact_class_matches(
    *,
    entry: _ArtifactClassEntry,
    class_ref: str,
) -> bool:
    return class_ref in {
        item
        for item in (
            entry.class_fqn,
            entry.class_name,
            entry.projection_name,
        )
        if item
    }


def _artifact_set_payload_from_ref(
    artifact_ref: object,
) -> Mapping[str, object] | None:
    artifact_family = _optional_text(
        _artifact_ref_value(artifact_ref, "artifact_family")
    )
    artifact_role = _optional_text(_artifact_ref_value(artifact_ref, "artifact_role"))
    if artifact_family != "ontology_runtime_artifact_set" and (
        artifact_role != "runtime_artifact_set"
    ):
        return None
    receipt = _artifact_ref_mapping(artifact_ref, "receipt")
    artifact_set = _mapping_payload(receipt.get("ontology_runtime_artifact_set"))
    if artifact_set:
        return artifact_set
    provider_payload = _artifact_ref_mapping(artifact_ref, "provider_payload")
    artifact_set = _mapping_payload(
        provider_payload.get("ontology_runtime_artifact_set")
    )
    return artifact_set or None


def _artifact_ref_mapping(artifact_ref: object, key: str) -> Mapping[str, object]:
    return _mapping_payload(_artifact_ref_value(artifact_ref, key))


def _artifact_ref_value(artifact_ref: object, key: str) -> object | None:
    if isinstance(artifact_ref, Mapping):
        return artifact_ref.get(key)
    return getattr(artifact_ref, key, None)


def _resolve_function_target(
    *,
    index: object,
    query: object,
) -> ResolvedRuntimeFunctionTarget:
    query_key = _optional_text(getattr(query, "query_key", None))
    function_ref = _optional_text(getattr(query, "function_ref", None)) or ""
    call_target = _call_target(getattr(query, "call_target", None))
    projection_hash_hint = _optional_text(getattr(query, "projection_hash_hint", None))

    class_ref, separator, function_name = function_ref.rpartition(".")
    if not class_ref or not separator or not function_name:
        return _function_target_result(
            query_key=query_key,
            function_ref=function_ref,
            call_target=call_target,
            status="invalid_ref",
            error="function_ref must be a qualified '<class_fqn>.<function_name>' value.",
        )

    class_matches = _class_config_matches(index=index, class_ref=class_ref)
    if len(class_matches) != 1:
        return _function_target_result(
            query_key=query_key,
            function_ref=function_ref,
            call_target=call_target,
            status=("class_not_found" if not class_matches else "ambiguous_class_ref"),
            error=f"class_ref {class_ref!r} matched {len(class_matches)} classes.",
            evidence={
                "class_ref": class_ref,
                "match_count": len(class_matches),
            },
        )
    class_config = class_matches[0]
    function_links = [
        link
        for link in getattr(class_config, "class_config_function_configs", ())
        if _link_is_public(link)
        and getattr(getattr(link, "function_config", None), "name", None)
        == function_name
    ]
    if len(function_links) != 1:
        return _function_target_result(
            query_key=query_key,
            function_ref=function_ref,
            call_target=call_target,
            status=(
                "function_not_found" if not function_links else "ambiguous_function"
            ),
            error=(
                f"function_name {function_name!r} matched {len(function_links)} "
                f"public functions on {class_ref!r}."
            ),
            class_config=class_config,
            evidence={
                "class_ref": class_ref,
                "function_name": function_name,
                "match_count": len(function_links),
            },
        )
    function_link = function_links[0]
    function_config = function_link.function_config

    if call_target == InvokeFunctionCallTarget.opg_constructor:
        projection_result = _resolve_constructor_projection(
            index=index,
            class_config=class_config,
            function_link=function_link,
        )
    else:
        projection_result = _resolve_instance_projection(
            index=index,
            class_config=class_config,
            projection_hash_hint=projection_hash_hint,
        )
    if projection_result.status != "resolved":
        return _function_target_result(
            query_key=query_key,
            function_ref=function_ref,
            call_target=call_target,
            status=projection_result.status,
            error=projection_result.error,
            class_config=class_config,
            function_link=function_link,
            function_config=function_config,
            candidate_projection_hashes=projection_result.candidate_hashes,
            evidence={
                "class_ref": class_ref,
                "function_name": function_name,
                "projection_hash_hint": projection_hash_hint,
            },
        )

    return _function_target_result(
        query_key=query_key,
        function_ref=function_ref,
        call_target=call_target,
        status="resolved",
        class_config=class_config,
        function_link=function_link,
        function_config=function_config,
        projection=projection_result.projection,
        evidence={
            "resolver": "environment.runtime_ref",
            "class_ref": class_ref,
            "function_name": function_name,
            "projection_hash_hint": projection_hash_hint,
        },
    )


def _resolve_class_ref(
    *,
    index: object,
    query: object,
) -> ResolvedRuntimeClassRef:
    query_key = _optional_text(getattr(query, "query_key", None))
    class_ref = _optional_text(getattr(query, "class_ref", None)) or ""
    if not class_ref:
        return ResolvedRuntimeClassRef(
            query_key=query_key,
            status="invalid_ref",
            error="class_ref is required.",
            class_ref=class_ref,
        )
    matches = _class_config_matches(index=index, class_ref=class_ref)
    if len(matches) != 1:
        return ResolvedRuntimeClassRef(
            query_key=query_key,
            status=("class_not_found" if not matches else "ambiguous_class_ref"),
            error=f"class_ref {class_ref!r} matched {len(matches)} classes.",
            class_ref=class_ref,
            evidence=JsonObject({"match_count": len(matches)}),
        )
    class_config = matches[0]
    return ResolvedRuntimeClassRef(
        query_key=query_key,
        status="resolved",
        error=None,
        class_ref=class_ref,
        class_config_id=_uuid_or_none(getattr(class_config, "id", None)),
        class_name=_optional_text(getattr(class_config, "name", None)),
        class_fqn=_class_fqn(class_config),
        evidence=JsonObject({"resolver": "environment.runtime_ref"}),
    )


def _function_target_result(
    *,
    query_key: str | None,
    function_ref: str,
    call_target: InvokeFunctionCallTarget,
    status: str,
    error: str | None = None,
    class_config: object | None = None,
    function_link: object | None = None,
    function_config: object | None = None,
    projection: object | None = None,
    candidate_projection_hashes: tuple[str, ...] = (),
    evidence: dict[str, object] | None = None,
) -> ResolvedRuntimeFunctionTarget:
    return ResolvedRuntimeFunctionTarget(
        query_key=query_key,
        status=status,
        error=error,
        function_ref=function_ref,
        call_target=call_target,
        class_config_id=_uuid_or_none(getattr(class_config, "id", None)),
        class_name=_optional_text(getattr(class_config, "name", None)),
        class_fqn=_class_fqn(class_config),
        class_config_function_config_id=_uuid_or_none(
            getattr(function_link, "id", None)
        ),
        function_id=_uuid_or_none(getattr(function_config, "id", None)),
        function_name=_optional_text(getattr(function_config, "name", None)),
        projection_hash=_optional_text(getattr(projection, "projection_hash", None)),
        object_projection_graph_id=_uuid_or_none(getattr(projection, "id", None)),
        object_projection_graph_identity_id=_uuid_or_none(
            getattr(projection, "object_projection_graph_identity_id", None)
        ),
        candidate_projection_hashes=list(candidate_projection_hashes),
        evidence=cast(JsonObject, dict(evidence or {})),
    )


def _class_config_matches(*, index: object, class_ref: str) -> list[object]:
    class_configs = getattr(index, "class_configs_by_id", {})
    values = getattr(class_configs, "values", None)
    if not callable(values):
        return []
    return [
        class_config
        for class_config in cast(Iterable[object], values())
        if _class_fqn(class_config) == class_ref
    ]


def _resolve_constructor_projection(
    *,
    index: object,
    class_config: object,
    function_link: object,
) -> "_ProjectionResolution":
    class_config_id = _uuid_or_none(getattr(class_config, "id", None))
    function_link_id = _uuid_or_none(getattr(function_link, "id", None))
    matches = []
    for projection in _runtime_index_projections(index=index):
        root_nodes = [
            node
            for node in getattr(projection, "object_projection_graph_nodes", ())
            if bool(getattr(node, "is_root", False))
        ]
        if (
            len(root_nodes) != 1
            or class_config_id is None
            or getattr(root_nodes[0], "class_config_id", None) != class_config_id
        ):
            continue
        if any(
            getattr(constructor, "function_constructor_id", None) == function_link_id
            for constructor in getattr(
                projection,
                "object_projection_graph_constructors",
                (),
            )
        ):
            matches.append(projection)
    return _projection_resolution(matches=matches)


def _resolve_instance_projection(
    *,
    index: object,
    class_config: object,
    projection_hash_hint: str | None,
) -> "_ProjectionResolution":
    class_config_id = _uuid_or_none(getattr(class_config, "id", None))
    matches = [
        projection
        for projection in _runtime_index_projections(index=index)
        if any(
            getattr(node, "class_config_id", None) == class_config_id
            for node in getattr(projection, "object_projection_graph_nodes", ())
        )
    ]
    if projection_hash_hint is not None:
        matches = [
            projection
            for projection in matches
            if _optional_text(getattr(projection, "projection_hash", None))
            == projection_hash_hint
        ]
    return _projection_resolution(matches=matches)


class _ProjectionResolution:
    def __init__(
        self,
        *,
        status: str,
        projection: object | None = None,
        candidate_hashes: tuple[str, ...] = (),
        error: str | None = None,
    ) -> None:
        self.status = status
        self.projection = projection
        self.candidate_hashes = candidate_hashes
        self.error = error


def _projection_resolution(*, matches: list[object]) -> _ProjectionResolution:
    candidate_hashes = tuple(
        sorted(
            projection_hash
            for projection_hash in (
                _optional_text(getattr(projection, "projection_hash", None))
                for projection in matches
            )
            if projection_hash is not None
        )
    )
    if len(matches) == 1:
        return _ProjectionResolution(status="resolved", projection=matches[0])
    if not matches:
        return _ProjectionResolution(
            status="projection_not_found",
            candidate_hashes=(),
            error="No projection matched the runtime function target.",
        )
    return _ProjectionResolution(
        status="ambiguous_projection",
        candidate_hashes=candidate_hashes,
        error="Multiple projections matched the runtime function target.",
    )


def _runtime_index_projections(*, index: object) -> tuple[object, ...]:
    ocg = getattr(index, "ocg", None)
    projections = getattr(ocg, "object_projection_graphs", None)
    if projections is not None:
        return tuple(cast(Iterable[object], projections))
    opg_by_id = getattr(index, "opg_by_id", None)
    values = getattr(opg_by_id, "values", None)
    if callable(values):
        return tuple(cast(Iterable[object], values()))
    return ()


def _call_target(value: object) -> InvokeFunctionCallTarget:
    if isinstance(value, InvokeFunctionCallTarget):
        return value
    text = _optional_text(getattr(value, "value", value))
    if text == InvokeFunctionCallTarget.opg_constructor.value:
        return InvokeFunctionCallTarget.opg_constructor
    if text == "opg_read":
        raise ValueError(
            "call_target='opg_read' is retired; use service-owned reads/views"
        )
    return InvokeFunctionCallTarget.instance


def _class_fqn(class_config: object | None) -> str | None:
    if class_config is None:
        return None
    return _optional_text(
        getattr(class_config, "class_fqn", None) or getattr(class_config, "fqn", None)
    )


def _link_is_public(link: object) -> bool:
    return bool(getattr(link, "is_public", True))


def _uuid_or_none(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if value is None:
        return None
    try:
        return UUID(str(value))
    except ValueError:
        return None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _mapping_payload(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump(mode="json")
        if isinstance(dumped, Mapping):
            return {str(key): item for key, item in dumped.items()}
    return {}


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(payload for item in value if (payload := _mapping_payload(item)))


__all__ = [
    "EnvironmentRuntimeRefResolver",
    "resolve_runtime_refs",
    "resolve_runtime_refs_from_artifact_refs",
]
