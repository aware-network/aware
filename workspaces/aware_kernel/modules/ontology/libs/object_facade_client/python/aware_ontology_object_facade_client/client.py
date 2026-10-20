"""Detached read exchange; transport and witness bytes supply no authority."""

from collections.abc import Callable
from typing import NoReturn, cast

from . import source_read_codec as _read
from . import source_read_wire as _read_wire
from .source_read_codec import (
    _admitted_budget,
)
from .source_read_codec import (
    decode_canonical as _decode_frame,
)
from .source_read_codec import (
    decode_rejection as _decode_rejection,
)
from .source_read_codec import (
    decode_request as _decode_request,
)
from .source_read_codec import (
    match_result as _match_result,
)
from .source_read_wire import (
    REJECTION_CONTRACT,
    RESULT_CONTRACT,
    Rejection,
    Request,
    Result,
)
from .transport import FacadeTransport

# TypedDict validation produces a native dictionary; retain the same owner helper.
_admit_decoded_budget = cast(Callable[[Request], int], _admitted_budget)
_wire_fail = cast(Callable[..., NoReturn], _read._refuse)


async def exchange_read(
    transport: FacadeTransport, request: bytes, /
) -> Result | Rejection:
    """Exchange one prepared generic read frame, without retry or peer admission.

    Invalid requests and insufficient result budgets raise WireError before
    transport dispatch. Results require complete owning correlation validation;
    detached Rejections do not assert a verified caller or peer association.
    Transport errors and cancellation propagate to the owning infrastructure.
    """
    return cast(Result | Rejection, await _exchange_read(transport, request, v2=False))


async def exchange_read_v2(
    transport: FacadeTransport, request: bytes, /
) -> _read_wire.ResultV2 | _read_wire.RejectionV2:
    """Explicit V6 carriage, not a Subject, peer or View-entry admission."""
    return cast(_read_wire.ResultV2 | _read_wire.RejectionV2,
        await _exchange_read(transport, request, v2=True))


async def _exchange_read(
    transport: FacadeTransport, request: bytes, *, v2: bool
) -> Result | Rejection | _read_wire.ResultV2 | _read_wire.RejectionV2:
    # Retain the owning entrances before handing control to the transport.
    decode_request = _read.decode_request_v2 if v2 else _decode_request
    admit_decoded_budget = _admit_decoded_budget
    decode_frame = _decode_frame
    decode_rejection = _read.decode_rejection_v2 if v2 else _decode_rejection
    match_result = _read.match_result_v2 if v2 else _match_result
    result_contract = RESULT_CONTRACT
    rejection_contract = _read_wire.REJECTION_V2_CONTRACT if v2 else REJECTION_CONTRACT
    wire_fail = _wire_fail
    native_type, native_dict, native_str = type, dict, str
    admitted = decode_request(request)
    # The owning Request decoder already validated the complete frame.
    admit_decoded_budget(cast(Request, admitted))

    response = await transport.exchange(request)
    frame = decode_frame(response)
    if native_type(frame) is not native_dict:
        wire_fail("malformed")
    contract = frame.get("contract")
    if native_type(contract) is not native_str:
        wire_fail("malformed")
    if contract == result_contract:
        return match_result(admitted, frame)
    if contract == rejection_contract:
        return decode_rejection(response)
    wire_fail("unsupported_contract")
