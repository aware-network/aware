from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.types.json import JsonArray, JsonObject
from aware_environment_service_dto.environment.environment import (
    InvokeFunctionCallTarget,
    InvokeFunctionRequest,
    InvokeFunctionResponse,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materialization_cache import (
    CachedLaneMaterializer,
)
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)
from aware_environment.branching import stable_environment_thread_branch_id


class EnvironmentRuntimeResolverLike(Protocol):
    async def get_runtime(self, *, environment_id: UUID) -> Any: ...


class _OcgSupport:
    @staticmethod
    def find_projection_hash_by_name(
        *,
        index: MetaGraphRuntimeIndex,
        projection_name: str,
    ) -> str:
        target = (projection_name or "").strip()
        for opg in index.ocg.object_projection_graphs:
            name = (opg.name or "").strip()
            if name == target:
                return opg.projection_hash
        raise ValueError(
            f"Projection {projection_name!r} was not found in hosted environment OCG"
        )

    @staticmethod
    def resolve_public_function_id(
        *,
        index: MetaGraphRuntimeIndex,
        class_name_suffix: str,
        function_name: str,
    ) -> UUID:
        normalized_suffix = (class_name_suffix or "").strip()
        normalized_fn_name = (function_name or "").strip()
        if not normalized_suffix:
            raise ValueError("class_name_suffix is required")
        if not normalized_fn_name:
            raise ValueError("function_name is required")

        suffix_leaf = normalized_suffix.rsplit(".", 1)[-1]

        function_by_id: dict[UUID, object] = {}
        for node in index.ocg.object_config_graph_nodes:
            if (
                node.type == ObjectConfigGraphNodeType.function
                and node.function_config is not None
            ):
                function_by_id[node.function_config.id] = node.function_config

        matches: set[UUID] = set()
        for node in index.ocg.object_config_graph_nodes:
            if (
                node.type != ObjectConfigGraphNodeType.class_
                or node.class_config is None
            ):
                continue
            class_name = (node.class_config.name or "").strip()
            class_match = class_name.endswith(normalized_suffix)
            if not class_match and "." in normalized_suffix:
                class_match = class_name == suffix_leaf or class_name.endswith(
                    f".{suffix_leaf}"
                )
            if not class_match:
                continue
            for link in node.class_config.class_config_function_configs:
                if not link.is_public:
                    continue
                fn_cfg = link.function_config
                function_config_id = getattr(link, "function_config_id", None)
                if function_config_id is not None:
                    fn_cfg = function_by_id.get(function_config_id) or fn_cfg
                if fn_cfg is None:
                    continue
                if (fn_cfg.name or "").strip() == normalized_fn_name:
                    matches.add(fn_cfg.id)

        if not matches:
            raise ValueError(
                "Could not resolve function "
                f"{normalized_fn_name!r} for class suffix {normalized_suffix!r}"
            )
        if len(matches) > 1:
            raise ValueError(
                "Ambiguous function "
                f"{normalized_fn_name!r} for class suffix {normalized_suffix!r}"
            )
        return next(iter(matches))

    @staticmethod
    def resolve_class_config_id(
        *,
        index: MetaGraphRuntimeIndex,
        class_name_suffix: str,
    ) -> UUID:
        normalized_suffix = (class_name_suffix or "").strip()
        if not normalized_suffix:
            raise ValueError("class_name_suffix is required")

        suffix_leaf = normalized_suffix.rsplit(".", 1)[-1]

        matches: set[UUID] = set()
        for node in index.ocg.object_config_graph_nodes:
            if (
                node.type != ObjectConfigGraphNodeType.class_
                or node.class_config is None
            ):
                continue
            class_name = (node.class_config.name or "").strip()
            class_match = class_name.endswith(normalized_suffix)
            if not class_match and "." in normalized_suffix:
                class_match = class_name == suffix_leaf or class_name.endswith(
                    f".{suffix_leaf}"
                )
            if not class_match:
                continue
            matches.add(node.class_config.id)

        if not matches:
            raise ValueError(
                f"Could not resolve class config id for suffix {normalized_suffix!r}"
            )
        if len(matches) > 1:
            raise ValueError(
                f"Ambiguous class config id for suffix {normalized_suffix!r}"
            )
        return next(iter(matches))

    @staticmethod
    def build_attr_name_by_id_for_class_config(
        *,
        index: MetaGraphRuntimeIndex,
        class_config_id: UUID,
    ) -> dict[UUID, str]:
        class_cfg = None
        for node in index.ocg.object_config_graph_nodes:
            if (
                node.type == ObjectConfigGraphNodeType.class_
                and node.class_config is not None
                and node.class_config.id == class_config_id
            ):
                class_cfg = node.class_config
                break
        if class_cfg is None:
            return {}

        attr_name_by_id: dict[UUID, str] = {}
        for link in class_cfg.class_config_attribute_configs:
            if link.attribute_config is None:
                continue
            attr_name_by_id[link.attribute_config.id] = link.attribute_config.name
        return attr_name_by_id

    @staticmethod
    def resolve_single_opg_constructor_function_id(
        *,
        index: MetaGraphRuntimeIndex,
        object_projection_graph_id: UUID,
    ) -> UUID:
        opg = next(
            (
                item
                for item in index.ocg.object_projection_graphs
                if item.id == object_projection_graph_id
            ),
            None,
        )
        if opg is None:
            raise ValueError(
                "ObjectProjectionGraph not found: "
                f"object_projection_graph_id={object_projection_graph_id}"
            )

        constructors = list(opg.object_projection_graph_constructors or [])
        if len(constructors) != 1:
            raise ValueError(
                "Expected exactly one OPG constructor for bootstrap resolution: "
                f"object_projection_graph_id={object_projection_graph_id} "
                f"count={len(constructors)}"
            )

        constructor = constructors[0]
        constructor_link_id = constructor.function_constructor_id
        for node in index.ocg.object_config_graph_nodes:
            if (
                node.type != ObjectConfigGraphNodeType.class_
                or node.class_config is None
            ):
                continue
            for link in node.class_config.class_config_function_configs:
                if link.id != constructor_link_id:
                    continue
                function_config_id = getattr(link, "function_config_id", None)
                if not isinstance(function_config_id, UUID):
                    raise ValueError(
                        "OPG constructor link missing function_config_id: "
                        f"object_projection_graph_id={object_projection_graph_id} "
                        f"function_constructor_id={constructor_link_id}"
                    )
                return function_config_id

        raise ValueError(
            "OPG constructor link not found in OCG class-function edges: "
            f"object_projection_graph_id={object_projection_graph_id} "
            f"function_constructor_id={constructor_link_id}"
        )

    @staticmethod
    def build_opgi_index(
        *,
        index: MetaGraphRuntimeIndex,
    ) -> dict[str, tuple[UUID, set[str]]]:
        by_key: dict[str, tuple[UUID, set[str]]] = {}
        for opg in index.ocg.object_projection_graphs:
            _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
                index=index,
                projection_hash=opg.projection_hash,
            )
            if opgi is None:
                continue
            key = (opgi.projection_name or "").strip()
            if not key:
                continue
            view_keys = {
                (observable.observable_key or "").strip()
                for observable in (opgi.object_projection_graph_observables or [])
                if (observable.observable_key or "").strip()
            }
            if not view_keys:
                view_keys = {
                    (observable.key or "").strip()
                    for observable in (opgi.object_projection_graph_observables or [])
                    if (observable.key or "").strip()
                }
            by_key[key] = (opgi.id, view_keys)
        return by_key


class _OigSupport:
    @staticmethod
    def extract_primitive_scalar(value: Any | None) -> str | None:
        if value is None:
            return None
        try:
            raw = value.get("value")
            if isinstance(raw, str):
                return raw
            if raw is None:
                return None
            return str(raw)
        except Exception:
            try:
                return str(value)
            except Exception:
                return None

    @staticmethod
    def extract_primitive_json_value(value: Any | None) -> Any | None:
        if value is None:
            return None
        if isinstance(value, Mapping):
            return value.get("value")
        try:
            return value.get("value")
        except Exception:
            return None

    def extract_scalar_from_value_root(self, value_root: Any) -> str | None:
        if value_root is None:
            return None

        primitive = getattr(value_root, "primitive_value", None)
        if primitive is not None:
            return self.extract_primitive_scalar(primitive)

        enum_option_id = getattr(value_root, "enum_option_id", None)
        if enum_option_id is not None:
            enum_option_id_text = str(enum_option_id).strip()
            if enum_option_id_text:
                type_descriptor = getattr(value_root, "type_descriptor", None)
                enum_config = (
                    getattr(type_descriptor, "enum_config", None)
                    if type_descriptor is not None
                    else None
                )
                for option in getattr(enum_config, "enum_options", []) or []:
                    option_id_text = str(getattr(option, "id", "")).strip()
                    if option_id_text != enum_option_id_text:
                        continue
                    option_value = str(getattr(option, "value", "")).strip()
                    if option_value:
                        return option_value
                    option_label = str(getattr(option, "label", "")).strip()
                    if option_label:
                        return option_label
                return enum_option_id_text

        for link in getattr(value_root, "child_links", []) or []:
            child = getattr(link, "child", None)
            scalar = self.extract_scalar_from_value_root(child)
            if scalar is not None:
                return scalar

        return None

    def extract_json_from_value_root(self, value_root: Any) -> Any | None:
        if value_root is None:
            return None

        primitive = getattr(value_root, "primitive_value", None)
        if primitive is not None:
            extracted = self.extract_primitive_json_value(primitive)
            if extracted is not None:
                return extracted
            return primitive

        enum_option_id = getattr(value_root, "enum_option_id", None)
        if enum_option_id is not None:
            scalar = self.extract_scalar_from_value_root(value_root)
            if scalar is not None:
                return scalar

        child_links = list(getattr(value_root, "child_links", []) or [])
        if not child_links:
            return None

        grouped_mapping_children: dict[str, dict[str, Any]] = {}
        has_mapping_roles = False
        for link in child_links:
            raw_role = getattr(link, "role", None)
            role = str(getattr(raw_role, "value", raw_role) or "").strip().casefold()
            if role not in {"key", "value", "value_"}:
                continue
            has_mapping_roles = True
            group_key = str(getattr(link, "identity_key", "") or "").strip()
            if not group_key:
                position = getattr(link, "position", None)
                if isinstance(position, int):
                    group_key = str(position)
                else:
                    child = getattr(link, "child", None)
                    group_key = str(getattr(child, "id", "") or "").strip()
            child_value = self.extract_json_from_value_root(
                getattr(link, "child", None)
            )
            grouped_mapping_children.setdefault(group_key, {})[role] = child_value

        if has_mapping_roles:
            out: dict[Any, Any] = {}
            for group_key in sorted(grouped_mapping_children):
                entry = grouped_mapping_children[group_key]
                if "key" not in entry:
                    continue
                if "value" in entry:
                    out[entry["key"]] = entry["value"]
                elif "value_" in entry:
                    out[entry["key"]] = entry["value_"]
            return out

        sortable_children: list[tuple[int, str, Any]] = []
        for link in child_links:
            raw_role = getattr(link, "role", None)
            role = str(getattr(raw_role, "value", raw_role) or "").strip().casefold()
            if role and role not in {"element", "member"}:
                continue
            position = getattr(link, "position", None)
            sort_position = position if isinstance(position, int) else 10_000_000
            child = getattr(link, "child", None)
            child_id = str(getattr(child, "id", "") or "").strip()
            sortable_children.append((sort_position, child_id, child))

        if not sortable_children:
            return [
                self.extract_json_from_value_root(getattr(link, "child", None))
                for link in child_links
            ]

        sortable_children.sort(key=lambda item: (item[0], item[1]))
        return [
            self.extract_json_from_value_root(child)
            for _position, _child_id, child in sortable_children
        ]

    def extract_attr_scalar(
        self,
        *,
        class_instance: Any,
        attr_name_by_id: dict[UUID, str],
        name: str,
    ) -> str | None:
        for attr in getattr(class_instance, "attributes", []) or []:
            attr_id = getattr(attr, "attribute_config_id", None)
            if not isinstance(attr_id, UUID):
                continue
            attr_name = attr_name_by_id.get(attr_id)
            if attr_name != name:
                continue
            value_root = getattr(attr, "value_root", None)
            return self.extract_scalar_from_value_root(value_root)
        return None

    def extract_attr_json(
        self,
        *,
        class_instance: Any,
        attr_name_by_id: dict[UUID, str],
        name: str,
    ) -> Any | None:
        for attr in getattr(class_instance, "attributes", []) or []:
            attr_id = getattr(attr, "attribute_config_id", None)
            if not isinstance(attr_id, UUID):
                continue
            attr_name = attr_name_by_id.get(attr_id)
            if attr_name != name:
                continue
            value_root = getattr(attr, "value_root", None)
            return self.extract_json_from_value_root(value_root)
        return None


class _LaneSupport:
    @staticmethod
    async def materialize_lane_instance_ids(
        *,
        index: MetaGraphRuntimeIndex,
        branch_id: UUID,
        projection_hash: str,
    ) -> set[UUID]:
        head = await FSCommitStore().head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
        if head is None or not head.get("commit_id"):
            return set()

        commit_id = UUID(str(head["commit_id"]))
        oig_id_raw = head.get("object_instance_graph_id")
        oig_id = UUID(str(oig_id_raw)) if oig_id_raw else None

        opg = index.opg_by_hash.get(projection_hash)
        if opg is None:
            return set()

        oig, _idx = await CachedLaneMaterializer().get(
            branch_id=branch_id,
            ocg=index.ocg,
            opg=opg,
            commit_id=commit_id,
            oig_id=oig_id,
        )
        source_object_ids: set[UUID] = set()
        for instance in oig.class_instances:
            source_object_id = getattr(instance, "source_object_id", None)
            if not isinstance(source_object_id, UUID):
                raise RuntimeError(
                    "Lane materialization produced ClassInstance without "
                    "source_object_id "
                    f"(class_instance_id={getattr(instance, 'id', None)} "
                    f"projection_hash={projection_hash})"
                )
            source_object_ids.add(source_object_id)
        return source_object_ids


class _InvokeSupport:
    @staticmethod
    def assert_invoke_succeeded(
        *,
        response: InvokeFunctionResponse,
        label: str,
    ) -> None:
        if response.status == "succeeded":
            return
        if response.error:
            raise RuntimeError(f"{label} failed: {response.error}")
        raise RuntimeError(f"{label} failed")

    @staticmethod
    async def invoke_instance_environment_function(
        *,
        runtime: Any,
        index: MetaGraphRuntimeIndex,
        actor_id: UUID | None,
        environment_id: UUID | None,
        process_id: UUID | None,
        thread_id: UUID | None,
        branch_id: UUID,
        projection_hash: str,
        object_id: UUID,
        function_id: UUID,
        args: list[Any],
        commit: bool,
    ) -> InvokeFunctionResponse:
        request = InvokeFunctionRequest(
            operation="invoke_function",
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            call_target=InvokeFunctionCallTarget.instance,
            object_id=object_id,
            object_projection_graph_id=None,
            function_id=function_id,
            args=JsonArray(args),
            kwargs=JsonObject({}),
            expected_graph_hash_pre=None,
            expected_head_commit_id=None,
            commit=commit,
            publish=False,
        )
        return await runtime.invoker.invoke_function_with_index(
            index=index,
            request=request,
        )


class _StableIds:
    @staticmethod
    def stable_environment_experience_profile_id(*, environment_id: UUID) -> UUID:
        return uuid5(
            NAMESPACE_URL, f"aware:environment_experience_profile:{environment_id}"
        )

    @staticmethod
    def stable_process_id_for_key(*, environment_id: UUID, process_key: str) -> UUID:
        return uuid5(NAMESPACE_URL, f"aware:process:{environment_id}:{process_key}")

    @staticmethod
    def stable_thread_id_for_key(*, environment_id: UUID, thread_key: str) -> UUID:
        return uuid5(NAMESPACE_URL, f"aware:thread:{environment_id}:{thread_key}")

    @staticmethod
    def stable_process_config_id_for_process(*, process_id: UUID) -> UUID:
        return uuid5(NAMESPACE_URL, f"aware:process_config:{process_id}")

    @staticmethod
    def stable_thread_config_id_for_thread(*, thread_id: UUID) -> UUID:
        return uuid5(NAMESPACE_URL, f"aware:thread_config:{thread_id}")

    @staticmethod
    def stable_opgi_id_for_key(*, projection_identity_key: str) -> UUID:
        return uuid5(NAMESPACE_URL, f"aware:opgi:{projection_identity_key}")

    @staticmethod
    def stable_thread_config_projection_assoc_id(
        *,
        thread_config_id: UUID,
        object_projection_graph_identity_id: UUID,
    ) -> UUID:
        return uuid5(
            NAMESPACE_URL,
            "aware:thread_config_opgi_assoc:"
            f"{thread_config_id}:{object_projection_graph_identity_id}",
        )

    @staticmethod
    def stable_boot_process_id(*, environment_id: UUID) -> UUID:
        return uuid5(NAMESPACE_URL, f"aware:process:{environment_id}:environment")

    @staticmethod
    def stable_boot_thread_id(*, environment_id: UUID) -> UUID:
        return uuid5(NAMESPACE_URL, f"aware:thread:{environment_id}:bootstrap")

    @staticmethod
    def stable_branch_id(*, environment_id: UUID, thread_id: UUID) -> UUID:
        return stable_environment_thread_branch_id(
            environment_id=environment_id,
            thread_id=thread_id,
        )


ocg_support = _OcgSupport()
oig_support = _OigSupport()
lane_support = _LaneSupport()
invoke_support = _InvokeSupport()
stable_ids = _StableIds()

__all__ = [
    "EnvironmentRuntimeResolverLike",
    "invoke_support",
    "lane_support",
    "ocg_support",
    "oig_support",
    "stable_ids",
]
