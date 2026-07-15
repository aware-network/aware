"""Fail-fast validation for ordered Python function signatures."""

from collections.abc import Sequence

from aware_meta.materialization_diagnostics import MaterializationDiagnosticError


PYTHON_REQUIRED_AFTER_DEFAULT_DIAGNOSTIC = (
    "python.function.signature.required_after_default"
)


class PythonSignatureMaterializationError(MaterializationDiagnosticError):
    """Raised when ordered semantic inputs cannot form a Python signature."""

    diagnostic_code = PYTHON_REQUIRED_AFTER_DEFAULT_DIAGNOSTIC

    def __init__(
        self,
        *,
        context: str,
        required_parameter: str,
        preceding_defaulted_parameter: str,
    ) -> None:
        self.function_context = context
        self.required_parameter = required_parameter
        self.preceding_defaulted_parameter = preceding_defaulted_parameter
        super().__init__(
            code=self.diagnostic_code,
            message=(
                f"{self.diagnostic_code}: {context}: required parameter "
                f"{required_parameter!r} follows defaulted parameter "
                f"{preceding_defaulted_parameter!r}; Aware parameter order is canonical"
            ),
            classification="author_action_required",
            phase="python_signature_validation",
            remediation=(
                f"Move {required_parameter!r} before the first defaulted parameter "
                "or give it an explicit default."
            ),
            outputs_applied=False,
            target_language="python",
            symbol=context,
            context={
                "offending_parameter": required_parameter,
                "preceding_defaulted_parameter": preceding_defaulted_parameter,
            },
        )


def validate_python_parameter_default_order(
    *,
    context: str,
    parameters: Sequence[tuple[str, bool]],
) -> None:
    """Reject required parameters that follow a defaulted parameter."""

    preceding_defaulted_parameter: str | None = None
    for name, has_default in parameters:
        if has_default:
            preceding_defaulted_parameter = name
            continue
        if preceding_defaulted_parameter is not None:
            raise PythonSignatureMaterializationError(
                context=context,
                required_parameter=name,
                preceding_defaulted_parameter=preceding_defaulted_parameter,
            )


__all__ = [
    "PYTHON_REQUIRED_AFTER_DEFAULT_DIAGNOSTIC",
    "PythonSignatureMaterializationError",
    "validate_python_parameter_default_order",
]
