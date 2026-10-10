"""Original Code operation-context validator signature; not an issuer.

Workspace must obtain the original validator instance/method through fixed
bootstrap composition before calling it. Matching this Protocol, accepting a
copied expectation or returning None cannot authenticate a context.
"""
from typing import Protocol, TypeVar

from .retained_admission_interfaces import RetainedSemanticAdmissionExpectation

_Context_contra = TypeVar("_Context_contra", contravariant=True)


class RetainedSemanticOperationContextValidator(Protocol[_Context_contra]):
    def validate_retained_semantic_operation_context(
        self,
        admission: _Context_contra,
        *,
        expected: RetainedSemanticAdmissionExpectation,
    ) -> None:
        """Require original nominal Code context and exact retained expectation.

        Revalidate original host/policy, registration, operation/stage and input
        closure. Repeated validation is allowed; this is not execution admission.
        The concrete context handle and issuer remain Code-owned.
        """
        ...
