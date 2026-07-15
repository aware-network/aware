from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum
from typing import Any, Protocol

from aware_environment_service_dto.environment.view import (
    EnvironmentNavigatorViewStateV1,
    EnvironmentProcessNavigationItemV1,
    EnvironmentStatusBlockSummaryV1,
    EnvironmentThreadNavigationItemV1,
    ProcessWorkspaceThreadViewStateV1,
    ProcessWorkspaceViewStateV1,
    ThreadLayoutAttachmentViewStateV1,
    ThreadLayoutCandidateViewStateV1,
    ThreadLayoutLaneViewStateV1,
    ThreadLayoutSectionViewStateV1,
    ThreadLayoutViewStateV1,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentRequest,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentResponse,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentStatusRequest,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentStatusResponse,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyAttachment,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyLane,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyLayout,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyProcess,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyRequest,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyResponse,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologySection,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentTopologyThread,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentStatusAuthority,
)
from aware_environment_service_dto.environment.environment import (
    EnvironmentStatusBlock,
)
from pydantic import BaseModel, ConfigDict, Field


class ViewProviderProvenanceV1(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    source_kind: str | None = Field(default="environment_service_api")
    environment_id: str | None = Field(default=None)
    process_id: str | None = Field(default=None)
    thread_id: str | None = Field(default=None)
    branch_id: str | None = Field(default=None)
    projection_hash: str | None = Field(default=None)
    view_ref: str | None = Field(default=None)
    projection_view_key: str | None = Field(default=None)
    state_provider_ref: str | None = Field(default=None)

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class EnvironmentViewsV1ProviderInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    description: DescribeEnvironmentResponse | None = Field(default=None)
    status: DescribeEnvironmentStatusResponse | None = Field(default=None)
    topology: DescribeEnvironmentTopologyResponse | None = Field(default=None)
    selected_process_id: str | None = Field(default=None)
    selected_process_key: str | None = Field(default=None)
    selected_thread_id: str | None = Field(default=None)
    selected_thread_key: str | None = Field(default=None)
    provenance: ViewProviderProvenanceV1 = Field(
        default_factory=ViewProviderProvenanceV1
    )

    def to_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=True)


class _EnvironmentDescribeCapabilityClient(Protocol):
    async def describe_environment(
        self,
        request: DescribeEnvironmentRequest,
    ) -> DescribeEnvironmentResponse: ...


class _EnvironmentStatusCapabilityClient(Protocol):
    async def describe_environment_status(
        self,
        request: DescribeEnvironmentStatusRequest,
    ) -> DescribeEnvironmentStatusResponse: ...


class _EnvironmentTopologyCapabilityClient(Protocol):
    async def describe_environment_topology(
        self,
        request: DescribeEnvironmentTopologyRequest,
    ) -> DescribeEnvironmentTopologyResponse: ...


class _EnvironmentViewApiClient(Protocol):
    @property
    def describe(self) -> _EnvironmentDescribeCapabilityClient: ...

    @property
    def status(self) -> _EnvironmentStatusCapabilityClient: ...

    @property
    def topology(self) -> _EnvironmentTopologyCapabilityClient: ...


class EnvironmentViewGeneratedApiClient(Protocol):
    @property
    def environment(self) -> _EnvironmentViewApiClient: ...


_ENVIRONMENT_MODEL_TYPES_NAMESPACE = {
    "DescribeEnvironmentResponse": DescribeEnvironmentResponse,
    "DescribeEnvironmentStatusResponse": DescribeEnvironmentStatusResponse,
    "DescribeEnvironmentTopologyAttachment": DescribeEnvironmentTopologyAttachment,
    "DescribeEnvironmentTopologyLane": DescribeEnvironmentTopologyLane,
    "DescribeEnvironmentTopologyLayout": DescribeEnvironmentTopologyLayout,
    "DescribeEnvironmentTopologyProcess": DescribeEnvironmentTopologyProcess,
    "DescribeEnvironmentTopologyResponse": DescribeEnvironmentTopologyResponse,
    "DescribeEnvironmentTopologySection": DescribeEnvironmentTopologySection,
    "DescribeEnvironmentTopologyThread": DescribeEnvironmentTopologyThread,
    "EnvironmentStatusAuthority": EnvironmentStatusAuthority,
    "EnvironmentStatusBlock": EnvironmentStatusBlock,
}

ENVIRONMENT_NAVIGATOR_API_VIEW_REF = "environment.navigator"
ENVIRONMENT_NAVIGATOR_PROJECTION_VIEW_KEY = "environment.navigator.v1"
PROCESS_WORKSPACE_API_VIEW_REF = "environment.process_workspace"
PROCESS_WORKSPACE_PROJECTION_VIEW_KEY = "process.workspace.v1"
THREAD_LAYOUT_API_VIEW_REF = "environment.thread_layout"
THREAD_LAYOUT_PROJECTION_VIEW_KEY = "thread.layout.v1"


def _ensure_environment_models_ready() -> None:
    DescribeEnvironmentResponse.model_rebuild(
        _types_namespace=_ENVIRONMENT_MODEL_TYPES_NAMESPACE,
        force=True,
    )
    DescribeEnvironmentTopologyProcess.model_rebuild(
        _types_namespace=_ENVIRONMENT_MODEL_TYPES_NAMESPACE,
        force=True,
    )
    DescribeEnvironmentTopologyAttachment.model_rebuild(
        _types_namespace=_ENVIRONMENT_MODEL_TYPES_NAMESPACE,
        force=True,
    )
    DescribeEnvironmentTopologyLayout.model_rebuild(
        _types_namespace=_ENVIRONMENT_MODEL_TYPES_NAMESPACE,
        force=True,
    )
    DescribeEnvironmentTopologyThread.model_rebuild(
        _types_namespace=_ENVIRONMENT_MODEL_TYPES_NAMESPACE,
        force=True,
    )
    DescribeEnvironmentTopologyResponse.model_rebuild(
        _types_namespace=_ENVIRONMENT_MODEL_TYPES_NAMESPACE,
        force=True,
    )
    EnvironmentStatusBlock.model_rebuild(
        _types_namespace=_ENVIRONMENT_MODEL_TYPES_NAMESPACE,
        force=True,
    )
    DescribeEnvironmentStatusResponse.model_rebuild(
        _types_namespace=_ENVIRONMENT_MODEL_TYPES_NAMESPACE,
        force=True,
    )
    EnvironmentViewsV1ProviderInput.model_rebuild(
        _types_namespace=_ENVIRONMENT_MODEL_TYPES_NAMESPACE,
        force=True,
    )


_ensure_environment_models_ready()


async def environment_views_v1_provider_input_from_api(
    *,
    api_client: EnvironmentViewGeneratedApiClient,
    environment_id: object,
    actor_id: object | None = None,
    process_id: object | None = None,
    thread_id: object | None = None,
    branch_id: object | None = None,
    projection_hash: str | None = None,
    process_key: str | None = None,
    thread_key: str | None = None,
    include_status_blocks: Sequence[str] = (),
) -> EnvironmentViewsV1ProviderInput:
    description = await api_client.environment.describe.describe_environment(
        DescribeEnvironmentRequest(
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
        )
    )
    status = await api_client.environment.status.describe_environment_status(
        DescribeEnvironmentStatusRequest(
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            include_blocks=list(include_status_blocks),
        )
    )
    topology = await api_client.environment.topology.describe_environment_topology(
        DescribeEnvironmentTopologyRequest(
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
            process_key=process_key,
            thread_key=thread_key,
        )
    )
    return EnvironmentViewsV1ProviderInput(
        description=description,
        status=status,
        topology=topology,
        selected_process_id=_optional_text(process_id),
        selected_process_key=process_key,
        selected_thread_id=_optional_text(thread_id),
        selected_thread_key=thread_key,
        provenance=ViewProviderProvenanceV1(
            environment_id=_optional_text(environment_id),
            process_id=_optional_text(process_id),
            thread_id=_optional_text(thread_id),
            branch_id=_optional_text(branch_id),
            projection_hash=projection_hash,
        ),
    )


def environment_views_v1_provider_input(
    provider_context: object,
) -> EnvironmentViewsV1ProviderInput:
    return EnvironmentViewsV1ProviderInput(
        description=_context_value(provider_context, "environment_description"),
        status=_context_value(provider_context, "environment_status"),
        topology=_context_value(provider_context, "environment_topology"),
        selected_process_id=_optional_text(
            _context_value(provider_context, "selected_process_id")
        ),
        selected_process_key=_optional_text(
            _context_value(provider_context, "selected_process_key")
        ),
        selected_thread_id=_optional_text(
            _context_value(provider_context, "selected_thread_id")
        ),
        selected_thread_key=_optional_text(
            _context_value(provider_context, "selected_thread_key")
        ),
        provenance=ViewProviderProvenanceV1.model_validate(
            dict(getattr(provider_context, "provenance", {}) or {})
        ),
    )


def environment_navigator_view_state_from_input(
    provider_input: EnvironmentViewsV1ProviderInput | Mapping[str, Any],
) -> EnvironmentNavigatorViewStateV1:
    typed_input = EnvironmentViewsV1ProviderInput.model_validate(provider_input)
    selection = _resolve_selection(typed_input)
    processes = [
        _process_navigation_item(process, selection=selection)
        for process in _topology_processes(typed_input)
    ]
    return EnvironmentNavigatorViewStateV1(
        environment_id=_environment_id(typed_input),
        title=_environment_title(typed_input),
        status=_view_status(typed_input, materialized=bool(processes)),
        ready=_ready(typed_input),
        selected_process_id=_process_id(selection.process),
        selected_process_key=_optional_text(
            getattr(selection.process, "process_key", None)
        ),
        selected_thread_id=_thread_id(selection.thread),
        selected_thread_key=_optional_text(
            getattr(selection.thread, "thread_key", None)
        ),
        processes=processes,
        status_blocks=_status_blocks(typed_input),
        provenance=_provenance_payload(
            typed_input,
            view_ref=ENVIRONMENT_NAVIGATOR_API_VIEW_REF,
            projection_view_key=ENVIRONMENT_NAVIGATOR_PROJECTION_VIEW_KEY,
            state_provider_ref=(
                "aware_environment_sdk.view_state_providers."
                "environment_navigator_view_state"
            ),
        ),
    )


def environment_navigator_view_state(
    *,
    provider_input: EnvironmentViewsV1ProviderInput | Mapping[str, Any],
) -> EnvironmentNavigatorViewStateV1:
    return environment_navigator_view_state_from_input(provider_input)


def process_workspace_view_state_from_input(
    provider_input: EnvironmentViewsV1ProviderInput | Mapping[str, Any],
) -> ProcessWorkspaceViewStateV1:
    typed_input = EnvironmentViewsV1ProviderInput.model_validate(provider_input)
    selection = _resolve_selection(typed_input)
    process = selection.process
    threads = (
        [
            _process_workspace_thread(thread, selection=selection)
            for thread in list(getattr(process, "threads", []) or [])
        ]
        if process is not None
        else []
    )
    return ProcessWorkspaceViewStateV1(
        environment_id=_environment_id(typed_input),
        process_id=_process_id(process),
        process_key=_optional_text(getattr(process, "process_key", None)),
        title=_optional_text(getattr(process, "title", None)) or "Process",
        description=_optional_text(getattr(process, "description", None)),
        status=_view_status(typed_input, materialized=process is not None),
        selected_thread_id=_thread_id(selection.thread),
        selected_thread_key=_optional_text(
            getattr(selection.thread, "thread_key", None)
        ),
        threads=threads,
        provenance=_provenance_payload(
            typed_input,
            view_ref=PROCESS_WORKSPACE_API_VIEW_REF,
            projection_view_key=PROCESS_WORKSPACE_PROJECTION_VIEW_KEY,
            state_provider_ref=(
                "aware_environment_sdk.view_state_providers."
                "process_workspace_view_state"
            ),
        ),
    )


def process_workspace_view_state(
    *,
    provider_input: EnvironmentViewsV1ProviderInput | Mapping[str, Any],
) -> ProcessWorkspaceViewStateV1:
    return process_workspace_view_state_from_input(provider_input)


def thread_layout_view_state_from_input(
    provider_input: EnvironmentViewsV1ProviderInput | Mapping[str, Any],
) -> ThreadLayoutViewStateV1:
    typed_input = EnvironmentViewsV1ProviderInput.model_validate(provider_input)
    selection = _resolve_selection(typed_input)
    thread = selection.thread
    layouts = (
        [
            _thread_layout_candidate(layout)
            for layout in list(getattr(thread, "layouts", []) or [])
        ]
        if thread is not None
        else []
    )
    active_layout = next((layout for layout in layouts if bool(layout.is_active)), None)
    sections = list(active_layout.sections) if active_layout is not None else []
    attachments = (
        [
            _thread_layout_attachment(attachment)
            for attachment in list(getattr(thread, "attachments", []) or [])
        ]
        if thread is not None
        else []
    )
    return ThreadLayoutViewStateV1(
        environment_id=_environment_id(typed_input),
        process_id=_process_id(selection.process),
        process_key=_optional_text(getattr(selection.process, "process_key", None)),
        thread_id=_thread_id(thread),
        thread_key=_optional_text(getattr(thread, "thread_key", None)),
        title=_optional_text(getattr(thread, "title", None)) or "Thread",
        description=_optional_text(getattr(thread, "description", None)),
        status=_view_status(typed_input, materialized=thread is not None),
        active_layout_id=(
            active_layout.layout_id
            if active_layout is not None
            else _optional_text(getattr(thread, "active_layout_id", None))
        ),
        active_layout_key=(
            active_layout.layout_key
            if active_layout is not None
            else _optional_text(getattr(thread, "active_layout_key", None))
        ),
        layouts=layouts,
        sections=sections,
        attachments=attachments,
        empty_message=(
            "No thread layout available"
            if not layouts
            else "No active layout section available" if not sections else ""
        ),
        provenance=_provenance_payload(
            typed_input,
            view_ref=THREAD_LAYOUT_API_VIEW_REF,
            projection_view_key=THREAD_LAYOUT_PROJECTION_VIEW_KEY,
            state_provider_ref=(
                "aware_environment_sdk.view_state_providers." "thread_layout_view_state"
            ),
            extra={"layout_source": "environment_topology"},
        ),
    )


def thread_layout_view_state(
    *,
    provider_input: EnvironmentViewsV1ProviderInput | Mapping[str, Any],
) -> ThreadLayoutViewStateV1:
    return thread_layout_view_state_from_input(provider_input)


setattr(
    environment_navigator_view_state,
    "provider_input_resolver",
    environment_views_v1_provider_input,
)
setattr(
    process_workspace_view_state,
    "provider_input_resolver",
    environment_views_v1_provider_input,
)
setattr(
    thread_layout_view_state,
    "provider_input_resolver",
    environment_views_v1_provider_input,
)


class _Selection(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    process: DescribeEnvironmentTopologyProcess | None = None
    thread: DescribeEnvironmentTopologyThread | None = None


def _resolve_selection(typed_input: EnvironmentViewsV1ProviderInput) -> _Selection:
    processes = _topology_processes(typed_input)
    process = _select_process(typed_input, processes)
    thread = _select_thread(typed_input, process)
    return _Selection(process=process, thread=thread)


def _select_process(
    typed_input: EnvironmentViewsV1ProviderInput,
    processes: Sequence[DescribeEnvironmentTopologyProcess],
) -> DescribeEnvironmentTopologyProcess | None:
    selected_id = _optional_text(typed_input.selected_process_id)
    selected_key = _optional_text(typed_input.selected_process_key)
    for process in processes:
        if selected_id is not None and _process_id(process) == selected_id:
            return process
    for process in processes:
        if (
            selected_key is not None
            and getattr(process, "process_key", None) == selected_key
        ):
            return process
    description_process_id = _optional_text(
        getattr(typed_input.description, "boot_process_id", None)
    )
    for process in processes:
        if (
            description_process_id is not None
            and _process_id(process) == description_process_id
        ):
            return process
    return processes[0] if processes else None


def _select_thread(
    typed_input: EnvironmentViewsV1ProviderInput,
    process: DescribeEnvironmentTopologyProcess | None,
) -> DescribeEnvironmentTopologyThread | None:
    if process is None:
        return None
    threads = list(getattr(process, "threads", []) or [])
    selected_id = _optional_text(typed_input.selected_thread_id)
    selected_key = _optional_text(typed_input.selected_thread_key)
    for thread in threads:
        if selected_id is not None and _thread_id(thread) == selected_id:
            return thread
    for thread in threads:
        if (
            selected_key is not None
            and getattr(thread, "thread_key", None) == selected_key
        ):
            return thread
    description_thread_id = _optional_text(
        getattr(typed_input.description, "boot_thread_id", None)
    )
    for thread in threads:
        if (
            description_thread_id is not None
            and _thread_id(thread) == description_thread_id
        ):
            return thread
    return threads[0] if threads else None


def _process_navigation_item(
    process: DescribeEnvironmentTopologyProcess,
    *,
    selection: _Selection,
) -> EnvironmentProcessNavigationItemV1:
    threads = list(getattr(process, "threads", []) or [])
    return EnvironmentProcessNavigationItemV1(
        process_id=_process_id(process),
        process_key=_optional_text(getattr(process, "process_key", None)),
        title=_optional_text(getattr(process, "title", None)) or "Process",
        description=_optional_text(getattr(process, "description", None)),
        thread_count=len(threads),
        is_selected=_same_process(process, selection.process),
        threads=[
            EnvironmentThreadNavigationItemV1(
                thread_id=_thread_id(thread),
                thread_key=_optional_text(getattr(thread, "thread_key", None)),
                title=_optional_text(getattr(thread, "title", None)) or "Thread",
                description=_optional_text(getattr(thread, "description", None)),
                attachment_count=len(list(getattr(thread, "attachments", []) or [])),
                active_attachment_count=_active_attachment_count(thread),
                is_selected=_same_thread(thread, selection.thread),
            )
            for thread in threads
        ],
    )


def _process_workspace_thread(
    thread: DescribeEnvironmentTopologyThread,
    *,
    selection: _Selection,
) -> ProcessWorkspaceThreadViewStateV1:
    attachments = list(getattr(thread, "attachments", []) or [])
    layouts = list(getattr(thread, "layouts", []) or [])
    return ProcessWorkspaceThreadViewStateV1(
        thread_id=_thread_id(thread),
        thread_key=_optional_text(getattr(thread, "thread_key", None)),
        title=_optional_text(getattr(thread, "title", None)) or "Thread",
        description=_optional_text(getattr(thread, "description", None)),
        attachment_count=len(attachments),
        active_attachment_count=_active_attachment_count(thread),
        lane_count=sum(
            len(list(getattr(attachment, "lanes", []) or []))
            for attachment in attachments
        ),
        layout_count=len(layouts),
        is_selected=_same_thread(thread, selection.thread),
    )


def _thread_layout_candidate(
    layout: DescribeEnvironmentTopologyLayout,
) -> ThreadLayoutCandidateViewStateV1:
    return ThreadLayoutCandidateViewStateV1(
        layout_id=_optional_text(getattr(layout, "layout_id", None)),
        layout_key=_optional_text(getattr(layout, "layout_key", None)),
        title=_optional_text(getattr(layout, "title", None)) or "Layout",
        description=_optional_text(getattr(layout, "description", None)),
        is_active=bool(getattr(layout, "is_active", False)),
        sections=[
            _thread_layout_section(section)
            for section in list(getattr(layout, "sections", []) or [])
        ],
    )


def _thread_layout_section(
    section: DescribeEnvironmentTopologySection,
) -> ThreadLayoutSectionViewStateV1:
    return ThreadLayoutSectionViewStateV1(
        section_key=str(section.section_key),
        title=_optional_text(getattr(section, "title", None)) or "Section",
        description=_optional_text(getattr(section, "description", None)),
        order=int(getattr(section, "order", 0) or 0),
        flex=float(getattr(section, "flex", 1.0) or 1.0),
        is_visible=bool(getattr(section, "is_visible", True)),
        focus_scope_id=_optional_text(getattr(section, "focus_scope_id", None)),
        view_ref=_optional_text(getattr(section, "view_ref", None)),
        view_key=_optional_text(getattr(section, "view_key", None)),
        package_name=_optional_text(getattr(section, "package_name", None)),
        pane_key=_optional_text(getattr(section, "pane_key", None)),
    )


def _thread_layout_attachment(
    attachment: DescribeEnvironmentTopologyAttachment,
) -> ThreadLayoutAttachmentViewStateV1:
    return ThreadLayoutAttachmentViewStateV1(
        attachment_id=_optional_text(getattr(attachment, "assoc_id", None)),
        title=_optional_text(getattr(attachment, "title", None)),
        is_active=bool(getattr(attachment, "is_active", True)),
        object_instance_graph_branch_id=_optional_text(
            getattr(attachment, "object_instance_graph_branch_id", None)
        ),
        object_instance_graph_identity_id=_optional_text(
            getattr(attachment, "object_instance_graph_identity_id", None)
        ),
        domain_branch_id=_optional_text(getattr(attachment, "domain_branch_id", None)),
        lanes=[
            ThreadLayoutLaneViewStateV1(
                lane_hash=str(lane.lane_hash),
                opg_id=_optional_text(getattr(lane, "opg_id", None)),
                opg_name=_optional_text(getattr(lane, "opg_name", None)),
            )
            for lane in list(getattr(attachment, "lanes", []) or [])
        ],
    )


def _status_blocks(
    typed_input: EnvironmentViewsV1ProviderInput,
) -> list[EnvironmentStatusBlockSummaryV1]:
    return [
        EnvironmentStatusBlockSummaryV1(
            name=str(block.name),
            available=bool(getattr(block, "available", True)),
            authority_kind=_enum_value(
                getattr(getattr(block, "authority", None), "kind", None)
            ),
            unavailable_reason=_optional_text(
                getattr(block, "unavailable_reason", None)
            ),
            payload=dict(getattr(block, "payload", {}) or {}),
        )
        for block in list(getattr(typed_input.status, "blocks", []) or [])
    ]


def _topology_processes(
    typed_input: EnvironmentViewsV1ProviderInput,
) -> list[DescribeEnvironmentTopologyProcess]:
    return list(getattr(typed_input.topology, "processes", []) or [])


def _active_attachment_count(thread: DescribeEnvironmentTopologyThread) -> int:
    return sum(
        1
        for attachment in list(getattr(thread, "attachments", []) or [])
        if bool(getattr(attachment, "is_active", True))
    )


def _ready(typed_input: EnvironmentViewsV1ProviderInput) -> bool:
    status = _optional_text(getattr(typed_input.status, "status", None))
    if status is None:
        return False
    if status in {"failed", "blocked", "error", "unavailable"}:
        return False
    blocks = list(getattr(typed_input.status, "blocks", []) or [])
    return all(bool(getattr(block, "available", True)) for block in blocks)


def _view_status(
    typed_input: EnvironmentViewsV1ProviderInput,
    *,
    materialized: bool,
) -> str:
    status = (
        _optional_text(getattr(typed_input.topology, "status", None))
        or _optional_text(getattr(typed_input.status, "status", None))
        or _optional_text(getattr(typed_input.description, "status", None))
    )
    if not materialized:
        return "waiting" if status in {None, "succeeded", "ready"} else status
    return "materialized" if status in {None, "succeeded", "ready"} else status


def _environment_id(typed_input: EnvironmentViewsV1ProviderInput) -> str | None:
    for source in (typed_input.description, typed_input.topology, typed_input.status):
        value = _optional_text(getattr(source, "environment_id", None))
        if value is not None:
            return value
    return typed_input.provenance.environment_id


def _environment_title(typed_input: EnvironmentViewsV1ProviderInput) -> str:
    return (
        _optional_text(getattr(typed_input.description, "environment_title", None))
        or _optional_text(
            getattr(typed_input.description, "environment_config_title", None)
        )
        or "Environment"
    )


def _provenance_payload(
    typed_input: EnvironmentViewsV1ProviderInput,
    *,
    view_ref: str,
    projection_view_key: str,
    state_provider_ref: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = typed_input.provenance.to_json()
    payload.update(
        {
            "view_ref": view_ref,
            "projection_view_key": projection_view_key,
            "state_provider_ref": state_provider_ref,
            "topology_status": _optional_text(
                getattr(typed_input.topology, "status", None)
            ),
            "status_status": _optional_text(
                getattr(typed_input.status, "status", None)
            ),
            "process_count": len(_topology_processes(typed_input)),
        }
    )
    if extra:
        payload.update(dict(extra))
    return payload


def _context_value(provider_context: object, name: str) -> Any:
    value = getattr(provider_context, name, None)
    return value() if callable(value) else value


def _process_id(process: object | None) -> str | None:
    return _optional_text(getattr(process, "process_id", None))


def _thread_id(thread: object | None) -> str | None:
    return _optional_text(getattr(thread, "thread_id", None))


def _same_process(
    left: DescribeEnvironmentTopologyProcess | None,
    right: DescribeEnvironmentTopologyProcess | None,
) -> bool:
    return (
        left is not None
        and right is not None
        and _process_id(left) == _process_id(right)
    )


def _same_thread(
    left: DescribeEnvironmentTopologyThread | None,
    right: DescribeEnvironmentTopologyThread | None,
) -> bool:
    return (
        left is not None and right is not None and _thread_id(left) == _thread_id(right)
    )


def _enum_value(value: object | None) -> str | None:
    if isinstance(value, Enum):
        return str(value.value)
    return _optional_text(value)


def _optional_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "EnvironmentViewGeneratedApiClient",
    "EnvironmentViewsV1ProviderInput",
    "ViewProviderProvenanceV1",
    "environment_navigator_view_state",
    "environment_navigator_view_state_from_input",
    "environment_views_v1_provider_input",
    "environment_views_v1_provider_input_from_api",
    "process_workspace_view_state",
    "process_workspace_view_state_from_input",
    "thread_layout_view_state",
    "thread_layout_view_state_from_input",
]
