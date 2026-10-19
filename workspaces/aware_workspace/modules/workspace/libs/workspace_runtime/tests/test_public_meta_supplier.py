"""Actual Meta dependency graph; disposable package publication, no OIG effects."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
import tomllib
from contextlib import ExitStack, asynccontextmanager
from pathlib import Path

import pytest
from aware_code_retained_registry_policy_runtime.product_execution_inputs import (
    read_product_execution_input_completion,
)
from aware_code_semantic_contract_runtime import product_contribution as contributions
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_meta_contract_runtime_provider import selected_factory as meta
from aware_meta_contract_runtime_provider.observable_identity_codec import (
    ObservableModelSelectionV2,
    encode_observable_model_selection_v2,
)
from aware_meta_contract_runtime_provider.profile import (
    META_PROVIDER_V2_KEY,
    meta_provider_profile_v2,
)
from aware_ontology_meta_preparation_provider.meta_product_source import (
    construct_ontology_meta_authored_primitives_construction_factory_product,
)

# isort: split

from aware_workspace_materialize_transport import WorkspaceMaterializeCommandProposalV3
from aware_workspace_runtime import direct_cli_selected_host as local
from aware_workspace_runtime import direct_command_composition as composition
from aware_workspace_runtime.direct_cli_product_planning import (
    plan_direct_cli_selected_product,
)
from aware_workspace_runtime.direct_cli_product_publication import (
    publish_direct_cli_selected_product,
    read_direct_cli_product_execution_context,
)

# isort: split

from test_dependency_scope_admission import fixture as sources
from test_observed_semantic_issuers import PROVIDER, occurrence

REPO = Path(__file__).resolve().parents[6]
PACKAGES = {
    name: REPO / "aware_kernel/modules" / name / "ontology"
    for name in ("storage", "content", "code", "history", "meta")
}
PACKAGES["workflow"] = REPO / "aware_coordination/modules/workflow/ontology"


def repository(root, target):
    """Author only disposable participation; copy complete original source trees."""
    pending, closure = [target], {}
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        original = PACKAGES[name]
        manifest = tomllib.loads((original / "structure/aware.toml").read_text())
        closure[name] = manifest
        pending.extend(row["package_name"].removesuffix("-ontology") for row in manifest.get("dependencies", ()))
    module = root / "consumer/modules/main"
    declarations = ["aware=3\n"]
    for name, manifest in sorted(closure.items()):
        original = PACKAGES[name]
        destination = module / name
        destination.mkdir()
        shutil.copyfile(original / "aware.ontology.toml", destination / "aware.ontology.toml")
        (destination / "structure").mkdir()
        shutil.copyfile(original / "structure/aware.toml", destination / "structure/aware.toml")
        source_directory = manifest.get("build", {}).get("sources_dir", "aware")
        shutil.copytree(original / "structure" / source_directory, destination / "structure" / source_directory)
        package = manifest["package"]
        mappings = [{
            "dependency_kind": "meta-package", "dependency_ref": row["package_name"],
            "targets": [{"scope": {"kind": "local"}, "module_id": "main",
                         "package_id": row["package_name"].removesuffix("-ontology")}],
            "constraints": [{"constraint_kind": "semantic_provider_key", "constraint_value": META_PROVIDER_V2_KEY}],
        } for row in manifest.get("dependencies", ())]
        # JSON scalar syntax is TOML-compatible; inline tables require '='.
        def inline(value):
            if isinstance(value, dict):
                return "{" + ",".join(key + "=" + inline(item) for key, item in value.items()) + "}"
            if isinstance(value, list):
                return "[" + ",".join(map(inline, value)) + "]"
            return json.dumps(value)
        admission = occurrence(package["package_name"], inline(mappings))
        admission = admission.replace('value={module_id="main",', 'value={scope={kind="local"},module_id="main",')
        admission = admission.replace('value="1.0"', 'value="' + str(package.get("version_number", 1)) + '"')
        admission = admission.replace('namespace={state="present",value="' + package["package_name"] + '"}',
            'namespace={state="present",value="' + package["fqn_prefix"] + '"}')
        # The declared package namespace owns all original source definitions;
        # no guessed classes, cropped sources or transitive dependencies.
        admission = admission.replace('value=["' + package["package_name"] + '.a","' + package["package_name"] + '.b"]',
            'value=["' + package["fqn_prefix"] + '"]')
        declarations.append(f'[[packages]]\nid="{name}"\nkind="ontology"\nmanifest="{name}/aware.ontology.toml"\n' + admission)
    (module / "provider").mkdir()
    (module / "provider/pyproject.toml").write_bytes(b"source-qualified original Meta factory")
    profile = meta_provider_profile_v2()
    provider = PROVIDER.replace('provider_key="demo"', f'provider_key="{META_PROVIDER_V2_KEY}"')
    provider = provider.replace("example_toml", "aware_meta_toml").replace("aware.example.toml", "aware.ontology.toml")
    provider = provider.replace('semantic_package_family="example"', 'semantic_package_family="ontology"')
    provider = provider.replace('semantic_package_kind="example"', 'semantic_package_kind="ontology"')
    provider = provider.replace('role="example",name="example"', 'role="aware_meta.provider",name="meta_aware_package"')
    provider = re.sub(r"profiles=\[.*?\n\]", 'profiles=[{stage="graph_product",profile_ref="' + profile.profile_ref
        + '",profile_version="' + profile.version + '",profile_digest="' + profile.digest.to_wire() + '"}]',
        provider, flags=re.DOTALL)
    declarations.append(provider)
    (module / "aware.module.toml").write_text("\n".join(declarations))
    return closure


@asynccontextmanager
async def retained_genuine_meta_dependency_graph(tmp_path, monkeypatch, *, target, execute=True):
    """Yield original operands only while their command/host/source lifetime lives.

    Test support, not another issuer, assembler or portable custody contract.
    A fixed Meta consumer must run inside this context, never from its JSON log.
    """
    phases = []
    started = time.perf_counter()
    evidence = os.environ.get("WORKSPACE_META_PHASE_EVIDENCE")

    def record(phase, since, **fields):
        row = {"phase": phase, "seconds": time.perf_counter() - since, **fields}
        phases.append(row)
        if evidence:
            with Path(evidence).open("a") as stream:
                stream.write(json.dumps({"target": target, "execute": execute, **row}) + "\n")

    factory = selected._admit_selected_provider_factory(
        factory_ref="proof:original-meta-head-backed:" + target, provider_key=META_PROVIDER_V2_KEY,
        selection_factory=construct_ontology_meta_authored_primitives_construction_factory_product)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "package-product-state"))
    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: factory)
    closure = {}

    def author(root):
        closure.update(repository(root, target))

    try:
        since = time.perf_counter()
        async with sources(tmp_path, author, retention_limits={"body_capacity": 4096}) as (root, _, _, borrowed, _, _):
            record("source_observation", since, packages=len(closure))
            proposal = WorkspaceMaterializeCommandProposalV3.create(
                attempt_ref="proof:genuine-meta:" + target, participant_checkout_root=str(root),
                workspace_manifest_name="consumer/aware.workspace.toml",
                package_address=("Consumer", "main", target), plan_only=not execute)
            since = time.perf_counter()
            with composition._compose_direct_workspace_command_source(
                session=borrowed._session, store=borrowed._store, proposal=proposal,
            ) as (command, _, source), local.compose_direct_cli_product_candidates(command, source) as candidates, \
                    local.compose_direct_cli_selected_product(command, source, participating_sources=candidates) as product, \
                    ExitStack() as retained:
                record("command_source_catalog", since, participants=len(product.participants))
                since = time.perf_counter()
                planned = await plan_direct_cli_selected_product(command, source, product, retention=retained,
                    allow_unused_sources=True)
                record("graph_planning", since, nodes=len(planned.plan.graph.nodes), edges=len(planned.plan.graph.edges))
                assert len(planned.plan.graph.nodes) == len(closure)
                if not execute:
                    yield planned
                    return
                participant = next(item for item in product.participants if item.source is source)
                original = contributions.read_selected_provider_product_contribution(participant.contribution)
                owner = meta.export_meta_construction_owner(original.expected.runtime,
                    original.expected.registration, original.executable)
                retained.callback(owner.close)
                since = time.perf_counter()
                published = await publish_direct_cli_selected_product(command, source, product, planned, retention=retained)
                record("tracked_graph_execution_and_publication", since,
                    nodes=len(published.result.ordered_node_results), products=len(published.result.ordered_fulfilled_products))
                binding = next(item for item in planned.plan.graph_execution_binding.ordered_node_bindings
                               if item.package.package_ref == product.package_ref)
                context = read_direct_cli_product_execution_context(command, product, planned, node_digest=binding.node_digest)
                completion = read_product_execution_input_completion(product.host.code_host, context)
                since = time.perf_counter()
                head = owner.retain(original.expected.registration, completion)
                coordinate, body = owner.read_construction(original.expected.registration, head, completion=completion)
                source_export = owner.capture_construction_root_export(original.expected.registration, head,
                    completion=completion)
                retained.callback(owner.close_construction_root_export, original.expected.registration, source_export)
                owner.require_construction_root_export(original.expected.registration, source_export)
                decoded = meta.decode_meta_aware_package_portable_result_v2(body)
                meaning = json.loads(decoded.semantic_body)
                name = "ObjectConfigGraph" if target == "meta" else "Issue"
                declaration = next(row for row in meaning[6] if row[1] == name)
                observable = declaration[9][0]
                path = "graph/config/object_config_graph_projection.aware" if target == "meta" else "issue/issue_projection.aware"
                selection = encode_observable_model_selection_v2(ObservableModelSelectionV2(
                    "aware.meta.observable-model-selection.v2", "aware.meta.observable-branch-identity.v2",
                    declaration[1], observable[0], declaration[6], "root", path))
                model = owner.capture_original_source_model(original.expected.registration, head,
                    completion=completion, selection_body=selection)
                schema = original.executable.capture_observable_identity_schema(model)
                export = owner.capture_governing_definition_export(original.expected.registration, head,
                    completion=completion, model=model, schema=schema)
                retained.callback(owner.close_governing_definition_export, original.expected.registration, export)
                assert owner.require_governing_definition_export(original.expected.registration, export)[:2] == (coordinate, body)
                record("original_custody_and_export", since, body_sha256=hashlib.sha256(body).hexdigest())
                yield owner, original.expected.registration, head, completion, source_export, export
        record("complete", started)
    except BaseException as error:
        record("refusal", started, error_type=type(error).__name__, message=str(error)[:1200])
        raise
    finally:
        state = selected._factory_state(factory)
        if selected._FACTORY_PROVIDER_KEYS.get(state.provider_key) is factory:
            del selected._FACTORY_PROVIDER_KEYS[state.provider_key]
        if selected._FACTORY_REFS.get(state.factory_ref) is factory:
            del selected._FACTORY_REFS[state.factory_ref]
        selected._FACTORIES.pop(id(factory), None)


@pytest.mark.parametrize("target", ["meta", "workflow"])
@pytest.mark.parametrize("execute", [False, True])
async def test_genuine_meta_dependency_graph(tmp_path, monkeypatch, target, execute):
    async with retained_genuine_meta_dependency_graph(tmp_path, monkeypatch, target=target, execute=execute) as value:
        if not execute:
            assert len(value.plan.graph.nodes) >= 3
            return
        owner, registration, head, completion, source_export, governing_export = value
        owner.require_construction_root_export(registration, source_export)
        owner.require_governing_definition_export(registration, governing_export)
        owner.read_construction(registration, head, completion=completion)
