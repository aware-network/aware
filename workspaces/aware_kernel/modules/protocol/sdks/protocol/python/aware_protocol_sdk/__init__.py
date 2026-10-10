from .admission_error import (
    PROTOCOL_TARGET_ADMISSION_ERROR_CONTRACT,
    ProtocolTargetAdmissionError,
)
from .client import ProtocolSdkClient
from .contracts import (
    PROTOCOL_ADMIT_TARGET_OPERATION_REF,
    PROTOCOL_ADMIT_TARGET_PROVIDER_OPERATION_REF,
    PROTOCOL_TARGET_ADMISSION_REQUEST_CONTRACT,
    PROTOCOL_TARGET_ADMISSION_RESULT_CONTRACT,
    ProtocolTargetAdmissionProvider,
    ProtocolTargetAdmissionRequest,
    ProtocolTargetAdmissionResult,
)
from .specification_setup import (
    PROTOCOL_SETUP_SPECIFICATION_OPERATION_REF,
    PROTOCOL_SETUP_SPECIFICATION_PROVIDER_OPERATION_REF,
    ProtocolSpecificationSetupClient,
    ProtocolSpecificationSetupEffect,
    ProtocolSpecificationSetupError,
    ProtocolSpecificationSetupProvider,
    ProtocolSpecificationSetupRequest,
    ProtocolSpecificationSetupResult,
)

__all__ = [
    "PROTOCOL_ADMIT_TARGET_OPERATION_REF",
    "PROTOCOL_ADMIT_TARGET_PROVIDER_OPERATION_REF",
    "PROTOCOL_SETUP_SPECIFICATION_OPERATION_REF",
    "PROTOCOL_SETUP_SPECIFICATION_PROVIDER_OPERATION_REF",
    "PROTOCOL_TARGET_ADMISSION_ERROR_CONTRACT",
    "PROTOCOL_TARGET_ADMISSION_REQUEST_CONTRACT",
    "PROTOCOL_TARGET_ADMISSION_RESULT_CONTRACT",
    "ProtocolSdkClient",
    "ProtocolSpecificationSetupClient",
    "ProtocolSpecificationSetupEffect",
    "ProtocolSpecificationSetupError",
    "ProtocolSpecificationSetupProvider",
    "ProtocolSpecificationSetupRequest",
    "ProtocolSpecificationSetupResult",
    "ProtocolTargetAdmissionError",
    "ProtocolTargetAdmissionProvider",
    "ProtocolTargetAdmissionRequest",
    "ProtocolTargetAdmissionResult",
]

_BOOTSTRAP_EXPORTS = (
    "ProtocolBootstrapAdmission",
    "ProtocolBootstrapClient",
    "ProtocolBootstrapEffect",
    "ProtocolBootstrapError",
    "ProtocolBootstrapErrorEvidence",
    "ProtocolBootstrapFile",
    "ProtocolBootstrapInput",
    "ProtocolBootstrapPlan",
    "ProtocolBootstrapPlanObservation",
    "ProtocolBootstrapRequest",
    "ProtocolBootstrapResult",
    "ProtocolBootstrapValueError",
    "protocol_bootstrap_value_from_json",
    "protocol_bootstrap_value_from_payload",
    "protocol_bootstrap_value_to_json",
    "protocol_bootstrap_value_to_payload",
)
__all__.extend(_BOOTSTRAP_EXPORTS)


def __getattr__(name):
    if name in _BOOTSTRAP_EXPORTS:
        from . import bootstrap

        return getattr(bootstrap, name)
    raise AttributeError(name)
