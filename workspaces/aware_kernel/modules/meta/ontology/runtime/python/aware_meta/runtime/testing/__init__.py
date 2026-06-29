from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_meta.graph.instance.commit.fs_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime.graph_lane import MetaGraphBoundRuntimeLane
from aware_meta.runtime.graph_runtime import MetaGraphRuntime
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_value_decoder import decode_oig_attribute_value
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_relationship import (
    ClassConfigRelationship,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
)
from aware_meta_ontology.graph.config.object_config_graph import ObjectConfigGraph
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)


@dataclass(frozen=True, slots=True)
class IsolatedMetaAwareRoot:
    """Isolate `.aware` writes for Meta runtime tests."""

    root: Path
    persistence_backend: str = "fs"
    database_url: str | None = None
    _env_overrides: dict[str, str | None] = field(
        default_factory=dict,
        init=False,
        repr=False,
        compare=False,
    )

    def __enter__(self) -> Path:
        root = self.root.expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        (root / ".aware").mkdir(parents=True, exist_ok=True)

        env_overrides = {
            "AWARE_ROOT": os.environ.get("AWARE_ROOT"),
            "AWARE_PERSISTENCE_BACKEND": os.environ.get("AWARE_PERSISTENCE_BACKEND"),
            "DATABASE_URL": os.environ.get("DATABASE_URL"),
        }
        object.__setattr__(self, "_env_overrides", env_overrides)

        os.environ["AWARE_ROOT"] = str(root)
        os.environ["AWARE_PERSISTENCE_BACKEND"] = self.persistence_backend
        if self.database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self.database_url
        return root

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        _ = exc_type, exc, tb
        for key, previous in self._env_overrides.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous

    @contextmanager
    def activate(self) -> Iterator[Path]:
        with self as root:
            yield root


async def materialize_meta_runtime_lane_head(
    *,
    runtime: MetaGraphRuntime,
    lane: MetaGraphBoundRuntimeLane,
) -> ObjectInstanceGraph:
    """Read the committed OIG head for a bound Meta runtime lane."""

    context = runtime.context
    if context is None:
        raise ValueError(
            "materialize_meta_runtime_lane_head requires a runtime built with "
            "MetaGraphRuntimeContext."
        )
    opg = context.index.opg_by_hash.get(lane.binding.projection_hash)
    if opg is None:
        raise ValueError(
            "Meta runtime lane projection hash is not present in context index: "
            f"{lane.binding.projection_hash}"
        )
    head = await FSCommitStore().head(
        branch_id=lane.branch_id,
        projection_hash=lane.binding.projection_hash,
    )
    if head is None:
        raise AssertionError(
            "No committed OIG head found for Meta runtime lane: "
            f"branch_id={lane.branch_id} "
            f"projection_hash={lane.binding.projection_hash}"
        )
    oig, _ = await OIGMaterializer().get(
        branch_id=lane.branch_id,
        ocg=context.index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        oig_id=UUID(str(head["object_instance_graph_id"])),
        attribute_configs_by_id=context.index.attribute_configs_by_id,
        class_configs_by_id=context.index.class_configs_by_id,
    )
    return oig


class MetaOIGAssertions:
    """Focused committed-OIG assertions for Meta runtime proofs."""

    def __init__(
        self,
        *,
        oig: ObjectInstanceGraph,
        index: MetaGraphRuntimeIndex | None = None,
        ocg: ObjectConfigGraph | None = None,
        class_configs_by_id: dict[UUID, ClassConfig] | None = None,
        relationships_by_id: (
            dict[
                UUID,
                ClassConfigRelationship,
            ]
            | None
        ) = None,
    ) -> None:
        self._oig = oig
        if index is not None:
            self._class_configs_by_id = dict(index.class_configs_by_id)
            self._relationships_by_id = dict(index.relationships_by_id)
        elif class_configs_by_id is not None and relationships_by_id is not None:
            self._class_configs_by_id = dict(class_configs_by_id)
            self._relationships_by_id = dict(relationships_by_id)
        elif ocg is not None:
            self._class_configs_by_id = _class_configs_by_id(ocg)
            self._relationships_by_id = _relationships_by_id(ocg)
        else:
            raise ValueError(
                "MetaOIGAssertions requires index, ocg, or explicit config " "indexes."
            )

        self._attribute_names_by_id: dict[UUID, str] = {}
        for class_config in self._class_configs_by_id.values():
            for link in class_config.class_config_attribute_configs:
                attribute_config = link.attribute_config
                self._attribute_names_by_id[attribute_config.id] = attribute_config.name

    @property
    def oig(self) -> ObjectInstanceGraph:
        return self._oig

    def expect_root(self, expected: UUID) -> None:
        assert self._oig.root_class_instance_id == self._resolve_instance_id(expected)

    def expect_instance(self, instance_id: UUID) -> None:
        ids = {
            instance.id
            for instance in self._oig.class_instances
            if instance.id is not None
        }
        assert self._resolve_instance_id(instance_id) in ids

    def expect_edge(
        self,
        *,
        source_id: UUID,
        target_id: UUID,
        relationship_name: str | None = None,
    ) -> None:
        resolved_source_id = self._resolve_instance_id(source_id)
        resolved_target_id = self._resolve_instance_id(target_id)
        if relationship_name is None:
            pairs = {
                (
                    relationship.source_class_instance_id,
                    relationship.target_class_instance_id,
                )
                for relationship in self._oig.class_instance_relationships
            }
            assert (resolved_source_id, resolved_target_id) in pairs
            return

        source = next(
            instance
            for instance in self._oig.class_instances
            if instance.id == resolved_source_id
        )
        target = next(
            instance
            for instance in self._oig.class_instances
            if instance.id == resolved_target_id
        )
        relationship_id = self._resolve_relationship_id_by_name(
            source_class_config_id=source.class_config_id,
            target_class_config_id=target.class_config_id,
            relationship_name=relationship_name,
        )
        assert any(
            relationship.source_class_instance_id == resolved_source_id
            and relationship.target_class_instance_id == resolved_target_id
            and relationship.class_config_relationship_id == relationship_id
            for relationship in self._oig.class_instance_relationships
        )

    def primitive(
        self,
        *,
        instance_id: UUID,
        field_name: str,
    ) -> Any:
        resolved_instance_id = self._resolve_instance_id(instance_id)
        instance = next(
            item
            for item in self._oig.class_instances
            if item.id == resolved_instance_id
        )
        class_config = self._class_configs_by_id[instance.class_config_id]
        attribute_config_id = next(
            link.attribute_config.id
            for link in class_config.class_config_attribute_configs
            if link.attribute_config.name == field_name
        )
        attribute = next(
            item
            for item in instance.attributes
            if item.attribute_config_id == attribute_config_id
        )
        return decode_oig_attribute_value(
            attribute.value_root,
            class_configs_by_id=self._class_configs_by_id,
        )

    def expect_primitive(
        self,
        *,
        instance_id: UUID,
        field_name: str,
        expected: Any,
    ) -> None:
        assert (
            self.primitive(instance_id=instance_id, field_name=field_name) == expected
        )

    def _resolve_instance_id(self, candidate_id: UUID) -> UUID:
        for instance in self._oig.class_instances:
            if instance.id == candidate_id:
                return candidate_id
        for instance in self._oig.class_instances:
            if instance.source_object_id != candidate_id:
                continue
            if instance.id is None:
                break
            return instance.id
        raise AssertionError(
            "Class instance not found in Meta proof OIG: "
            f"candidate_id={candidate_id} "
            f"class_instance_ids={self._class_instance_ids()} "
            f"source_object_ids={self._source_object_ids()}"
        )

    def _resolve_relationship_id_by_name(
        self,
        *,
        source_class_config_id: UUID,
        target_class_config_id: UUID,
        relationship_name: str,
    ) -> UUID:
        candidates: list[UUID] = []
        available: list[str] = []
        for relationship in self._relationships_by_id.values():
            if relationship.class_config_id != source_class_config_id:
                continue
            if relationship.target_class_config_id != target_class_config_id:
                continue
            for attribute in relationship.class_config_relationship_attributes:
                if attribute.role != ClassConfigRelationshipAttributeRole.reference:
                    continue
                if attribute.direction != ClassConfigRelationshipDirection.forward:
                    continue
                name = self._attribute_names_by_id.get(attribute.attribute_config_id)
                if not name:
                    continue
                available.append(name)
                if name == relationship_name:
                    candidates.append(relationship.id)

        if len(candidates) == 1:
            return candidates[0]
        if candidates:
            raise AssertionError(
                "Relationship edge name is ambiguous: "
                f"{relationship_name!r} "
                f"({source_class_config_id} -> {target_class_config_id}) "
                f"matches {candidates}"
            )
        raise AssertionError(
            "Relationship edge not found by name: "
            f"{relationship_name!r} "
            f"({source_class_config_id} -> {target_class_config_id}). "
            f"Available={sorted(set(available))}"
        )

    def _class_instance_ids(self) -> list[UUID]:
        return [
            instance.id
            for instance in self._oig.class_instances
            if instance.id is not None
        ]

    def _source_object_ids(self) -> list[UUID | None]:
        return [instance.source_object_id for instance in self._oig.class_instances]


def _class_configs_by_id(ocg: ObjectConfigGraph) -> dict[UUID, ClassConfig]:
    return {
        node.class_config.id: node.class_config
        for node in ocg.object_config_graph_nodes
        if node.class_config is not None
    }


def _relationships_by_id(
    ocg: ObjectConfigGraph,
) -> dict[UUID, ClassConfigRelationship]:
    relationships = {
        node.class_config_relationship.id: node.class_config_relationship
        for node in ocg.object_config_graph_nodes
        if node.class_config_relationship is not None
    }
    for ocg_relationship in ocg.object_config_graph_relationships:
        for relationship in ocg_relationship.class_config_relationships:
            relationships.setdefault(relationship.id, relationship)
    return relationships


from aware_meta.runtime.testing.proof import (  # noqa: E402
    ROOT_OBJECT_ID,
    LaneIds,
    MultiLaneProofCall,
    ProofCall,
    ProofResult,
    RootObjectId,
    SourceObjectId,
    run_meta_runtime_proof,
    run_multi_lane_meta_runtime_proof,
)


__all__ = [
    "IsolatedMetaAwareRoot",
    "LaneIds",
    "MetaOIGAssertions",
    "MultiLaneProofCall",
    "ProofCall",
    "ProofResult",
    "ROOT_OBJECT_ID",
    "RootObjectId",
    "SourceObjectId",
    "materialize_meta_runtime_lane_head",
    "run_meta_runtime_proof",
    "run_multi_lane_meta_runtime_proof",
]
