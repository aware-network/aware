from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from aware_meta.graph.config.stable_ids import (
    stable_attribute_config_id,
    stable_class_config_attribute_config_id,
    stable_class_config_id,
    stable_class_relationship_id,
    stable_enum_config_id,
    stable_enum_option_id,
    stable_function_config_id,
    stable_object_config_graph_id,
    stable_object_config_graph_identity_id,
    stable_object_config_graph_node_id,
)
from aware_meta.semantic_operation_resolution import (
    META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_IDENTITY_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_OPERATION,
    META_OBJECT_CONFIG_GRAPH_PACKAGE_CREATE_OPERATION,
    META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION,
)
from aware_meta_ontology.stable_ids import stable_object_config_graph_package_id


META_OCG_PACKAGE_OPERATION_PLAN_CONTRACT_VERSION = (
    "aware.meta.ocg.package-derived-operation-plan.v0"
)

MetaOcgPackageOperationPlanStatus = Literal["operation_plan_ready", "blocked"]


@dataclass(frozen=True, slots=True)
class MetaOcgPackageAttributeDescriptor:
    owner_class_fqn: str
    name: str
    primitive_base_type: str = "string"
    description: str | None = None
    position: int = 0
    required: bool = True
    public: bool = True
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MetaOcgPackageFunctionDescriptor:
    owner_class_fqn: str
    name: str
    description: str | None = None
    kind: str = "instance"
    verb: str | None = None
    is_async: bool = False
    is_public: bool = True
    is_constructor: bool = False
    position: int = 0
    inputs: tuple[Mapping[str, object], ...] = ()
    outputs: tuple[Mapping[str, object], ...] = ()
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MetaOcgPackageClassDescriptor:
    class_fqn: str
    class_name: str | None = None
    description: str | None = None
    attributes: tuple[MetaOcgPackageAttributeDescriptor, ...] = ()
    functions: tuple[MetaOcgPackageFunctionDescriptor, ...] = ()
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MetaOcgPackageEnumOptionDescriptor:
    value: str
    label: str | None = None
    description: str | None = None
    position: int = 0
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MetaOcgPackageEnumDescriptor:
    enum_fqn: str
    enum_name: str | None = None
    description: str | None = None
    options: tuple[MetaOcgPackageEnumOptionDescriptor, ...] = ()
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MetaOcgPackageRelationshipDescriptor:
    source_class_fqn: str
    target_class_fqn: str
    relationship_key: str
    relationship_type: str
    target_class_config_id: str | None = None
    description: str | None = None
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MetaOcgPackageDescriptor:
    package_name: str
    fqn_prefix: str
    source_refs: tuple[str, ...]
    language: str = "aware"
    graph_name: str | None = None
    package_title: str | None = None
    package_description: str | None = None
    classes: tuple[MetaOcgPackageClassDescriptor, ...] = ()
    enums: tuple[MetaOcgPackageEnumDescriptor, ...] = ()
    relationships: tuple[MetaOcgPackageRelationshipDescriptor, ...] = ()

    @property
    def graph_semantic_key(self) -> str:
        return f"ocg:{self.fqn_prefix}"

    @property
    def package_semantic_key(self) -> str:
        return f"ocg_package:{self.package_name}"

    @property
    def resolved_graph_name(self) -> str:
        return self.graph_name or self.package_name


@dataclass(frozen=True, slots=True)
class MetaOcgPackageOperationIntent:
    operation_key: str
    operation_family: str
    semantic_operation_type: str
    semantic_key: str
    semantic_subject_type: str
    source_refs: tuple[str, ...]
    after_payload: Mapping[str, object]
    field_path: str = "definition"
    contract_version: str = "aware.workspace.semantic_operation_intent.v0"
    source: str = "aware_meta.ocg_package_operation_plan"

    def evidence_payload(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "operation_key": self.operation_key,
            "operation_family": self.operation_family,
            "semantic_operation_type": self.semantic_operation_type,
            "semantic_key": self.semantic_key,
            "semantic_subject_type": self.semantic_subject_type,
            "field_path": self.field_path,
            "source": self.source,
            "source_refs": self.source_refs,
            "requires_baseline_object_identity": False,
            "before_payload": None,
            "after_payload": dict(self.after_payload),
            "semantic_contract_provider_key": "aware_meta",
            "semantic_contract_role": "meta_ocg_semantic_operation_plan",
            "semantic_contract_name": "meta_ocg_package_operation_plan",
            "metadata": {
                "contract_version": META_OCG_PACKAGE_OPERATION_PLAN_CONTRACT_VERSION,
                "meta_owned_operation_plan": True,
                "workspace_orchestration_only": True,
            },
        }


@dataclass(frozen=True, slots=True)
class MetaOcgPackageCoverageMember:
    category: str
    key: str
    source_refs: tuple[str, ...] = ()

    def evidence_payload(self) -> dict[str, object]:
        return {
            "category": self.category,
            "key": self.key,
            "source_refs": self.source_refs,
        }


@dataclass(frozen=True, slots=True)
class MetaOcgPackageOperationPlan:
    package_name: str
    status: MetaOcgPackageOperationPlanStatus
    operation_intents: tuple[MetaOcgPackageOperationIntent, ...] = ()
    coverage_members: tuple[MetaOcgPackageCoverageMember, ...] = ()
    blockers: tuple[str, ...] = ()
    contract_version: str = META_OCG_PACKAGE_OPERATION_PLAN_CONTRACT_VERSION

    @property
    def operation_intent_count(self) -> int:
        return len(self.operation_intents)

    @property
    def coverage_member_count(self) -> int:
        return len(self.coverage_members)

    def evidence_payload(self) -> dict[str, object]:
        return {
            "contract_version": self.contract_version,
            "plan_kind": "meta_ocg_package_derived_operation_plan",
            "package_name": self.package_name,
            "status": self.status,
            "operation_intent_count": self.operation_intent_count,
            "coverage_member_count": self.coverage_member_count,
            "blockers": self.blockers,
            "operation_intents": tuple(
                intent.evidence_payload() for intent in self.operation_intents
            ),
            "coverage_members": tuple(
                member.evidence_payload() for member in self.coverage_members
            ),
            "builder_fallback_used": False,
            "workspace_internals_used": False,
            "content_specific": False,
        }


def build_meta_ocg_package_operation_plan(
    *,
    descriptor: MetaOcgPackageDescriptor,
) -> MetaOcgPackageOperationPlan:
    blockers = _descriptor_blockers(descriptor=descriptor)
    if blockers:
        return MetaOcgPackageOperationPlan(
            package_name=descriptor.package_name,
            status="blocked",
            blockers=blockers,
        )

    context = _PlanContext(descriptor=descriptor)
    operation_intents = (
        *_root_operation_intents(context=context),
        *(
            _class_operation_intent(context=context, class_descriptor=item)
            for item in descriptor.classes
        ),
        *(
            _enum_operation_intent(context=context, enum_descriptor=item)
            for item in descriptor.enums
        ),
        *(
            _enum_option_operation_intent(
                context=context,
                enum_descriptor=enum_descriptor,
                option_descriptor=option_descriptor,
            )
            for enum_descriptor in descriptor.enums
            for option_descriptor in enum_descriptor.options
        ),
        *(
            _relationship_operation_intent(
                context=context,
                relationship_descriptor=item,
            )
            for item in descriptor.relationships
        ),
        *(
            _attribute_operation_intent(
                context=context,
                class_descriptor=class_descriptor,
                attribute_descriptor=attribute_descriptor,
            )
            for class_descriptor in descriptor.classes
            for attribute_descriptor in class_descriptor.attributes
        ),
        *(
            _function_operation_intent(
                context=context,
                class_descriptor=class_descriptor,
                function_descriptor=function_descriptor,
            )
            for class_descriptor in descriptor.classes
            for function_descriptor in class_descriptor.functions
        ),
    )
    return MetaOcgPackageOperationPlan(
        package_name=descriptor.package_name,
        status="operation_plan_ready",
        operation_intents=operation_intents,
        coverage_members=_coverage_members(
            descriptor=descriptor,
            context=context,
            operation_intents=operation_intents,
        ),
    )


def build_meta_ocg_package_descriptor_from_materialized_ocg(
    *,
    package_name: str,
    ocg_snapshot: Mapping[str, object],
    source_refs: tuple[str, ...] = (),
    function_models: Mapping[str, object] | None = None,
) -> MetaOcgPackageDescriptor:
    fqn_prefix = _required_text(
        ocg_snapshot.get("fqn_prefix"),
        blocker="fqn_prefix_required",
    )
    nodes = tuple(_mapping(item) for item in _sequence(ocg_snapshot.get("object_config_graph_nodes")))
    resolved_source_refs = source_refs or _all_node_source_refs(nodes=nodes)
    function_entries_by_owner = _function_entries_by_owner(function_models=function_models)
    class_id_to_fqn = _class_id_to_fqn(nodes=nodes)
    classes = tuple(
        _class_descriptor_from_node(
            node=node,
            package_source_refs=resolved_source_refs,
            function_entries_by_owner=function_entries_by_owner,
        )
        for node in nodes
        if node.get("type") == "class"
    )
    return MetaOcgPackageDescriptor(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
        source_refs=resolved_source_refs,
        language=_optional_text(ocg_snapshot.get("language")) or "aware",
        graph_name=_optional_text(ocg_snapshot.get("name")),
        package_description=_optional_text(ocg_snapshot.get("description")),
        classes=classes,
        enums=tuple(
            _enum_descriptor_from_node(
                node=node,
                package_source_refs=resolved_source_refs,
            )
            for node in nodes
            if node.get("type") == "enum"
        ),
        relationships=tuple(
            relationship
            for node in nodes
            if node.get("type") == "relationship"
            for relationship in (
                _relationship_descriptor_from_node(
                    node=node,
                    class_id_to_fqn=class_id_to_fqn,
                    package_source_refs=resolved_source_refs,
                ),
            )
            if relationship is not None
        ),
    )


@dataclass(frozen=True, slots=True)
class _PlanContext:
    descriptor: MetaOcgPackageDescriptor

    @property
    def graph_id(self) -> UUID:
        return stable_object_config_graph_id(
            fqn_prefix=self.descriptor.fqn_prefix,
            language=self.descriptor.language,
        )

    @property
    def graph_identity_id(self) -> UUID:
        return stable_object_config_graph_identity_id(
            key=self.descriptor.graph_semantic_key,
        )

    @property
    def package_id(self) -> UUID:
        return stable_object_config_graph_package_id(
            package_name=self.descriptor.package_name,
            fqn_prefix=self.descriptor.fqn_prefix,
        )


def _root_operation_intents(
    *,
    context: _PlanContext,
) -> tuple[MetaOcgPackageOperationIntent, ...]:
    descriptor = context.descriptor
    root_refs = descriptor.source_refs
    return (
        MetaOcgPackageOperationIntent(
            operation_key=f"meta_ocg.package.create:{descriptor.package_semantic_key}",
            operation_family="create",
            semantic_operation_type=META_OBJECT_CONFIG_GRAPH_PACKAGE_CREATE_OPERATION,
            semantic_key=descriptor.package_semantic_key,
            semantic_subject_type="aware_meta.ObjectConfigGraphPackage",
            source_refs=root_refs,
            after_payload={
                "package_name": descriptor.package_name,
                "fqn_prefix": descriptor.fqn_prefix,
                "package_id": str(context.package_id),
                "title": descriptor.package_title,
                "description": descriptor.package_description,
            },
        ),
        MetaOcgPackageOperationIntent(
            operation_key=(
                f"meta_ocg.graph_identity.create:{descriptor.graph_semantic_key}"
            ),
            operation_family="create",
            semantic_operation_type=META_OBJECT_CONFIG_GRAPH_IDENTITY_CREATE_OPERATION,
            semantic_key=f"{descriptor.graph_semantic_key}/identity",
            semantic_subject_type="aware_meta.ObjectConfigGraphIdentity",
            source_refs=root_refs,
            after_payload={
                "object_config_graph_identity_id": str(context.graph_identity_id),
                "object_config_graph_id": str(context.graph_id),
                "key": descriptor.graph_semantic_key,
                "fqn_prefix": descriptor.fqn_prefix,
                "language": descriptor.language,
            },
        ),
        MetaOcgPackageOperationIntent(
            operation_key=f"meta_ocg.graph.create:{descriptor.graph_semantic_key}",
            operation_family="create",
            semantic_operation_type=META_OBJECT_CONFIG_GRAPH_CREATE_OPERATION,
            semantic_key=descriptor.graph_semantic_key,
            semantic_subject_type="aware_meta.ObjectConfigGraph",
            source_refs=root_refs,
            after_payload={
                "fqn_prefix": descriptor.fqn_prefix,
                "object_config_graph_id": str(context.graph_id),
                "name": descriptor.resolved_graph_name,
                "language": descriptor.language,
                "description": descriptor.package_description,
            },
        ),
        MetaOcgPackageOperationIntent(
            operation_key=(
                f"meta_ocg.package.attach_graph:{descriptor.package_semantic_key}"
            ),
            operation_family="create",
            semantic_operation_type=META_OBJECT_CONFIG_GRAPH_PACKAGE_ATTACH_GRAPH_OPERATION,
            semantic_key=descriptor.package_semantic_key,
            semantic_subject_type="aware_meta.ObjectConfigGraphPackage",
            source_refs=root_refs,
            after_payload={
                "package_name": descriptor.package_name,
                "package_id": str(context.package_id),
                "object_config_graph_id": str(context.graph_id),
                "graph_semantic_key": descriptor.graph_semantic_key,
                "fqn_prefix": descriptor.fqn_prefix,
            },
        ),
    )


def _class_operation_intent(
    *,
    context: _PlanContext,
    class_descriptor: MetaOcgPackageClassDescriptor,
) -> MetaOcgPackageOperationIntent:
    class_fqn = class_descriptor.class_fqn
    class_name = class_descriptor.class_name or _tail(class_fqn)
    node_id = _class_node_id(context=context, class_fqn=class_fqn)
    class_config_id = _class_config_id(context=context, class_fqn=class_fqn)
    semantic_key = _class_semantic_key(context=context, class_fqn=class_fqn)
    return MetaOcgPackageOperationIntent(
        operation_key=f"meta_ocg.class.create:{semantic_key}",
        operation_family="create",
        semantic_operation_type=META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION,
        semantic_key=semantic_key,
        semantic_subject_type="aware_meta.ObjectConfigGraphNode",
        source_refs=_member_source_refs(context.descriptor, class_descriptor.source_refs),
        after_payload={
            "graph_semantic_key": context.descriptor.graph_semantic_key,
            "object_config_graph_id": str(context.graph_id),
            "object_config_graph_node_id": str(node_id),
            "class_config_id": str(class_config_id),
            "class_name": class_name,
            "name": class_name,
            "class_fqn": class_fqn,
            "node_key": class_fqn,
            "description": class_descriptor.description,
        },
    )


def _enum_operation_intent(
    *,
    context: _PlanContext,
    enum_descriptor: MetaOcgPackageEnumDescriptor,
) -> MetaOcgPackageOperationIntent:
    enum_fqn = enum_descriptor.enum_fqn
    enum_name = enum_descriptor.enum_name or _tail(enum_fqn)
    node_id = _enum_node_id(context=context, enum_fqn=enum_fqn)
    enum_config_id = _enum_config_id(context=context, enum_fqn=enum_fqn)
    semantic_key = _enum_semantic_key(context=context, enum_fqn=enum_fqn)
    return MetaOcgPackageOperationIntent(
        operation_key=f"meta_ocg.enum.create:{semantic_key}",
        operation_family="create",
        semantic_operation_type=META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION,
        semantic_key=semantic_key,
        semantic_subject_type="aware_meta.ObjectConfigGraphNode",
        source_refs=_member_source_refs(context.descriptor, enum_descriptor.source_refs),
        after_payload={
            "graph_semantic_key": context.descriptor.graph_semantic_key,
            "object_config_graph_id": str(context.graph_id),
            "object_config_graph_node_id": str(node_id),
            "enum_config_id": str(enum_config_id),
            "enum_name": enum_name,
            "name": enum_name,
            "enum_fqn": enum_fqn,
            "node_key": enum_fqn,
            "description": enum_descriptor.description,
        },
    )


def _enum_option_operation_intent(
    *,
    context: _PlanContext,
    enum_descriptor: MetaOcgPackageEnumDescriptor,
    option_descriptor: MetaOcgPackageEnumOptionDescriptor,
) -> MetaOcgPackageOperationIntent:
    enum_fqn = enum_descriptor.enum_fqn
    enum_config_id = _enum_config_id(context=context, enum_fqn=enum_fqn)
    option_id = stable_enum_option_id(
        enum_config_id=enum_config_id,
        value=option_descriptor.value,
    )
    enum_semantic_key = _enum_semantic_key(context=context, enum_fqn=enum_fqn)
    semantic_key = f"{enum_semantic_key}/option:{option_descriptor.value}"
    return MetaOcgPackageOperationIntent(
        operation_key=f"meta_ocg.enum_option.create:{semantic_key}",
        operation_family="create",
        semantic_operation_type=META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION,
        semantic_key=semantic_key,
        semantic_subject_type="aware_meta.EnumOption",
        source_refs=_member_source_refs(
            context.descriptor,
            option_descriptor.source_refs or enum_descriptor.source_refs,
        ),
        after_payload={
            "enum_semantic_key": enum_semantic_key,
            "enum_config_id": str(enum_config_id),
            "enum_option_id": str(option_id),
            "value": option_descriptor.value,
            "label": option_descriptor.label or option_descriptor.value,
            "description": option_descriptor.description,
            "position": option_descriptor.position,
        },
    )


def _relationship_operation_intent(
    *,
    context: _PlanContext,
    relationship_descriptor: MetaOcgPackageRelationshipDescriptor,
) -> MetaOcgPackageOperationIntent:
    source_class_id = _class_config_id(
        context=context,
        class_fqn=relationship_descriptor.source_class_fqn,
    )
    target_class_id = _relationship_target_class_id(
        context=context,
        relationship_descriptor=relationship_descriptor,
    )
    relationship_id = stable_class_relationship_id(
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        relationship_key=relationship_descriptor.relationship_key,
    )
    relationship_node_id = stable_object_config_graph_node_id(
        object_config_graph_id=context.graph_id,
        type="relationship",
        node_key=(
            f"{relationship_descriptor.source_class_fqn}:"
            f"{relationship_descriptor.relationship_key}:"
            f"{relationship_descriptor.relationship_type}:"
            f"{relationship_descriptor.target_class_fqn}"
        ),
    )
    source_semantic_key = _class_semantic_key(
        context=context,
        class_fqn=relationship_descriptor.source_class_fqn,
    )
    target_semantic_key = _class_semantic_key(
        context=context,
        class_fqn=relationship_descriptor.target_class_fqn,
    )
    semantic_key = (
        f"{source_semantic_key}/relationship:"
        f"{relationship_descriptor.relationship_key}"
    )
    return MetaOcgPackageOperationIntent(
        operation_key=f"meta_ocg.relationship.create:{semantic_key}",
        operation_family="create",
        semantic_operation_type=META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION,
        semantic_key=semantic_key,
        semantic_subject_type="aware_meta.ClassConfigRelationship",
        source_refs=_member_source_refs(
            context.descriptor,
            relationship_descriptor.source_refs,
        ),
        after_payload={
            "graph_semantic_key": context.descriptor.graph_semantic_key,
            "object_config_graph_id": str(context.graph_id),
            "object_config_graph_node_id": str(relationship_node_id),
            "node_id": str(relationship_node_id),
            "relationship_config_id": str(relationship_id),
            "class_config_relationship_id": str(relationship_id),
            "source_class_fqn": relationship_descriptor.source_class_fqn,
            "target_class_fqn": relationship_descriptor.target_class_fqn,
            "source_class_config_id": str(source_class_id),
            "target_class_config_id": str(target_class_id),
            "relationship_key": relationship_descriptor.relationship_key,
            "relationship_type": relationship_descriptor.relationship_type,
            "owner_semantic_key": source_semantic_key,
            "target_semantic_key": target_semantic_key,
            "description": relationship_descriptor.description,
            "relationship_signature": {
                "source_class_fqn": relationship_descriptor.source_class_fqn,
                "target_class_fqn": relationship_descriptor.target_class_fqn,
                "source_class_config_id": str(source_class_id),
                "target_class_config_id": str(target_class_id),
                "relationship_key": relationship_descriptor.relationship_key,
                "relationship_type": relationship_descriptor.relationship_type,
            },
        },
    )


def _attribute_operation_intent(
    *,
    context: _PlanContext,
    class_descriptor: MetaOcgPackageClassDescriptor,
    attribute_descriptor: MetaOcgPackageAttributeDescriptor,
) -> MetaOcgPackageOperationIntent:
    class_fqn = class_descriptor.class_fqn
    class_config_id = _class_config_id(context=context, class_fqn=class_fqn)
    class_node_id = _class_node_id(context=context, class_fqn=class_fqn)
    attribute_config_id = stable_attribute_config_id(
        owner_key=class_fqn,
        name=attribute_descriptor.name,
    )
    class_attribute_config_id = stable_class_config_attribute_config_id(
        class_config_id=class_config_id,
        attribute_config_id=attribute_config_id,
    )
    owner_semantic_key = _class_semantic_key(context=context, class_fqn=class_fqn)
    semantic_key = f"{owner_semantic_key}/attribute:{attribute_descriptor.name}"
    return MetaOcgPackageOperationIntent(
        operation_key=f"meta_ocg.attribute.create:{semantic_key}",
        operation_family="create",
        semantic_operation_type=META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION,
        semantic_key=semantic_key,
        semantic_subject_type="aware_meta.AttributeConfig",
        source_refs=_member_source_refs(
            context.descriptor,
            attribute_descriptor.source_refs or class_descriptor.source_refs,
        ),
        after_payload={
            "graph_semantic_key": context.descriptor.graph_semantic_key,
            "object_config_graph_id": str(context.graph_id),
            "object_config_graph_node_id": str(class_node_id),
            "node_id": str(class_node_id),
            "class_config_id": str(class_config_id),
            "class_name": class_descriptor.class_name or _tail(class_fqn),
            "class_fqn": class_fqn,
            "owner_key": class_fqn,
            "owner_semantic_key": owner_semantic_key,
            "owner_object_id": str(class_config_id),
            "attribute_config_id": str(attribute_config_id),
            "class_config_attribute_config_id": str(class_attribute_config_id),
            "object_id": str(attribute_config_id),
            "entity_id": str(attribute_config_id),
            "object_kind": "attribute",
            "attribute_name": attribute_descriptor.name,
            "name": attribute_descriptor.name,
            "attribute_signature": {
                "name": attribute_descriptor.name,
                "description": attribute_descriptor.description,
                "is_required": attribute_descriptor.required,
                "is_public": attribute_descriptor.public,
                "position": attribute_descriptor.position,
                "type_descriptor": {
                    "kind": "primitive",
                    "primitive_base_type": attribute_descriptor.primitive_base_type,
                },
            },
        },
    )


def _function_operation_intent(
    *,
    context: _PlanContext,
    class_descriptor: MetaOcgPackageClassDescriptor,
    function_descriptor: MetaOcgPackageFunctionDescriptor,
) -> MetaOcgPackageOperationIntent:
    class_fqn = class_descriptor.class_fqn
    class_config_id = _class_config_id(context=context, class_fqn=class_fqn)
    function_config_id = stable_function_config_id(
        owner_key=class_fqn,
        name=function_descriptor.name,
        kind=function_descriptor.kind,
    )
    owner_semantic_key = _class_semantic_key(context=context, class_fqn=class_fqn)
    semantic_key = f"{owner_semantic_key}/function:{function_descriptor.name}"
    return MetaOcgPackageOperationIntent(
        operation_key=f"meta_ocg.function.create:{semantic_key}",
        operation_family="create",
        semantic_operation_type=META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION,
        semantic_key=semantic_key,
        semantic_subject_type="aware_meta.FunctionConfig",
        source_refs=_member_source_refs(
            context.descriptor,
            function_descriptor.source_refs or class_descriptor.source_refs,
        ),
        after_payload={
            "semantic_key": semantic_key,
            "object_kind": "function",
            "owner_semantic_key": owner_semantic_key,
            "class_config_id": str(class_config_id),
            "entity_id": str(function_config_id),
            "function_config_id": str(function_config_id),
            "entity_name": function_descriptor.name,
            "function_name": function_descriptor.name,
            "owner_key": class_fqn,
            "kind": function_descriptor.kind,
            "description": function_descriptor.description,
            "verb": function_descriptor.verb,
            "is_async": function_descriptor.is_async,
            "is_public": function_descriptor.is_public,
            "is_constructor": function_descriptor.is_constructor,
            "position": function_descriptor.position,
            "function_signature": {
                "owner_key": class_fqn,
                "name": function_descriptor.name,
                "kind": function_descriptor.kind,
                "description": function_descriptor.description,
                "verb": function_descriptor.verb,
                "is_async": function_descriptor.is_async,
                "inputs": tuple(dict(item) for item in function_descriptor.inputs),
                "outputs": tuple(dict(item) for item in function_descriptor.outputs),
            },
            "function_membership_signature": {
                "class_config_id": str(class_config_id),
                "function_config_id": str(function_config_id),
                "is_public": function_descriptor.is_public,
                "is_constructor": function_descriptor.is_constructor,
                "position": function_descriptor.position,
            },
        },
    )


def _coverage_members(
    *,
    descriptor: MetaOcgPackageDescriptor,
    context: _PlanContext,
    operation_intents: tuple[MetaOcgPackageOperationIntent, ...],
) -> tuple[MetaOcgPackageCoverageMember, ...]:
    members: list[MetaOcgPackageCoverageMember] = [
        MetaOcgPackageCoverageMember(
            category="package_identity",
            key=descriptor.package_semantic_key,
            source_refs=descriptor.source_refs,
        ),
        MetaOcgPackageCoverageMember(
            category="graph_identity",
            key=f"{descriptor.graph_semantic_key}/identity",
            source_refs=descriptor.source_refs,
        ),
    ]
    members.extend(
        MetaOcgPackageCoverageMember(
            category="graph_node",
            key=_class_semantic_key(context=context, class_fqn=class_descriptor.class_fqn),
            source_refs=_member_source_refs(
                descriptor,
                class_descriptor.source_refs,
            ),
        )
        for class_descriptor in descriptor.classes
    )
    members.extend(
        MetaOcgPackageCoverageMember(
            category="graph_node",
            key=_enum_semantic_key(context=context, enum_fqn=enum_descriptor.enum_fqn),
            source_refs=_member_source_refs(
                descriptor,
                enum_descriptor.source_refs,
            ),
        )
        for enum_descriptor in descriptor.enums
    )
    members.extend(
        MetaOcgPackageCoverageMember(
            category="graph_node",
            key=_relationship_node_semantic_key(
                context=context,
                relationship_descriptor=relationship_descriptor,
            ),
            source_refs=_member_source_refs(
                descriptor,
                relationship_descriptor.source_refs,
            ),
        )
        for relationship_descriptor in descriptor.relationships
    )
    for intent in operation_intents:
        category = _intent_coverage_category(intent)
        if category is not None:
            members.append(
                MetaOcgPackageCoverageMember(
                    category=category,
                    key=intent.semantic_key,
                    source_refs=intent.source_refs,
                )
            )
    members.extend(
        MetaOcgPackageCoverageMember(
            category="namespace_membership",
            key=namespace,
            source_refs=descriptor.source_refs,
        )
        for namespace in _namespaces(descriptor=descriptor)
    )
    members.extend(
        MetaOcgPackageCoverageMember(
            category="source_ref",
            key=source_ref,
            source_refs=(source_ref,),
        )
        for source_ref in _all_source_refs(descriptor=descriptor)
    )
    return tuple(_unique_members(members))


def _intent_coverage_category(
    intent: MetaOcgPackageOperationIntent,
) -> str | None:
    operation_type = intent.semantic_operation_type
    if operation_type == META_OBJECT_CONFIG_GRAPH_CLASS_CREATE_OPERATION:
        return "class_config"
    if operation_type == META_OBJECT_CONFIG_GRAPH_ENUM_CREATE_OPERATION:
        return "enum_config"
    if operation_type == META_OBJECT_CONFIG_GRAPH_ENUM_OPTION_CREATE_OPERATION:
        return "enum_option"
    if operation_type == META_OBJECT_CONFIG_GRAPH_RELATIONSHIP_CREATE_OPERATION:
        return "relationship_config"
    if operation_type == META_OBJECT_CONFIG_GRAPH_ATTRIBUTE_CREATE_OPERATION:
        return "attribute_config"
    if operation_type == META_OBJECT_CONFIG_GRAPH_FUNCTION_CREATE_OPERATION:
        return "function_config"
    return None


def _descriptor_blockers(
    *,
    descriptor: MetaOcgPackageDescriptor,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if not _has_text(descriptor.package_name):
        blockers.append("package_name_required")
    if not _has_text(descriptor.fqn_prefix):
        blockers.append("fqn_prefix_required")
    if not descriptor.source_refs:
        blockers.append("source_refs_required")
    class_fqns = {item.class_fqn for item in descriptor.classes}
    enum_fqns = {item.enum_fqn for item in descriptor.enums}
    for class_descriptor in descriptor.classes:
        if not _has_text(class_descriptor.class_fqn):
            blockers.append("class_fqn_required")
        for attribute in class_descriptor.attributes:
            if attribute.owner_class_fqn != class_descriptor.class_fqn:
                blockers.append(
                    f"attribute_owner_class_mismatch:{attribute.name or 'unknown'}"
                )
            if not _has_text(attribute.name):
                blockers.append("attribute_name_required")
        for function in class_descriptor.functions:
            if function.owner_class_fqn != class_descriptor.class_fqn:
                blockers.append(
                    f"function_owner_class_mismatch:{function.name or 'unknown'}"
                )
            if not _has_text(function.name):
                blockers.append("function_name_required")
    for enum_descriptor in descriptor.enums:
        if not _has_text(enum_descriptor.enum_fqn):
            blockers.append("enum_fqn_required")
        for option in enum_descriptor.options:
            if not _has_text(option.value):
                blockers.append(f"enum_option_value_required:{enum_descriptor.enum_fqn}")
    for relationship in descriptor.relationships:
        if relationship.source_class_fqn not in class_fqns:
            blockers.append(
                f"relationship_source_class_missing:{relationship.source_class_fqn}"
            )
        if (
            relationship.target_class_fqn not in class_fqns
            and not _has_text(relationship.target_class_config_id)
        ):
            blockers.append(
                f"relationship_target_class_missing:{relationship.target_class_fqn}"
            )
        if not _has_text(relationship.relationship_key):
            blockers.append("relationship_key_required")
        if not _has_text(relationship.relationship_type):
            blockers.append("relationship_type_required")
    if class_fqns & enum_fqns:
        blockers.append("class_enum_fqn_collision")
    return tuple(blockers)


def _class_descriptor_from_node(
    *,
    node: Mapping[str, object],
    package_source_refs: tuple[str, ...],
    function_entries_by_owner: Mapping[str, tuple[Mapping[str, object], ...]],
) -> MetaOcgPackageClassDescriptor:
    class_config = _mapping(node.get("class_config"))
    class_fqn = _required_text(
        node.get("node_key") or class_config.get("class_fqn"),
        blocker="class_fqn_required",
    )
    source_refs = _node_source_refs(node=node) or package_source_refs
    return MetaOcgPackageClassDescriptor(
        class_fqn=class_fqn,
        class_name=_optional_text(class_config.get("name")) or _tail(class_fqn),
        description=_optional_text(class_config.get("description")),
        attributes=tuple(
            _attribute_descriptor_from_entry(
                owner_class_fqn=class_fqn,
                entry=_mapping(entry),
                source_refs=source_refs,
            )
            for entry in _sequence(class_config.get("class_config_attribute_configs"))
        ),
        functions=tuple(
            _function_descriptor_from_entry(
                owner_class_fqn=class_fqn,
                entry=entry,
                source_refs=source_refs,
                position=position,
            )
            for position, entry in enumerate(
                function_entries_by_owner.get(class_fqn, ())
            )
        ),
        source_refs=source_refs,
    )


def _attribute_descriptor_from_entry(
    *,
    owner_class_fqn: str,
    entry: Mapping[str, object],
    source_refs: tuple[str, ...],
) -> MetaOcgPackageAttributeDescriptor:
    attribute_config = _mapping(entry.get("attribute_config"))
    return MetaOcgPackageAttributeDescriptor(
        owner_class_fqn=owner_class_fqn,
        name=_required_text(
            attribute_config.get("name"),
            blocker=f"attribute_name_required:{owner_class_fqn}",
        ),
        primitive_base_type=_type_descriptor_primitive_base(
            _mapping(attribute_config.get("type_descriptor")),
        ),
        description=_optional_text(attribute_config.get("description")),
        position=_int_value(entry.get("position")),
        required=attribute_config.get("is_required") is not False,
        public=attribute_config.get("is_public") is not False,
        source_refs=source_refs,
    )


def _function_descriptor_from_entry(
    *,
    owner_class_fqn: str,
    entry: Mapping[str, object],
    source_refs: tuple[str, ...],
    position: int,
) -> MetaOcgPackageFunctionDescriptor:
    name = _required_text(
        entry.get("name"),
        blocker=f"function_name_required:{owner_class_fqn}",
    )
    return MetaOcgPackageFunctionDescriptor(
        owner_class_fqn=owner_class_fqn,
        name=name,
        description=_optional_text(entry.get("description")),
        kind=_optional_text(entry.get("kind")) or "instance",
        verb=_optional_text(entry.get("verb")),
        is_async=entry.get("is_async") is True,
        is_public=entry.get("is_public") is not False,
        is_constructor=entry.get("is_constructor") is True,
        position=_int_value(entry.get("position"), default=position),
        inputs=_mapping_tuple(entry.get("inputs")),
        outputs=_mapping_tuple(entry.get("outputs")),
        source_refs=source_refs,
    )


def _enum_descriptor_from_node(
    *,
    node: Mapping[str, object],
    package_source_refs: tuple[str, ...],
) -> MetaOcgPackageEnumDescriptor:
    enum_config = _mapping(node.get("enum_config"))
    enum_fqn = _required_text(
        node.get("node_key") or enum_config.get("enum_fqn"),
        blocker="enum_fqn_required",
    )
    source_refs = _node_source_refs(node=node) or package_source_refs
    return MetaOcgPackageEnumDescriptor(
        enum_fqn=enum_fqn,
        enum_name=_optional_text(enum_config.get("name")) or _tail(enum_fqn),
        description=_optional_text(enum_config.get("description")),
        options=tuple(
            _enum_option_descriptor_from_entry(
                entry=_mapping(entry),
                source_refs=source_refs,
            )
            for entry in _sequence(enum_config.get("enum_options"))
        ),
        source_refs=source_refs,
    )


def _enum_option_descriptor_from_entry(
    *,
    entry: Mapping[str, object],
    source_refs: tuple[str, ...],
) -> MetaOcgPackageEnumOptionDescriptor:
    return MetaOcgPackageEnumOptionDescriptor(
        value=_required_text(entry.get("value"), blocker="enum_option_value_required"),
        label=_optional_text(entry.get("label")),
        description=_optional_text(entry.get("description")),
        position=_int_value(entry.get("position")),
        source_refs=source_refs,
    )


def _relationship_descriptor_from_node(
    *,
    node: Mapping[str, object],
    class_id_to_fqn: Mapping[str, str],
    package_source_refs: tuple[str, ...],
) -> MetaOcgPackageRelationshipDescriptor | None:
    relationship = _mapping(node.get("class_config_relationship"))
    source_class_id = _optional_text(relationship.get("class_config_id"))
    target_class_id = _optional_text(relationship.get("target_class_config_id"))
    source_class_fqn = (
        class_id_to_fqn.get(source_class_id) if source_class_id is not None else None
    )
    target_class_fqn = (
        class_id_to_fqn.get(target_class_id) if target_class_id is not None else None
    ) or _relationship_target_from_node_key(node=node)
    relationship_key = _optional_text(relationship.get("relationship_key"))
    relationship_type = _optional_text(relationship.get("relationship_type"))
    if relationship_key is None or relationship_type is None:
        node_parts = _relationship_node_key_parts(node=node)
        relationship_key = relationship_key or node_parts[1]
        relationship_type = relationship_type or node_parts[2]
        target_class_fqn = target_class_fqn or node_parts[3]
    if source_class_fqn is None or target_class_fqn is None:
        return None
    return MetaOcgPackageRelationshipDescriptor(
        source_class_fqn=source_class_fqn,
        target_class_fqn=target_class_fqn,
        relationship_key=_required_text(
            relationship_key,
            blocker="relationship_key_required",
        ),
        relationship_type=_required_text(
            relationship_type,
            blocker="relationship_type_required",
        ),
        target_class_config_id=target_class_id,
        description=_optional_text(relationship.get("description")),
        source_refs=_node_source_refs(node=node) or package_source_refs,
    )


def _relationship_target_class_id(
    *,
    context: _PlanContext,
    relationship_descriptor: MetaOcgPackageRelationshipDescriptor,
) -> UUID:
    package_class_fqns = {item.class_fqn for item in context.descriptor.classes}
    if relationship_descriptor.target_class_fqn not in package_class_fqns:
        if relationship_descriptor.target_class_config_id is not None:
            return UUID(relationship_descriptor.target_class_config_id)
    return _class_config_id(
        context=context,
        class_fqn=relationship_descriptor.target_class_fqn,
    )


def _class_id_to_fqn(
    *,
    nodes: tuple[Mapping[str, object], ...],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for node in nodes:
        if node.get("type") != "class":
            continue
        class_config = _mapping(node.get("class_config"))
        class_id = _optional_text(class_config.get("id"))
        class_fqn = _optional_text(node.get("node_key")) or _optional_text(
            class_config.get("class_fqn"),
        )
        if class_id is not None and class_fqn is not None:
            result[class_id] = class_fqn
    return result


def _relationship_target_from_node_key(
    *,
    node: Mapping[str, object],
) -> str | None:
    return _relationship_node_key_parts(node=node)[3]


def _relationship_node_key_parts(
    *,
    node: Mapping[str, object],
) -> tuple[str | None, str | None, str | None, str | None]:
    node_key = _optional_text(node.get("node_key"))
    if node_key is None:
        return (None, None, None, None)
    parts = node_key.split(":", maxsplit=3)
    if len(parts) != 4:
        return (None, None, None, None)
    return (parts[0], parts[1], parts[2], parts[3])


def _function_entries_by_owner(
    *,
    function_models: Mapping[str, object] | None,
) -> dict[str, tuple[Mapping[str, object], ...]]:
    result: dict[str, tuple[Mapping[str, object], ...]] = {}
    if function_models is None:
        return result
    for class_entry in _sequence(function_models.get("classes")):
        class_mapping = _mapping(class_entry)
        owner = _optional_text(class_mapping.get("aware_class_ref"))
        if owner is None:
            continue
        result[owner] = tuple(
            _mapping(function_entry)
            for function_entry in _sequence(class_mapping.get("functions"))
        )
    return result


def _all_node_source_refs(
    *,
    nodes: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    return _unique_texts(
        source_ref
        for node in nodes
        for source_ref in _node_source_refs(node=node)
    )


def _node_source_refs(
    *,
    node: Mapping[str, object],
) -> tuple[str, ...]:
    return _unique_texts(
        source_ref
        for layout in _sequence(node.get("layouts"))
        for source_ref in (
            _optional_text(_mapping(layout).get("relative_path")),
        )
        if source_ref is not None
    )


def _type_descriptor_primitive_base(type_descriptor: Mapping[str, object]) -> str:
    primitive_config = _mapping(type_descriptor.get("primitive_config"))
    primitive_type = _mapping(primitive_config.get("primitive_type"))
    base_type = _optional_text(primitive_type.get("base_type"))
    if base_type is not None:
        return base_type
    for child_link in _sequence(type_descriptor.get("child_links")):
        child = _mapping(_mapping(child_link).get("child"))
        child_base_type = _type_descriptor_primitive_base(child)
        if child_base_type:
            return child_base_type
    kind = _optional_text(type_descriptor.get("kind"))
    return kind or "string"


def _class_node_id(*, context: _PlanContext, class_fqn: str) -> UUID:
    return stable_object_config_graph_node_id(
        object_config_graph_id=context.graph_id,
        type="class",
        node_key=class_fqn,
    )


def _enum_node_id(*, context: _PlanContext, enum_fqn: str) -> UUID:
    return stable_object_config_graph_node_id(
        object_config_graph_id=context.graph_id,
        type="enum",
        node_key=enum_fqn,
    )


def _class_config_id(*, context: _PlanContext, class_fqn: str) -> UUID:
    return stable_class_config_id(
        object_config_graph_node_id=_class_node_id(context=context, class_fqn=class_fqn),
        class_fqn=class_fqn,
    )


def _enum_config_id(*, context: _PlanContext, enum_fqn: str) -> UUID:
    return stable_enum_config_id(
        object_config_graph_node_id=_enum_node_id(context=context, enum_fqn=enum_fqn),
        enum_fqn=enum_fqn,
    )


def _class_semantic_key(*, context: _PlanContext, class_fqn: str) -> str:
    return f"{context.descriptor.graph_semantic_key}/node:{class_fqn}"


def _enum_semantic_key(*, context: _PlanContext, enum_fqn: str) -> str:
    return f"{context.descriptor.graph_semantic_key}/node:{enum_fqn}"


def _relationship_node_semantic_key(
    *,
    context: _PlanContext,
    relationship_descriptor: MetaOcgPackageRelationshipDescriptor,
) -> str:
    return (
        f"{context.descriptor.graph_semantic_key}/node:"
        f"{relationship_descriptor.source_class_fqn}:"
        f"{relationship_descriptor.relationship_key}:"
        f"{relationship_descriptor.relationship_type}:"
        f"{relationship_descriptor.target_class_fqn}"
    )


def _member_source_refs(
    descriptor: MetaOcgPackageDescriptor,
    source_refs: tuple[str, ...],
) -> tuple[str, ...]:
    return source_refs or descriptor.source_refs


def _all_source_refs(
    *,
    descriptor: MetaOcgPackageDescriptor,
) -> tuple[str, ...]:
    return _unique_texts(
        (
            *descriptor.source_refs,
            *(
                source_ref
                for class_descriptor in descriptor.classes
                for source_ref in class_descriptor.source_refs
            ),
            *(
                source_ref
                for class_descriptor in descriptor.classes
                for attribute in class_descriptor.attributes
                for source_ref in attribute.source_refs
            ),
            *(
                source_ref
                for class_descriptor in descriptor.classes
                for function in class_descriptor.functions
                for source_ref in function.source_refs
            ),
            *(
                source_ref
                for enum_descriptor in descriptor.enums
                for source_ref in enum_descriptor.source_refs
            ),
            *(
                source_ref
                for enum_descriptor in descriptor.enums
                for option in enum_descriptor.options
                for source_ref in option.source_refs
            ),
            *(
                source_ref
                for relationship in descriptor.relationships
                for source_ref in relationship.source_refs
            ),
        )
    )


def _namespaces(
    *,
    descriptor: MetaOcgPackageDescriptor,
) -> tuple[str, ...]:
    return _unique_texts(
        (
            *(_namespace(item.class_fqn) for item in descriptor.classes),
            *(_namespace(item.enum_fqn) for item in descriptor.enums),
        )
    )


def _unique_members(
    members: Iterable[MetaOcgPackageCoverageMember],
) -> tuple[MetaOcgPackageCoverageMember, ...]:
    result: list[MetaOcgPackageCoverageMember] = []
    seen: set[tuple[str, str]] = set()
    for member in members:
        key = (member.category, member.key)
        if key in seen:
            continue
        seen.add(key)
        result.append(member)
    return tuple(result)


def _unique_texts(values: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = value.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return tuple(result)


def _namespace(fqn: str) -> str:
    parts = fqn.rsplit(".", maxsplit=1)
    return parts[0] if len(parts) == 2 else ""


def _tail(fqn: str) -> str:
    return fqn.rsplit(".", maxsplit=1)[-1]


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return ()


def _mapping_tuple(value: object) -> tuple[Mapping[str, object], ...]:
    return tuple(_mapping(item) for item in _sequence(value))


def _optional_text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _required_text(value: object, *, blocker: str) -> str:
    text = _optional_text(value)
    if text is not None:
        return text
    return blocker


def _int_value(value: object, *, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(value.strip())
        except ValueError:
            return default
    return default


def _has_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


__all__ = [
    "META_OCG_PACKAGE_OPERATION_PLAN_CONTRACT_VERSION",
    "MetaOcgPackageAttributeDescriptor",
    "MetaOcgPackageClassDescriptor",
    "MetaOcgPackageCoverageMember",
    "MetaOcgPackageDescriptor",
    "MetaOcgPackageEnumDescriptor",
    "MetaOcgPackageEnumOptionDescriptor",
    "MetaOcgPackageFunctionDescriptor",
    "MetaOcgPackageOperationIntent",
    "MetaOcgPackageOperationPlan",
    "MetaOcgPackageRelationshipDescriptor",
    "build_meta_ocg_package_descriptor_from_materialized_ocg",
    "build_meta_ocg_package_operation_plan",
]
