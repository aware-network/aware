from __future__ import annotations

from uuid import uuid4

import pytest

from aware_network.network.operation.handlers import build_environment_response
from aware_network.network.operation.validator import (
    validate_polymorphism_and_type_constraints,
)
from aware_network_ontology.network.network_enums import (
    NetworkOperationMessageType,
    NetworkOperationType,
    NetworkRequestStatus,
)
from aware_network_ontology.network.network_operation import NetworkOperation
from aware_network_ontology.network.network_response import NetworkResponse


def test_network_validator_rejects_retired_environment_operation_type() -> None:
    network_operation = NetworkOperation(
        message_type=NetworkOperationMessageType.notification,
        type=NetworkOperationType.environment,
    )

    with pytest.raises(ValueError, match=r"NetworkOperation\(type=environment\) is retired"):
        validate_polymorphism_and_type_constraints(network_operation)


def test_network_validator_rejects_retired_environment_config_operation_type() -> None:
    network_operation = NetworkOperation(
        message_type=NetworkOperationMessageType.notification,
        type=NetworkOperationType.environment_config,
    )

    with pytest.raises(ValueError, match=r"NetworkOperation\(type=environment_config\) is retired"):
        validate_polymorphism_and_type_constraints(network_operation)


def test_network_validator_allows_current_api_type_without_removed_payload_fields() -> None:
    network_operation = NetworkOperation(
        message_type=NetworkOperationMessageType.notification,
        type=NetworkOperationType.api,
    )

    assert validate_polymorphism_and_type_constraints(network_operation) is network_operation


def test_build_environment_response_fails_closed_without_environment_payload() -> None:
    network_response = NetworkResponse(
        id=uuid4(),
        network_request_id=uuid4(),
        status=NetworkRequestStatus.failed,
    )

    with pytest.raises(RuntimeError, match=r"NetworkOperation\(type=environment\) is retired"):
        build_environment_response(network_response=network_response)
