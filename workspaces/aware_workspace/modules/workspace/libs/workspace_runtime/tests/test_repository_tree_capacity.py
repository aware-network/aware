"""Original physical forecasts and descriptive bounds; no replacement authority."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from aware_file_system import retained_tree_projection as native
from aware_workspace_runtime import repository_tree_capacity as capacity
from aware_workspace_sdk import repository_tree_projection as sdk
from aware_workspace_sdk.repository_tree_projection import (
    WorkspaceTreeProjectionRefusal,
)
from aware_workspace_sdk.repository_tree_projection_codec import (
    repository_tree_projection_value_to_json,
)
from aware_workspace_sdk.repository_tree_projection_values import (
    DEFAULT_TREE_LIMITS,
    MAX_TREE_METADATA_BYTES,
    MAX_TREE_RECEIPTS,
    WorkspaceTreeFileIntent,
    WorkspaceTreeProjectionRequest,
)

from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_tree_projection import (
    enroll_original_request,
    genuine_issue_enrollment,
    setup,
)
from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_tree_projection import (
    inputs as inputs,  # noqa: PLC0414 - original pytest fixture
)


def runtime_of(client):
    return sdk._CLIENTS[client][0]


@pytest.mark.parametrize(
    "dimension",
    ["metadata_bytes", "resource_table_rows", "logical_resource_references"],
)
def test_exact_quota_and_one_over(dimension):
    exact = capacity.TreeCapacityBound(
        MAX_TREE_METADATA_BYTES,
        MAX_TREE_RECEIPTS,
        MAX_TREE_RECEIPTS * 512,
        0,
    )
    capacity.enforce_capacity(exact, MAX_TREE_METADATA_BYTES)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="quota_exceeded"):
        capacity.enforce_capacity(
            replace(exact, **{dimension: getattr(exact, dimension) + 1}),
            MAX_TREE_METADATA_BYTES,
        )


@pytest.mark.parametrize("bad", [True, -1, 1.2, "8", None])
def test_capacity_scalars_are_exact_nonnegative(bad):
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="physical_refused"):
        capacity.enforce_capacity(
            capacity.TreeCapacityBound(bad, 1, 1, 0), MAX_TREE_METADATA_BYTES
        )


def test_tighter_request_limit_is_enforced():
    bound = capacity.TreeCapacityBound(1000, 1, 1, 0)
    capacity.enforce_capacity(bound, 1000)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="quota_exceeded"):
        capacity.enforce_capacity(bound, 999)


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["create", "delete", "directory", "nested"])
async def test_genuine_result_and_resolution_fit_bound(inputs, kind):
    (
        attempt,
        source,
        workspace,
        plan,
        binding,
        issuer,
        issue,
        enrollment,
        _,
    ) = await genuine_issue_enrollment(inputs, kind)
    assert attempt is not None and source is not None
    result = await workspace.project_tree(plan, admission=enrollment)
    runtime = runtime_of(workspace)
    bound = runtime.capacity_bound
    assert type(bound) is capacity.TreeCapacityBound
    observed = sdk.read_original_tree_projection_result(
        result, expected_binding=binding
    )
    resolution = await workspace.resolve_tree_projection_receipts(enrollment)
    for value in (observed, resolution):
        assert (
            len(repository_tree_projection_value_to_json(value).encode())
            < bound.metadata_bytes
        )
    assert bound.logical_resource_references >= sum(
        len(r.cleanup.resources) for r in observed.receipts
    ) + 2 * len(observed.cleanup.resources)
    assert bound.resource_table_rows >= len(
        {
            json.dumps(asdict(r), sort_keys=True)
            for group in [
                observed.cleanup.resources,
                *(r.cleanup.resources for r in observed.receipts),
            ]
            for r in group
        }
    )
    await issuer.release_tree_projection_admission(issue)
    await workspace.release_tree_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field,bad",
    [
        ("schema", "foreign"),
        ("preparation_ref", "foreign"),
        ("request_ref", "foreign"),
        ("request_digest", "sha256:" + "0" * 64),
        ("root_identity", (0, 0)),
        ("forecast_revision", True),
        ("observed_acquisition_rows", -1),
        ("remaining_scratch_rows", 2**64),
        ("transition_order", []),
        ("prefixes", ()),
        ("forecast_wire_bytes", 0),
    ],
)
async def test_forecast_correspondence_and_shape_refuse(inputs, field, bad):
    (
        attempt,
        source,
        workspace,
        _plan,
        binding,
        issuer,
        issue,
        _enrollment,
        _,
    ) = await genuine_issue_enrollment(inputs)
    assert attempt is not None and source is not None
    original = runtime_of(workspace).preparation.observe_capacity_forecast()
    object.__setattr__(original, field, bad)
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="physical_refused"):
        capacity.capacity_bound(original, binding)
    await issuer.release_tree_projection_admission(issue)
    await workspace.release_tree_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("section", ["schedule", "encoding", "prefixes"])
async def test_nested_foreign_descriptions_execute_no_behavior(inputs, section):
    calls = []

    class Foreign:
        def __getattribute__(self, name):
            calls.append(name)
            raise AssertionError("foreign dispatch")

    (
        attempt,
        source,
        workspace,
        _plan,
        binding,
        issuer,
        issue,
        _enrollment,
        _,
    ) = await genuine_issue_enrollment(inputs)
    assert attempt is not None and source is not None
    forecast = runtime_of(workspace).preparation.observe_capacity_forecast()
    object.__setattr__(
        forecast, section, (Foreign(),) * 2 if section == "prefixes" else Foreign()
    )
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="physical_refused"):
        capacity.capacity_bound(forecast, binding)
    assert not calls
    await issuer.release_tree_projection_admission(issue)
    await workspace.release_tree_projection()


@pytest.mark.parametrize("change", ["code", "defaults", "kwdefaults", "export"])
def test_original_forecast_definition_is_authenticated(monkeypatch, change):
    original = capacity._FORECAST
    calls = []

    def foreign(self):
        calls.append(self)

    if change == "export":
        monkeypatch.setattr(
            native.RetainedPhysicalTreeProjection, "observe_capacity_forecast", foreign
        )
    elif change == "code":

        def foreign_code(self):
            raise AssertionError("foreign code executed")

        monkeypatch.setattr(original, "__code__", foreign_code.__code__)
    elif change == "defaults":
        monkeypatch.setattr(original, "__defaults__", (foreign,))
    else:
        monkeypatch.setattr(original, "__kwdefaults__", {"guard": foreign})
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="physical_refused"):
        capacity.require_forecast_origin(original)
    assert not calls


@pytest.mark.asyncio
@pytest.mark.parametrize("prefix", [0, 1, 2])
@pytest.mark.parametrize("lost_return", [False, True])
async def test_genuine_failure_prefix_and_refusal_encoding_fit_bound(
    inputs, monkeypatch, prefix, lost_return
):
    parent, source, _observed, workspace, request = setup(inputs)
    request = replace(
        request,
        files=tuple(replace(request.files[0], path=f"file{i}.py") for i in range(3)),
    )
    plan, binding, issuer, issue, enrollment, _ = await enroll_original_request(
        inputs, request, source, workspace
    )
    original = os.link

    def fail(*args, **kwargs):
        if args[1] == f"file{prefix}.py":
            if lost_return:
                original(*args, **kwargs)
            raise OSError("genuine filesystem failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(os, "link", fail)
    with pytest.raises(WorkspaceTreeProjectionRefusal) as caught:
        await workspace.project_tree(plan, admission=enrollment)
    bound = runtime_of(workspace).capacity_bound
    observation = caught.value.evidence.observation
    assert observation.completed_prefix == prefix
    assert observation.receipts and parent is not None
    assert (
        len(repository_tree_projection_value_to_json(caught.value.evidence).encode())
        < bound.metadata_bytes
    )
    for i in range(prefix):
        assert (inputs[1] / f"file{i}.py").read_bytes() == (
            inputs[0] / binding.files[i].source_path
        ).read_bytes()
    assert (inputs[1] / f"file{prefix}.py").exists() is lost_return
    await issuer.release_tree_projection_admission(issue)
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_original_1000_transition_exact_8mib_fits_complete_capacity(inputs):
    # Original source/plan/physical input, but no Issue spend or tree execution:
    # this qualifies the calculator, never the whole-SDK latency/RSS gate.
    from workspaces.aware_workspace.modules.workspace.libs.workspace_runtime.tests.test_repository_workflow import (
        commit,
        workflow_source,
    )

    package = inputs[3]
    (package / "base.py").write_bytes(b"x" * 8388)
    (package / "extra.py").write_bytes(b"x" * 8389)
    args = (*inputs[:-1], replace(inputs[-1], source_commit=commit(inputs[0])))
    parent, source, observed = workflow_source(args)
    outputs = {Path(row.source_path).name: row for row in observed.files}
    workspace = sdk.WorkspaceRepositoryTreeProjectionClient.filesystem(
        repository_root=inputs[1],
        state_root=inputs[2] / "tree",
        execution_id=observed.binding.execution_id,
    )
    request = WorkspaceTreeProjectionRequest(
        observed.binding.workflow_ref,
        "layout:explicit",
        "invocation:capacity",
        observed.binding,
        tuple(
            WorkspaceTreeFileIntent(
                f"file{i:04d}.py",
                "CREATE",
                outputs["extra.py" if i < 608 else "base.py"].output_path,
                0o644,
            )
            for i in range(1000)
        ),
        (),
        "descriptor_walk_v1",
        DEFAULT_TREE_LIMITS,
    )
    plan = await workspace.prepare_tree_projection(request, source_delivery=source)
    binding = workspace.observe_tree_projection_plan(plan).binding
    assert sum(row.successor_size_bytes for row in binding.files) == 8 * 1024 * 1024
    runtime = runtime_of(workspace)
    forecast = runtime.preparation.observe_capacity_forecast()
    bound = capacity.capacity_bound(forecast, binding)
    # Original source, preparation and complete future envelope are admitted.
    # This proves capacity only; execution/latency is the separate whole-SDK gate.
    assert bound.metadata_bytes <= binding.limits.maximum_metadata_bytes
    capacity.enforce_capacity(bound, binding.limits.maximum_metadata_bytes)
    assert bound.logical_resource_references > MAX_TREE_RECEIPTS
    assert runtime.preparation.observe_effects().effects == ()
    assert not any((inputs[1] / row.path).exists() for row in binding.files)
    assert parent is not None
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_each_native_integer_slot_rejects_bool_without_new_authority(inputs):
    (
        parent,
        source,
        workspace,
        _plan,
        binding,
        issuer,
        issue,
        _enrollment,
        _,
    ) = await genuine_issue_enrollment(inputs)
    forecast = runtime_of(workspace).preparation.observe_capacity_forecast()
    count = 0
    for value in (forecast, forecast.schedule, forecast.encoding, *forecast.prefixes):
        for name in type(value).__slots__:
            saved = getattr(value, name)
            if type(saved) is int:
                object.__setattr__(value, name, True)
                try:
                    with pytest.raises(
                        WorkspaceTreeProjectionRefusal, match="physical_refused"
                    ):
                        capacity.capacity_bound(forecast, binding)
                    count += 1
                finally:
                    object.__setattr__(value, name, saved)
    assert count >= 40 and parent is not None and source is not None
    await issuer.release_tree_projection_admission(issue)
    await workspace.release_tree_projection()


@pytest.mark.asyncio
async def test_compact_genuine_result_remains_within_the_original_forecast(inputs):
    parent, source, _observed, workspace, request = setup(inputs)
    request = replace(
        request,
        files=tuple(
            replace(request.files[0], path=f"file{i:04d}.py") for i in range(80)
        ),
    )
    plan, binding, issuer, issue, enrollment, _ = await enroll_original_request(
        inputs, request, source, workspace
    )
    returned = await workspace.project_tree(plan, admission=enrollment)
    observed = sdk.read_original_tree_projection_result(
        returned, expected_binding=binding
    )
    payload = json.loads(repository_tree_projection_value_to_json(observed))
    assert payload["encoding"] == "aware.workspace.tree-cleanup-resource-table.v1"
    bound = runtime_of(workspace).capacity_bound
    assert (
        len(json.dumps(payload, separators=(",", ":")).encode()) < bound.metadata_bytes
    )
    assert len(payload["resources"]) <= bound.resource_table_rows
    assert (
        sum(len(r.cleanup.resources) for r in observed.receipts)
        + 2 * len(observed.cleanup.resources)
        <= bound.logical_resource_references
    )
    assert observed.completed_prefix == 80 and parent is not None
    await issuer.release_tree_projection_admission(issue)
    await workspace.release_tree_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("behavior", ["return", "raise", "restore"])
async def test_nested_validator_substitution_is_terminal_before_issue_spend(
    inputs, monkeypatch, behavior
):
    (
        parent,
        source,
        workspace,
        plan,
        binding,
        issuer,
        issue,
        enrollment,
        _,
    ) = await genuine_issue_enrollment(inputs)
    original = capacity.validate_forecast
    calls = []

    def foreign(*args, **kwargs):
        calls.append(True)
        if behavior == "restore":
            capacity.validate_forecast = original
        if behavior == "raise":
            raise OSError("foreign validation executed")
        return original(*args, **kwargs)

    physical = runtime_of(workspace).preparation
    before = {
        str(p.relative_to(inputs[1])): p.read_bytes()
        for p in inputs[1].rglob("*")
        if p.is_file()
    }
    with monkeypatch.context() as patch:
        patch.setattr(capacity, "validate_forecast", foreign)
        with pytest.raises(WorkspaceTreeProjectionRefusal, match="physical_refused"):
            await workspace.project_tree(plan, admission=enrollment)
    assert calls == []
    assert (
        issuer.observe_tree_projection_admission(issue).consumption_state == "not_spent"
    )
    assert physical.observe_effects().effects == ()
    assert runtime_of(workspace).phase == "held"
    assert {
        str(p.relative_to(inputs[1])): p.read_bytes()
        for p in inputs[1].rglob("*")
        if p.is_file()
    } == before
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(plan, admission=enrollment)
    # Rejection preserves the borrowed source while retiring this attempt.
    from aware_workspace_sdk.repository_workflow import (
        verify_original_repository_workflow_source,
    )

    verify_original_repository_workflow_source(
        source, expected_binding=binding.source_binding
    )
    assert parent is not None
    await issuer.release_tree_projection_admission(issue)
    await workspace.release_tree_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("attribute", ["__code__", "__defaults__", "__kwdefaults__"])
async def test_nested_validator_definition_mutation_never_dispatches(
    inputs, monkeypatch, attribute
):
    (
        parent,
        source,
        workspace,
        plan,
        _binding,
        issuer,
        issue,
        enrollment,
        _,
    ) = await genuine_issue_enrollment(inputs)
    original = capacity.validate_forecast

    def foreign_code(value, binding):
        raise AssertionError("foreign validator executed")

    value = (
        foreign_code.__code__
        if attribute == "__code__"
        else (None,)
        if attribute == "__defaults__"
        else {"guard": foreign_code}
    )
    with monkeypatch.context() as patch:
        patch.setattr(original, attribute, value)
        with pytest.raises(WorkspaceTreeProjectionRefusal, match="physical_refused"):
            await workspace.project_tree(plan, admission=enrollment)
    assert (
        issuer.observe_tree_projection_admission(issue).consumption_state == "not_spent"
    )
    assert not (inputs[1] / "out.py").exists()
    assert parent is not None and source is not None
    with pytest.raises(WorkspaceTreeProjectionRefusal, match="retired"):
        await workspace.project_tree(plan, admission=enrollment)
    await issuer.release_tree_projection_admission(issue)
    await workspace.release_tree_projection()


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ("OSError", "X" * 16385, 'escaped"\nname', "é" * 200))
async def test_own_release_diagnostic_is_bounded_without_losing_cause(inputs, name):
    import hashlib

    from aware_workspace_runtime import repository_tree_projection as owner

    calls = []

    class ErrorMeta(type):
        def __getattribute__(cls, attribute):
            if attribute == "__name__":
                calls.append(attribute)
                raise AssertionError("exception metaclass behavior must not execute")
            return super().__getattribute__(attribute)

    failure = ErrorMeta(name, (RuntimeError,), {})("original release return lost")
    parent, source, _observed, workspace, request = setup(inputs)
    await workspace.prepare_tree_projection(request, source_delivery=source)
    runtime = runtime_of(workspace)
    original = runtime.preparation_methods["release"]
    released = []

    def lost_return(handle):
        released.append(handle)
        original(handle)
        raise failure

    runtime.preparation_methods["release"] = lost_return
    with pytest.raises(RuntimeError) as caught:
        owner._release_physical(runtime)
    assert caught.value is failure and calls == []
    assert runtime.cleanup.cleanup_state == "unknown"
    assert not runtime.cleanup.ledger_complete
    row = runtime.cleanup.resources[-1]
    expected = (
        name
        if name == "OSError"
        else "exception-type:sha256:"
        + hashlib.sha256(name.encode("utf-8", errors="surrogatepass")).hexdigest()
    )
    assert row.diagnostics == (expected,)
    assert len(expected.encode("ascii")) <= 128
    assert runtime.preparation is None and len(released) == 1
    owner._release_physical(runtime)
    assert len(released) == 1
    await workspace.release_tree_projection()
    assert parent is not None
