from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, cast
from uuid import UUID

from aware_meta.runtime.handler_executor.contracts import (
    MetaGraphCommitIndex,
    MetaGraphFunctionImplementationDescriptor,
    MetaGraphImplementationKind,
    MetaGraphResolvedFunctionTarget,
)
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_function_config import (
    ClassConfigFunctionConfig,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.function.function_config_attribute_config import (
    FunctionConfigAttributeConfig,
)
from aware_meta_ontology.function.function_config_enums import FunctionAttributeType
from aware_meta_ontology.function.function_impl import FunctionImpl
from aware_meta_ontology.function.function_impl_enums import FunctionImplKind
from aware_meta_ontology.graph.config.object_config_graph_package import (
    ObjectConfigGraphPackage,
)
from aware_meta_ontology.graph.config.object_config_graph_package_implementation_policy_enums import (
    ObjectConfigGraphPackageFunctionImplOwnership,
)
from aware_meta_ontology.graph.config.object_config_graph_enums import (
    ObjectConfigGraphNodeType,
)


class _FunctionObjectConfigGraphNode(Protocol):
    type: ObjectConfigGraphNodeType
    function_config: FunctionConfig | None


class MetaGraphFunctionImplOwnership(Enum):
    """FunctionImpl execution ownership policy for one Meta function scope."""

    authored = "authored"
    compiler = "compiler"


@dataclass(frozen=True, slots=True)
class MetaGraphImplementationPolicy:
    """Resolve whether FunctionImpl truth is executable or handler-backed."""

    default_function_impl_ownership: MetaGraphFunctionImplOwnership = (
        MetaGraphFunctionImplOwnership.authored
    )
    function_impl_ownership_by_owner_key: Mapping[
        str,
        MetaGraphFunctionImplOwnership,
    ] = field(default_factory=dict)
    function_impl_ownership_by_owner_prefix: Mapping[
        str,
        MetaGraphFunctionImplOwnership,
    ] = field(default_factory=dict)

    def function_impl_ownership(
        self,
        function_config: FunctionConfig,
    ) -> MetaGraphFunctionImplOwnership:
        owner_key = function_config.owner_key.strip()
        if owner_key:
            ownership = self.function_impl_ownership_by_owner_key.get(owner_key)
            if ownership is not None:
                return ownership
            prefix_ownership = self._function_impl_ownership_by_prefix(owner_key)
            if prefix_ownership is not None:
                return prefix_ownership
        return self.default_function_impl_ownership

    def _function_impl_ownership_by_prefix(
        self,
        owner_key: str,
    ) -> MetaGraphFunctionImplOwnership | None:
        owner_segments = owner_key.split(".")
        for segment_count in range(len(owner_segments), 0, -1):
            owner_prefix = ".".join(owner_segments[:segment_count])
            ownership = self.function_impl_ownership_by_owner_prefix.get(owner_prefix)
            if ownership is not None:
                return ownership
        return None


def build_meta_graph_implementation_policy_from_packages(
    packages: Iterable[ObjectConfigGraphPackage],
) -> MetaGraphImplementationPolicy:
    """Build Meta executor policy from committed OCG package truth."""

    ownership_by_owner_prefix: dict[str, MetaGraphFunctionImplOwnership] = {}
    for package in packages:
        fqn_prefix = package.fqn_prefix.strip()
        if not fqn_prefix:
            raise ValueError(
                "ObjectConfigGraphPackage.fqn_prefix is required for Meta implementation policy"
            )
        ownership = _meta_graph_function_impl_ownership_from_package(package)
        existing = ownership_by_owner_prefix.get(fqn_prefix)
        if existing is not None and existing is not ownership:
            raise ValueError(
                "Conflicting ObjectConfigGraphPackage FunctionImpl ownership policy "
                f"for fqn_prefix={fqn_prefix!r}: {existing.value!r} != {ownership.value!r}"
            )
        ownership_by_owner_prefix[fqn_prefix] = ownership
    return MetaGraphImplementationPolicy(
        function_impl_ownership_by_owner_prefix=ownership_by_owner_prefix,
    )


def _meta_graph_function_impl_ownership_from_package(
    package: ObjectConfigGraphPackage,
) -> MetaGraphFunctionImplOwnership:
    ownership = package.function_impl_ownership
    if ownership is ObjectConfigGraphPackageFunctionImplOwnership.compiler:
        return MetaGraphFunctionImplOwnership.compiler
    if ownership is ObjectConfigGraphPackageFunctionImplOwnership.authored:
        return MetaGraphFunctionImplOwnership.authored
    if isinstance(ownership, str):
        try:
            return MetaGraphFunctionImplOwnership(ownership)
        except ValueError as exc:
            raise ValueError(
                "Unsupported ObjectConfigGraphPackage.function_impl_ownership: "
                f"{ownership!r}"
            ) from exc
    raise ValueError(
        "Unsupported ObjectConfigGraphPackage.function_impl_ownership: "
        f"{ownership!r}"
    )


@dataclass(slots=True)
class MetaGraphRuntimeIndexView:
    """Cached Meta view over graph runtime index truth.

    The view gives Meta executor code stable O(1) access to hot-path lookups and
    keeps the heavy composed index behind a small protocol boundary.
    """

    index: MetaGraphCommitIndex
    implementation_policy: MetaGraphImplementationPolicy = field(
        default_factory=MetaGraphImplementationPolicy,
    )
    _function_targets_by_id: dict[UUID, MetaGraphResolvedFunctionTarget] | None = field(
        default=None, init=False, repr=False
    )
    _implementation_descriptors_by_id: (
        dict[UUID, MetaGraphFunctionImplementationDescriptor] | None
    ) = field(default=None, init=False, repr=False)
    _function_input_edges_by_id: (
        dict[UUID, FunctionConfigAttributeConfig] | None
    ) = field(default=None, init=False, repr=False)
    _function_input_edges_by_function_id: (
        dict[UUID, tuple[FunctionConfigAttributeConfig, ...]] | None
    ) = field(default=None, init=False, repr=False)
    _function_input_edges_by_attribute_config_id: (
        dict[UUID, dict[UUID, FunctionConfigAttributeConfig]] | None
    ) = field(default=None, init=False, repr=False)

    @property
    def function_targets_by_id(
        self,
    ) -> Mapping[UUID, MetaGraphResolvedFunctionTarget]:
        targets = self._function_targets_by_id
        if targets is None:
            targets = build_meta_graph_function_target_index(self.index)
            self._function_targets_by_id = targets
        return targets

    def resolve_function_target(
        self,
        function_id: UUID,
    ) -> MetaGraphResolvedFunctionTarget:
        resolved_target = self.function_targets_by_id.get(function_id)
        if resolved_target is None:
            raise ValueError(
                f"FunctionConfig not found in Meta graph index: {function_id}"
            )
        return resolved_target

    @property
    def implementation_descriptors_by_id(
        self,
    ) -> Mapping[UUID, MetaGraphFunctionImplementationDescriptor]:
        descriptors = self._implementation_descriptors_by_id
        if descriptors is None:
            descriptors = build_meta_graph_implementation_descriptor_index(
                self.index,
                implementation_policy=self.implementation_policy,
            )
            self._implementation_descriptors_by_id = descriptors
        return descriptors

    def resolve_implementation_descriptor(
        self,
        function_id: UUID,
    ) -> MetaGraphFunctionImplementationDescriptor:
        descriptor = self.implementation_descriptors_by_id.get(function_id)
        if descriptor is None:
            raise ValueError(
                "Function implementation descriptor not found in Meta graph index: "
                f"{function_id}"
            )
        return descriptor

    @property
    def function_input_edges_by_id(
        self,
    ) -> Mapping[UUID, FunctionConfigAttributeConfig]:
        self._ensure_function_input_edge_indexes()
        return self._function_input_edges_by_id or {}

    @property
    def function_input_edges_by_function_id(
        self,
    ) -> Mapping[UUID, tuple[FunctionConfigAttributeConfig, ...]]:
        self._ensure_function_input_edge_indexes()
        return self._function_input_edges_by_function_id or {}

    @property
    def function_input_edges_by_attribute_config_id(
        self,
    ) -> Mapping[UUID, Mapping[UUID, FunctionConfigAttributeConfig]]:
        self._ensure_function_input_edge_indexes()
        return self._function_input_edges_by_attribute_config_id or {}

    def _ensure_function_input_edge_indexes(self) -> None:
        if self._function_input_edges_by_id is not None:
            return
        by_id: dict[UUID, FunctionConfigAttributeConfig] = {}
        by_function_id: dict[UUID, tuple[FunctionConfigAttributeConfig, ...]] = {}
        by_attribute_config_id: dict[
            UUID,
            dict[UUID, FunctionConfigAttributeConfig],
        ] = {}
        for resolved_target in self.function_targets_by_id.values():
            function_config = resolved_target.function_config
            input_edges = tuple(
                sorted(
                    (
                        edge
                        for edge in function_config.function_config_attribute_configs
                        if _function_attribute_type(edge.type)
                        is FunctionAttributeType.input
                    ),
                    key=lambda edge: int(edge.position),
                )
            )
            by_function_id[function_config.id] = input_edges
            by_attribute_config_id[function_config.id] = {
                edge.attribute_config_id: edge
                for edge in input_edges
                if edge.attribute_config_id is not None
            }
            for edge in input_edges:
                by_id[edge.id] = edge
        self._function_input_edges_by_id = by_id
        self._function_input_edges_by_function_id = by_function_id
        self._function_input_edges_by_attribute_config_id = by_attribute_config_id


def build_meta_graph_function_target_index(
    index: MetaGraphCommitIndex,
) -> dict[UUID, MetaGraphResolvedFunctionTarget]:
    """Build a function target index from Meta graph index fields."""

    function_configs_by_id: dict[UUID, FunctionConfig] = {}
    operation_labels_by_id: dict[UUID, str] = {}

    def remember_function(
        *,
        function_config: FunctionConfig | None,
        class_config: ClassConfig | None = None,
    ) -> None:
        if function_config is None:
            return
        function_configs_by_id.setdefault(function_config.id, function_config)
        function_name = function_config.name.strip()
        if not function_name:
            return
        if class_config is None:
            operation_labels_by_id.setdefault(function_config.id, function_name)
            return
        class_name = class_config.name.strip()
        operation_labels_by_id[function_config.id] = (
            f"{class_name}.{function_name}" if class_name else function_name
        )

    for node in index.ocg.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.function:
            continue
        remember_function(
            function_config=cast(
                _FunctionObjectConfigGraphNode,
                cast(object, node),
            ).function_config
        )

    for class_config in tuple(index.class_configs_by_id.values()):
        for link in class_config.class_config_function_configs:
            remember_function(
                function_config=link.function_config,
                class_config=class_config,
            )

    return {
        function_id: MetaGraphResolvedFunctionTarget(
            function_config=function_config,
            operation_label=operation_labels_by_id.get(
                function_id,
                f"function:{function_id}",
            ),
        )
        for function_id, function_config in function_configs_by_id.items()
    }


def build_meta_graph_implementation_descriptor_index(
    index: MetaGraphCommitIndex,
    *,
    implementation_policy: MetaGraphImplementationPolicy | None = None,
) -> dict[UUID, MetaGraphFunctionImplementationDescriptor]:
    """Build implementation descriptors from class/function graph contracts."""

    policy = implementation_policy or MetaGraphImplementationPolicy()
    descriptors_by_id: dict[UUID, MetaGraphFunctionImplementationDescriptor] = {}
    function_configs_by_id: dict[UUID, FunctionConfig] = {}

    def remember_descriptor(
        *,
        function_config: FunctionConfig,
        class_config: ClassConfig | None,
        class_function_edge: ClassConfigFunctionConfig | None,
        is_constructor: bool,
    ) -> None:
        descriptor = MetaGraphFunctionImplementationDescriptor(
            kind=_implementation_kind(
                function_config,
                implementation_policy=policy,
            ),
            function_config=function_config,
            owner_class_config=class_config,
            class_function_edge=class_function_edge,
            is_constructor=is_constructor,
        )
        existing = descriptors_by_id.get(function_config.id)
        if existing is not None:
            if (
                existing.owner_class_config is class_config
                and existing.class_function_edge is class_function_edge
            ):
                return
            raise ValueError(
                "Function implementation descriptor is ambiguous in Meta graph index: "
                f"{function_config.id}"
            )
        descriptors_by_id[function_config.id] = descriptor

    for node in index.ocg.object_config_graph_nodes:
        if node.type != ObjectConfigGraphNodeType.function:
            continue
        function_config = cast(
            _FunctionObjectConfigGraphNode,
            cast(object, node),
        ).function_config
        if function_config is not None:
            function_configs_by_id.setdefault(function_config.id, function_config)

    for class_config in tuple(index.class_configs_by_id.values()):
        for link in class_config.class_config_function_configs:
            function_config = link.function_config
            if function_config is None:
                continue
            function_configs_by_id.setdefault(function_config.id, function_config)
            remember_descriptor(
                function_config=function_config,
                class_config=class_config,
                class_function_edge=link,
                is_constructor=bool(link.is_constructor),
            )

    for function_id, function_config in function_configs_by_id.items():
        if function_id in descriptors_by_id:
            continue
        remember_descriptor(
            function_config=function_config,
            class_config=None,
            class_function_edge=None,
            is_constructor=False,
        )

    return descriptors_by_id


def _implementation_kind(
    function_config: FunctionConfig,
    *,
    implementation_policy: MetaGraphImplementationPolicy,
) -> MetaGraphImplementationKind:
    function_impl = function_config.function_impl
    if function_impl is None:
        return MetaGraphImplementationKind.language_handler

    function_impl_kind = _function_impl_kind(function_impl)
    if function_impl_kind is FunctionImplKind.auto_constructor:
        return MetaGraphImplementationKind.language_handler

    if not _function_impl_has_executable_instructions(function_impl):
        return MetaGraphImplementationKind.language_handler

    if (
        implementation_policy.function_impl_ownership(function_config)
        is MetaGraphFunctionImplOwnership.compiler
    ):
        return MetaGraphImplementationKind.aware_function_impl
    return MetaGraphImplementationKind.language_handler


def _function_impl_has_executable_instructions(
    function_impl: FunctionImpl,
) -> bool:
    function_impl_kind = _function_impl_kind(function_impl)
    if function_impl_kind is not FunctionImplKind.instruction_body:
        return False
    return bool(tuple(function_impl.instructions or ()))


def _function_impl_kind(function_impl: FunctionImpl) -> FunctionImplKind:
    kind = function_impl.kind
    if isinstance(kind, FunctionImplKind):
        return kind
    if isinstance(kind, str):
        try:
            return FunctionImplKind(kind)
        except ValueError as exc:
            raise ValueError(f"Unsupported FunctionImpl.kind: {kind!r}") from exc
    raise ValueError(f"Unsupported FunctionImpl.kind: {kind!r}")


def _function_attribute_type(
    attribute_type: FunctionAttributeType,
) -> FunctionAttributeType:
    if isinstance(attribute_type, FunctionAttributeType):
        return attribute_type
    return FunctionAttributeType(attribute_type)


__all__ = [
    "build_meta_graph_implementation_policy_from_packages",
    "build_meta_graph_implementation_descriptor_index",
    "build_meta_graph_function_target_index",
    "MetaGraphFunctionImplOwnership",
    "MetaGraphImplementationPolicy",
    "MetaGraphRuntimeIndexView",
]
