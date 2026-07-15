"""Async messenger utilities for aware-comms duplex connections."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import ClassVar, cast
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from aware_comms.duplex.protocol import (
    DuplexMessageFrame,
    DuplexMessageFrameType,
)

logger = logging.getLogger(__name__)


class DuplexFutureStatus(Enum):
    CREATED = "created"
    RECEIVED_ACK = "received_ack"
    FINISHED_FAILED = "finished_failed"
    FINISHED_SUCCEEDED = "finished_succeeded"


class DuplexFuture(BaseModel):
    """Future used to correlate request/response pairs."""

    connection_id: UUID
    request_id: UUID
    created_at_s: float = Field(default_factory=time.monotonic, exclude=True)
    event: asyncio.Event = Field(default_factory=asyncio.Event, exclude=True)
    result: object | None = None
    exception: Exception | None = None
    status: DuplexFutureStatus = DuplexFutureStatus.CREATED

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    async def wait_for_result(self, timeout: float | None = None) -> object:
        _ = await asyncio.wait_for(self.event.wait(), timeout=timeout)
        if self.exception:
            raise self.exception
        if self.result is None:
            raise ValueError("No result set")
        return self.result

    def set_result(self, result: object) -> None:
        self.result = result
        _ = self.event.set()

    def set_exception(self, exception: Exception) -> None:
        self.exception = exception
        _ = self.event.set()


class DuplexMessenger(BaseModel):
    """Messenger that sends requests and waits for correlated responses."""

    send_data_fn: Callable[[str, UUID], Awaitable[bool]]
    default_timeout: float = 5.0
    pending_futures: dict[UUID, DuplexFuture] = Field(default_factory=dict)

    async def send_request(
        self,
        request_id: UUID,
        request_data: str,
        connection_id: UUID,
        timeout_s: float | None = None,
    ) -> object | None:
        future = DuplexFuture(
            connection_id=connection_id,
            request_id=request_id,
        )
        self.pending_futures[request_id] = future

        try:
            success = await self.send_data_fn(request_data, connection_id)
            if not success:
                raise ConnectionError(f"Failed to send message to {connection_id}")
            timeout = self.default_timeout if timeout_s is None else timeout_s
            return await future.wait_for_result(timeout=timeout)
        except asyncio.TimeoutError as exc:  # pragma: no cover
            # network failure path
            elapsed_ms = int((time.monotonic() - future.created_at_s) * 1000)
            logger.error(
                (
                    "duplex.req.timeout connection_id=%s request_id=%s "
                    "timeout_s=%s elapsed_ms=%s pending=%s"
                ),
                connection_id,
                request_id,
                self.default_timeout if timeout_s is None else timeout_s,
                elapsed_ms,
                len(self.pending_futures),
            )
            _ = self.pending_futures.pop(request_id, None)
            future.set_exception(exc)
            future.status = DuplexFutureStatus.FINISHED_FAILED
            return None
        except Exception as exc:  # pragma: no cover - network failure path
            logger.error(
                ("duplex.req.send_failed connection_id=%s " "request_id=%s error=%s"),
                connection_id,
                request_id,
                str(exc),
            )
            _ = self.pending_futures.pop(request_id, None)
            future.set_exception(exc)
            future.status = DuplexFutureStatus.FINISHED_FAILED
            return None

    async def send_feedback(
        self,
        connection_id: UUID,
        feedback_data: str,
    ) -> bool:
        return await self.send_data_fn(feedback_data, connection_id)

    def pop_future(self, request_id: UUID) -> DuplexFuture:
        future = self.pending_futures.pop(request_id, None)
        if not future:
            raise ValueError(f"No future found for request_id: {request_id}")
        return future

    async def recv(
        self,
        ws_frame: DuplexMessageFrame,
        _data: object,
    ) -> None:
        request_id = ws_frame.request_id
        if request_id is None:
            return

        future = self.pending_futures.get(request_id)
        if not future:
            logger.warning(
                "duplex.req.orphan frame_type=%s request_id=%s pending=%s",
                ws_frame.type.value,
                request_id,
                len(self.pending_futures),
            )
            return

        if ws_frame.type is DuplexMessageFrameType.ACK:
            future.status = DuplexFutureStatus.RECEIVED_ACK
            return

        if ws_frame.type is DuplexMessageFrameType.ERROR:
            message_payload: object = ws_frame.data
            try:
                message_payload = cast(object, json.loads(ws_frame.data))
            except json.JSONDecodeError:
                pass

            if isinstance(message_payload, dict):
                payload_dict = cast(dict[object, object], message_payload)
                message_value = payload_dict.get("message") or payload_dict.get("error")
                message = str(message_value) if message_value is not None else None
            else:
                message = str(message_payload)
            elapsed_ms = int((time.monotonic() - future.created_at_s) * 1000)
            logger.error(
                (
                    "duplex.req.error_frame connection_id=%s request_id=%s "
                    "elapsed_ms=%s error=%s"
                ),
                future.connection_id,
                request_id,
                elapsed_ms,
                message or "unknown error",
            )
            future.set_exception(RuntimeError(message or "unknown error"))
            future.status = DuplexFutureStatus.FINISHED_FAILED
            return

        if ws_frame.type is DuplexMessageFrameType.RESPONSE:
            future = self.pop_future(request_id)
            future.status = DuplexFutureStatus.FINISHED_SUCCEEDED
            elapsed_ms = int((time.monotonic() - future.created_at_s) * 1000)
            logger.debug(
                ("duplex.req.response connection_id=%s request_id=%s " "elapsed_ms=%s"),
                future.connection_id,
                request_id,
                elapsed_ms,
            )
            try:
                payload: object = cast(object, json.loads(ws_frame.data))
            except json.JSONDecodeError:
                payload = ws_frame.data
            if isinstance(payload, dict):
                payload_dict = cast(dict[object, object], payload)
                if "result" in payload_dict:
                    payload = payload_dict["result"]
            future.set_result(cast(object, payload))
            return

        raise ValueError(f"Received unknown message type: {ws_frame.type}")
