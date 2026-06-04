"""
Smart test configuration that conditionally applies mocks.

This conftest.py detects whether tests are unit tests or integration tests
and only applies mocks for unit tests, allowing integration tests to run
against real implementations.
"""

import pytest
from unittest.mock import patch
from aware_orm.models.orm_model import ORMModel


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


# Skip integration tests if testcontainers is not available
def pytest_runtest_setup(item):
    """
    Skip integration tests if required dependencies are not available.
    """
    if item.get_closest_marker("integration"):
        try:
            import testcontainers
        except ImportError:
            pytest.skip("testcontainers not available, skipping integration test")


# Add useful markers for different test types
pytestmark = [
    pytest.mark.filterwarnings("ignore::DeprecationWarning"),
    pytest.mark.filterwarnings("ignore::PendingDeprecationWarning"),
]
