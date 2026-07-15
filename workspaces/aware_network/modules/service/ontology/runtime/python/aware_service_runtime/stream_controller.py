from __future__ import annotations

from collections.abc import Mapping
from typing import Final
from uuid import UUID

from aware_service_runtime.contracts import (
    RequestStatus,
    ServiceStreamControlKind,
    ServiceStreamControlRequest,
    ServiceStreamControlResponse,
    ServiceStreamPublisher,
    ServiceStreamSession,
    ServiceStreamSubscriber,
)

_TERMINAL_CONTROL_KINDS: Final[set[ServiceStreamControlKind]] = {
    ServiceStreamControlKind.REJECT_SESSION,
    ServiceStreamControlKind.CANCEL_SESSION,
    ServiceStreamControlKind.CLOSE_SESSION,
}


class InMemoryServiceStreamController(ServiceStreamPublisher, ServiceStreamSubscriber):
    """Small in-memory semantic session/control owner for first consumers."""

    def __init__(self) -> None:
        self._sessions_by_id: dict[UUID, ServiceStreamSession] = {}

    @property
    def sessions(self) -> Mapping[UUID, ServiceStreamSession]:
        return self._sessions_by_id

    def get_session(self, *, session_id: UUID) -> ServiceStreamSession | None:
        return self._sessions_by_id.get(session_id)

    async def open_stream_session(
        self,
        *,
        session: ServiceStreamSession,
    ) -> ServiceStreamControlResponse:
        if session.session_id in self._sessions_by_id:
            return ServiceStreamControlResponse(
                session_id=session.session_id,
                kind=ServiceStreamControlKind.OPEN_SESSION,
                status=RequestStatus.failed,
                error=f"Service stream session already exists: {session.session_id}",
            )
        self._sessions_by_id[session.session_id] = session
        return ServiceStreamControlResponse(
            session_id=session.session_id,
            kind=ServiceStreamControlKind.OPEN_SESSION,
            status=RequestStatus.succeeded,
        )

    async def send_stream_control(
        self,
        *,
        request: ServiceStreamControlRequest,
    ) -> ServiceStreamControlResponse:
        return await self.handle_stream_control(request=request)

    async def handle_stream_control(
        self,
        *,
        request: ServiceStreamControlRequest,
    ) -> ServiceStreamControlResponse:
        if request.kind is ServiceStreamControlKind.OPEN_SESSION:
            return ServiceStreamControlResponse(
                session_id=request.session_id,
                kind=request.kind,
                status=RequestStatus.failed,
                error="Use open_stream_session() for open_session control.",
                detail_payload=request.detail_payload,
            )

        if request.session_id not in self._sessions_by_id:
            return ServiceStreamControlResponse(
                session_id=request.session_id,
                kind=request.kind,
                status=RequestStatus.failed,
                error=f"Unknown service stream session: {request.session_id}",
                detail_payload=request.detail_payload,
            )

        if request.kind in _TERMINAL_CONTROL_KINDS:
            self._sessions_by_id.pop(request.session_id, None)

        return ServiceStreamControlResponse(
            session_id=request.session_id,
            kind=request.kind,
            status=RequestStatus.succeeded,
            detail_payload=request.detail_payload,
        )
