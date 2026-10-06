"""Optional Protocol composition; no import edge from ordinary SPEC sources.

The trusted receiver accepts the actual issuer's descriptor, roots and guard.
It never reads Protocol private state or reconstructs an admission from data.
"""

from collections.abc import Callable
from importlib import import_module

from aware_specification_sdk import SpecificationOperationError

from .provider import SpecificationFsSdkProvider


def provider_from_protocol_selection(selection: object) -> SpecificationFsSdkProvider:
    try:
        protocol = import_module("aware_protocol_fs_adapter")
        consume = protocol.consume_specification_selection
        refusal_type = protocol.SpecificationSelectionError
    except (ImportError, AttributeError) as error:
        raise SpecificationOperationError("protocol_integration_unavailable") from error

    constructed: list[SpecificationFsSdkProvider] = []

    def receiver(
        source_base_fd: int, roots: tuple[str, ...], guard: Callable[[], None]
    ) -> SpecificationFsSdkProvider:
        if constructed or not callable(guard):
            raise SpecificationOperationError("protocol_selection_receiver_invalid")
        provider = SpecificationFsSdkProvider(source_base_fd, roots)
        constructed.append(provider)

        def revalidate() -> None:
            try:
                guard()
            except refusal_type as error:
                raise SpecificationOperationError(
                    f"protocol_selection_refused:{error.code}"
                ) from error

        provider._protocol_guard = revalidate
        provider._protocol_read_only = True
        provider._check_protocol_selection()
        return provider

    try:
        result = consume(selection, receiver)
        if (
            len(constructed) != 1
            or type(result) is not SpecificationFsSdkProvider
            or result is not constructed[0]
        ):
            raise SpecificationOperationError(
                "protocol_selection_factory_result_invalid"
            )
        result._check_protocol_selection()
        return result
    except BaseException as error:
        # The Protocol owner also closes a returned receiver result on its own
        # final refusal. SPEC close is idempotent; failures during the receiver
        # itself still need SPEC-owned cleanup here.
        for provider in constructed:
            try:
                provider.close()
            except BaseException as cleanup_error:  # noqa: BLE001 - preserve the primary refusal during cleanup
                error.add_note(
                    f"source_provider_cleanup_failed:{type(cleanup_error).__name__}"
                )
        if isinstance(error, refusal_type):
            code = getattr(error, "code", "protocol_selection_owner_refusal")
            raise SpecificationOperationError(
                f"protocol_selection_refused:{code}"
            ) from error
        raise
