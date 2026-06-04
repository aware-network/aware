"""
Relationship Mixin for handling ClassConfig-based relationships.

This mixin provides clean relationship management leveraging
bound `ClassConfig` metadata for relationship discovery and FK propagation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, model_validator

from aware_orm._support import logger

from aware_orm.models.base_model import BaseORMModel

def _token(value: Any) -> str:
    raw = getattr(value, "value", value)
    return str(raw).rsplit(".", 1)[-1].lower()


def _matches(value: Any, expected: str) -> bool:
    return _token(value) == expected


class RelationshipMixin(BaseORMModel):
    """
    Focused mixin for relationship management.

    This mixin inherits from BaseORMModel to ensure access to all ORM attributes
    and ClassConfig binding metadata.

    Responsibilities:
    - Relationship discovery from ClassConfig
    - Lazy loading strategy determination
    - Relationship traversal
    - Foreign key propagation
    - Lazy relationship descriptor setup
    """

    # Propagation context for preventing cycles during relationship traversal
    _propagation_context: ClassVar[set[UUID]] = set()

    @classmethod
    def _attribute_name_by_id(cls) -> dict[UUID, str]:
        """
        Build an `AttributeConfig.id -> AttributeConfig.name` map for the bound ClassConfig.

        This allows FK propagation to work even when relationship attribute instances only
        carry `attribute_config_id` (the canonical schema) rather than a denormalized name.
        """
        cc = cls.get_class_config()
        if cc is None:
            return {}
        out: dict[UUID, str] = {}
        for link in cc.class_config_attribute_configs:
            ac = link.attribute_config
            if ac is None:
                continue
            out[ac.id] = ac.name
        return out

    @classmethod
    def _get_relationships(cls) -> list[Any]:
        """
        Return canonical relationships for this model from the bound ClassConfig.
        """
        cc = cls.get_class_config()
        if cc is None:
            return []
        rels = cc.class_config_relationships
        if not isinstance(rels, list):
            return []
        return [r for r in rels if r is not None]

    @model_validator(mode="before")
    @classmethod
    def set_foreign_keys(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Set foreign key fields based on related objects using bound ClassConfig relationship metadata.

        This validator ensures bidirectional foreign key propagation:

        1. FORWARD relationships (this model has the foreign key):
           - If obj.related_object is set, obj.[source_column] gets automatically set
           - Example: If analytic.metric is set, analytic.metric_id gets set to metric.id

        2. REVERSE relationships (other model has the foreign key):
           - If obj.children_list is set, each child's FK gets set to this object's ID
           - Example: If analytic.metric_list is set, each metric's analytic_id gets set

        First-pass FK resolution happens during model validation. For complex object graphs,
        use propagate_ids() before saving to ensure all relationships are properly connected.
        """
        # Handle None data case
        if data is None:
            logger.error(f"CRITICAL: set_foreign_keys received None data for {cls.__name__}")
            logger.error(
                f"Model fields: {list(cls.model_fields.keys()) if hasattr(cls, 'model_fields') else 'No model_fields'}"
            )
            logger.error("This usually indicates a constructor call with invalid arguments")
            # Return empty dict with defaults applied
            data = {}

        try:
            from aware_orm.session.change_collector import is_change_tracking_hooks_enabled

            if not bool(is_change_tracking_hooks_enabled()):
                if data.get("id") is None:
                    data["id"] = uuid4()
                return data
        except Exception:
            pass

        # Ensure we have an ID available for reverse propagation when callers omit it.
        # This mirrors the default_factory on BaseORMModel.id.
        obj_id = data.get("id")
        if obj_id is None:
            data["id"] = uuid4()
            obj_id = data["id"]

        class_config = cls.get_class_config()
        if class_config is not None:
            logger.debug(f"Processing ClassConfig relationships for {cls.__name__}")
            cls._process_class_config_relationships(data, obj_id)

        return data

    @classmethod
    def _process_class_config_relationships(cls, data: dict[str, Any], obj_id: Optional[UUID]) -> None:
        """
        Process canonical relationships declared on the bound ClassConfig.

        Canonical model:
        - Relationship attributes are represented as `ClassConfigRelationshipAttribute` entries
          keyed by `attribute_config_id` (no denormalized names).
        - Names are resolved via the bound ClassConfig's `class_config_attribute_configs`.
        """
        if obj_id is None:
            return

        # Avoid work when we don't have any relationships or no fields to set.
        relationships = cls._get_relationships()
        if not relationships:
            return

        # Map AttributeConfig.id -> AttributeConfig.name so we can resolve field names.
        name_by_id = cls._attribute_name_by_id()

        for rel in relationships:
            attrs = rel.class_config_relationship_attributes
            if not isinstance(attrs, list) or not attrs:
                continue

            # Helper: pick first matching relationship-attribute id for a (direction, role) pair.
            def pick_attr_id(*, direction: str, role: str) -> UUID | None:
                for ra in attrs:
                    if ra is None:
                        continue
                    if not _matches(ra.direction, direction):
                        continue
                    if not _matches(ra.role, role):
                        continue
                    return ra.attribute_config_id
                return None

            fwd_ref_id = pick_attr_id(
                direction="forward",
                role="reference",
            )
            fwd_fk_id = pick_attr_id(
                direction="forward",
                role="foreign_key",
            )
            rev_ref_id = pick_attr_id(
                direction="reverse",
                role="reference",
            )
            rev_fk_id = pick_attr_id(
                direction="reverse",
                role="foreign_key",
            )

            fwd_ref_name = name_by_id.get(fwd_ref_id) if isinstance(fwd_ref_id, UUID) else None
            fwd_fk_name = name_by_id.get(fwd_fk_id) if isinstance(fwd_fk_id, UUID) else None
            rev_ref_name = name_by_id.get(rev_ref_id) if isinstance(rev_ref_id, UUID) else None
            rev_fk_name = name_by_id.get(rev_fk_id) if isinstance(rev_fk_id, UUID) else None

            # --- Forward FK propagation (this object owns FK) ---
            if isinstance(fwd_ref_name, str) and isinstance(fwd_fk_name, str):
                if fwd_ref_name in data:
                    related_obj = data.get(fwd_ref_name)
                    if related_obj is None:
                        # Preserve explicit FK if present; otherwise allow null.
                        if data.get(fwd_fk_name) is None:
                            data[fwd_fk_name] = None
                        continue

                    # Only set if FK isn't already set.
                    if data.get(fwd_fk_name) is None:
                        if isinstance(related_obj, BaseModel) and hasattr(related_obj, "id"):
                            data[fwd_fk_name] = getattr(related_obj, "id", None)
                        elif isinstance(related_obj, dict) and "id" in related_obj:
                            data[fwd_fk_name] = related_obj.get("id")

            # --- Reverse FK propagation (children own FK) ---
            if isinstance(rev_ref_name, str) and isinstance(rev_fk_name, str):
                value = data.get(rev_ref_name)
                if value is None:
                    # Preserve explicit FK if present; otherwise allow null.
                    if data.get(rev_fk_name) is None:
                        data[rev_fk_name] = None
                    continue

                # If the reverse reference is a collection, propagate this object's id into each child.
                # (Typical ONE_TO_MANY reverse-side behavior when this object is the parent container.)
                if isinstance(value, list):
                    for child in value:
                        if child is None:
                            continue
                        if isinstance(child, BaseModel):
                            # Only assign if the field exists on the child; otherwise skip to avoid
                            # Pydantic "no field" errors when relationship metadata is asymmetric.
                            if hasattr(child, rev_fk_name) and getattr(child, rev_fk_name, None) is None:
                                setattr(child, rev_fk_name, obj_id)
                            else:
                                logger.debug(
                                    "Skipping reverse FK propagation: "
                                    f"{type(child).__name__} has no field {rev_fk_name!r}"
                                )
                        elif isinstance(child, dict):
                            child.setdefault(rev_fk_name, obj_id)
                    continue

                # Otherwise, this is a scalar reference present on *this* model in REVERSE direction
                # (common for ONE_TO_MANY where the child has `parent` + `parent_id` and the canonical
                # relationship is declared on the parent's collection attribute).
                #
                # In this case, set *this object's* FK from the related object's id (do not mutate the related object).
                if data.get(rev_fk_name) is None:
                    if isinstance(value, BaseModel) and hasattr(value, "id"):
                        data[rev_fk_name] = getattr(value, "id", None)
                    elif isinstance(value, dict) and "id" in value:
                        data[rev_fk_name] = value.get("id")

    @classmethod
    def __init_subclass__(cls, **kwargs):
        """
        Initialize subclass with automatic relationship setup.

        This method is called when a subclass of RelationshipMixin is defined.

        Note: lazy relationship descriptors are intentionally not installed here yet.
        The canonical relationship schema represents relationship attributes by
        `attribute_config_id`, which requires resolution through the bound ClassConfig.
        We'll add descriptor installation only once the lazy loader contract is finalized.
        """
        super().__init_subclass__(**kwargs)

    if not TYPE_CHECKING:
        # We put `__getattr__` in a non-TYPE_CHECKING block because otherwise, mypy allows arbitrary attribute access
        def __getattr__(self, name: str):
            """
            If someone does `instance.foo` and there's no real attr,
            but there _is_ a private deferred relationship loader, delegate to it.
            """
            # Check if it's a lazy relationship
            if self._is_field_lazy(name):
                # trigger the private descriptor: getattr(self, "_foo")
                return getattr(self, f"_{name}", None)

            # Fall back to base class behavior
            return super().__getattr__(name)

    @classmethod
    def _start_propagation(cls) -> None:
        """Clear the propagation context to start a fresh propagation."""
        cls._propagation_context.clear()

    @classmethod
    def _is_field_lazy(cls, field_name: str) -> bool:  # Default context
        """
        Check if a field should be loaded lazily based on ClassConfig relationship metadata.

        Args:
            field_name: The field name to check

        Returns:
            True if field should be lazy loaded
        """
        # Defensive default: not lazy.
        cc = cls.get_class_config()
        if cc is None:
            return False

        name_by_id = cls._attribute_name_by_id()
        rels = cls._get_relationships()
        if not rels:
            return False

        for rel in rels:
            attrs = rel.class_config_relationship_attributes
            for ra in attrs:
                if ra is None:
                    continue
                if not _matches(ra.role, "reference"):
                    continue
                attr_id = ra.attribute_config_id
                if not isinstance(attr_id, UUID):
                    continue
                if name_by_id.get(attr_id) != field_name:
                    continue
                if _matches(ra.direction, "forward"):
                    strategy = rel.forward_loading_strategy
                else:
                    strategy = rel.reverse_loading_strategy
                return _matches(strategy or "lazy", "lazy")

        return False

    @classmethod
    def get_loading_strategy(cls, field_name: str) -> str:
        """
        Get the loading strategy for a field from ClassConfig relationship metadata.

        Args:
            field_name: The field name to check

        Returns:
            `eager` or `lazy`.
        """
        # Canonical default is LAZY when unspecified.
        if cls._is_field_lazy(field_name):
            return "lazy"
        return "eager"

    def propagate_ids(self) -> None:
        """
        Propagate foreign key IDs through the relationship graph.

        This ensures all related objects have their foreign keys properly set
        before persistence operations.
        """
        if not self.id:
            logger.warning(f"Cannot propagate IDs for {self.__class__.__name__} without ID")
            return

        obj_id = self.id

        # Use class-level propagation context to prevent cycles
        propagation_context = getattr(self.__class__, "_propagation_context", set())

        if obj_id in propagation_context:
            logger.debug(f"Skipping already processed object {self.__class__.__name__} {obj_id}")
            return

        # Mark this object as processed
        propagation_context.add(obj_id)
        self.__class__._propagation_context = propagation_context

        try:
            logger.debug(f"Propagating IDs for {self.__class__.__name__} {obj_id}")
            self._propagate_class_config_relationships(obj_id)
        finally:
            # Remove from context when done
            if obj_id in propagation_context:
                propagation_context.remove(obj_id)

    def _propagate_class_config_relationships(self, obj_id: UUID) -> None:
        """
        Propagate IDs using canonical ClassConfig relationship metadata.

        This is the instance-level counterpart to the `set_foreign_keys` before-validator:
        it walks the in-memory object graph and ensures FK id fields are populated.
        """
        cls = self.__class__
        rels = cls._get_relationships()
        if not rels:
            return
        name_by_id = cls._attribute_name_by_id()

        for rel in rels:
            attrs = rel.class_config_relationship_attributes
            if not isinstance(attrs, list) or not attrs:
                continue

            def pick_attr_id(*, direction: str, role: str) -> UUID | None:
                for ra in attrs:
                    if ra is None:
                        continue
                    if not _matches(ra.direction, direction):
                        continue
                    if not _matches(ra.role, role):
                        continue
                    return ra.attribute_config_id
                return None

            fwd_ref_id = pick_attr_id(
                direction="forward",
                role="reference",
            )
            fwd_fk_id = pick_attr_id(
                direction="forward",
                role="foreign_key",
            )
            rev_fk_id = pick_attr_id(
                direction="reverse",
                role="foreign_key",
            )

            fwd_ref_name = name_by_id.get(fwd_ref_id) if isinstance(fwd_ref_id, UUID) else None
            fwd_fk_name = name_by_id.get(fwd_fk_id) if isinstance(fwd_fk_id, UUID) else None
            rev_fk_name = name_by_id.get(rev_fk_id) if isinstance(rev_fk_id, UUID) else None

            if not isinstance(fwd_ref_name, str):
                continue

            related = getattr(self, fwd_ref_name, None)
            if related is None:
                continue

            # List → FK lives on children (reverse FK attribute).
            if isinstance(related, list):
                if not isinstance(rev_fk_name, str):
                    continue
                for child in related:
                    if child is None:
                        continue
                    if hasattr(child, rev_fk_name) and getattr(child, rev_fk_name) is None:
                        setattr(child, rev_fk_name, obj_id)
                    if hasattr(child, "propagate_ids"):
                        child.propagate_ids()
                continue

            # Scalar → FK likely lives on this object (forward FK attribute).
            if isinstance(fwd_fk_name, str) and hasattr(self, fwd_fk_name) and getattr(self, fwd_fk_name) is None:
                if isinstance(related, BaseModel) and hasattr(related, "id"):
                    setattr(self, fwd_fk_name, getattr(related, "id", None))
                elif isinstance(related, dict) and "id" in related:
                    setattr(self, fwd_fk_name, related.get("id"))
