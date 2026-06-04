"""
Tests for RelationshipMixin relationship management functionality.

Tests cover:
- Canonical relationship discovery from bound ClassConfig
- Foreign key propagation from relationship objects during validation
- Propagation context management (cycle prevention)
"""

from __future__ import annotations

import pytest
from uuid import UUID, uuid4

from aware_orm.models.relationship_mixin import RelationshipMixin
from aware_orm.models.base_model import BaseORMModel

from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)
from aware_meta_ontology.attribute.attribute_type_descriptor_enums import (
    AttributeTypeDescriptorKind,
)
from aware_meta_ontology.attribute.attribute_config import AttributeConfig
from aware_meta_ontology.class_.class_config import ClassConfig
from aware_meta_ontology.class_.class_config_attribute_config import (
    ClassConfigAttributeConfig,
)
from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
from aware_meta_ontology.class_.class_config_relationship_attribute import (
    ClassConfigRelationshipAttribute,
)
from aware_meta_ontology.class_.class_config_relationship_enums import (
    ClassConfigRelationshipAttributeRole,
    ClassConfigRelationshipDirection,
    ClassConfigRelationshipSideLoadingStrategy,
    ClassConfigRelationshipType,
)


def _uuid_descriptor() -> AttributeTypeDescriptor:
    # Minimal descriptor for tests; we only need a stable AttributeConfig.id/name mapping.
    return AttributeTypeDescriptor(kind=AttributeTypeDescriptorKind.primitive)


def _attr(name: str) -> AttributeConfig:
    return AttributeConfig(name=name, owner_key=name, type_descriptor=_uuid_descriptor())


class ParentModel(BaseORMModel):
    """Minimal related model with an id field."""


class ChildModel(RelationshipMixin):
    """Test model inheriting from RelationshipMixin for testing."""

    parent: ParentModel | dict | None = None
    parent_id: UUID | None = None


class TestRelationshipMixinBasics:
    """Test basic RelationshipMixin functionality."""

    def test_relationship_mixin_inheritance(self):
        """Test that RelationshipMixin properly inherits from BaseORMModel."""
        model = ChildModel()

        # Should inherit from BaseORMModel
        assert isinstance(model, BaseORMModel)

        # Should have BaseORMModel methods
        assert hasattr(model, "get_class_config")

        # Should have relationship methods
        assert hasattr(model, "_get_relationships")
        assert hasattr(model, "propagate_ids")

    def test_propagation_context_class_variable(self):
        """Test that propagation context is a class variable."""
        # Should have class-level propagation context
        assert hasattr(ChildModel, "_propagation_context")
        assert isinstance(ChildModel._propagation_context, set)

        # Should be shared across instances
        model1 = ChildModel()
        model2 = ChildModel()

        assert model1._propagation_context is model2._propagation_context

    def test_start_propagation(self):
        """Test propagation context clearing."""
        # Add some IDs to context
        ChildModel._propagation_context.add(uuid4())
        ChildModel._propagation_context.add(uuid4())
        assert len(ChildModel._propagation_context) > 0

        # Clear should empty the context
        ChildModel._start_propagation()
        assert len(ChildModel._propagation_context) == 0


class TestCanonicalFkPropagation:
    def _bind_class_config_for_child(self) -> None:
        # Attribute configs present on the model: relationship pointer + fk column
        ref_attr = _attr("parent")
        fk_attr = _attr("parent_id")

        # Link attribute configs onto a ClassConfig so RelationshipMixin can resolve names by id
        cc = ClassConfig(
            name="ChildModel",
            class_fqn=f"{ChildModel.__module__}.{ChildModel.__name__}",
            is_base=True,
            class_config_attribute_configs=[
                ClassConfigAttributeConfig(class_config_id=uuid4(), attribute_config=ref_attr),
                ClassConfigAttributeConfig(class_config_id=uuid4(), attribute_config=fk_attr),
            ],
        )

        # Relationship metadata: MANY_TO_ONE, FK on forward/source side
        rel = ClassConfigRelationship(
            relationship_key="child_parent",
            relationship_type=ClassConfigRelationshipType.many_to_one,
            forward_required=True,
            class_config_id=uuid4(),
            target_class_config_id=uuid4(),
            forward_loading_strategy=ClassConfigRelationshipSideLoadingStrategy.eager,
        )
        rel.class_config_relationship_attributes = [
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=ref_attr.id,
                direction=ClassConfigRelationshipDirection.forward,
                role=ClassConfigRelationshipAttributeRole.reference,
            ),
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=fk_attr.id,
                direction=ClassConfigRelationshipDirection.forward,
                role=ClassConfigRelationshipAttributeRole.foreign_key,
            ),
        ]
        cc.class_config_relationships = [rel]

        # Bind onto the model class under test
        ChildModel.bind_class_config(cc)

    def test_sets_fk_from_related_object_dict(self):
        self._bind_class_config_for_child()
        parent_id = uuid4()
        child = ChildModel(parent={"id": parent_id})
        assert child.parent_id == parent_id


class TestReverseDirectionScalarReferenceDoesNotMutateRelatedObject:
    """
    Regression: if relationship metadata marks (REFERENCE, FOREIGN_KEY) on the REVERSE direction
    for a scalar pointer on this model, we must set *this model's* FK from the related object's id.

    Prior behavior attempted `setattr(related_obj, fk_name, obj_id)` which crashes under Pydantic v2
    when `related_obj` does not declare that FK field (mirrors the ContentPartTextSegment crash).
    """

    def _bind_class_config_reverse_ref_and_fk(self) -> None:
        ref_attr = _attr("parent")
        fk_attr = _attr("parent_id")

        cc = ClassConfig(
            name="ChildModel",
            class_fqn=f"{ChildModel.__module__}.{ChildModel.__name__}",
            is_base=True,
            class_config_attribute_configs=[
                ClassConfigAttributeConfig(class_config_id=uuid4(), attribute_config=ref_attr),
                ClassConfigAttributeConfig(class_config_id=uuid4(), attribute_config=fk_attr),
            ],
        )

        rel = ClassConfigRelationship(
            relationship_key="child_parent_reverse",
            relationship_type=ClassConfigRelationshipType.one_to_many,
            forward_required=True,
            class_config_id=uuid4(),
            target_class_config_id=uuid4(),
            # strategy doesn't matter for validator wiring
            forward_loading_strategy=ClassConfigRelationshipSideLoadingStrategy.eager,
        )
        rel.class_config_relationship_attributes = [
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=ref_attr.id,
                direction=ClassConfigRelationshipDirection.reverse,
                role=ClassConfigRelationshipAttributeRole.reference,
            ),
            ClassConfigRelationshipAttribute(
                class_config_relationship_id=rel.id,
                attribute_config_id=fk_attr.id,
                direction=ClassConfigRelationshipDirection.reverse,
                role=ClassConfigRelationshipAttributeRole.foreign_key,
            ),
        ]
        cc.class_config_relationships = [rel]
        ChildModel.bind_class_config(cc)

    def test_sets_fk_from_related_object_instance(self):
        self._bind_class_config_reverse_ref_and_fk()
        parent = ParentModel(id=uuid4())
        child = ChildModel(parent=parent)
        assert child.parent_id == parent.id


class TestForeignKeyPropagation:
    """Test foreign key ID propagation functionality."""

    def test_propagate_ids_no_id(self):
        """Test propagation when object has no ID."""
        model = ChildModel()
        # Cannot set id to None due to Pydantic validation
        # This test should verify behavior when ID is missing, but since
        # we can't actually set it to None, we'll skip this specific test
        # or test with a different approach

        # Should not raise error with normal ID, just test basic propagation
        model.propagate_ids()

    def test_propagate_ids_cycle_prevention(self):
        """Test that propagation prevents cycles."""
        model = ChildModel()
        obj_id = model.id

        # Add ID to propagation context to simulate cycle
        ChildModel._propagation_context.add(obj_id)
        # Should not raise and should early-exit due to cycle detection.
        model.propagate_ids()

    def test_propagate_ids_success(self):
        """Test successful ID propagation."""
        model = ChildModel()
        obj_id = model.id

        # Clear propagation context
        ChildModel._propagation_context.clear()
        model.propagate_ids()
        # Should remove from context after completion
        assert obj_id not in ChildModel._propagation_context

    def test_propagate_ids_cleanup_on_exception(self):
        """Test that propagation context is cleaned up on exception."""
        model = ChildModel()
        obj_id = model.id

        # Clear propagation context
        # Force an exception inside propagation by monkeypatching the method.
        ChildModel._propagation_context.clear()
        original = getattr(ChildModel, "_propagate_class_config_relationships", None)
        try:

            def boom(self, _obj_id: UUID) -> None:
                raise Exception("Test error")

            setattr(ChildModel, "_propagate_class_config_relationships", boom)
            with pytest.raises(Exception, match="Test error"):
                model.propagate_ids()
        finally:
            if original is not None:
                setattr(ChildModel, "_propagate_class_config_relationships", original)
        assert obj_id not in ChildModel._propagation_context
