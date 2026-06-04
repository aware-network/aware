"""
CRUD Mixin for database operations.

This mixin provides clean, focused CRUD operations that leverage
ClassConfig metadata for SQL generation.
"""

# @doc-ref: ../../docs/models/crud.md
# @test-ref: ../../tests/models/test_crud_mixin.py


from enum import Enum
from typing import Any, TypeVar
from uuid import UUID

from aware_orm._support import logger

# ORM
from aware_orm.sql_generator import SQLGenerator
from aware_orm.helpers import collect_primitive_and_enum_values_fallback
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session import mutation_log


T = TypeVar("T", bound="CRUDMixin")


def _metadata_for_model_class(model_type: type) -> Any | None:
    try:
        from aware_orm.runtime.sql_metadata import get_sql_metadata_for_class

        class_fqn = f"{model_type.__module__}.{model_type.__name__}"
        return get_sql_metadata_for_class(class_fqn)
    except Exception:
        return None


def _sql_metadata_for_model(model_type: type, class_config: Any) -> Any:
    metadata = _metadata_for_model_class(model_type)
    if metadata is not None:
        return metadata
    raise ValueError(
        f"Missing SQL metadata for {model_type.__name__}; "
        "install package-local SQLRuntimeMetadata for the model class FQN"
    )


class CRUDMixin(BaseORMModel):
    """
    Focused mixin for CRUD operations.

    This mixin inherits from BaseORMModel to ensure access to all ORM attributes
    and ClassConfig functionality.

    Responsibilities:
    - Database persistence (push, upsert, delete)
    - SQL generation coordination
    - Error handling for database operations
    - Lifecycle hook integration
    - ClassConfig-aware data collection

    Provides:
    - self.class_config property (from BaseORMModel)
    - self.is_new property (from BaseORMModel)
    - self.mark_persisted() method (from BaseORMModel)
    - self.id property (from BaseORMModel)
    """

    # ==================== Lifecycle Hooks ====================
    async def before_save(self) -> None:
        """Hook called before saving. Override in subclasses."""
        pass

    async def after_save(self) -> None:
        """Hook called after saving. Override in subclasses."""
        pass

    async def before_delete(self) -> None:
        """Hook called before deleting. Override in subclasses."""
        pass

    async def after_delete(self) -> None:
        """Hook called after deleting. Override in subclasses."""
        pass

    # ==================== Core CRUD Operations ====================
    async def push(self) -> None:
        """
        Save instance to database via current session.

        Handles both INSERT (new records) and UPDATE (existing records).
        Enhanced with graceful handling for bootstrap/offline scenarios.
        """
        self.ensure_session()

        # Validate ClassConfig is available (only for database operations)
        class_config = self._class_config
        if not class_config:
            if getattr(self.session, "skip_db", False) is True:
                logger.debug(f"skip_db=True → skipping push for {self.__class__.__name__}")
                return
            raise ValueError(f"No ClassConfig bound to {self.__class__.__name__}")

        # Call lifecycle hook
        await self.before_save()

        # Enforce "mutate self only" if configured
        import os

        enforce = os.getenv("AWARE_PROPAGATION_ENFORCE", "0") == "1"
        if enforce:
            from aware_orm.session.execution_guard import current_mutation_owner

            owner = current_mutation_owner()
            if owner is not None and owner != self.id:
                raise PermissionError(
                    f"Cross-object mutation detected: owner={owner} target={self.id}. Call the object's public method instead."
                )

        logger.debug(f"Pushing {self.__class__.__name__} {self.id}")

        # Collect values once
        # !!!! TODO: UPDATE USE CANONICAL CLASS CONFIG RESOLUTION VIA TYPE DESCRIPTOR ONLY.
        values = self._collect_primitive_and_enum_values()
        if not values:
            logger.warning(f"No data to persist for {self.__class__.__name__} {self.id}")
            # still mark persisted to avoid re-entry loops in offline flows
            self.mark_persisted()
            await self.after_save()
            return

        # Check if we're in skip_db mode (bootstrap/offline scenarios)
        if getattr(self.session, "skip_db", False) is True:
            logger.debug("skip_db=True → marking persisted without queuing SQL")
            self.mark_persisted()
            await self.after_save()
            return

        # Resolve table metadata (kernel-lite bindings via SQLRuntimeMetadata).
        sql_metadata = _sql_metadata_for_model(type(self), class_config)

        # Generate and queue SQL
        if self.is_new:
            sql, params = SQLGenerator.generate_insert(sql_metadata, values)
            self.session.add_insert(sql, params)
            logger.debug(f"Queued INSERT for {self.__class__.__name__}")
            # Record mutation for ChangeCollector
            try:
                if self.id is not None and class_config.id is not None:
                    mutation_log.add_pair(class_config.id, self.id)
            except Exception:
                pass
        else:
            sql, params = SQLGenerator.generate_update(sql_metadata, values)
            if params:  # Only queue if there are changes
                self.session.add_update(sql, params)
                logger.debug(f"Queued UPDATE for {self.__class__.__name__}")
                try:
                    if self.id is not None and class_config.id is not None:
                        mutation_log.add_pair(class_config.id, self.id)
                except Exception:
                    pass
            else:
                logger.debug(f"No changes to update for {self.__class__.__name__}")

        # Mark as persisted
        self.mark_persisted()

        # Call lifecycle hook
        await self.after_save()

    async def upsert(self) -> None:
        """
        Upsert (INSERT or UPDATE) this model via the current Session.

        Uses ON CONFLICT DO UPDATE for PostgreSQL.
        """
        self.ensure_session()

        class_config = self._class_config
        if not class_config:
            raise ValueError(f"No ClassConfig bound to {self.__class__.__name__}")

        try:
            await self.before_save()

            values = self._collect_primitive_and_enum_values()
            if not values:
                raise ValueError(f"No data to upsert for {self.__class__.__name__}")

            sql_metadata = _sql_metadata_for_model(type(self), class_config)
            sql, params = SQLGenerator.generate_upsert(sql_metadata, values)
            self.session.add_insert(sql, params)  # UPSERT is technically an INSERT

            self.mark_persisted()
            await self.after_save()

            logger.debug(f"Queued UPSERT for {self.__class__.__name__}")

        except Exception as e:
            logger.error(f"Error upserting {self.__class__.__name__}: {e}")
            raise

    async def delete_via_session(self) -> None:
        """
        Delete this model from the database via the current Session.
        """
        self.ensure_session()

        class_config = self._class_config
        if not class_config:
            raise ValueError(f"No ClassConfig bound to {self.__class__.__name__}")

        try:
            await self.before_delete()

            sql_metadata = _sql_metadata_for_model(type(self), class_config)
            sql, params = SQLGenerator.generate_delete(sql_metadata, self.id)
            self.session.add_delete(sql, params)

            # Remove from session identity map using proper method
            self.session._identity_map.remove(type(self), self.id)

            await self.after_delete()

            logger.debug(f"Queued DELETE for {self.__class__.__name__}")

        except Exception as e:
            logger.error(f"Error deleting {self.__class__.__name__}: {e}")
            raise

    # ==================== ClassConfig-Aware Data Collection ====================
    def _collect_primitive_and_enum_values(self) -> dict[str, Any]:
        """
        ClassConfig-aware primitive value collection.

        Uses ClassConfig metadata to determine which attributes
        should be persisted to the database.
        """
        class_config = self._class_config
        if not class_config:
            logger.warning("No ClassConfig available, using fallback")
            return collect_primitive_and_enum_values_fallback(self)

        # Latest path: use SQL runtime metadata derived from bindings manifest.
        metadata = _metadata_for_model_class(type(self))

        if metadata is None:
            logger.warning(
                "Missing SQL runtime metadata for %s; using fallback collection",
                type(self).__name__,
            )
            return collect_primitive_and_enum_values_fallback(self)

        values = {}
        logger.debug(f"Collecting SQL-mapped values for {self.__class__.__name__}")

        try:
            # Get model data once to properly handle default values
            model_data = None
            if hasattr(self, "model_dump"):
                model_data = self.model_dump(exclude_none=False, exclude_unset=False)
                logger.debug(f"Model data from model_dump: {model_data}")

            virtuals = self.get_virtual_values()
            persisted = set(metadata.persisted_attributes or ())
            persisted.add("id")  # ensure PK is always available for writes

            for attr_name in sorted(persisted):
                column_name = metadata.column_by_attribute.get(attr_name, attr_name)

                if attr_name in virtuals:
                    value = virtuals[attr_name]
                elif model_data is not None:
                    value = model_data.get(attr_name, None)
                else:
                    value = getattr(self, attr_name, None)

                if isinstance(value, UUID):
                    value = str(value)
                elif isinstance(value, Enum):
                    value = value.value

                values[column_name] = value
                logger.debug(f"Collected {column_name} = {value}")

        except Exception as e:
            logger.error(f"Error in ClassConfig value collection: {e}")
            return collect_primitive_and_enum_values_fallback(self)

        # Ensure we have some data
        if not values:
            logger.warning("ClassConfig collection returned empty, using fallback")
            return collect_primitive_and_enum_values_fallback(self)

        # Add virtual attributes
        # NOTE: virtual values are included above when present in metadata.persisted_attributes.
        return values
