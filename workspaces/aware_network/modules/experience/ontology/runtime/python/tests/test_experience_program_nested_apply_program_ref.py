from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import pytest

from aware_experience.program.language import (
    compile_invocation_plans,
    encode_invocation_plan_artifact,
)
from aware_experience.program.runtime_invocation import (
    ProgramApplyError,
    RuntimeInvocationPlanExecutor,
    compile_program_by_ref,
)


def _invocation_plan_payload(*, source: str, program_name: str) -> dict[str, object]:
    plans = compile_invocation_plans(source)
    matches = [plan for plan in plans if plan.name == program_name]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected one InvocationPlan for {program_name!r}, got {len(matches)}"
        )
    return encode_invocation_plan_artifact(matches[0])


@pytest.mark.asyncio
async def test_nested_apply_program_ref_forwards_symbols(tmp_path: Path) -> None:
    repo_root = tmp_path.resolve()
    root_path = repo_root / "modules" / "test" / "programs" / "root.aware"
    root_path.parent.mkdir(parents=True, exist_ok=True)

    root_source = """
program Root {
    call plan.apply_program_ref(
        program_ref="test:Child",
        symbols=kernel.symbols(
            "plan.invocation_plan_artifact",
            plan.child_artifact,
            "plan.child_ref",
            "test:Leaf",
            "plan.leaf_artifact",
            plan.leaf_artifact
        )
    )
}
"""
    root_path.write_text(root_source, encoding="utf-8")
    child_source = """
program Child {
    input child_ref from plan.child_ref
    input leaf_artifact from plan.leaf_artifact
    call plan.apply_program_ref(
        program_ref=child_ref,
        symbols=kernel.symbols(
            "plan.invocation_plan_artifact",
            leaf_artifact
        )
    )
}
"""
    leaf_source = """
program Leaf {
    let marker = "ok"
}
"""

    plan = compile_program_by_ref(
        src=root_path.read_text(encoding="utf-8"),
        program_name="Root",
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
        symbols={
            "plan.child_artifact": _invocation_plan_payload(
                source=child_source,
                program_name="Child",
            ),
            "plan.leaf_artifact": _invocation_plan_payload(
                source=leaf_source,
                program_name="Leaf",
            ),
        },
        program_ref_stack=("test:Root",),
    )

    results = await executor.execute(plan)
    assert len(results) == 1
    assert results[0]["target"] == "plan.apply_program_ref"
    assert results[0]["program_ref"] == "test:Child"
    nested = results[0]["results"]
    assert isinstance(nested, list) and len(nested) == 1
    assert nested[0]["target"] == "plan.apply_program_ref"
    assert nested[0]["program_ref"] == "test:Leaf"


@pytest.mark.asyncio
async def test_nested_apply_program_ref_forwards_symbols_via_kernel_symbols(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path.resolve()
    root_path = repo_root / "modules" / "test" / "programs" / "root.aware"
    root_path.parent.mkdir(parents=True, exist_ok=True)

    root_source = """
program Root {
    let child_ref = "test:Leaf"
    call plan.apply_program_ref(
        program_ref="test:Child",
        symbols=kernel.symbols(
            "plan.invocation_plan_artifact",
            plan.child_artifact,
            "plan.child_ref",
            child_ref,
            "plan.leaf_artifact",
            plan.leaf_artifact
        )
    )
}
"""
    root_path.write_text(root_source, encoding="utf-8")
    child_source = """
program Child {
    input child_ref from plan.child_ref
    input leaf_artifact from plan.leaf_artifact
    call plan.apply_program_ref(
        program_ref=child_ref,
        symbols=kernel.symbols(
            "plan.invocation_plan_artifact",
            leaf_artifact
        )
    )
}
"""
    leaf_source = """
program Leaf {
    let marker = "ok"
}
"""

    plan = compile_program_by_ref(
        src=root_path.read_text(encoding="utf-8"),
        program_name="Root",
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
        symbols={
            "plan.child_artifact": _invocation_plan_payload(
                source=child_source,
                program_name="Child",
            ),
            "plan.leaf_artifact": _invocation_plan_payload(
                source=leaf_source,
                program_name="Leaf",
            ),
        },
        program_ref_stack=("test:Root",),
    )

    results = await executor.execute(plan)
    assert len(results) == 1
    assert results[0]["target"] == "plan.apply_program_ref"
    assert results[0]["program_ref"] == "test:Child"
    nested = results[0]["results"]
    assert isinstance(nested, list) and len(nested) == 1
    assert nested[0]["target"] == "plan.apply_program_ref"
    assert nested[0]["program_ref"] == "test:Leaf"


@pytest.mark.asyncio
async def test_nested_apply_program_ref_uses_symbol_plan(tmp_path: Path) -> None:
    repo_root = tmp_path.resolve()
    root_path = repo_root / "modules" / "test" / "programs" / "root.aware"
    root_path.parent.mkdir(parents=True, exist_ok=True)

    root_source = """
program Root {
    call plan.apply_program_ref(
        program_ref="test:Child",
        symbols=kernel.symbols(
            "plan.invocation_plan_artifact",
            plan.child_artifact,
            "plan.child_ref",
            "test:Leaf"
        )
    )
}
"""
    root_path.write_text(root_source, encoding="utf-8")
    child_source = """
program Child {
    input child_ref from plan.child_ref
    let marker = child_ref
}
"""
    plan = compile_program_by_ref(
        src=root_path.read_text(encoding="utf-8"),
        program_name="Root",
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
        symbols={
            "plan.child_artifact": _invocation_plan_payload(
                source=child_source,
                program_name="Child",
            )
        },
        program_ref_stack=("test:Root",),
    )

    results = await executor.execute(plan)
    assert len(results) == 1
    assert results[0]["target"] == "plan.apply_program_ref"
    assert results[0]["program_ref"] == "test:Child"
    assert results[0]["results"] == []


@pytest.mark.asyncio
async def test_nested_apply_program_ref_requires_symbol_plan(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path.resolve()
    root_path = repo_root / "modules" / "test" / "programs" / "root.aware"
    root_path.parent.mkdir(parents=True, exist_ok=True)

    root_source = """
program Root {
    call plan.apply_program_ref(
        program_ref="test:Child",
        symbols={"plan.child_ref": "test:Leaf"}
    )
}
"""
    root_path.write_text(root_source, encoding="utf-8")
    plan = compile_program_by_ref(
        src=root_path.read_text(encoding="utf-8"),
        program_name="Root",
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
        program_ref_stack=("test:Root",),
    )

    with pytest.raises(ProgramApplyError, match="plan.invocation_plan_artifact"):
        await executor.execute(plan)


@pytest.mark.asyncio
async def test_nested_apply_program_ref_missing_required_symbols_fails(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path.resolve()
    root_path = repo_root / "modules" / "test" / "programs" / "root.aware"
    root_path.parent.mkdir(parents=True, exist_ok=True)

    root_source = """
program Root {
    call plan.apply_program_ref(
        program_ref="test:Child",
        symbols=kernel.symbols(
            "plan.invocation_plan_artifact",
            plan.child_artifact
        )
    )
}
"""
    root_path.write_text(root_source, encoding="utf-8")
    child_source = """
program Child {
    input child_ref from plan.child_ref
    let marker = child_ref
}
"""
    plan = compile_program_by_ref(
        src=root_path.read_text(encoding="utf-8"),
        program_name="Root",
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
        symbols={
            "plan.child_artifact": _invocation_plan_payload(
                source=child_source,
                program_name="Child",
            )
        },
        program_ref_stack=("test:Root",),
    )

    with pytest.raises(ProgramApplyError, match="missing required symbols"):
        await executor.execute(plan)


@pytest.mark.asyncio
async def test_nested_apply_program_ref_cycle_fails(tmp_path: Path) -> None:
    repo_root = tmp_path.resolve()
    a_path = repo_root / "modules" / "test" / "programs" / "a.aware"
    a_path.parent.mkdir(parents=True, exist_ok=True)

    a_source = """
program A {
    call plan.apply_program_ref(
        program_ref="test:B",
        symbols=kernel.symbols(
            "plan.invocation_plan_artifact",
            plan.b_artifact,
            "plan.a_artifact",
            plan.a_artifact
        )
    )
}
"""
    a_path.write_text(a_source, encoding="utf-8")
    b_source = """
program B {
    input a_artifact from plan.a_artifact
    call plan.apply_program_ref(
        program_ref="test:A",
        symbols=kernel.symbols(
            "plan.invocation_plan_artifact",
            a_artifact,
            "plan.b_artifact",
            plan.invocation_plan_artifact
        )
    )
}
"""
    plan = compile_program_by_ref(
        src=a_path.read_text(encoding="utf-8"),
        program_name="A",
    )
    executor = RuntimeInvocationPlanExecutor(
        invoker=cast(Any, object()),
        index=cast(Any, object()),
        actor_id=uuid4(),
        environment_id=uuid4(),
        process_id=uuid4(),
        thread_id=uuid4(),
        commit=True,
        publish=False,
        symbols={
            "plan.a_artifact": _invocation_plan_payload(
                source=a_source,
                program_name="A",
            ),
            "plan.b_artifact": _invocation_plan_payload(
                source=b_source,
                program_name="B",
            ),
        },
        program_ref_stack=("test:A",),
    )

    with pytest.raises(ProgramApplyError, match="Cycle detected"):
        await executor.execute(plan)
