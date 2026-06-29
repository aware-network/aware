"""
Query Mixin for generated-model reads.

The canonical service-consumer rail is QuerySpec-backed:
- User.by_id(uuid)
- User.one(email="alice@example.com")
- User.where(status="active").all()
- User.where(account_id=account_id).match_if_present(region_id=region_id).all()

The older get/get_list/find/count helpers remain compatibility-only until their
callers are migrated. New Service ontology-replica and product service code
should not use them because they can route through generated SQL strings or
implicit eager GraphSQL.
"""

# @doc-ref: ../../docs/graph/query_mixin.md
# @test-ref: ../../tests/graph/test_query_mixin_graph.py

from __future__ import annotations

from dataclasses import replace
from typing import Any, ClassVar, Coroutine, Self
from uuid import UUID

from aware_orm.filters import EqFilter, InFilter, FilterType
from aware_orm.models.base_model import BaseORMModel
from aware_orm.query_builder import ModelQuery, QueryFieldNamespace
from aware_orm.query_spec import QueryPage, QuerySpec
from aware_orm.query.graph_loader import bind_graph_value, extract_graph_list, merge_graph_model
from aware_orm.query.graph_spec import GraphSpec
from aware_orm.sql_generator import SQLGenerator
from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata
from aware_orm.sql_generator.graph_generator_plan import get_graphsql_generator

from aware_orm._support import logger


class QueryMixin(BaseORMModel):
    """
    Mixin that provides convenience query methods for ORM models.

    Service code should use the QuerySpec-backed exact-match helpers and
    ModelQuery builder. The legacy helper block near the bottom of this mixin is
    retained for old runtime callers only.
    """

    f: ClassVar[QueryFieldNamespace] = QueryFieldNamespace()

    # ==================== Core Query Methods ====================

    @classmethod
    def _exact_match_predicates(cls, fields: dict[str, Any]) -> tuple[EqFilter, ...]:
        predicates: list[EqFilter] = []
        for field_name, value in fields.items():
            if not isinstance(field_name, str) or not field_name.strip():
                raise ValueError(f"{cls.__name__}.where() received an empty field name")
            normalized_field_name = field_name.strip()
            if normalized_field_name not in cls.model_fields:
                raise ValueError(
                    f"{cls.__name__}.where() received unknown field "
                    f"{normalized_field_name!r}."
                )
            predicates.append(EqFilter(column=normalized_field_name, value=value))
        return tuple(predicates)

    @classmethod
    def _graph_queries_supported_for_session(cls, session: Any, graph_spec: GraphSpec | None = None) -> bool:
        backend_name = getattr(session, "_backend_name", None)
        if not isinstance(backend_name, str):
            return True
        try:
            (graph_spec or GraphSpec()).validate_backend(backend_name)
            return True
        except Exception:
            return False

    @classmethod
    def _should_use_eager_graph(cls, session: Any, eager: bool, operation: str) -> bool:
        if not eager:
            return False
        if cls._graph_queries_supported_for_session(session):
            return True

        backend_name = getattr(session, "_backend_name", "unknown")
        logger.debug(
            "Eager graph load disabled for %s.%s because backend %s does not support GraphSQL",
            cls.__name__,
            operation,
            backend_name,
        )
        return False

    @classmethod
    def _raise_if_graph_queries_unsupported(cls, session: Any) -> None:
        if cls._graph_queries_supported_for_session(session):
            return
        backend_name = getattr(session, "_backend_name", "unknown")
        raise RuntimeError(
            f"GraphSQL eager loading is not supported for backend {backend_name!r}. "
            "Use eager=False until a backend-specific GraphSQL generator is available."
        )

    @classmethod
    def _hydrate_query_rows(
        cls: type[Self],
        *,
        session: Any,
        rows: list[dict[str, Any]],
        cache_valid: bool,
    ) -> list[Self]:
        instances: list[Self] = []
        for row_data in rows:
            if cache_valid:
                obj_id = row_data.get("id")
                if obj_id:
                    if isinstance(obj_id, str):
                        obj_id = UUID(obj_id)
                    cached = session.imap_get(cls, obj_id)
                    if cached:
                        instances.append(cached)
                        session.log_read(cls, obj_id)
                        continue

            instance = session._deserialize_to_model(cls, row_data)
            session.imap_add(instance)
            if instance.id:
                session.log_read(cls, instance.id)
            instances.append(instance)
        return instances

    @classmethod
    def query(
        cls: type[Self],
        query_spec: QuerySpec | None = None,
        *,
        cache_valid: bool = True,
    ) -> ModelQuery[Self] | Coroutine[Any, Any, list[Self]]:
        """Build a model query, or execute a strict QuerySpec for compatibility."""
        builder: ModelQuery[Self] = ModelQuery(cls, cache_valid=cache_valid)
        if query_spec is None:
            return builder
        return cls._query_spec(query_spec, cache_valid=cache_valid)

    @classmethod
    def where(
        cls: type[Self],
        *,
        cache_valid: bool = True,
        **eq_fields: Any,
    ) -> ModelQuery[Self]:
        """Build an exact-match query for common agent-authored reads."""
        query = ModelQuery(cls, cache_valid=cache_valid)
        predicates = cls._exact_match_predicates(eq_fields)
        return query.where(*predicates) if predicates else query

    @classmethod
    async def one(
        cls: type[Self],
        *,
        cache_valid: bool = True,
        **eq_fields: Any,
    ) -> Self | None:
        """Return the first model matching exact field values."""
        return await cls.where(cache_valid=cache_valid, **eq_fields).first()

    @classmethod
    async def first(
        cls: type[Self],
        *,
        cache_valid: bool = True,
        **eq_fields: Any,
    ) -> Self | None:
        """Alias for one(...) for service code that reads more naturally."""
        return await cls.one(cache_valid=cache_valid, **eq_fields)

    @classmethod
    async def by_id(
        cls: type[Self],
        obj_id: UUID,
        *,
        cache_valid: bool = True,
    ) -> Self | None:
        """Return one model by primary id through the QuerySpec-backed path."""
        return await cls.one(cache_valid=cache_valid, id=obj_id)

    @classmethod
    async def many(
        cls: type[Self],
        *,
        cache_valid: bool = True,
        **eq_fields: Any,
    ) -> list[Self]:
        """Return all models matching exact field values."""
        return await cls.where(cache_valid=cache_valid, **eq_fields).all()

    @classmethod
    async def _query_spec(
        cls: type[Self],
        query_spec: QuerySpec,
        *,
        cache_valid: bool = True,
    ) -> list[Self]:
        """Run a strict QuerySpec against the active session."""
        from aware_orm.session.current_session_ctx import current_session

        session = current_session()
        if not session:
            raise RuntimeError("No active session")
        if session.skip_db:
            logger.debug(f"Skipping query for {cls.__name__}.query() (session.skip_db=True)")
            return []

        sql_runtime_metadata = cls._resolve_sql_runtime()
        source_fqn = getattr(cls, "_registry_key", f"{cls.__module__}.{cls.__name__}")
        rows = await session.execute_query_spec(
            sql_metadata=sql_runtime_metadata,
            query_spec=query_spec,
            source_class_fqn=source_fqn,
            count=False,
        )
        return cls._hydrate_query_rows(session=session, rows=rows, cache_valid=cache_valid)

    @classmethod
    async def count_query(cls: type[Self], query_spec: QuerySpec) -> int:
        """Count rows matching a strict QuerySpec WHERE contract."""
        from aware_orm.session.current_session_ctx import current_session

        session = current_session()
        if not session:
            raise RuntimeError("No active session")
        if session.skip_db:
            logger.debug(f"Skipping query for {cls.__name__}.count_query() (session.skip_db=True)")
            return 0

        sql_runtime_metadata = cls._resolve_sql_runtime()
        source_fqn = getattr(cls, "_registry_key", f"{cls.__module__}.{cls.__name__}")
        rows = await session.execute_query_spec(
            sql_metadata=sql_runtime_metadata,
            query_spec=query_spec,
            source_class_fqn=source_fqn,
            count=True,
        )
        if rows and "count" in rows[0]:
            return int(rows[0]["count"])
        return 0

    @classmethod
    async def first_query(
        cls: type[Self],
        query_spec: QuerySpec,
        *,
        cache_valid: bool = True,
    ) -> Self | None:
        """Return the first row matching a strict QuerySpec, if any."""
        page = query_spec.page
        if page is None:
            first_spec = replace(query_spec, page=QueryPage(limit=1))
        elif page.limit is None or page.limit > 1:
            first_spec = replace(query_spec, page=replace(page, limit=1))
        else:
            first_spec = query_spec
        rows = await cls.query(first_spec, cache_valid=cache_valid)
        return rows[0] if rows else None

    @classmethod
    async def get_by_id(cls: type[Self], obj_id: UUID, cache_valid: bool = True, eager: bool = True) -> Self | None:
        """
        Legacy compatibility helper for UUID lookup.

        New service/product code should use by_id(...), which compiles through
        QuerySpec and cannot implicitly choose eager GraphSQL.

        CRITICAL FIX: Always check identity map FIRST, then apply skip_db protection.
        This ensures skip_db sessions can find objects that were loaded during bootstrap
        but never attempt database operations if objects aren't cached.

        Args:
            obj_id: UUID of the object to find
            cache_valid: Whether to use cached results
            eager: Whether to use graph queries for complete object loading

        Returns:
            Object instance if found, None otherwise
        """
        # Get current session
        from aware_orm.session.current_session_ctx import current_session

        session = current_session()
        if not session:
            logger.error(f"No active session for {cls.__name__}.get_by_id({obj_id})")
            return None

        try:
            # STEP 1: IM-first eager — return cached immediately when available
            if cache_valid:
                cached = session.imap_get(cls, obj_id)
                if cached:
                    session.log_read(cls, obj_id)
                    logger.debug(f"Found {cls.__name__} {obj_id} in identity map (IM-first eager)")
                    # Branch isolation is enforced inside imap_get; return cached unconditionally
                    return cached

            # STEP 2: CRITICAL - Apply skip_db protection AFTER identity map check
            # If object not in identity map AND we're in skip_db mode, return None
            if session.skip_db:
                logger.debug(f"Object {cls.__name__} {obj_id} not in identity map, skipping database (skip_db=True)")
                return None

            # STEP 3: Object not cached and persistence backend available - proceed with queries
            eager = cls._should_use_eager_graph(session, eager, "get_by_id")

            sql_runtime_metadata = cls._resolve_sql_runtime()
            if eager:
                return await cls.get_graph_by_id(
                    obj_id,
                    sql_metadata=sql_runtime_metadata,
                )

            # Use SQLGenerator for consistency with write operations
            sql, params = SQLGenerator.generate_select_by_id(
                sql_metadata=sql_runtime_metadata,
                obj_id=obj_id,
            )

            # Execute with identity map integration
            results = await session.execute_query(sql, *params)
            logger.debug(f"Results: {results}")
            if not results:
                return None

            # Deserialize result into model instance
            instance_data = results[0]
            instance = session._deserialize_to_model(cls, instance_data)

            # Add to identity map and log read
            session.imap_add(instance)
            session.log_read(cls, obj_id)

            return instance

        except PermissionError:
            logger.error(f"PermissionError in {cls.__name__}.get_by_id({obj_id})")
            raise
        except Exception as e:
            logger.error(f"Error in {cls.__name__}.get_by_id({obj_id}): {e}")
            return None

    @classmethod
    def get_by_id_cached(cls: type[Self], obj_id: UUID) -> Self | None:
        """
        Get object by ID from identity map only (never queries persistence).

        This method ONLY checks the session identity map and never hits the database.
        Use this in write/bootstrap paths where DB/Graph reads are not allowed.

        Args:
            obj_id: The object ID to look up

        Returns:
            Model instance if found in identity map, None otherwise
        """
        try:
            # Get current session (if available)
            from aware_orm.session.current_session_ctx import current_session

            session = current_session()
            if not session:
                logger.info(f"No active session for {cls.__name__}.get_by_id_cached({obj_id})")
                return None

            # ONLY check identity map (no database)
            cached = session.imap_get(cls, obj_id)
            if cached:
                logger.debug(f"Retrieved {cls.__name__} {obj_id} from identity map (cache-only)")
                session.log_read(cls, obj_id)
                return cached

            logger.debug(f"Object {cls.__name__} {obj_id} not found in identity map (cache-only)")
            return None

        except Exception as e:
            logger.debug(f"Error in {cls.__name__}.get_by_id_cached({obj_id}): {e}")
            return None

    @classmethod
    def get_by_id_sync(cls: type[Self], obj_id: UUID) -> Self | None:
        """Backward-compatible alias for cache-only identity-map lookup."""
        return cls.get_by_id_cached(obj_id)

    @classmethod
    async def get(
        cls: type[Self],
        field_name: str | None = None,
        field_value: Any | None = None,
        filters: list[FilterType] | None = None,
        cache_valid: bool = True,
        eager: bool = True,
    ) -> Self | None:
        """
        Legacy compatibility helper for single-row string/filter reads.

        New service/product code should use one(...), first(...), or
        where(...).first() so reads compile through QuerySpec.

        Behavior:
        - Always anchor by current session branch_id to ensure branch isolation
        - First find a matching ID via simple filter query (non-eager)
        - Then fetch eagerly via get_by_id() to hydrate relationships

        Args:
            field_name: Field to filter on (optional)
            field_value: Value to match (optional)
            filters: List of FilterType objects (optional)
            cache_valid: Whether to use the identity map (default True)
            eager: Whether to use graph queries for complete object loading (default True)
        Returns:
            A single model instance, or None if not found
        """
        # Get current session
        from aware_orm.session.current_session_ctx import current_session

        session = current_session()
        if not session:
            raise RuntimeError("No active session")

        # ==================== SKIP_DB PROTECTION ====================
        # Check if we're in a skip_db session (bootstrap/offline mode)
        if session.skip_db:
            logger.debug(f"Skipping query for {cls.__name__}.get() (session.skip_db=True)")
            return None

        try:
            # Convert field filter to FilterType if provided
            if field_name is not None and field_value is not None:

                if filters is None:
                    filters = []
                filters = list(filters)  # Make a copy
                filters.append(EqFilter(column=field_name, value=field_value))
            elif field_name is not None or field_value is not None:
                raise ValueError("Both field_name and field_value must be provided together")

            if not filters:
                raise ValueError("Either field_name/field_value or filters must be provided")

            # Anchor by branch_id from current session
            class_config = cls.get_class_config()
            if class_config:
                filters = list(filters)
                filters.append(EqFilter(column="branch_id", value=str(session.branch_id)))

            # Use non-eager list to find ID only (avoid heavy graph twice)
            candidates = await cls.get_list(filters=filters, limit=1, cache_valid=cache_valid, eager=False)
            if not candidates:
                return None

            target = candidates[0]
            if not target.id:
                return None

            # Fetch eagerly by ID for full hydration
            return await cls.get_by_id(target.id, cache_valid=cache_valid, eager=eager)

        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"Error in {cls.__name__}.get(): {e}")
            return None

    @classmethod
    async def get_list(
        cls: type[Self],
        field_name: str | None = None,
        field_value: Any | None = None,
        filters: list[FilterType] | None = None,
        limit: int = 100,
        offset: int = 0,
        cache_valid: bool = True,
        eager: bool = True,
    ) -> list[Self]:
        """
        Legacy compatibility helper for list reads.

        New service/product code should use where(...).all(), many(...), or the
        explicit ModelQuery builder so reads compile through QuerySpec.

        Args:
            field_name: Field to filter on (optional)
            field_value: Value to match (optional)
            filters: List of FilterType objects (optional)
            limit: Maximum number of results (default 100)
            offset: Number of results to skip (default 0)
            cache_valid: Whether to use the identity map (default True)
            eager: Whether to fetch complete object graphs (default True)

        Returns:
            List of model instances matching the criteria (may be empty)
        """
        # Get current session
        from aware_orm.session.current_session_ctx import current_session
        from aware_orm.sql_generator import SQLGenerator

        session = current_session()
        if not session:
            raise RuntimeError("No active session")

        # ==================== SKIP_DB PROTECTION ====================
        # Check if we're in a skip_db session (bootstrap/offline mode)
        if session.skip_db:
            logger.debug(f"Skipping query for {cls.__name__}.get_list() (session.skip_db=True)")
            return []

        sql_runtime_metadata = cls._resolve_sql_runtime()
        if sql_runtime_metadata is None:
            raise ValueError(f"No SQL runtime metadata bound to {cls.__name__}")

        # Use graph query if eager loading is requested and supported by the backend.
        if cls._should_use_eager_graph(session, eager, "get_list"):
            # Convert field filter to FilterType if provided
            if field_name is not None and field_value is not None:
                if filters is None:
                    filters = []
                filters = list(filters)  # Make a copy
                filters.append(EqFilter(column=field_name, value=field_value))
            elif field_name is not None or field_value is not None:
                raise ValueError("Both field_name and field_value must be provided together")

            return await cls.get_graph_list(
                sql_metadata=sql_runtime_metadata,
                filters=filters,
                limit=limit,
                offset=offset,
            )

        try:
            # Get ClassConfig
            class_config = cls.get_class_config()
            if not class_config:
                raise ValueError(f"No ClassConfig bound to {cls.__name__}")

            # Convert field filter to FilterType if provided
            if field_name is not None and field_value is not None:
                if filters is None:
                    filters = []
                filters = list(filters)  # Make a copy
                filters.append(EqFilter(column=field_name, value=field_value))
            elif field_name is not None or field_value is not None:
                raise ValueError("Both field_name and field_value must be provided together")

            # Use SQLGenerator for consistency with write operations
            source_fqn = getattr(cls, "_registry_key", f"{cls.__module__}.{cls.__name__}")

            sql, params = SQLGenerator.generate_select_many(
                sql_metadata=sql_runtime_metadata,
                filters=filters,
                limit=limit,
                offset=offset,
                source_class_fqn=source_fqn,
            )

            # Execute with identity map integration
            results = await session.execute_query(sql, *params)
            instances = []

            for row_data in results:
                if cache_valid:
                    # Check if we already have this in identity map
                    obj_id = row_data.get("id")
                    if obj_id:
                        # Convert string UUID to UUID object if needed
                        if isinstance(obj_id, str):
                            obj_id = UUID(obj_id)

                        cached = session.imap_get(cls, obj_id)
                        if cached:
                            instances.append(cached)
                            session.log_read(cls, obj_id)
                            continue

                # Deserialize new instance
                instance = session._deserialize_to_model(cls, row_data)

                # Add to identity map and track read
                session.imap_add(instance)
                if instance.id:
                    session.log_read(cls, instance.id)

                instances.append(instance)

            return instances

        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"Error in {cls.__name__}.get_list(): {e}")
            return []

    # ==================== Graph Query Methods (New) ====================

    @classmethod
    async def get_graph_by_id(
        cls: type[Self],
        obj_id: UUID,
        *,
        sql_metadata: SQLRuntimeMetadata,
        graph_spec: GraphSpec | None = None,
    ) -> Self | None:
        """
        Get a model instance with complete object graph by ID in a single query.

        This method uses SQL runtime metadata to build a single query that
        returns the complete object graph, eliminating N+1 queries.

        NOTE: skip_db protection is now handled in get_by_id() before this method
        is called, so this method assumes database operations are allowed.

        Args:
            obj_id: The UUID of the object to retrieve

        Returns:
            Model instance with relationships loaded, or None if not found
        """

        # Get current session
        from aware_orm.session.current_session_ctx import current_session

        session = current_session()
        if not session:
            raise RuntimeError("No active session")
        cls._raise_if_graph_queries_unsupported(session)

        # Use GraphSQLGenerator for single round-trip query
        generator = get_graphsql_generator(
            sql_metadata,
            source_class_fqn=cls.get_registry_key(),
            graph_spec=graph_spec,
        )
        sql, params = generator.generate_select_by_id(obj_id)
        logger.info(f"SQL: {sql}")
        logger.info(f"Params: {params}")

        # Execute graph query (skip_db protection handled in get_by_id())
        results = await session.execute_query(sql, *params)
        logger.debug(f"Graph query results: {results}")

        if not results or not results[0]:
            return None

        # Extract JSON graph from result
        graph_data = results[0].get("graph")
        if not graph_data:
            return None

        # Hydrate the complete object graph using identity-map aware factory
        return cls._hydrate_object_graph(graph_data)

    @classmethod
    def _resolve_sql_runtime(
        cls,
    ) -> SQLRuntimeMetadata:
        sql_runtime_metadata = cls.get_sql_runtime_metadata()
        if sql_runtime_metadata is None:
            raise ValueError(f"No SQL runtime metadata bound to {cls.__name__}")
        return sql_runtime_metadata

    @classmethod
    async def get_graph_list(
        cls: type[Self],
        filters: list[FilterType] | None = None,
        limit: int = 100,
        offset: int = 0,
        *,
        sql_metadata: SQLRuntimeMetadata,
        graph_spec: GraphSpec | None = None,
    ) -> list[Self]:
        """
        Get a list of model instances with complete object graphs in a single query.

        This method uses SQL runtime metadata to build a single query that
        returns complete object graphs for all matching records.

        Args:
            filters: List of FilterType objects (optional)
            limit: Maximum number of results (default 100)
            offset: Number of results to skip (default 0)

        Returns:
            List of model instances with relationships loaded
        """
        # Get current session
        from aware_orm.session.current_session_ctx import current_session

        session = current_session()
        if not session:
            raise RuntimeError("No active session")
        cls._raise_if_graph_queries_unsupported(session)

        # ==================== SKIP_DB PROTECTION ====================
        # Check if we're in a skip_db session (bootstrap/offline mode)
        if session.skip_db:
            logger.debug(f"Skipping graph list query for {cls.__name__} (session.skip_db=True)")
            return []

        # Use GraphSQLGenerator for single round-trip query
        generator = get_graphsql_generator(
            sql_metadata,
            source_class_fqn=cls.get_registry_key(),
            graph_spec=graph_spec,
        )
        sql, params = generator.generate_select_many(filters, limit, offset)

        # Execute graph query
        results = await session.execute_query(sql, *params)
        logger.debug(f"Graph list query results: {results}")

        if not results or not results[0]:
            return []

        # Extract JSON graph array from result (guard against empty json_agg)
        graph_array = extract_graph_list(results)

        # Normalize: database may return JSON as text or bytes/memoryview
        try:
            import json as _json

            if isinstance(graph_array, (bytes, bytearray, memoryview)):
                try:
                    graph_array = bytes(graph_array).decode("utf-8")
                except Exception:
                    graph_array = str(graph_array)

            if isinstance(graph_array, str):
                try:
                    graph_array = _json.loads(graph_array)
                except Exception:
                    logger.error("Failed to parse graph array JSON string; returning empty list")
                    return []
        except Exception:
            pass

        if not graph_array:
            return []

        # Hydrate each object graph using identity-map aware factory
        instances = []
        for graph_data in graph_array:
            # Each element may itself be JSON text/bytes
            try:
                if isinstance(graph_data, (bytes, bytearray, memoryview)):
                    try:
                        graph_data = bytes(graph_data).decode("utf-8")
                    except Exception:
                        graph_data = str(graph_data)
                if isinstance(graph_data, str):
                    try:
                        import json as _json

                        graph_data = _json.loads(graph_data)
                    except Exception:
                        logger.error(f"Failed to parse graph element; skipping. Data: {graph_data}")
                        continue
            except Exception:
                pass
            instance = cls._hydrate_object_graph(graph_data)
            if instance:
                instances.append(instance)

        return instances

    @classmethod
    def _from_graph(cls, payload: dict) -> Self | None:
        """
        Create model instance from graph payload, respecting identity-map.

        If an instance with the same ID already exists in the identity-map,
        returns that instance to maintain referential identity.

        Args:
            payload: JSON object data from graph query

        Returns:
            Model instance, reusing existing identity-map entry if available
        """
        from aware_orm.session.current_session_ctx import current_session

        try:
            sess = current_session()
            obj_id = payload.get("id")

            if sess and obj_id:
                # Convert string UUID to UUID object if needed
                if isinstance(obj_id, str):
                    obj_id = UUID(obj_id)

                # Check if we already have this instance in identity-map
                cached = sess.imap_get(cls, obj_id)
                if cached:
                    # Merge graph payload into the cached instance to hydrate relationships
                    try:
                        fresh = cls.model_validate(payload)
                        return merge_graph_model(sess, cached, fresh)
                    except Exception:
                        return cached  # Fallback: return cached if merge fails

            # First sighting → build new instance (will auto-register in identity-map)
            instance = cls.model_validate(payload)
            instance._is_new = False  # Mark as loaded from database
            if sess is not None:
                return bind_graph_value(sess, instance)
            return instance

        except Exception as e:
            logger.error(f"Error creating {cls.__name__} from graph payload: {e}")
            logger.debug(f"Payload was: {payload}")
            return None

    @classmethod
    def _hydrate_object_graph(cls, graph_data: object) -> Self | None:
        """
        Hydrate a complete object graph from JSON data with identity-map awareness.

        Args:
            graph_data: JSON object graph from database (dict, str, bytes, memoryview)

        Returns:
            Hydrated model instance with relationships, or None on error
        """
        import json

        try:
            # Handle asyncpg returning JSON as string or bytes/memoryview
            if isinstance(graph_data, (bytes, bytearray, memoryview)):
                try:
                    graph_data = bytes(graph_data).decode("utf-8")
                except Exception:
                    graph_data = str(graph_data)
            if isinstance(graph_data, str):
                graph_data = json.loads(graph_data)

            # Use identity-map aware factory for canonical instances
            if isinstance(graph_data, dict):
                return cls._from_graph(graph_data)
            else:
                logger.error(f"Graph payload has unexpected type: {type(graph_data)}")
                return None

        except Exception as e:
            logger.error(f"Error hydrating object graph for {cls.__name__}: {e}")
            logger.error(f"Graph data: {graph_data}")
            return None

    # ==================== Legacy Compatibility Methods ====================

    @classmethod
    async def batch_get(cls: type[Self], ids: list[UUID]) -> list[Self]:
        """
        Legacy compatibility helper for multiple ID lookup.

        New service/product code should prefer QuerySpec-backed exact-match or
        builder reads. This helper still routes through get_list/get_by_id.

        Args:
            ids: List of UUIDs to retrieve

        Returns:
            List of model instances (only those found)
        """
        try:
            if not ids:
                return []

            # Use IN filter for batch retrieval
            filters: list[FilterType] = [InFilter(column="id", values=[str(id) for id in ids])]

            return await cls.get_list(filters=filters, limit=len(ids))

        except Exception as e:
            logger.error(f"Error in {cls.__name__}.batch_get(): {e}")

            # Fallback to individual gets
            results = []
            for obj_id in ids:
                entity = await cls.get_by_id(obj_id)
                if entity:
                    results.append(entity)
            return results

    @classmethod
    async def count(cls: type[Self], filters: list[FilterType] | None = None) -> int:
        """
        Legacy compatibility helper for filter-list counts.

        New service/product code should use where(...).count() or
        query().where(...).count().

        Args:
            filters: List of FilterType objects (optional)

        Returns:
            Number of instances matching the filters
        """
        try:
            sql_runtime_metadata = cls._resolve_sql_runtime()

            # Use SQLGenerator for consistency
            source_fqn = getattr(cls, "_registry_key", f"{cls.__module__}.{cls.__name__}")

            sql, params = SQLGenerator.generate_count_query(
                sql_metadata=sql_runtime_metadata,
                filters=filters,
                source_class_fqn=source_fqn,
            )

            # Get current session
            from aware_orm.session.current_session_ctx import current_session

            session = current_session()
            if not session:
                raise RuntimeError("No active session")

            # Execute count query
            results = await session.execute_query(sql, *params)

            if results and "count" in results[0]:
                return int(results[0]["count"])

            return 0

        except Exception as e:
            logger.error(f"Error in {cls.__name__}.count(): {e}")
            return 0

    @classmethod
    async def exists(cls: type[Self], obj_id: UUID) -> bool:
        """
        Legacy compatibility helper for existence checks.

        New service/product code should use by_id(...) is not None, or an
        explicit QuerySpec-backed count when count semantics matter.

        Args:
            obj_id: The UUID to check

        Returns:
            True if the instance exists, False otherwise
        """
        try:
            result = await cls.get_by_id(obj_id)
            return result is not None

        except Exception as e:
            logger.error(f"Error in {cls.__name__}.exists(): {e}")
            return False

    @classmethod
    async def find_by_id(cls: type[Self], obj_id: UUID) -> Self | None:
        """Legacy alias for get_by_id for backward compatibility."""
        return await cls.get_by_id(obj_id)

    @classmethod
    async def find(cls: type[Self], field_name: str | None = None, field_value: Any | None = None) -> Self | None:
        """Legacy string-field helper; use one(...) or where(...).first()."""
        if not field_name or not field_value:
            return None

        # Convert kwargs to filters
        filters: list[FilterType] = []
        filters.append(EqFilter(column=field_name, value=field_value))

        return await cls.get(filters=filters)

    @classmethod
    async def find_all(cls: type[Self], field_name: str | None = None, field_value: Any | None = None) -> list[Self]:
        """Legacy string-field helper; use where(...).all() or many(...)."""
        if not field_name or not field_value:
            return await cls.get_list()

        # Convert kwargs to filters
        filters: list[FilterType] = []
        filters.append(EqFilter(column=field_name, value=field_value))

        return await cls.get_list(filters=filters)
