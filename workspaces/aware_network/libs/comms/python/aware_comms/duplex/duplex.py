"""Network duplex helpers built on top of the base websocket classes."""

from __future__ import annotations

import logging
from typing import ClassVar, Generic, Self, override
from uuid import UUID, uuid4

from pydantic import ConfigDict, PrivateAttr, model_validator

from aware_comms.duplex.base import DuplexBase, DuplexSide, WRTC_T, WS_T
from aware_comms.duplex.messenger import DuplexMessenger
from aware_comms.duplex.websocket.models import WsMessageFrame, WsMessageFrameType

logger = logging.getLogger(__name__)


class Duplex(DuplexBase[WS_T, WRTC_T], Generic[WS_T, WRTC_T], frozen=False):
    """Duplex helper that understands WsMessageFrame envelopes."""

    side: DuplexSide
    _messenger: DuplexMessenger | None = PrivateAttr(default=None)

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="after")
    def _ensure_messenger(self) -> Self:
        if self._messenger is None:
            self._messenger = DuplexMessenger(send_data_fn=self._send_data)
        return self

    @property
    def messenger(self) -> DuplexMessenger:
        if self._messenger is None:
            raise RuntimeError("Duplex messenger not initialised")
        return self._messenger

    def _build_message(
        self,
        message_type: WsMessageFrameType,
        data_serialized: str,
        request_id: UUID | None = None,
    ) -> WsMessageFrame:
        if message_type is WsMessageFrameType.REQUEST and request_id is None:
            request_id = uuid4()
        return WsMessageFrame(
            type=message_type, data=data_serialized, request_id=request_id
        )

    async def send_request(
        self,
        connection_id: UUID,
        data_serialized: str,
        request_id: UUID | None = None,
        timeout_s: float | None = None,
    ) -> object | None:
        frame = self._build_message(
            message_type=WsMessageFrameType.REQUEST,
            data_serialized=data_serialized,
            request_id=request_id,
        )
        return await self.messenger.send_request(
            request_id=frame.request_id or uuid4(),
            request_data=frame.model_dump_json(),
            connection_id=connection_id,
            timeout_s=timeout_s,
        )

    async def send_notification(
        self, connection_id: UUID, data_serialized: str
    ) -> bool:
        frame = self._build_message(
            message_type=WsMessageFrameType.NOTIFICATION,
            data_serialized=data_serialized,
        )
        return await self.messenger.send_feedback(
            connection_id=connection_id,
            feedback_data=frame.model_dump_json(),
        )

    @override
    async def handle_data(self, connection_id: UUID, data: dict[str, object]) -> None:
        try:
            frame = WsMessageFrame.model_validate(data)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Invalid websocket payload on %s: %s", connection_id, exc)
            return

        if frame.type in (
            WsMessageFrameType.RESPONSE,
            WsMessageFrameType.ACK,
            WsMessageFrameType.ERROR,
        ):
            await self.messenger.recv(frame, data)
        else:
            logger.debug(
                "Ignoring websocket frame type %s from %s (client side has no handler)",
                frame.type,
                connection_id,
            )
