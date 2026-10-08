"""Pure lowering from exact filesystem source closures to Specification meaning."""

from __future__ import annotations

from typing import cast

from aware_specification_fs_source_contract import (
    SpecificationFsSourceClosure,
    SpecificationFsSourceRole,
)
from aware_specification_runtime import (
    SpecificationDefinition,
    SpecificationInvariantDefinition,
    SpecificationIterationPlan,
    SpecificationPhaseDefinition,
    SpecificationPhaseDependency,
    SpecificationPhaseDependencyKind,
    SpecificationPhaseGateDefinition,
    SpecificationSnapshot,
    phase_ref,
)

from .contracts import (
    SpecificationFsLoweringResult,
    SpecificationFsSchemaResolutionContext,
    digest,
    validate_context,
)
from .manifest import (
    ManifestError,
    ParsedManifest,
    manifest_entrypoints,
    parse_manifest,
)
from .markdown import (
    MarkdownError,
    ParsedMarkdown,
    bullet_rows,
    decode_rationale,
    parse_markdown,
    table_rows,
)


class LoweringError(ValueError):
    pass


_INVARIANT_HEADER = "| Invariant Ref | Path |"
_INVARIANT_DELIMITER = "| --- | --- |"
_PHASE_HEADER = "| Phase Ref | Path |"
_PHASE_DELIMITER = "| --- | --- |"
_DEPENDENCY_HEADER = (
    "| Dependency Key | Kind | Required Phase Ref | Required Gate Digest | Rationale |"
)
_DEPENDENCY_DELIMITER = "| --- | --- | --- | --- | --- |"


def closure_coordinate(value: SpecificationFsSourceClosure) -> tuple[str, str, str]:
    return ("specification_fs_source", value.profile.profile_ref, value.spec_root)


def root_set_digest(closures: tuple[SpecificationFsSourceClosure, ...]) -> str:
    return digest(
        "aware.specification.fs-source-root-set.v1",
        {
            "members": [
                {
                    "closure_coordinate": list(closure_coordinate(closure)),
                    "closure_digest": closure.closure_digest,
                }
                for closure in closures
            ]
        },
    )


def _exact_closures(value: object) -> tuple[SpecificationFsSourceClosure, ...]:
    if type(value) is not tuple or not value:
        raise LoweringError("closures must be a nonempty exact tuple")
    closures = cast(tuple[object, ...], value)
    if any(type(item) is not SpecificationFsSourceClosure for item in closures):
        raise LoweringError("closure values must be exact")
    exact = cast(tuple[SpecificationFsSourceClosure, ...], closures)
    for closure in exact:
        closure.__post_init__()
    coordinates = tuple(closure_coordinate(item) for item in exact)
    ordered = tuple(sorted(coordinates, key=lambda item: _coordinate_bytes(item)))
    if coordinates != ordered or len(set(coordinates)) != len(coordinates):
        raise LoweringError("closures must be unique and canonically ordered")
    return exact


def _coordinate_bytes(value: tuple[str, str, str]) -> bytes:
    from .contracts import canonical_json_bytes

    return canonical_json_bytes(list(value))


def _member_map(
    closure: SpecificationFsSourceClosure,
) -> dict[str, tuple[SpecificationFsSourceRole, str]]:
    return {
        item.relative_path: (item.role, item.canonical_body) for item in closure.members
    }


def _text(item: dict[str, object], name: str) -> str:
    value = item[name]
    if type(value) is not str:
        raise LoweringError(f"{name} must be exact text")
    return value


def _integer(item: dict[str, object], name: str) -> int:
    value = item[name]
    if type(value) is not int:
        raise LoweringError(f"{name} must be exact integer")
    return value


def _doc(
    members: dict[str, tuple[SpecificationFsSourceRole, str]], path: str, role: str
) -> ParsedMarkdown:
    value = members.get(path)
    if value is None or value[0].value != role:
        raise LoweringError("manifest path/role is absent or mismatched")
    return parse_markdown(role, value[1])


def _unquote(value: str) -> str:
    if (
        len(value) < 2
        or not value.startswith("`")
        or not value.endswith("`")
        or "`" in value[1:-1]
    ):
        raise LoweringError("projection cell must be exactly backticked")
    return value[1:-1]


def _require_projection_equality(
    manifest: ParsedManifest,
    documents: dict[str, ParsedMarkdown],
) -> None:
    key = _text(manifest.specification, "key")
    invariant_expected = tuple(
        (
            f"specification:{key}/invariant:{_text(item, 'key')}",
            _text(item, "entrypoint"),
        )
        for item in manifest.invariants
    )
    invariant_rows = tuple(
        (_unquote(row[0]), _unquote(row[1]))
        for row in table_rows(
            documents["invariants/README.md"].sections.get("Members", ()),
            _INVARIANT_HEADER,
            _INVARIANT_DELIMITER,
            2,
        )
    )
    if invariant_rows != invariant_expected:
        raise LoweringError("invariant index projection does not match manifest")

    phase_expected = tuple(
        (phase_ref(key, _text(item, "key")), _text(item, "entrypoint"))
        for item in manifest.phases
    )
    phase_rows = tuple(
        (_unquote(row[0]), _unquote(row[1]))
        for row in table_rows(
            documents["PHASES.md"].sections.get("Members", ()),
            _PHASE_HEADER,
            _PHASE_DELIMITER,
            2,
        )
    )
    if phase_rows != phase_expected:
        raise LoweringError("phase index projection does not match manifest")

    for phase in manifest.phases:
        phase_key = _text(phase, "key")
        owner = phase_ref(key, phase_key)
        doc = documents[_text(phase, "entrypoint")]
        refs = phase["invariant_refs"]
        if type(refs) is not list:
            raise LoweringError("phase invariant refs must be an array")
        if bullet_rows(doc.sections.get("Advances", ())) != tuple(
            cast(list[str], refs)
        ):
            raise LoweringError("Advances projection does not match manifest")
        dependencies = tuple(
            item
            for item in manifest.dependencies
            if _text(item, "owner_phase_ref") == owner
        )
        expected_dependencies = tuple(
            (
                _text(item, "key"),
                _text(item, "kind"),
                _text(item, "required_phase_ref"),
                _text(item, "required_gate_digest"),
                _text(item, "rationale") or None,
            )
            for item in dependencies
        )
        actual_dependencies = tuple(
            (
                _unquote(row[0]),
                _unquote(row[1]),
                _unquote(row[2]),
                _unquote(row[3]),
                decode_rationale(row[4]),
            )
            for row in table_rows(
                doc.sections.get("Dependencies", ()),
                _DEPENDENCY_HEADER,
                _DEPENDENCY_DELIMITER,
                5,
            )
        )
        if actual_dependencies != expected_dependencies:
            raise LoweringError("Dependencies projection does not match manifest")
        iterations = tuple(
            item for item in manifest.iterations if _text(item, "phase_ref") == owner
        )
        if bullet_rows(doc.sections.get("Iterations", ())) != tuple(
            _text(item, "entrypoint") for item in iterations
        ):
            raise LoweringError("Iterations projection does not match manifest")


def _lower_definition(
    closure: SpecificationFsSourceClosure,
    context: SpecificationFsSchemaResolutionContext,
) -> SpecificationDefinition:
    members = _member_map(closure)
    manifest_value = members.get("aware.spec.toml")
    if (
        manifest_value is None
        or manifest_value[0] is not SpecificationFsSourceRole.MANIFEST
    ):
        raise LoweringError("manifest source member is absent")
    manifest = parse_manifest(manifest_value[1])
    expected_paths = {"aware.spec.toml": "manifest", **manifest_entrypoints(manifest)}
    actual_paths = {path: role.value for path, (role, _) in members.items()}
    if actual_paths != expected_paths:
        raise LoweringError("closure membership does not match manifest")
    documents = {
        path: _doc(members, path, role)
        for path, role in expected_paths.items()
        if role != "manifest"
    }
    _require_projection_equality(manifest, documents)
    specification = manifest.specification
    key = _text(specification, "key")

    invariants = tuple(
        SpecificationInvariantDefinition(
            invariant_key=_text(item, "key"),
            statement=cast(
                str, documents[_text(item, "entrypoint")].bodies["Statement"]
            ),
            semantic_revision=_integer(item, "semantic_revision"),
        )
        for item in manifest.invariants
    )
    phases: list[SpecificationPhaseDefinition] = []
    for item in manifest.phases:
        phase_key = _text(item, "key")
        owner = phase_ref(key, phase_key)
        document = documents[_text(item, "entrypoint")]
        expected_h1 = f"# Phase {_integer(item, 'ordinal'):02d} — {document.title}"
        if members[_text(item, "entrypoint")][1].split("\n", 1)[0] != expected_h1:
            raise LoweringError("phase H1 ordinal/title does not match manifest")
        refs = item["invariant_refs"]
        if type(refs) is not list:
            raise LoweringError("phase invariant refs must be exact array")
        dependencies = tuple(
            SpecificationPhaseDependency(
                dependency_key=_text(dep, "key"),
                required_phase_ref=_text(dep, "required_phase_ref"),
                required_gate_digest=_text(dep, "required_gate_digest"),
                kind=SpecificationPhaseDependencyKind(_text(dep, "kind")),
                rationale=_text(dep, "rationale") or None,
            )
            for dep in manifest.dependencies
            if _text(dep, "owner_phase_ref") == owner
        )
        iterations = tuple(
            SpecificationIterationPlan(
                iteration_key=_text(iteration, "key"),
                title=documents[_text(iteration, "entrypoint")].title,
                objective=cast(
                    str, documents[_text(iteration, "entrypoint")].bodies["Goal"]
                ),
                plan_revision=_integer(iteration, "plan_revision"),
            )
            for iteration in manifest.iterations
            if _text(iteration, "phase_ref") == owner
        )
        phases.append(
            SpecificationPhaseDefinition(
                phase_key=phase_key,
                title=document.title,
                ordinal=_integer(item, "ordinal"),
                gate=SpecificationPhaseGateDefinition(
                    gate_key=_text(item, "gate_key"),
                    promise=cast(str, document.bodies["Gate"]),
                    gate_contract=_text(item, "gate_contract"),
                    evidence_schema_ref=_text(item, "evidence_schema_ref"),
                    invariant_refs=tuple(cast(list[str], refs)),
                ),
                dependencies=dependencies,
                iterations=iterations,
                description=document.bodies["Goal"],
            )
        )
    root_doc = documents["SPEC.md"]
    return SpecificationDefinition(
        key=key,
        title=root_doc.title,
        version_number=_integer(specification, "semantic_version"),
        semantic_resolution_digest=context.semantic_resolution_digest,
        invariants=invariants,
        phases=tuple(phases),
        description=root_doc.bodies["Goal"],
    )


def lower_closures(
    closures: object,
    schema_context: object,
    expected_root_set_digest: object = None,
) -> SpecificationFsLoweringResult:
    exact = _exact_closures(closures)
    context = validate_context(schema_context)
    derived_root_set = root_set_digest(exact)
    if expected_root_set_digest is not None and (
        type(expected_root_set_digest) is not str
        or expected_root_set_digest != derived_root_set
    ):
        raise LoweringError("expected root-set digest does not match")
    try:
        definitions = tuple(_lower_definition(closure, context) for closure in exact)
        snapshot = SpecificationSnapshot(
            definitions=tuple(sorted(definitions, key=lambda item: item.key))
        )
        return SpecificationFsLoweringResult(exact, context, derived_root_set, snapshot)
    except (ManifestError, MarkdownError, ValueError, KeyError) as error:
        if type(error) is LoweringError:
            raise
        raise LoweringError("Specification semantic lowering failed") from error
