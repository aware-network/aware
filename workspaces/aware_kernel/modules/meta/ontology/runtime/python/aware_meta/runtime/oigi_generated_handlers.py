from __future__ import annotations

from collections.abc import Mapping
from typing import Final, cast

from pydantic import TypeAdapter

from aware_code.types import JsonArray, JsonObject
from aware_meta.class_.instance.builder import build_class_instance
from aware_meta.graph.instance.builder import (
    build_include_relationship_attribute_config_ids_by_class_config_id,
    build_relationship_attribute_config_ids_by_class_config_id,
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
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_instance import ClassInstance
from aware_meta_ontology.graph.instance.object_instance_graph import ObjectInstanceGraph
from aware_meta_ontology.graph.instance.object_instance_graph_identity import (
    ObjectInstanceGraphIdentity,
    ObjectInstanceGraphIdentityCreateViaObjectProjectionGraphIdentityInput,
)
from aware_meta_ontology.stable_ids import stable_object_instance_graph_identity_id
from aware_orm.session.autobind import disable_autobind
from aware_orm.session.change_collector import disable_change_tracking_hooks


OIGI_OWNER_KEY: Final = "aware_meta.graph.instance.ObjectInstanceGraphIdentity"
OIGI_OWNER_CLASS_FQN: Final = OIGI_OWNER_KEY
OIGI_OWNER_CLASS_NAME: Final = "ObjectInstanceGraphIdentity"
OIGI_CREATE_VIA_OPGI: Final = "create_via_object_projection_graph_identity"

_CREATE_VIA_OPGI_FIELDS: Final = (
    "object_projection_graph_identity_id",
    "object_instance_graph_id",
    "label",
)
_CREATE_VIA_OPGI_INPUT_ADAPTER: Final = TypeAdapter(
    ObjectInstanceGraphIdentityCreateViaObjectProjectionGraphIdentityInput
)


def object_instance_graph_identity__create_via_object_projection_graph_identity__handler(
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    positional: JsonArray,
    keyword: JsonObject,
) -> MetaGraphLanguageHandlerExecution:
    bound_input = cast(
        ObjectInstanceGraphIdentityCreateViaObjectProjectionGraphIdentityInput,
        _CREATE_VIA_OPGI_INPUT_ADAPTER.validate_python(
            _bind_keyword_payload(
                positional=positional,
                keyword=keyword,
                field_names=_CREATE_VIA_OPGI_FIELDS,
                function_name=OIGI_CREATE_VIA_OPGI,
            )
        ),
    )
    identity = _build_object_instance_graph_identity(bound_input)
    post_oig = _post_oig_with_identity_root(
        request=request,
        pre_state=pre_state,
        identity=identity,
    )
    return MetaGraphLanguageHandlerExecution(
        success=True,
        payload=JsonObject({"value": identity.model_dump(mode="json")}),
        post_oig=post_oig,
        root_object_id=identity.id,
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


def _build_object_instance_graph_identity(
    bound_input: ObjectInstanceGraphIdentityCreateViaObjectProjectionGraphIdentityInput,
) -> ObjectInstanceGraphIdentity:
    identity_id = stable_object_instance_graph_identity_id(
        object_projection_graph_identity_id=(
            bound_input.object_projection_graph_identity_id
        ),
        object_instance_graph_id=bound_input.object_instance_graph_id,
    )
    with disable_change_tracking_hooks():
        with disable_autobind():
            return ObjectInstanceGraphIdentity(
                id=identity_id,
                label=bound_input.label,
                object_projection_graph_identity_id=(
                    bound_input.object_projection_graph_identity_id
                ),
                object_instance_graph_id=bound_input.object_instance_graph_id,
            )


def _post_oig_with_identity_root(
    *,
    request: MetaGraphHandlerExecutionRequest,
    pre_state: MetaGraphPreState,
    identity: ObjectInstanceGraphIdentity,
) -> ObjectInstanceGraph:
    if pre_state.before_oig.id != identity.id:
        raise MetaGraphLanguageHandlerExecutionError(
            "ObjectInstanceGraphIdentity constructor must run against the "
            "OIGI lane rooted by the constructed identity: "
            f"pre_state_oig_id={pre_state.before_oig.id} identity_id={identity.id}"
        )
    owner_class_config = request.execution_plan.implementation.owner_class_config
    if not isinstance(owner_class_config, ClassConfig):
        raise MetaGraphLanguageHandlerExecutionError(
            "ObjectInstanceGraphIdentity constructor requires a resolved "
            "owner ClassConfig."
        )
    post_oig = pre_state.before_oig.model_copy(deep=True)
    class_configs_by_id = dict(request.execution_plan.index.class_configs_by_id)
    relationships_by_id = dict(request.execution_plan.index.relationships_by_id)
    relationship_attribute_config_ids_by_class_config_id = (
        build_relationship_attribute_config_ids_by_class_config_id(
            class_configs_by_id=class_configs_by_id,
            relationships_by_id=relationships_by_id,
        )
    )
    include_relationship_attribute_config_ids_by_class_config_id = (
        build_include_relationship_attribute_config_ids_by_class_config_id(
            object_projection_graph=request.execution_plan.object_projection_graph,
            class_configs_by_id=class_configs_by_id,
            relationships_by_id=relationships_by_id,
        )
    )
    root_class_instance = build_class_instance(
        object_instance_graph_id=post_oig.id,
        class_config=owner_class_config,
        class_configs_by_id=class_configs_by_id,
        source=identity,
        relationship_attribute_config_ids=(
            relationship_attribute_config_ids_by_class_config_id.get(
                owner_class_config.id
            )
        ),
        include_relationship_attribute_config_ids=(
            include_relationship_attribute_config_ids_by_class_config_id.get(
                owner_class_config.id
            )
        ),
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
    raise MetaGraphLanguageHandlerExecutionError(
        "ObjectInstanceGraphIdentity constructor pre-state is not rooted by "
        "the expected ClassInstance: "
        f"class_instance_id={root_class_instance.id}"
    )


AWARE_META_GRAPH_HANDLERS: Mapping[
    MetaGraphGeneratedLanguageHandlerKey,
    MetaGraphGeneratedLanguageHandlerCallable,
] = {
    MetaGraphGeneratedLanguageHandlerKey(
        owner_key=OIGI_OWNER_KEY,
        function_name=OIGI_CREATE_VIA_OPGI,
        is_constructor=True,
        owner_class_fqn=OIGI_OWNER_CLASS_FQN,
        owner_class_name=OIGI_OWNER_CLASS_NAME,
    ): object_instance_graph_identity__create_via_object_projection_graph_identity__handler,
}


__all__ = [
    "AWARE_META_GRAPH_HANDLERS",
    "OIGI_CREATE_VIA_OPGI",
    "OIGI_OWNER_CLASS_FQN",
    "OIGI_OWNER_CLASS_NAME",
    "OIGI_OWNER_KEY",
    "object_instance_graph_identity__create_via_object_projection_graph_identity__handler",
]
