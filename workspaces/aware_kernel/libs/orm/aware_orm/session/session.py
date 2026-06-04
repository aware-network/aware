"""
Session implementation for Unit of Work pattern in ORM operations.

This provides a thin abstraction over database connections to collect SQL operations
and execute them atomically in a single transaction using asyncpg.
"""

# @doc-ref: ../../docs/session/runtime.md
# @test-ref: ../../tests/session/test_backends.py
# @test-ref: ../../tests/test_session_integration.py

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Optional, List, Tuple, TYPE_CHECKING, Type, Dict, TypeVar
from contextlib import asynccontextmanager, contextmanager
from uuid import UUID
import copy

from aware_orm._support import logger
from aware_orm.helpers import get_main_branch_id
from aware_orm.cache.identity_map import SessionScopedIdentityMap
from aware_orm.session.backends import PersistenceBackendProtocol, resolve_backend

if TYPE_CHECKING:
    from aware_orm.models.base_model import BaseORMModel
    from aware_orm.session.backends import SqlitePersistenceConfig

# Type variable for generic model types
T = TypeVar("T", bound="BaseORMModel")


def _get_current_branch_id():
    """Get current branch ID from any available context."""
    try:
        from aware_orm.session.current_session_ctx import current_branch_id

        return current_branch_id()
    except ImportError:
        # Fallback for testing without full runtime context
        return get_main_branch_id()


class Session:
    """
    Unit of Work session for collecting and executing SQL operations atomically.

    This class collects INSERT, UPDATE, and DELETE operations and executes them
    in a single database transaction using asyncpg for direct PostgreSQL connections.

    Also supports executing SELECT queries with result deserialization and maintains
    a session-scoped identity map for ORM objects using the session's branch context.
    """

    connection: Any | None
    skip_db: bool
    sqlite_backend_config: "SqlitePersistenceConfig | None"
    _pending_inserts: list[tuple[str, tuple[Any, ...]]]
    _pending_updates: list[tuple[str, tuple[Any, ...]]]
    _pending_deletes: list[tuple[str, tuple[Any, ...]]]

    def __init__(
        self,
        connection: Optional[Any] = None,
        branch_id: Optional[UUID] = None,
        skip_db: bool = False,
        backend: Optional[PersistenceBackendProtocol] = None,
        backend_name: Optional[str] = None,
        sqlite_backend_config: "SqlitePersistenceConfig | None" = None,
    ):
        """
        Initialize a new session.

        Args:
            connection: Database connection (optional, will create if not provided)
            branch_id: Branch ID for this session (optional, will get from current context)
            skip_db: If True, skip all database operations (offline mode for build-time use)
            backend_name: Optional explicit backend selection.
            sqlite_backend_config: Required when `backend_name="sqlite"`.
        """
        self.connection = connection
        self._branch_id = branch_id or _get_current_branch_id()
        self.skip_db = skip_db
        self.sqlite_backend_config = sqlite_backend_config

        # Use proper SessionScopedIdentityMap instead of manual implementation
        self._identity_map = SessionScopedIdentityMap(branch_id=self._branch_id)

        self._pending_inserts: List[Tuple[str, Tuple[Any, ...]]] = []
        self._pending_updates: List[Tuple[str, Tuple[Any, ...]]] = []
        self._pending_deletes: List[Tuple[str, Tuple[Any, ...]]] = []
        self._read_set: set[Tuple[Any, Any]] = set()  # Track (model_cls, obj_id) pairs
        self._in_transaction = False

        # Persistence backend (defaults to environment selection)
        self._backend: PersistenceBackendProtocol = backend or resolve_backend(self, backend_name=backend_name)
        if backend is not None:
            backend_token = getattr(backend, "name", None)
            if isinstance(backend_token, str) and backend_token.strip():
                setattr(self, "_backend_name", backend_token.strip().lower())

    @property
    def branch_id(self) -> UUID:
        """Get the branch ID for this session."""
        return self._branch_id

    # ---------- Identity map helpers (used by ORMModel) ------------------ #

    def _cache_key(self, cls: type, obj_id: UUID) -> tuple[type, UUID]:
        """Create identity map cache key from (cls, obj_id). Branch is implicit from session."""
        return self._identity_map._cache_key(cls, obj_id)

    def imap_get(self, cls: type[T], obj_id: UUID) -> T | None:
        """Get an object from the session identity map using session's branch context."""
        # 1) Try this session's identity map first
        obj = self._identity_map.get(cls, obj_id)
        if obj:
            obj_branch_id = obj.get_branch_id()
            if obj_branch_id != self._branch_id:
                logger.error(
                    f"Object {cls.__name__} {obj_id} has branch {obj_branch_id} but session branch is {self._branch_id}"
                )
                return None
            return obj
        return None

    def imap_contains(self, cls: type[T], obj_id: UUID) -> bool:
        """Check if an object exists in the session identity map."""
        return bool(self._identity_map.get(cls, obj_id) is not None)

    def imap_remove(self, cls: type[T], obj_id: UUID) -> bool:
        """Remove an object from the session identity map."""
        return bool(self._identity_map.remove(cls, obj_id))

    def imap_add(self, instance: "BaseORMModel") -> None:
        """Add an object to the session identity map using session's branch context."""
        # Canonical contract: a Session is branch-scoped; any instance added to the
        # identity-map must adopt the session branch so reads are deterministic.
        try:
            instance._branch_id = self._branch_id
        except Exception:
            pass
        self._identity_map.add(instance)
        # Track session binding for safety
        instance._bound_session = self

        # If we're executing inside a runtime change-collection scope, treat
        # new instances entering the identity map as "created" changes.
        try:
            from aware_orm.session.change_collector import current_change_collector
        except Exception:
            current_change_collector = None  # type: ignore[assignment]

        if current_change_collector is not None:
            collector = current_change_collector()
            if collector is not None and getattr(instance, "is_new", False):
                collector.record_create(instance)

        logger.debug(
            f"Added {instance.__class__.__name__} {instance.id} to session identity map (branch: {self._branch_id})"
        )

    def merge(self, instance: "BaseORMModel") -> "BaseORMModel":
        """
        Bring an instance into this Session using copy semantics.

        Creates a deep copy of the instance so the original remains bound to its
        original session (or detached), ensuring session isolation.

        The merged instance will be associated with this session's branch context.

        Args:
            instance: The BaseORMModel instance to merge

        Returns:
            A copy of the instance managed by this session
        """
        # Check if we already have this object in our branch context
        existing = self._identity_map.get(type(instance), instance.id)
        if existing:
            logger.debug(
                f"Object {instance.__class__.__name__} {instance.id} already in session (branch: {self._branch_id})"
            )
            return existing

        # Create a deep copy to ensure session isolation
        managed_copy = copy.deepcopy(instance)

        # Set the copy's branch to this session's branch
        managed_copy._branch_id = self._branch_id

        # Add to our identity map
        self._identity_map.add(managed_copy)
        managed_copy._bound_session = self

        logger.debug(
            f"Merged {instance.__class__.__name__} {instance.id} into session (branch: {self._branch_id}, copy)"
        )
        return managed_copy

    def log_read(self, model_cls, obj_id):
        """Log a read operation for tracking purposes."""
        self._read_set.add((model_cls, obj_id))

    @property
    def read_set(self):
        """Get the set of read operations (model_cls, obj_id) pairs."""
        return self._read_set

    def size(self) -> int:
        """Get the number of objects in the identity map."""
        return self._identity_map.size()

    def imap_all_objects(self) -> list["BaseORMModel"]:
        """Return all ORM objects currently present in this Session's identity map."""
        return self._identity_map.get_all_objects()

    # ---------- SQL Operation Collection ------------------ #

    def add_insert(self, sql: str, params: Tuple[Any, ...]) -> None:
        """Add an INSERT operation to the session."""
        self._backend.enqueue_insert(sql, params)

    def add_update(self, sql: str, params: Tuple[Any, ...]) -> None:
        """Add an UPDATE operation to the session."""
        self._backend.enqueue_update(sql, params)

    def add_delete(self, sql: str, params: Tuple[Any, ...]) -> None:
        """Add a DELETE operation to the session."""
        self._backend.enqueue_delete(sql, params)

    @abstractmethod
    def model_copy(self, **kwargs) -> "Session":
        """Create a copy of the session."""
        pass

    # ---------- Query Execution Methods ------------------ #

    def _ensure_reads_allowed(self) -> None:
        try:
            from aware_orm.session.execution_guard import current_execution_mode

            if current_execution_mode() == "write":
                raise PermissionError(
                    "DB/GraphSQL reads are not allowed during write execution. "
                    "Use OIG(pre) state, commit reads, or a service-owned read model instead."
                )
        except PermissionError:
            raise
        except Exception:
            # Guardrail is best-effort; default to legacy behavior when unavailable.
            pass

    async def execute_query(self, sql: str, *params) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dictionaries.

        Args:
            sql: SQL query string
            *params: Query parameters

        Returns:
            List of dictionaries representing query results
        """
        self._ensure_reads_allowed()
        return await self._backend.execute_read(sql, params)

    async def execute_query_spec(
        self,
        *,
        sql_metadata: Any,
        query_spec: Any,
        source_class_fqn: str | None = None,
        count: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Execute the public QuerySpec contract through this session.

        Backends may implement a structured `execute_query_spec(...)` hook. When
        absent, the ORM falls back to SQL generation and normal read execution.
        """
        self._ensure_reads_allowed()
        backend_query_spec = getattr(self._backend, "execute_query_spec", None)
        if callable(backend_query_spec):
            return await backend_query_spec(
                sql_metadata=sql_metadata,
                query_spec=query_spec,
                source_class_fqn=source_class_fqn,
                count=count,
            )

        from aware_orm.sql_generator import SQLGenerator

        if count:
            sql, params = SQLGenerator.generate_count_for_spec(
                sql_metadata=sql_metadata,
                query_spec=query_spec,
                source_class_fqn=source_class_fqn,
            )
        else:
            sql, params = SQLGenerator.generate_select_for_spec(
                sql_metadata=sql_metadata,
                query_spec=query_spec,
                source_class_fqn=source_class_fqn,
            )
        return await self._backend.execute_read(sql, params)

    def _deserialize_to_model(self, model_class: Type[T], row_data: Dict[str, Any]) -> T:
        """
        Deserialize a database row to a model instance.

        Args:
            model_class: The model class to create
            row_data: Dictionary of column values from database

        Returns:
            Model instance with data from database row
        """
        original_row_data = row_data
        try:
            row_data = self._map_sql_columns_to_attributes(model_class, row_data)

            # Convert any UUIDs from strings
            processed_data = {}
            for key, value in row_data.items():
                if key == "id" and isinstance(value, str):
                    # Convert string UUID to UUID object
                    processed_data[key] = UUID(value)
                elif key.endswith("_id") and isinstance(value, str) and value:
                    # Convert foreign key UUIDs
                    try:
                        processed_data[key] = UUID(value)
                    except (ValueError, TypeError):
                        processed_data[key] = value
                else:
                    processed_data[key] = value

            # Create model instance
            try:
                instance = model_class.model_validate(processed_data)
            except Exception as exc:
                instance = self._fallback_construct_model(
                    model_class=model_class, processed_data=processed_data, exc=exc
                )

            # Set branch context and mark as not new
            instance._branch_id = self._branch_id
            instance._is_new = False
            instance._bound_session = self

            return instance

        except Exception as e:
            logger.error(f"Error deserializing {model_class.__name__} from row data: {e}")
            logger.error(f"Row data: {original_row_data}")
            raise

    @classmethod
    def _fallback_construct_model(cls, *, model_class: Type[T], processed_data: Dict[str, Any], exc: Exception) -> T:
        """Best-effort fallback when strict model validation fails during reads.

        Some generated ORM models declare required relationship fields (e.g. `Actor.identity: Identity`),
        but persistence rows only contain primitive attributes + foreign keys. Runtime pipelines that
        hydrate relationships from OIG(pre) must still be able to construct the owning instance before
        applying edges. When validation fails *only* due to missing non-persisted fields, fall back to
        `model_construct` and let the caller (runtime hydration) populate relationships deterministically.
        """
        try:
            from pydantic import ValidationError
        except Exception:  # pragma: no cover
            raise exc

        if not isinstance(exc, ValidationError):
            raise exc

        try:
            from aware_orm.models.base_model import BaseORMModel
        except Exception:  # pragma: no cover
            BaseORMModel = None  # type: ignore[assignment]

        if BaseORMModel is None or not issubclass(model_class, BaseORMModel):  # type: ignore[arg-type]
            raise exc

        metadata = model_class.get_sql_runtime_metadata()  # type: ignore[attr-defined]
        if metadata is None:
            raise exc

        persisted = set(metadata.persisted_attributes or ())
        persisted.add("id")

        missing_fields: set[str] = set()
        for err in exc.errors():
            if err.get("type") != "missing":
                raise exc
            loc = err.get("loc")
            if not loc:
                raise exc
            field = loc[0]
            if not isinstance(field, str):
                raise exc
            missing_fields.add(field)

        if not missing_fields:
            raise exc

        # Only tolerate missing fields that are not persisted (relationship references, helper lists, etc.).
        if any(field in persisted for field in missing_fields):
            raise exc

        patched = dict(processed_data)
        for field in sorted(missing_fields):
            patched.setdefault(field, None)
        return model_class.model_construct(**patched)  # type: ignore[return-value]

    @staticmethod
    def _map_sql_columns_to_attributes(model_class: Type[T], row_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map persisted SQL column names back to Python attribute names when possible.

        Runtime installs register SQLRuntimeMetadata keyed by class FQN. Write paths
        use `metadata.column_by_attribute` to translate attribute names to SQL columns
        (e.g. `type` → `type_`). Read paths must translate back before validating
        Pydantic models.
        """
        try:
            from aware_orm.models.base_model import BaseORMModel
        except Exception:
            BaseORMModel = None  # type: ignore[assignment]

        if BaseORMModel is None or not issubclass(model_class, BaseORMModel):  # type: ignore[arg-type]
            return row_data

        metadata = model_class.get_sql_runtime_metadata()  # type: ignore[attr-defined]
        if metadata is None:
            return row_data

        inverse: dict[str, str] = {}
        for attr_name, column_name in (metadata.column_by_attribute or {}).items():
            if not column_name:
                continue
            existing = inverse.get(column_name)
            if existing is not None and existing != attr_name:
                raise ValueError(
                    "SQL metadata column mapping collision for "
                    f"{model_class.__module__}.{model_class.__name__}: "
                    f"column={column_name!r} attrs={existing!r},{attr_name!r}"
                )
            inverse[column_name] = attr_name

        if not inverse:
            return row_data

        mapped: dict[str, Any] = {}
        for key, value in row_data.items():
            mapped_key = inverse.get(key)
            if mapped_key is None and "." in key:
                mapped_key = inverse.get(key.rsplit(".", 1)[-1])
            mapped_key = mapped_key or key
            if mapped_key in mapped and mapped[mapped_key] != value:
                raise ValueError(
                    "SQL row contains duplicate mapped keys for "
                    f"{model_class.__module__}.{model_class.__name__}: "
                    f"key={mapped_key!r}"
                )
            mapped[mapped_key] = value
        return mapped

    # ---------- Transaction Management ------------------ #

    async def commit(self) -> None:
        """
        Execute all pending operations in a single transaction.

        Operations are executed in order:
        1. DELETE operations (to avoid FK constraint violations)
        2. INSERT operations
        3. UPDATE operations

        In skip_db mode, this is a no-op (operations remain queued but are not executed).
        """
        await self._backend.commit()

    def _has_pending_operations(self) -> bool:
        """Check if there are any pending operations."""
        return self._backend.has_pending_operations()

    def _clear_pending(self) -> None:
        """Clear all pending operations."""
        self._backend.clear_pending()

    async def rollback(self) -> None:
        """
        Rollback the session by clearing pending operations.

        Note: If operations have already been executed, this won't undo them.
        True rollback requires transaction support at the connection level.
        """
        await self._backend.rollback()
        self._read_set.clear()  # Also clear read tracking
        logger.debug("Session rolled back")

    def get_pending_operations_count(self) -> dict[str, int]:
        """Get count of pending operations by type."""
        backend_counts = self._backend.get_pending_counts()
        return {
            "inserts": backend_counts.get("inserts", 0),
            "updates": backend_counts.get("updates", 0),
            "deletes": backend_counts.get("deletes", 0),
            "reads": len(self._read_set),
            "total": backend_counts.get("inserts", 0)
            + backend_counts.get("updates", 0)
            + backend_counts.get("deletes", 0),
        }

    def get_offline_status(self) -> dict[str, Any]:
        """Get status information for offline sessions."""
        return {
            "skip_db": self.skip_db,
            "identity_map_size": self.size(),
            "pending_operations": self.get_pending_operations_count(),
            "branch_id": str(self._branch_id),
        }


@asynccontextmanager
async def create_session(
    connection=None,
    skip_db=False,
    backend_name: str | None = None,
    sqlite_backend_config: "SqlitePersistenceConfig | None" = None,
):
    """
    Context manager for creating and managing a session.

    Args:
        connection: Optional database connection
        skip_db: If True, create an offline session that skips database operations

    Usage:
        async with create_session() as session:
            # perform operations
            await model.push(session)
            # session is automatically committed

        # For build-time/offline operations:
        async with create_session(skip_db=True) as session:
            # operations are queued but not executed
            await model.push(session)
    """
    session = Session(
        connection,
        skip_db=skip_db,
        backend_name=backend_name,
        sqlite_backend_config=sqlite_backend_config,
    )
    try:
        # Provide a local SessionContext so ORM helpers that rely on current_session()
        # work in tools/tests without orchestrator/runtime or env scopes.
        from aware_orm.session.current_session_ctx import set_session

        with set_session(session):
            yield session
            await session.commit()
    except Exception:
        await session.rollback()
        raise


@contextmanager
def switch_session(new_session: "Session"):
    """
    Temporarily replace the session in the active ORM SessionContext.

    Runtime and host packages can participate by registering their own
    SessionContext variable with `aware_orm.session.current_session_ctx`.

    Usage:
        with switch_session(new_session):
            # code here sees new_session via current_session()
        # outside the 'with', the original session is restored
    """
    from aware_orm.session.current_session_ctx import switch_session_context

    with switch_session_context(new_session):
        yield new_session


@asynccontextmanager
async def scratch_uow():
    """
    Convenience context manager for creating a scratch session for diff operations.

    Creates a fresh Session and switches to it temporarily, ensuring complete
    isolation from the runtime session for operations like cloning and diffing.

    Usage:
        async with scratch_uow():
            # Everything here is sandboxed
            repo_copy = scratch_session.merge(live_repo)
            change = repo_copy.update_from_file_changes()
            # No need to rollback - automatically handled
    """
    async with create_session() as scratch:
        with switch_session(scratch):
            try:
                yield scratch
            finally:
                # Ensure we don't commit any changes to the database
                await scratch.rollback()
