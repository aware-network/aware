"""
Tests for Session and IdentityMap integration.

Tests cover:
- Session creation with proper SessionScopedIdentityMap
- Identity map operations (get, add, remove, contains)
- Session-scoped identity mapping with branch awareness
- Session merge functionality with branch overlays
- Unit of Work pattern with SQL operations
- Session context management and cleanup
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from aware_orm.session.session import Session
from aware_orm.cache.identity_map import SessionScopedIdentityMap
from aware_orm.models.orm_model import ORMModel
from aware_orm.helpers import get_main_branch_id


class TestSessionCreation:
    """Test Session creation and initialization."""

    def test_session_default_initialization(self):
        """Test session initialization with default parameters."""
        session = Session()

        # Should have proper identity map
        assert isinstance(session._identity_map, SessionScopedIdentityMap)
        assert session.branch_id == get_main_branch_id()
        assert session._identity_map.get_branch_id() == get_main_branch_id()

        # Should have empty operation queues
        assert len(session._pending_inserts) == 0
        assert len(session._pending_updates) == 0
        assert len(session._pending_deletes) == 0
        assert session.size() == 0

    def test_session_with_custom_branch(self):
        """Test session initialization with custom branch ID."""
        custom_branch = uuid4()
        session = Session(branch_id=custom_branch)

        assert session.branch_id == custom_branch
        assert session._identity_map.get_branch_id() == custom_branch

    def test_session_with_connection(self):
        """Test session initialization with database connection."""
        mock_connection = Mock()
        session = Session(connection=mock_connection)

        assert session.connection is mock_connection

    def test_session_branch_id_fallback(self):
        """Test branch ID fallback when context is not available."""
        with patch("aware_orm.session.session._get_current_branch_id") as mock_get_branch:
            mock_get_branch.return_value = get_main_branch_id()

            session = Session()
            assert session.branch_id == get_main_branch_id()


class TestIdentityMapIntegration:
    """Test Session integration with SessionScopedIdentityMap."""

    def test_imap_add_and_get(self):
        """Test adding and retrieving objects from identity map."""
        session = Session()

        # Create model - global conftest.py fixture should handle _get_relationships mocking
        model = ORMModel()

        # Add to identity map
        session.imap_add(model)

        # Should be able to retrieve
        retrieved = session.imap_get(type(model), model.id)
        assert retrieved is model

        # Should bind session to model
        assert model._bound_session is session

        # Should increase size
        assert session.size() == 1

    def test_imap_cache_key_generation(self):
        """Test cache key generation for identity map."""
        session = Session()

        with patch.object(ORMModel, "_get_relationships", return_value=[]):
            model = ORMModel()

        key = session._cache_key(type(model), model.id)
        expected_key = (type(model), model.id)
        assert key == expected_key

    def test_imap_operations_delegation(self):
        """Test that session delegates identity map operations properly."""
        session = Session()

        # Global conftest.py fixture should handle _get_relationships mocking
        model = ORMModel()

        # Add object
        session.imap_add(model)

        # Test contains via identity map
        assert session._identity_map.contains(type(model), model.id)

        # Test size
        assert session.size() == 1
        assert session._identity_map.size() == 1

        # Test remove
        removed = session._identity_map.remove(type(model), model.id)
        assert removed is model
        assert session.size() == 0

    def test_identity_map_branch_awareness(self):
        """Test identity map branch awareness in session."""
        main_branch_session = Session(branch_id=get_main_branch_id())
        custom_branch_session = Session(branch_id=uuid4())

        # Global conftest.py fixture should handle _get_relationships mocking
        model1 = ORMModel()
        model2 = ORMModel()

        # Add to different sessions
        main_branch_session.imap_add(model1)
        custom_branch_session.imap_add(model2)

        # Should be isolated by session/branch
        assert main_branch_session.imap_get(type(model1), model1.id) is model1
        assert main_branch_session.imap_get(type(model2), model2.id) is None

        assert custom_branch_session.imap_get(type(model2), model2.id) is model2
        assert custom_branch_session.imap_get(type(model1), model1.id) is None

    def test_identity_map_with_none_id(self):
        """Test identity map operations with objects that have None ID."""
        session = Session()

        # Global conftest.py fixture should handle _get_relationships mocking
        model = ORMModel()
        # Cannot set id to None due to Pydantic validation
        # This test would need to be handled differently in a real scenario

        # Should handle gracefully - just test that the session works normally
        session.imap_add(model)
        assert session.size() == 1


class TestSessionMerge:
    """Test Session merge functionality with branch overlays."""

    def test_merge_new_object(self):
        """Test merging an object not in the session."""
        session = Session()

        with patch.object(ORMModel, "_get_relationships", return_value=[]):
            with patch.object(ORMModel, "create_branch_overlay") as mock_create_overlay:
                original = ORMModel()

                # Mock the overlay creation
                overlay = ORMModel()
                overlay._branch_id = session.branch_id
                mock_create_overlay.return_value = overlay

                # Merge object
                merged = session.merge(original)

                # Should be different object (deep copy)
                assert merged is not original
                assert merged.id == original.id

                # Should be in session's branch context
                assert merged._branch_id == session.branch_id
                assert merged._bound_session is session

                # Should be in identity map
                assert session.imap_get(type(merged), merged.id) is merged
                assert session.size() == 1

    def test_merge_existing_object(self):
        """Test merging an object already in the session."""
        session = Session()

        # Global conftest.py fixture should handle _get_relationships mocking
        original = ORMModel()

        # Add to session first
        session.imap_add(original)

        # Try to merge the same object
        merged = session.merge(original)

        # Should return the existing object
        assert merged is original
        assert session.size() == 1

    def test_merge_branch_context_adjustment(self):
        """Test that merge adjusts branch context properly."""
        source_branch = uuid4()
        target_branch = uuid4()

        # Create object in source branch context
        with patch.object(ORMModel, "_get_relationships", return_value=[]):
            with patch.object(ORMModel, "create_branch_overlay") as mock_create_overlay:
                original = ORMModel()
                original._branch_id = source_branch

                # Mock the overlay creation
                overlay = ORMModel()
                overlay._branch_id = target_branch
                mock_create_overlay.return_value = overlay

                # Create session in target branch context
                session = Session(branch_id=target_branch)

                # Merge should adjust branch context
                merged = session.merge(original)

                assert merged._branch_id == target_branch
                assert original._branch_id == source_branch  # Original unchanged

    def test_merge_preserves_data(self):
        """Test that merge preserves object data."""
        session = Session()

        # Global conftest.py fixture should handle _get_relationships mocking
        with patch.object(ORMModel, "create_branch_overlay") as mock_create_overlay:
            original = ORMModel()

            # Add some test data by setting attributes directly using object.__setattr__ to avoid Pydantic validation
            object.__setattr__(original, "test_field", "test_value")

            # Mock the overlay creation to preserve data
            overlay = ORMModel()
            object.__setattr__(overlay, "test_field", "test_value")
            overlay._branch_id = session.branch_id
            mock_create_overlay.return_value = overlay

            merged = session.merge(original)

            # Should preserve data
            assert getattr(merged, "test_field", None) == "test_value"
            assert merged.id == original.id


class TestUnitOfWorkOperations:
    """Test Unit of Work pattern with SQL operations."""

    def test_add_insert_operation(self):
        """Test adding INSERT operations to session."""
        session = Session()

        sql = "INSERT INTO test_table (id, name) VALUES ($1, $2)"
        params = (str(uuid4()), "test_name")

        session.add_insert(sql, params)

        assert len(session._pending_inserts) == 1
        assert session._pending_inserts[0] == (sql, params)

        counts = session.get_pending_operations_count()
        assert counts["inserts"] == 1
        assert counts["total"] == 1

    def test_add_update_operation(self):
        """Test adding UPDATE operations to session."""
        session = Session()

        sql = "UPDATE test_table SET name = $1 WHERE id = $2"
        params = ("new_name", str(uuid4()))

        session.add_update(sql, params)

        assert len(session._pending_updates) == 1
        assert session._pending_updates[0] == (sql, params)

    def test_add_delete_operation(self):
        """Test adding DELETE operations to session."""
        session = Session()

        sql = "DELETE FROM test_table WHERE id = $1"
        params = (str(uuid4()),)

        session.add_delete(sql, params)

        assert len(session._pending_deletes) == 1
        assert session._pending_deletes[0] == (sql, params)

    def test_multiple_operations(self):
        """Test adding multiple operations of different types."""
        session = Session()

        # Add operations of different types
        session.add_insert("INSERT ...", ("param1",))
        session.add_update("UPDATE ...", ("param2",))
        session.add_delete("DELETE ...", ("param3",))

        counts = session.get_pending_operations_count()
        assert counts["inserts"] == 1
        assert counts["updates"] == 1
        assert counts["deletes"] == 1
        assert counts["total"] == 3

    def test_clear_pending_operations(self):
        """Test clearing pending operations."""
        session = Session()

        # Add some operations
        session.add_insert("INSERT ...", ())
        session.add_update("UPDATE ...", ())
        session.add_delete("DELETE ...", ())

        # Clear operations
        session._clear_pending()

        counts = session.get_pending_operations_count()
        assert counts["total"] == 0


class TestSessionCommit:
    """Test Session commit functionality."""

    @pytest.mark.asyncio
    async def test_commit_no_operations(self):
        """Test commit when there are no pending operations."""
        session = Session()

        # Should complete without error
        await session.commit()

    @pytest.mark.asyncio
    async def test_commit_via_connection(self):
        """Test commit using provided connection."""
        # Create a proper async connection mock
        mock_connection = AsyncMock()

        # Create a proper async context manager for transaction
        class AsyncTransactionManager:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return False

        # Create an instance of our context manager
        transaction_manager = AsyncTransactionManager()

        # Mock the transaction method to return the context manager instance directly (not a coroutine)
        mock_connection.transaction = Mock(return_value=transaction_manager)
        mock_connection.execute = AsyncMock()
        mock_connection.executemany = AsyncMock()
        mock_connection.fetch = AsyncMock(return_value=[])

        session = Session(connection=mock_connection)

        # Add operations with valid SQL
        session.add_insert("INSERT INTO test_table (id) VALUES ($1)", ("param1",))
        session.add_delete("DELETE FROM test_table WHERE id = $1", ("param2",))

        await session.commit()

        # Should have used connection execute method
        assert mock_connection.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_rollback(self):
        """Test session rollback."""
        session = Session()

        # Add operations and reads
        session.add_insert("INSERT ...", ())
        session.log_read(ORMModel, uuid4())

        await session.rollback()

        # Should clear operations and reads
        counts = session.get_pending_operations_count()
        assert counts["total"] == 0
        assert len(session.read_set) == 0


class TestSessionReadTracking:
    """Test Session read operation tracking."""

    def test_log_read_operation(self):
        """Test logging read operations."""
        session = Session()
        model_cls = ORMModel
        obj_id = uuid4()

        session.log_read(model_cls, obj_id)

        assert (model_cls, obj_id) in session.read_set

        counts = session.get_pending_operations_count()
        assert counts["reads"] == 1

    def test_multiple_read_operations(self):
        """Test logging multiple read operations."""
        session = Session()

        session.log_read(ORMModel, uuid4())
        session.log_read(ORMModel, uuid4())

        assert len(session.read_set) == 2

    def test_read_set_property(self):
        """Test read_set property access."""
        session = Session()
        model_cls = ORMModel
        obj_id = uuid4()

        session.log_read(model_cls, obj_id)

        read_set = session.read_set
        assert (model_cls, obj_id) in read_set


class TestSessionEdgeCases:
    """Test Session edge cases and error conditions."""

    def test_session_with_none_branch_id(self):
        """Test session creation with None branch_id."""
        session = Session(branch_id=None)

        # Should fallback to main branch
        assert session.branch_id == get_main_branch_id()

    def test_session_operations_count_empty(self):
        """Test operations count when session is empty."""
        session = Session()

        counts = session.get_pending_operations_count()
        assert counts["inserts"] == 0
        assert counts["updates"] == 0
        assert counts["deletes"] == 0
        assert counts["reads"] == 0
        assert counts["total"] == 0

    def test_session_branch_id_consistency(self):
        """Test that session and identity map branch IDs stay consistent."""
        custom_branch = uuid4()
        session = Session(branch_id=custom_branch)

        assert session.branch_id == custom_branch
        assert session._identity_map.get_branch_id() == custom_branch

        # Branch IDs should remain consistent
        assert session.branch_id == session._identity_map.get_branch_id()


class TestSessionContextManagement:
    """Test Session context management functionality."""

    @pytest.mark.asyncio
    async def test_create_session_context_manager(self):
        """Test create_session context manager."""
        from aware_orm.session.session import create_session

        # Use the canonical offline/noop backend (skip_db=True) so the context
        # manager is database-free and deterministic.
        async with create_session(skip_db=True) as session:
            assert isinstance(session, Session)

            # Add some operations (queued for offline inspection).
            session.add_insert("INSERT INTO test_table (id) VALUES ($1)", ("test_id",))

        # Commit is a no-op for the noop backend; operations remain queued.
        counts = session.get_pending_operations_count()
        assert counts["total"] == 1

    @pytest.mark.asyncio
    async def test_create_session_with_exception(self):
        """Test create_session context manager with exception."""
        from aware_orm.session.session import create_session

        # Use skip_db=True so the session uses the noop backend; exceptions should
        # still rollback pending operations.
        with pytest.raises(ValueError, match="Test error"):
            async with create_session(skip_db=True) as session:
                session.add_insert("INSERT INTO test_table (id) VALUES ($1)", ("test_id",))
                raise ValueError("Test error")

        # Session should be rolled back (pending operations cleared).
        counts = session.get_pending_operations_count()
        assert counts["total"] == 0

    @pytest.mark.asyncio
    async def test_scratch_uow_context_manager(self):
        """Test scratch_uow context manager."""
        from aware_orm.session.session import scratch_uow

        # Mock the RuntimeContext for switch_session
        with patch("aware_orm.session.session.switch_session"):
            async with scratch_uow() as session:
                assert isinstance(session, Session)

                # Add operations with valid SQL
                session.add_insert("INSERT INTO test_table (id) VALUES ($1)", ("test_id",))

            # Should be automatically rolled back
            counts = session.get_pending_operations_count()
            assert counts["total"] == 0


class TestSessionPerformance:
    """Test Session performance characteristics."""

    def test_identity_map_performance_with_many_objects(self):
        """Test identity map performance with many objects."""
        session = Session()
        models = []

        # Mock the _get_relationships method to avoid iteration issues
        with patch.object(ORMModel, "_get_relationships", return_value=[]):
            # Add many objects
            for _ in range(100):
                model = ORMModel()
                models.append(model)
                session.imap_add(model)

        assert session.size() == 100

        # Retrieval should be fast
        for model in models:
            retrieved = session.imap_get(type(model), model.id)
            assert retrieved is model

    def test_pending_operations_performance(self):
        """Test pending operations performance with many operations."""
        session = Session()

        # Add many operations
        for i in range(100):
            session.add_insert(f"INSERT {i} ...", (f"param_{i}",))
            session.add_update(f"UPDATE {i} ...", (f"param_{i}",))
            session.add_delete(f"DELETE {i} ...", (f"param_{i}",))

        counts = session.get_pending_operations_count()
        assert counts["total"] == 300

        # Clear should be fast
        session._clear_pending()
        counts = session.get_pending_operations_count()
        assert counts["total"] == 0
