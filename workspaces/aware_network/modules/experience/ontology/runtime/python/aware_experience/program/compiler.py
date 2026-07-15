from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from aware_experience.program.language import (
    PlanCall,
    PlanExpr,
    PlanInvoke,
    PlanLet,
    PlanSymbolRef,
    compile_program_config_apply_calls,
    compile_program_config_plans,
    compile_invocation_plans,
    encode_invocation_plan_artifact,
    encode_program_apply_calls_artifact,
    encode_program_config_plan_artifact,
    parse_program_declarations,
)
from aware_experience.compiler.models import ExperienceProgramOwnership
from aware_experience.compiler.models import ExperienceProjectionExperienceOwnership
from aware_experience.program.spec import AwareProgramsTomlProgramSpec


def load_program_ownership_from_sources(
    *,
    package_root: Path,
    source_files: tuple[Path, ...],
    fqn_prefix: str,
    projection_experience_ownership: (
        tuple[ExperienceProjectionExperienceOwnership, ...] | None
    ) = None,
) -> tuple[ExperienceProgramOwnership, ...]:
    owned: list[ExperienceProgramOwnership] = []
    seen_names: dict[str, str] = {}
    seen_refs: set[str] = set()
    prefix = (fqn_prefix or "").strip()
    projection_contracts = _build_projection_contracts(
        projection_experience_ownership=projection_experience_ownership
    )
    program_registry = _load_program_registry(package_root=package_root)
    program_registry_by_ref = {program.ref: program for program in program_registry}
    program_registry_by_path = {program.path: program for program in program_registry}
    for relpath in source_files:
        source_path = (package_root / relpath).resolve()
        _assert_within(base=package_root, candidate=source_path, label="program source")
        source_text = source_path.read_text(encoding="utf-8")
        source_rel = relpath.as_posix()
        try:
            declarations = parse_program_declarations(source_text)
        except Exception as exc:
            raise ValueError(f"Invalid program source {source_rel}: {exc}") from exc
        if not declarations:
            continue

        try:
            config_plans = compile_program_config_plans(
                source_text,
                require_config_contract_surface=True,
            )
        except Exception as exc:
            raise ValueError(f"Invalid program source {source_rel}: {exc}") from exc
        _validate_program_projection_contracts(
            source_rel=source_rel,
            plans=config_plans,
            projection_contracts=projection_contracts,
        )
        required_catalog_keys_by_name = _collect_required_port_catalog_keys(
            plans=config_plans
        )
        program_config_plan_payload_by_name: dict[str, dict[str, object]] = {}
        program_apply_calls_payload_by_name: dict[str, dict[str, object]] = {}
        for plan in config_plans:
            plan_name = (plan.name or "").strip()
            if not plan_name:
                continue
            program_config_plan_payload_by_name[plan_name] = (
                encode_program_config_plan_artifact(plan)
            )
            program_apply_calls_payload_by_name[plan_name] = (
                encode_program_apply_calls_artifact(
                    compile_program_config_apply_calls(plan)
                )
            )

        try:
            invocation_plans = compile_invocation_plans(source_text)
        except Exception as exc:
            raise ValueError(f"Invalid program source {source_rel}: {exc}") from exc
        required_symbols_by_name: dict[str, tuple[str, ...]] = {}
        invocation_plan_payload_by_name: dict[str, dict[str, object]] = {}
        for plan in invocation_plans:
            plan_name = (plan.name or "").strip()
            required_symbols_by_name[plan_name] = _collect_program_symbols_from_plan(
                plan
            )
            invocation_plan_payload_by_name[plan_name] = (
                encode_invocation_plan_artifact(plan)
            )

        executable_names = tuple(
            (plan.name or "").strip()
            for plan in config_plans
            if (plan.name or "").strip()
        )
        for name in executable_names:
            if not name:
                raise ValueError(
                    f"Program declaration name is empty (source={source_rel})"
                )
            prior_source = seen_names.get(name)
            if prior_source is not None:
                raise ValueError(
                    f"Duplicate program declaration {name!r} across experience sources "
                    f"(source={source_rel}, prior={prior_source})"
                )
            seen_names[name] = source_rel

            ref = f"{prefix}:{name}" if prefix else name
            if ref in seen_refs:
                raise ValueError(
                    f"Duplicate program ref {ref!r} across experience sources"
                )
            seen_refs.add(ref)
            registry_program = program_registry_by_ref.get(ref)
            if registry_program is None:
                registry_program = program_registry_by_path.get(source_rel)
            dependencies = (
                tuple(dict.fromkeys(registry_program.dependencies))
                if registry_program is not None
                else ()
            )
            required_symbols = required_symbols_by_name.get(name, ())
            (
                required_projection_ids,
                required_projection_node_ids,
                required_projection_node_identity_ids,
            ) = required_catalog_keys_by_name.get(name, ((), (), ()))
            owned.append(
                ExperienceProgramOwnership(
                    ref=ref,
                    name=name,
                    path=source_rel,
                    dependencies=dependencies,
                    required_symbols=required_symbols,
                    optional_symbols=(),
                    invocation_plan_artifact=invocation_plan_payload_by_name.get(name),
                    program_config_plan_artifact=program_config_plan_payload_by_name.get(
                        name
                    ),
                    program_apply_calls_artifact=program_apply_calls_payload_by_name.get(
                        name
                    ),
                    required_projection_ids=required_projection_ids,
                    required_projection_node_ids=required_projection_node_ids,
                    required_projection_node_identity_ids=required_projection_node_identity_ids,
                )
            )
    owned.sort(key=lambda item: item.ref)
    return tuple(owned)


def _load_program_registry(
    package_root: Path,
) -> tuple[AwareProgramsTomlProgramSpec, ...]:
    manifest_path = package_root / "aware.programs.toml"
    if not manifest_path.is_file():
        return ()
    from aware_experience.program.loader import (  # noqa: WPS433
        load_aware_programs_toml_spec,
    )

    return tuple(load_aware_programs_toml_spec(toml_path=manifest_path).programs)


def select_program_source_files(source_files: Iterable[Path]) -> tuple[Path, ...]:
    return tuple(path for path in source_files if is_program_source_file(path))


def is_program_source_file(path: Path | str) -> bool:
    source_path = path.as_posix() if isinstance(path, Path) else str(path)
    source_path = source_path.replace("\\", "/")
    return source_path.startswith("programs/") or "/programs/" in source_path


def _build_projection_contracts(
    *,
    projection_experience_ownership: (
        tuple[ExperienceProjectionExperienceOwnership, ...] | None
    ),
) -> dict[str, dict[str, tuple[frozenset[str], frozenset[str]]]]:
    catalog: dict[str, dict[str, tuple[frozenset[str], frozenset[str]]]] = {}
    for ownership in projection_experience_ownership or ():
        projection_name = _normalize_projection_name(ownership.name)
        if not projection_name:
            continue
        nodes: dict[str, tuple[frozenset[str], frozenset[str]]] = {}
        for node in ownership.nodes:
            node_name = (node.name or "").strip()
            if not node_name:
                continue
            param_names = frozenset(
                (param.name or "").strip()
                for param in node.params
                if (param.name or "").strip()
            )
            identity_names = frozenset(
                (identity.key or "").strip()
                for identity in node.identities
                if (identity.key or "").strip()
            )
            nodes[node_name] = (param_names, identity_names)
        catalog[projection_name] = nodes
    return catalog


def _validate_program_projection_contracts(
    *,
    source_rel: str,
    plans: tuple[object, ...],
    projection_contracts: dict[str, dict[str, tuple[frozenset[str], frozenset[str]]]],
) -> None:
    for plan in plans:
        plan_name = (getattr(plan, "name", "") or "").strip() or "<anonymous>"
        for port in getattr(plan, "ports", ()):
            port_key = (getattr(port, "key", "") or "").strip() or "<port>"
            projection_token = (getattr(port, "projection", "") or "").strip()
            projection_name = _normalize_projection_name(projection_token)
            if not projection_name or projection_name not in projection_contracts:
                raise ValueError(
                    f"Program declaration {plan_name!r} port {port_key!r} references unknown projection experience "
                    f"{projection_token!r} (source={source_rel})"
                )
            projection_nodes = projection_contracts[projection_name]
            for node_contract in getattr(port, "projection_node_identities", ()):
                node_key = (getattr(node_contract, "key", "") or "").strip() or "<node>"
                node_name = (getattr(node_contract, "node", "") or "").strip()
                if not node_name or node_name not in projection_nodes:
                    raise ValueError(
                        f"Program declaration {plan_name!r} port {port_key!r} node {node_key!r} "
                        f"references unknown projection node {node_name!r} for experience "
                        f"{projection_token!r} (source={source_rel})"
                    )
                expected_params, expected_identities = projection_nodes[node_name]
                identity_name = (getattr(node_contract, "identity", "") or "").strip()
                arg_names = frozenset(
                    (getattr(arg, "name", "") or "").strip()
                    for arg in getattr(node_contract, "args", ())
                    if (getattr(arg, "name", "") or "").strip()
                )
                if identity_name:
                    if identity_name not in expected_identities:
                        raise ValueError(
                            f"Program declaration {plan_name!r} port {port_key!r} node {node_key!r} "
                            f"references unknown node identity {identity_name!r} for node {node_name!r} "
                            f"(source={source_rel})"
                        )
                    continue
                expected_resolver_keys = (
                    expected_params if expected_params else expected_identities
                )
                missing = sorted(expected_resolver_keys - arg_names)
                extra = sorted(arg_names - expected_resolver_keys)
                if missing or extra:
                    raise ValueError(
                        f"Program declaration {plan_name!r} port {port_key!r} node {node_key!r} "
                        f"resolver key contract mismatch for {node_name!r}: missing={missing!r} extra={extra!r} "
                        f"(source={source_rel})"
                    )


def _normalize_projection_name(raw: str) -> str:
    token = (raw or "").strip()
    if not token:
        return ""
    return token.casefold()


def _collect_required_port_catalog_keys(
    *, plans: tuple[object, ...]
) -> dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]]:
    out: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = {}
    for plan in plans:
        plan_name = (getattr(plan, "name", "") or "").strip()
        if not plan_name:
            continue
        if plan_name in out:
            raise ValueError(
                f"Duplicate compiled program plan name {plan_name!r} while collecting required port catalog keys"
            )
        projection_ids: set[str] = set()
        projection_node_ids: set[str] = set()
        projection_node_identity_ids: set[str] = set()
        for port in getattr(plan, "ports", ()):
            port_key = (getattr(port, "key", "") or "").strip()
            if not port_key:
                continue
            projection_ids.add(f"program.port.{port_key}.projection")
            for node_contract in getattr(port, "projection_node_identities", ()):
                node_key = (getattr(node_contract, "key", "") or "").strip()
                if not node_key:
                    continue
                projection_node_ids.add(
                    f"program.port.{port_key}.projection_node.{node_key}"
                )
                identity = (getattr(node_contract, "identity", "") or "").strip()
                if identity:
                    projection_node_identity_ids.add(
                        f"program.port.{port_key}.projection_node_identity.{node_key}"
                    )
        out[plan_name] = (
            tuple(sorted(projection_ids)),
            tuple(sorted(projection_node_ids)),
            tuple(sorted(projection_node_identity_ids)),
        )
    return out


def _collect_program_symbols_from_expr(expr: PlanExpr, *, out: set[str]) -> None:
    if isinstance(expr, PlanSymbolRef):
        name = (expr.name or "").strip()
        if name.startswith("plan.") or name.startswith("boot."):
            out.add(name)
        return
    if isinstance(expr, PlanCall):
        for arg in expr.args:
            _collect_program_symbols_from_expr(arg.value, out=out)
        if expr.object_expr is not None:
            _collect_program_symbols_from_expr(expr.object_expr, out=out)
        return


def _collect_program_symbols_from_plan(plan: object) -> tuple[str, ...]:
    out: set[str] = set()
    steps = getattr(plan, "steps", ())
    for step in steps:
        if isinstance(step, PlanLet):
            _collect_program_symbols_from_expr(step.value, out=out)
            continue
        if isinstance(step, PlanInvoke):
            for arg in step.call.args:
                _collect_program_symbols_from_expr(arg.value, out=out)
            if step.call.object_expr is not None:
                _collect_program_symbols_from_expr(step.call.object_expr, out=out)
    return tuple(sorted(out))


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}"
    )


__all__ = [
    "is_program_source_file",
    "load_program_ownership_from_sources",
    "select_program_source_files",
]
