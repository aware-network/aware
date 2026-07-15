"""
Smart test configuration that conditionally applies mocks.

This conftest.py detects whether tests are unit tests or integration tests
and only applies mocks for unit tests, allowing integration tests to run
against real implementations.
"""

import importlib.util
import os
from pathlib import Path

import pytest
from unittest.mock import patch
from aware_orm.models.orm_model import ORMModel


_DB_TEST_FILE_NAMES = frozenset(
    {
        "test_ocg_sql_migrations_postgres.py",
        "test_postgres_runtime_ci_proof.py",
        "test_service_query_conformance.py",
    }
)


def _db_test_configured():
    if os.getenv("AWARE_DB_TEST_ADMIN_URL") or os.getenv("AWARE_DB_TEST_URL"):
        return True
    return bool(
        os.getenv("AWARE_DB_TEST_BOOTSTRAP")
        and (os.getenv("AWARE_DB_TEST_BOOTSTRAP_URL") or os.getenv("AWARE_DB_TEST_URL"))
    )


def _db_tests_requested():
    return os.getenv("AWARE_RUN_DB_TESTS") == "1" or _db_test_configured()


def _db_test_path_explicitly_selected(config):
    for arg in config.args:
        path_text = arg.split("::", 1)[0]
        if Path(path_text).name in _DB_TEST_FILE_NAMES:
            return True
    return False


def is_integration_test(request):
    """
    Determine if the current test is an integration test.

    Integration tests are identified by:
    1. Having the @pytest.mark.integration marker
    2. Being in the tests/integration/ directory
    """
    # Check for integration marker
    if request.node.get_closest_marker("integration"):
        return True

    # Check if test is in integration directory
    test_file_path = str(request.node.fspath)
    if "/integration/" in test_file_path or "\\integration\\" in test_file_path:
        return True

    return False


@pytest.fixture(autouse=True)
def conditional_mock_relationships(request):
    """
    Conditionally mock _get_relationships method only for unit tests.

    Integration tests run without mocks to test real functionality.
    """
    if is_integration_test(request):
        # For integration tests, don't apply any mocks
        yield
    else:
        # For unit tests, apply the relationship mocks with create=True to handle missing methods
        # Use create=True for all models to ensure the method exists
        with patch.object(ORMModel, "_get_relationships", return_value=[], create=True):
            yield


@pytest.fixture(autouse=True)
def conditional_mock_class_config_setup(request):
    """
    Conditionally reserve ClassConfig mock setup only for unit tests.

    Integration tests should set up their own ClassConfig bindings properly.
    """
    if is_integration_test(request):
        # For integration tests, don't apply ClassConfig mocks
        yield
    else:
        # For unit tests, we might want to add more comprehensive ClassConfig mocks here.
        # For now, just yield without additional mocks since the relationship mock handles most cases
        yield


# Configure pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test (requires real database)",
    )
    config.addinivalue_line(
        "markers",
        "db: mark test as requiring an external Postgres test database",
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically mark tests in integration directory with integration marker.
    """
    for item in items:
        # Get the test file path
        test_file_path = str(item.fspath)

        # If test is in integration directory, mark it as integration
        if "/integration/" in test_file_path or "\\integration\\" in test_file_path:
            item.add_marker(pytest.mark.integration)

    db_items = [item for item in items if item.get_closest_marker("db")]
    if not db_items:
        return
    if _db_tests_requested() and not _db_test_configured():
        raise pytest.UsageError(
            "AWARE_RUN_DB_TESTS=1 requires AWARE_DB_TEST_ADMIN_URL, "
            "AWARE_DB_TEST_URL, or AWARE_DB_TEST_BOOTSTRAP=1 with "
            "AWARE_DB_TEST_BOOTSTRAP_URL."
        )
    if _db_tests_requested():
        return
    if _db_test_path_explicitly_selected(config):
        raise pytest.UsageError(
            "DB-backed ORM tests require AWARE_RUN_DB_TESTS=1 plus "
            "AWARE_DB_TEST_ADMIN_URL, AWARE_DB_TEST_URL, or bootstrap DB env."
        )
    kept_items = [item for item in items if item not in db_items]
    items[:] = kept_items
    config.hook.pytest_deselected(items=db_items)


# Skip integration tests if testcontainers is not available
def pytest_runtest_setup(item):
    """
    Skip integration tests if required dependencies are not available.
    """
    if item.get_closest_marker("integration"):
        if importlib.util.find_spec("testcontainers") is None:
            pytest.skip("testcontainers not available, skipping integration test")


# Add useful markers for different test types
pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::PendingDeprecationWarning"),
]
