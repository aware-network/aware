from __future__ import annotations

from collections import defaultdict
from typing import Optional, ClassVar, TypeVar, TYPE_CHECKING
from uuid import UUID

from aware_orm.models.orm_model import ORMModel

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config import ClassConfig

from aware_orm._support import logger

# Type for model classes
T = TypeVar("T", bound=ORMModel)


class ORMModelRegistry:
    """
    Unified registry for ORM Model classes using fully qualified names (FQN) as primary keys.

    Primary Key: module_path.ClassName (e.g., "aware_identity.user.User")

    Phase A (Import Time): Metaclass calls register_class_stub(cls)
    Phase B (Binding Time): External code provides exact FQN for lookup/binding

    Registry determines FQN internally. External users provide exact FQN keys.
    """

    # Singleton instance
    _instance: ClassVar[Optional[ORMModelRegistry]] = None

    # PRIMARY REGISTRY: fully qualified name → class
    _fqn_to_class: ClassVar[dict[str, type[ORMModel]]] = {}

    # CANONICAL (ClassConfig) BINDING STATE: class_config_id → ORM model
    _class_config_id_to_model: ClassVar[dict[UUID, type[ORMModel]]] = {}

    # CONVENIENCE INDEX: class name → list of classes (for collision detection)
    _name_to_classes: ClassVar[dict[str, list[type[ORMModel]]]] = defaultdict(list)

    _initialized: ClassVar[bool] = False

    @classmethod
    def initialize(cls) -> None:
        """Initialize the registry."""
        if cls._initialized:
            return
        cls._initialized = True

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the registry is initialized."""
        return cls._initialized

    @classmethod
    def set_initialized(cls) -> None:
        """Set the registry to initialized."""
        cls._initialized = True

    @classmethod
    def get_fqn_for_class(cls, model_class: type[ORMModel]) -> str:
        # Compute FQN internally
        return f"{model_class.__module__}.{model_class.__name__}"

    @classmethod
    def register_class_stub(cls, model_class: type[ORMModel]) -> str:
        """
        Register a model class during import time (Phase A).

        Registry determines the FQN internally from cls.__module__ + cls.__name__.

        Args:
            model_class: The ORM model class to register

        Returns:
            The computed FQN key
        """
        fqn = cls.get_fqn_for_class(model_class)

        # Register in primary registry
        cls._fqn_to_class[fqn] = model_class

        # Update convenience index
        class_name = model_class.__name__
        # NOTE: `_name_to_classes` may be a plain dict in some long-running test
        # harnesses that snapshot/restore registry state across pytest runs.
        # Use `setdefault` instead of relying on defaultdict semantics.
        cls._name_to_classes.setdefault(class_name, []).append(model_class)

        logger.debug(f"Registered class stub with FQN: {fqn}")
        return fqn

    @classmethod
    def get_class_by_fqn(cls, fqn: str) -> Optional[type[ORMModel]]:
        """
        Get a model class by its exact FQN.

        External users provide the exact FQN key.

        Args:
            fqn: Fully qualified name (e.g., "aware_identity.user.User")

        Returns:
            Model class or None if not found
        """
        return cls._fqn_to_class.get(fqn)

    @classmethod
    def attach_class_config(cls, fqn: str, class_config: "ClassConfig") -> bool:
        """Attach a canonical ClassConfig to a model class using exact FQN."""
        model_class = cls._fqn_to_class.get(fqn)
        if not model_class:
            logger.warning(f"Cannot attach ClassConfig - class not found for FQN: {fqn}")
            return False
        cc_id = getattr(class_config, "id", None)
        if cc_id is None:
            logger.warning(f"Cannot attach ClassConfig - missing id for FQN: {fqn}")
            return False
        cls._class_config_id_to_model[cc_id] = model_class
        logger.debug(f"Attached ClassConfig to {fqn}")
        return True

    @classmethod
    def get_class_by_name(cls, class_name: str) -> Optional[type[ORMModel]]:
        """
        Get a model class by class name alone (convenience method).

        Returns None if multiple classes have the same name.
        """
        classes = cls._name_to_classes.get(class_name, [])
        if len(classes) == 1:
            return classes[0]
        elif len(classes) > 1:
            logger.warning(f"Multiple classes found for name '{class_name}' - use FQN instead")
            return None
        else:
            return None

    @classmethod
    def get_class_by_class_config_id(cls, class_config_id: UUID) -> Optional[type[ORMModel]]:
        """Get a model class by canonical ClassConfig ID."""
        return cls._class_config_id_to_model.get(class_config_id)

    @classmethod
    def clear_registry(cls) -> None:
        """Clear all registries (for testing)."""
        cls._fqn_to_class.clear()
        cls._name_to_classes.clear()
        cls._class_config_id_to_model.clear()

    @classmethod
    def get_all_fqn_to_class(cls) -> dict[str, type[ORMModel]]:
        """Get all FQN to class mappings."""
        return dict(cls._fqn_to_class)

    # --- Snapshot/Restore Utilities for Tests ---
    @classmethod
    def snapshot_state(cls) -> dict[str, object]:
        """
        Take a deep snapshot of the current registry state so tests can
        temporarily clear/modify it and then restore it after.
        """
        # We avoid deepcopy of classes; references are fine. Copy dicts/lists.
        return {
            "initialized": cls._initialized,
            "fqn_to_class": dict(cls._fqn_to_class),
            "name_to_classes": {k: list(v) for k, v in cls._name_to_classes.items()},
            "class_config_id_to_model": dict(cls._class_config_id_to_model),
        }

    @classmethod
    def restore_state(cls, snapshot: dict[str, object]) -> None:
        """
        Restore a previously captured snapshot via snapshot_state().
        Resets bootstrap flags to allow re-import if needed.
        """
        if "initialized" in snapshot:
            cls._initialized = bool(snapshot.get("initialized"))

        cls._fqn_to_class.clear()
        cls._name_to_classes.clear()
        cls._class_config_id_to_model.clear()

        cls._fqn_to_class.update(snapshot.get("fqn_to_class", {}))
        for name, classes in snapshot.get("name_to_classes", {}).items():
            cls._name_to_classes.setdefault(name, []).extend(classes)
        cls._class_config_id_to_model.update(snapshot.get("class_config_id_to_model", {}))

    @classmethod
    def temporary_clear(cls):
        """
        Context manager that snapshots the registry, clears it on enter,
        and restores the snapshot on exit. Useful for tests.
        Usage:
            with ORMModelRegistry.temporary_clear():
                ...  # manipulate registry freely
        """

        class _TemporaryClear:
            def __enter__(self_inner):
                self_inner._snapshot = cls.snapshot_state()
                cls.clear_registry()
                return cls

            def __exit__(self_inner, exc_type, exc, tb):
                cls.restore_state(self_inner._snapshot)
                # Do not suppress exceptions
                return False

        return _TemporaryClear()
