"""
Query Mixin for generated-model reads.

The canonical service-consumer rail is QuerySpec-backed:
- User.by_id(uuid)
- User.one(email="alice@example.com")
- User.where(status="active").all()
- User.where(account_id=account_id).match_if_present(region_id=region_id).all()
"""

# @doc-ref: ../../docs/graph/query_mixin.md
# @test-ref: ../../tests/graph/test_query_mixin_graph.py

from __future__ import annotations

from dataclasses import replace
from typing import Any, ClassVar, Self
from uuid import UUID

from aware_orm.filters import EqFilter, FilterType
from aware_orm.models.base_model import BaseORMModel
from aware_orm.query_builder import ModelQuery, QueryFieldNamespace
from aware_orm.query_spec import QueryPage, QuerySpec
from aware_orm.query.graph_loader import (
    bind_graph_value,
    extract_graph_list,
    merge_graph_model,
)
from aware_orm.query.graph_spec import GraphSpec
from aware_orm.runtime.sql_metadata import SQLRuntimeMetadata
from aware_orm.sql_generator.graph_generator_plan import get_graphsql_generator

from aware_orm._support import logger


class QueryMixin(BaseORMModel):
    """
    Mixin that provides convenience query methods for ORM models.

    Service code should use the QuerySpec-backed exact-match helpers and
    ModelQuery builder.
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
    def _graph_queries_supported_for_session(
        cls, session: Any, graph_spec: GraphSpec | None = None
    ) -> bool:
        backend_name = getattr(session, "_backend_name", None)
        if not isinstance(backend_name, str):
            return True
        try:
            (graph_spec or GraphSpec()).validate_backend(backend_name)
            return True
        except Exception:
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
        *,
        cache_valid: bool = True,
    ) -> ModelQuery[Self]:
        """Build a generated-model query."""
        return ModelQuery(cls, cache_valid=cache_valid)

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
            logger.debug(
                f"Skipping query for {cls.__name__}.query() (session.skip_db=True)"
            )
            return []

        sql_runtime_metadata = cls._resolve_sql_runtime()
        source_fqn = getattr(cls, "_registry_key", f"{cls.__module__}.{cls.__name__}")
        rows = await session.execute_query_spec(
            sql_metadata=sql_runtime_metadata,
            query_spec=query_spec,
            source_class_fqn=source_fqn,
            count=False,
        )
        return cls._hydrate_query_rows(
            session=session, rows=rows, cache_valid=cache_valid
        )

    @classmethod
    async def count_query(cls: type[Self], query_spec: QuerySpec) -> int:
        """Count rows matching a strict QuerySpec WHERE contract."""
        from aware_orm.session.current_session_ctx import current_session

        session = current_session()
        if not session:
            raise RuntimeError("No active session")
        if session.skip_db:
            logger.debug(
                f"Skipping query for {cls.__name__}.count_query() (session.skip_db=True)"
            )
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
        rows = await cls._query_spec(first_spec, cache_valid=cache_valid)
        return rows[0] if rows else None

    @classmethod
    def by_id_cached(cls: type[Self], obj_id: UUID) -> Self | None:
        """
        Return one object from the identity map only.

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
                logger.info(
                    f"No active session for {cls.__name__}.by_id_cached({obj_id})"
                )
                return None

            # ONLY check identity map (no database)
            cached = session.imap_get(cls, obj_id)
            if cached:
                logger.debug(
                    f"Retrieved {cls.__name__} {obj_id} from identity map (cache-only)"
                )
                session.log_read(cls, obj_id)
                return cached

            logger.debug(
                f"Object {cls.__name__} {obj_id} not found in identity map (cache-only)"
            )
            return None

        except Exception as e:
            logger.debug(f"Error in {cls.__name__}.by_id_cached({obj_id}): {e}")
            return None

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

        # Execute graph query.
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
            logger.debug(
                f"Skipping graph list query for {cls.__name__} (session.skip_db=True)"
            )
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
                    logger.error(
                        "Failed to parse graph array JSON string; returning empty list"
                    )
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
                        logger.error(
                            f"Failed to parse graph element; skipping. Data: {graph_data}"
                        )
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
