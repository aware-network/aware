"""One selected v3 graph keeps unrelated v1 declarations as nonparticipants."""

from dataclasses import replace

import pytest
from aware_code_retained_registry_policy_runtime.declaration_eligibility import (
    calculate_declaration_eligibility,
)
from aware_code_retained_registry_policy_runtime.selected_participant_calculation import (
    derive_selected_participant_view,
    selected_qualified_occurrences,
    validate_selected_participant_view,
)
from aware_code_semantic_contract_runtime.contracts import (
    ContentDigest,
    ContractViolation,
)
from aware_code_semantic_contract_runtime.retained_declaration_scope import (
    CodeRetainedDeclarationPackage,
)
from aware_code_semantic_contract_runtime.retained_scope_interfaces import (
    CodeRetainedScopeBody,
    CodeRetainedScopeModule,
)
from aware_code_semantic_contract_runtime.selected_participant_scope import (
    CodeSelectedParticipant,
)

from test_declaration_eligibility import fixture


def _body(path: str, body: bytes) -> CodeRetainedScopeBody:
    digest = ContentDigest.of_bytes(body)
    return CodeRetainedScopeBody(path, "body:" + digest.value, digest, body)


def _mixed_closure(*, direct_target: bool = True):
    closure = fixture()
    consumer, target = closure.scopes
    target_module = target.projection.modules[0]
    raw = target_module.manifest.body.replace(b"aware = 2", b"aware = 3", 1)
    raw = raw.replace(
        b'value={module_id="demo", package_id="provider", registration_key="demo"}',
        b'value={scope={kind="local"}, module_id="demo", package_id="provider", registration_key="demo"}',
    )
    assert raw != target_module.manifest.body
    target_module = replace(target_module, manifest=_body(
        target_module.manifest.relative_path, raw
    ))
    target = replace(target, projection=replace(
        target.projection, modules=(target_module,)
    ))

    consumer_module = consumer.projection.modules[0]
    raw = consumer_module.manifest.body
    if direct_target:
        raw = raw.replace(
            b'dependency_targets = {state="present", value=[]}',
            b'dependency_targets = {state="present", value=['
            b'{dependency_kind="module", dependency_ref="target_home", '
            b'targets=[{scope={kind="dependency",workspace_handle="target"},'
            b'module_id="demo",package_id="home"}],constraints=[]}]}'
        )
        assert raw != consumer_module.manifest.body
        consumer_module = replace(consumer_module, manifest=_body(
            consumer_module.manifest.relative_path, raw
        ))
    unrelated = CodeRetainedScopeModule(
        "unrelated", _body(
            "unrelated/aware.module.toml",
            b'aware = 1\n[[packages]]\nid = "extra"\nkind = "api"\n'
            b'manifest = "extra/aware.extra.toml"\n',
        )
    )
    unrelated_package = CodeRetainedDeclarationPackage(
        "unrelated", "extra", "api", unrelated.manifest.relative_path,
        "unrelated/extra", "aware.extra.toml",
        _body("unrelated/extra/aware.extra.toml", b"unrelated"),
    )
    consumer = replace(consumer, projection=replace(
        consumer.projection,
        modules=(consumer_module, unrelated),
        packages=(*consumer.projection.packages, unrelated_package),
    ))
    return replace(closure, scopes=(consumer, target))


def test_selected_view_retains_v1_nonparticipant_and_complete_v3_arrows():
    closure = _mixed_closure()
    result = derive_selected_participant_view(
        closure, scope_key="consumer", module_id="demo", package_id="home"
    )
    assert result.declaration_closure_digest == closure.closure_digest
    assert result.participants == (
        CodeSelectedParticipant("consumer", "demo", "home"),
        CodeSelectedParticipant("target", "demo", "home"),
        CodeSelectedParticipant("target", "demo", "provider"),
    )
    assert {row.kind for row in result.relationships} == {
        "registration", "direct_dependency"
    }
    assert len(result.profiles) == 1
    assert result.digest == derive_selected_participant_view(
        closure, scope_key="consumer", module_id="demo", package_id="home"
    ).digest
    assert all(item.module_id != "unrelated" for item in result.participants)
    assert {key for key, _package, _occurrence, _declaration in
            selected_qualified_occurrences(closure, result)} == {
        ("consumer", "demo", "home"), ("target", "demo", "home")
    }
    assert len(calculate_declaration_eligibility(
        closure, selected_view=result
    ).packages) == 2
    with pytest.raises(ContractViolation, match="requires all modules v2"):
        calculate_declaration_eligibility(closure)
    validate_selected_participant_view(closure, result)
    with pytest.raises(ContractViolation, match="selected participant set differs"):
        validate_selected_participant_view(
            closure, replace(result, profiles=())
        )


def test_selected_participant_scope_uses_canonical_manifest_path():
    participant = CodeSelectedParticipant(
        "consumer/aware.workspace.toml", "demo", "home"
    )
    assert participant.to_wire()["scope_key"] == "consumer/aware.workspace.toml"
    for scope_key in (
        "/consumer/aware.workspace.toml",
        "consumer/../aware.workspace.toml",
        "consumer\\aware.workspace.toml",
    ):
        with pytest.raises(ContractViolation):
            CodeSelectedParticipant(scope_key, "demo", "home")
    for module_id, package_id in (("module/child", "home"), ("demo", "home/child")):
        with pytest.raises(ContractViolation, match="one component"):
            CodeSelectedParticipant("consumer/aware.workspace.toml", module_id, package_id)


def test_selected_v1_root_refuses_without_affecting_unrelated_v1_membership():
    closure = _mixed_closure()
    with pytest.raises(ContractViolation, match="requires v3"):
        derive_selected_participant_view(
            closure, scope_key="consumer", module_id="unrelated", package_id="extra"
        )


def test_selected_direct_target_requires_complete_v3_occurrence():
    closure = _mixed_closure()
    target = closure.scopes[1]
    module = target.projection.modules[0]
    raw = module.manifest.body.replace(
        b'semantic_version = {state="present", value="1.0"}',
        b'semantic_version = {state="unavailable"}',
    )
    assert raw != module.manifest.body
    module = replace(module, manifest=_body(module.manifest.relative_path, raw))
    target = replace(target, projection=replace(
        target.projection, modules=(module,)
    ))
    with pytest.raises(ContractViolation, match="incomplete"):
        derive_selected_participant_view(
            replace(closure, scopes=(closure.scopes[0], target)),
            scope_key="consumer", module_id="demo", package_id="home"
        )


def test_unrelated_v1_package_still_requires_exact_declared_membership():
    closure = _mixed_closure()
    consumer = closure.scopes[0]
    extra = consumer.projection.packages[-1]
    consumer = replace(consumer, projection=replace(
        consumer.projection,
        packages=(*consumer.projection.packages[:-1], replace(
            extra, package_kind="ontology"
        )),
    ))
    with pytest.raises(ContractViolation, match="authored package membership"):
        derive_selected_participant_view(
            replace(closure, scopes=(consumer, closure.scopes[1])),
            scope_key="consumer", module_id="demo", package_id="home"
        )


def test_missing_direct_target_or_profile_refuses_complete_selection():
    closure = _mixed_closure()
    target = closure.scopes[1]
    target = replace(target, projection=replace(
        target.projection, packages=target.projection.packages[:1]
    ))
    with pytest.raises(ContractViolation):
        derive_selected_participant_view(
            replace(closure, scopes=(closure.scopes[0], target)),
            scope_key="consumer", module_id="demo", package_id="home"
        )
    edge = closure.edges[0]
    with pytest.raises(ContractViolation):
        derive_selected_participant_view(
            replace(closure, edges=(replace(
                edge, semantic_contract_provider_keys=replace(
                    edge.semantic_contract_provider_keys, value=("foreign",)
                )
            ),)),
            scope_key="consumer", module_id="demo", package_id="home"
        )


def test_selected_view_changes_with_unrelated_retained_v1_bytes():
    closure = _mixed_closure(direct_target=False)
    first = derive_selected_participant_view(
        closure, scope_key="consumer", module_id="demo", package_id="home"
    )
    consumer = closure.scopes[0]
    unrelated = consumer.projection.modules[1]
    changed = replace(unrelated, manifest=_body(
        unrelated.manifest.relative_path,
        unrelated.manifest.body + b"# retained comment\n",
    ))
    consumer = replace(consumer, projection=replace(
        consumer.projection, modules=(consumer.projection.modules[0], changed)
    ))
    second = derive_selected_participant_view(
        replace(closure, scopes=(consumer, closure.scopes[1])),
        scope_key="consumer", module_id="demo", package_id="home"
    )
    assert first.participants == second.participants
    assert first.declaration_closure_digest != second.declaration_closure_digest
    assert first.digest != second.digest
