from __future__ import annotations

from collections.abc import Mapping
from typing import Final, cast

from pydantic import TypeAdapter

from aware_code.types import JsonArray, JsonObject
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.config.stable_ids import (
    stable_object_config_graph_identity_id,
)
from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphHandlerExecutionRequest,
    MetaGraphPreState,
)
from aware_meta.runtime.handler_executor.language_handler import (
    MetaGraphGeneratedLanguageHandlerCallable,
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphLanguageHandlerExecution,
    MetaGraphLanguageHandlerExecutionError,
)
from aware_meta.runtime.handler_executor.pre_state import (
    MetaGraphEmptyLaneBootstrap,
    MetaGraphEmptyLaneBootstrapCallable,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.function.function_impl_enums import FunctionImplKind
from aware_meta_ontology.graph.config.object_config_graph_identity import (
    ObjectConfigGraphIdentity,
    ObjectConfigGraphIdentityCreateInput,
)
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)
from aware_meta_ontology.graph.projection.object_projection_graph_identity import (
    ObjectProjectionGraphIdentity,
    ObjectProjectionGraphIdentityCreateViaObjectConfigGraphIdentityInput,
)
from aware_meta_ontology.stable_ids import (
    stable_class_instance_identity_id,
    stable_object_projection_graph_identity_id,
)
from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import disable_change_tracking_hooks


OCGI_OWNER_KEY: Final = "aware_meta.graph.config.ObjectConfigGraphIdentity"
OCGI_OWNER_CLASS_FQN: Final = OCGI_OWNER_KEY
OCGI_OWNER_CLASS_NAME: Final = "ObjectConfigGraphIdentity"
OCGI_CREATE: Final = "create"
OPGI_OWNER_KEY: Final = "aware_meta.graph.projection.ObjectProjectionGraphIdentity"
OPGI_OWNER_CLASS_FQN: Final = OPGI_OWNER_KEY
OPGI_OWNER_CLASS_NAME: Final = "ObjectProjectionGraphIdentity"
OPGI_CREATE_VIA_OCGI: Final = "create_via_object_config_graph_identity"

_OCGI_CREATE_FIELDS: Final = ("key", "label")
_OCGI_CREATE_INPUT_ADAPTER: Final = TypeAdapter(
    ObjectConfigGraphIdentityCreateInput
)
_OPGI_CREATE_VIA_OCGI_FIELDS: Final = (
    "object_config_graph_identity_id",
    "object_projection_graph_id",
    "projection_name",
    "label",
)
_OPGI_CREATE_VIA_OCGI_INPUT_ADAPTER: Final = TypeAdapter(
    ObjectProjectionGraphIdentityCreateViaObjectConfigGraphIdentityInput
)


def object_config_graph_identity__create__handler(
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    positional: JsonArray,
    keyword: JsonObject,
) -> MetaGraphLanguageHandlerExecution:
    _assert_auto_constructor(request)
    bound_input = cast(
        ObjectConfigGraphIdentityCreateInput,
        _OCGI_CREATE_INPUT_ADAPTER.validate_python(
            _bind_keyword_payload(
                positional=positional,
                keyword=keyword,
                field_names=_OCGI_CREATE_FIELDS,
                function_name=OCGI_CREATE,
            )
        ),
    )
    identity = _build_object_config_graph_identity(bound_input)
    post_oig = _post_oig_with_identity_root(
        request=request,
        pre_state=pre_state,
        identity=identity,
    )
    root_class_instance = post_oig.root_class_instance
    root_class_instance_identity_id = None
    if root_class_instance is not None:
        root_class_instance_identity_id = stable_class_instance_identity_id(
            object_instance_graph_identity_id=(
                request.staged_call.lane_scope.object_instance_graph_identity_id
            ),
            class_instance_id=root_class_instance.id,
        )
    return MetaGraphLanguageHandlerExecution(
        success=True,
        payload=JsonObject({"value": identity.model_dump(mode="json")}),
        post_oig=post_oig,
        root_object_id=identity.id,
        root_class_instance_identity_id=root_class_instance_identity_id,
    )


def object_projection_graph_identity__create_via_object_config_graph_identity__handler(
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    positional: JsonArray,
    keyword: JsonObject,
) -> MetaGraphLanguageHandlerExecution:
    _assert_auto_constructor(request)
    bound_input = cast(
        ObjectProjectionGraphIdentityCreateViaObjectConfigGraphIdentityInput,
        _OPGI_CREATE_VIA_OCGI_INPUT_ADAPTER.validate_python(
            _bind_keyword_payload(
                positional=positional,
                keyword=keyword,
                field_names=_OPGI_CREATE_VIA_OCGI_FIELDS,
                function_name=OPGI_CREATE_VIA_OCGI,
            )
        ),
    )
    identity = _build_object_projection_graph_identity(bound_input)
    post_oig = _post_oig_with_identity_root(
        request=request,
        pre_state=pre_state,
        identity=identity,
    )
    root_class_instance = post_oig.root_class_instance
    root_class_instance_identity_id = None
    if root_class_instance is not None:
        root_class_instance_identity_id = stable_class_instance_identity_id(
            object_instance_graph_identity_id=(
                request.staged_call.lane_scope.object_instance_graph_identity_id
            ),
            class_instance_id=root_class_instance.id,
        )
    return MetaGraphLanguageHandlerExecution(
        success=True,
        payload=JsonObject({"value": identity.model_dump(mode="json")}),
        post_oig=post_oig,
        root_object_id=identity.id,
        root_class_instance_identity_id=root_class_instance_identity_id,
    )


def object_config_graph_identity__create__empty_lane_bootstrap(
    request: MetaGraphHandlerExecutionRequest,
) -> MetaGraphEmptyLaneBootstrap:
    bound_input = cast(
        ObjectConfigGraphIdentityCreateInput,
        _OCGI_CREATE_INPUT_ADAPTER.validate_python(
            _bind_keyword_payload(
                positional=JsonArray(list(request.request.args)),
                keyword=JsonObject(dict(request.request.kwargs)),
                field_names=_OCGI_CREATE_FIELDS,
                function_name=OCGI_CREATE,
            )
        ),
    )
    return MetaGraphEmptyLaneBootstrap(
        root_object_id=stable_object_config_graph_identity_id(
            key=bound_input.key,
        ),
        name=OCGI_OWNER_CLASS_NAME,
        description="Meta constructor bootstrap for ObjectConfigGraphIdentity.",
    )


def object_projection_graph_identity__create_via_object_config_graph_identity__empty_lane_bootstrap(
    request: MetaGraphHandlerExecutionRequest,
) -> MetaGraphEmptyLaneBootstrap:
    bound_input = cast(
        ObjectProjectionGraphIdentityCreateViaObjectConfigGraphIdentityInput,
        _OPGI_CREATE_VIA_OCGI_INPUT_ADAPTER.validate_python(
            _bind_keyword_payload(
                positional=JsonArray(list(request.request.args)),
                keyword=JsonObject(dict(request.request.kwargs)),
                field_names=_OPGI_CREATE_VIA_OCGI_FIELDS,
                function_name=OPGI_CREATE_VIA_OCGI,
            )
        ),
    )
    return MetaGraphEmptyLaneBootstrap(
        root_object_id=stable_object_projection_graph_identity_id(
            object_config_graph_identity_id=(
                bound_input.object_config_graph_identity_id
            ),
            object_projection_graph_id=bound_input.object_projection_graph_id,
        ),
        name=OPGI_OWNER_CLASS_NAME,
        description="Meta constructor bootstrap for ObjectProjectionGraphIdentity.",
    )


def _assert_auto_constructor(request: MetaGraphHandlerExecutionRequest) -> None:
    function_impl = request.execution_plan.implementation.function_config.function_impl
    if function_impl is None:
        return
    if function_impl.kind is FunctionImplKind.auto_constructor:
        return
    if isinstance(function_impl.kind, str) and function_impl.kind == "auto_constructor":
        return
    raise MetaGraphLanguageHandlerExecutionError(
        "ObjectConfigGraphIdentity.create native handler expects auto_constructor "
        f"FunctionImpl truth, got kind={function_impl.kind!r}."
    )


def _bind_keyword_payload(
    *,
    positional: JsonArray,
    keyword: JsonObject,
    field_names: tuple[str, ...],
    function_name: str,
) -> JsonObject:
    if len(positional) > len(field_names):
        raise MetaGraphLanguageHandlerExecutionError(
            "Too many positional arguments for generated Meta language handler: "
            f"function_name={function_name} have={len(positional)} "
            f"max={len(field_names)}"
        )
    payload = JsonObject(dict(keyword))
    valid_names = set(field_names)
    unknown_names = sorted(set(payload) - valid_names)
    if unknown_names:
        raise MetaGraphLanguageHandlerExecutionError(
            "Unknown generated Meta language-handler argument(s): "
            f"function_name={function_name} names={unknown_names}"
        )
    for position, value in enumerate(positional):
        field_name = field_names[position]
        if field_name in payload:
            raise MetaGraphLanguageHandlerExecutionError(
                "Generated Meta language-handler argument provided twice: "
                f"function_name={function_name} name={field_name}"
            )
        payload[field_name] = value
    return payload


def _build_object_config_graph_identity(
    bound_input: ObjectConfigGraphIdentityCreateInput,
) -> ObjectConfigGraphIdentity:
    identity_id = stable_object_config_graph_identity_id(key=bound_input.key)
    with disable_change_tracking_hooks(), disable_autobind():
        return ObjectConfigGraphIdentity(
            id=identity_id,
            key=bound_input.key,
            label=bound_input.label,
        )


def _build_object_projection_graph_identity(
    bound_input: ObjectProjectionGraphIdentityCreateViaObjectConfigGraphIdentityInput,
) -> ObjectProjectionGraphIdentity:
    identity_id = stable_object_projection_graph_identity_id(
        object_config_graph_identity_id=bound_input.object_config_graph_identity_id,
        object_projection_graph_id=bound_input.object_projection_graph_id,
    )
    with disable_change_tracking_hooks(), disable_autobind():
        return ObjectProjectionGraphIdentity(
            id=identity_id,
            object_config_graph_identity_id=(
                bound_input.object_config_graph_identity_id
            ),
            object_projection_graph_id=bound_input.object_projection_graph_id,
            projection_name=bound_input.projection_name,
            label=bound_input.label,
        )


def _post_oig_with_identity_root(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    identity: ObjectConfigGraphIdentity,
) -> ObjectInstanceGraph:
    owner_class_config = request.execution_plan.implementation.owner_class_config
    if not isinstance(owner_class_config, ClassConfig):
        raise MetaGraphLanguageHandlerExecutionError(
            "ObjectConfigGraphIdentity constructor requires a resolved owner ClassConfig."
        )
    post_oig = pre_state.before_oig.model_copy(deep=True)
    root_class_instance = build_class_instance(
        object_instance_graph_id=post_oig.id,
        class_config=owner_class_config,
        class_configs_by_id=dict(request.execution_plan.index.class_configs_by_id),
        source=identity,
    )
    _replace_root_class_instance(
        post_oig=post_oig,
        root_class_instance=root_class_instance,
    )
    return post_oig


def _replace_root_class_instance(
    *,
    post_oig: ObjectInstanceGraph,
    root_class_instance: ClassInstance,
) -> None:
    class_instances = list(post_oig.class_instances or [])
    for position, existing in enumerate(class_instances):
        if existing.id == root_class_instance.id:
            class_instances[position] = root_class_instance
            post_oig.class_instances = class_instances
            post_oig.root_class_instance = root_class_instance
            post_oig.root_class_instance_id = root_class_instance.id
            return
    class_instances.append(root_class_instance)
    post_oig.class_instances = class_instances
    post_oig.root_class_instance = root_class_instance
    post_oig.root_class_instance_id = root_class_instance.id


AWARE_META_GRAPH_HANDLERS: Mapping[
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphGeneratedLanguageHandlerCallable,
] = {
    MetaGraphGeneratedLanguageHandlerKey(
        owner_key=OCGI_OWNER_KEY,
        function_name=OCGI_CREATE,
        is_constructor=True,
        owner_class_fqn=OCGI_OWNER_CLASS_FQN,
        owner_class_name=OCGI_OWNER_CLASS_NAME,
    ): object_config_graph_identity__create__handler,
    MetaGraphGeneratedLanguageHandlerKey(
        owner_key=OPGI_OWNER_KEY,
        function_name=OPGI_CREATE_VIA_OCGI,
        is_constructor=True,
        owner_class_fqn=OPGI_OWNER_CLASS_FQN,
        owner_class_name=OPGI_OWNER_CLASS_NAME,
    ): (
        object_projection_graph_identity__create_via_object_config_graph_identity__handler
    ),
}


AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS: Mapping[
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphEmptyLaneBootstrapCallable,
] = {
    MetaGraphGeneratedLanguageHandlerKey(
        owner_key=OCGI_OWNER_KEY,
        function_name=OCGI_CREATE,
        is_constructor=True,
        owner_class_fqn=OCGI_OWNER_CLASS_FQN,
        owner_class_name=OCGI_OWNER_CLASS_NAME,
    ): object_config_graph_identity__create__empty_lane_bootstrap,
    MetaGraphGeneratedLanguageHandlerKey(
        owner_key=OPGI_OWNER_KEY,
        function_name=OPGI_CREATE_VIA_OCGI,
        is_constructor=True,
        owner_class_fqn=OPGI_OWNER_CLASS_FQN,
        owner_class_name=OPGI_OWNER_CLASS_NAME,
    ): (
        object_projection_graph_identity__create_via_object_config_graph_identity__empty_lane_bootstrap
    ),
}


__all__ = [
    "AWARE_META_GRAPH_EMPTY_LANE_BOOTSTRAPS",
    "AWARE_META_GRAPH_HANDLERS",
    "OCGI_CREATE",
    "OCGI_OWNER_CLASS_FQN",
    "OCGI_OWNER_CLASS_NAME",
    "OCGI_OWNER_KEY",
    "OPGI_CREATE_VIA_OCGI",
    "OPGI_OWNER_CLASS_FQN",
    "OPGI_OWNER_CLASS_NAME",
    "OPGI_OWNER_KEY",
    "object_config_graph_identity__create__empty_lane_bootstrap",
    "object_config_graph_identity__create__handler",
    "object_projection_graph_identity__create_via_object_config_graph_identity__empty_lane_bootstrap",
    "object_projection_graph_identity__create_via_object_config_graph_identity__handler",
]
