"""Real Home Attention supplier on the public graph; neutral consumer explicit."""

from pathlib import Path

import pytest
from aware_attention_definition_contract_runtime_provider.profile import (
    ATTENTION_DEFINITION_MANIFEST_REF,
    ATTENTION_DEFINITION_PROVIDER_KEY,
    attention_definition_profile,
)
from aware_attention_definition_contract_runtime_provider.selected_factory import (
    construct_attention_definition_factory_product,
)
from aware_code_semantic_contract_runtime import CodeSemanticRequiredResultProduct
from aware_code_semantic_contract_runtime import selected_provider as selected

# isort: split

from aware_workspace_command.materialize_command import (
    _continue_direct_materialize_profile,
)
from aware_workspace_materialize_transport import WorkspaceMaterializeCommandProposalV3
from aware_workspace_runtime import direct_cli_selected_host as local

# isort: split

from product_supplier_fixture import supplier_factory
from test_dependency_scope_admission import fixture as sources
from test_direct_cli_dependency_planning import ROOT_KEY, SUPPLIER_KEY, _repository

HOME = Path(__file__).resolve().parents[6] / "aware_home/modules/home/attentions/home_story_app_shell"


@pytest.fixture
def owners():
    calls = []
    target = CodeSemanticRequiredResultProduct.create(
        role="attention_definition_manifest", contract=ATTENTION_DEFINITION_MANIFEST_REF)
    consumer = supplier_factory(calls, consumer=True, supplier_product=target)
    supplier = selected._admit_selected_provider_factory(
        factory_ref="proof:public-original-attention-supplier", provider_key=ATTENTION_DEFINITION_PROVIDER_KEY,
        selection_factory=construct_attention_definition_factory_product)
    admitted = {ROOT_KEY: consumer, ATTENTION_DEFINITION_PROVIDER_KEY: (supplier, attention_definition_profile())}
    try:
        yield admitted, calls
    finally:
        for admission, _ in admitted.values():
            state = selected._factory_state(admission)
            if selected._FACTORY_PROVIDER_KEYS.get(state.provider_key) is admission:
                del selected._FACTORY_PROVIDER_KEYS[state.provider_key]
            if selected._FACTORY_REFS.get(state.factory_ref) is admission:
                del selected._FACTORY_REFS[state.factory_ref]
            selected._FACTORIES.pop(id(admission), None)


def authored(root, profiles):
    _repository(root, {ROOT_KEY: profiles[ROOT_KEY], SUPPLIER_KEY: profiles[ATTENTION_DEFINITION_PROVIDER_KEY]})
    directory = root / "consumer/modules/main/supplier"
    for path in directory.iterdir():
        path.unlink()
    for path in HOME.iterdir():
        assert path.is_file(), "complete fixture capture must support every original member"
        (directory / path.name).write_bytes(path.read_bytes())
    module = root / "consumer/modules/main/aware.module.toml"
    chunks = module.read_text().replace(SUPPLIER_KEY, ATTENTION_DEFINITION_PROVIDER_KEY).split("[[packages]]")
    for index, chunk in enumerate(chunks):
        if chunk.startswith('\nid="supplier"\n'):
            chunk = chunk.replace('kind="example"', 'kind="attention"').replace('supplier/aware.example.toml', 'supplier/aware.attention.toml')
            chunk = chunk.replace('semantic_package_name={state="present",value="supplier"}',
                'semantic_package_name={state="present",value="home_story_app_shell"}')
            chunk = chunk.replace('semantic_version={state="present",value="1.0"}', 'semantic_version={state="present",value="1"}')
            chunk = chunk.replace('namespace={state="present",value="supplier"}', 'namespace={state="present",value="home_story_app_shell"}')
            chunk = chunk.replace('value=["supplier.a","supplier.b"]',
                'value=["home_story_app_shell.configuration_map","home_story_app_shell.scene_view"]')
        elif chunk.startswith('\nid="provider_supplier"\n'):
            chunk = chunk.replace("example_toml", "aware_attention_toml").replace("aware.example.toml", "aware.attention.toml")
            chunk = chunk.replace('semantic_package_family="example"', 'semantic_package_family="attention"')
            chunk = chunk.replace('semantic_package_kind="example"', 'semantic_package_kind="attention"')
            chunk = chunk.replace('role="example",name="example"', 'role="aware_attention.provider",name="attention_definition"')
        chunks[index] = chunk
    module.write_text("[[packages]]".join(chunks))


@pytest.mark.parametrize("execute", [False, True])
async def test_public_original_attention_supplier(tmp_path, monkeypatch, owners, execute):
    admitted, calls = owners
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "public-state"))
    monkeypatch.setattr(local, "admit_installed_semantic_stage_factory", lambda key: admitted[key][0])
    profiles = {key: profile for key, (_, profile) in admitted.items()}
    original = {path.name: path.read_bytes() for path in HOME.iterdir()}
    async with sources(tmp_path, lambda root: authored(root, profiles)) as (root, *_):
        copied = root / "consumer/modules/main/supplier"
        assert {path.name: path.read_bytes() for path in copied.iterdir()} == original
        proposal = WorkspaceMaterializeCommandProposalV3.create(
            attempt_ref="proof:public-attention-dependency", participant_checkout_root=str(root),
            workspace_manifest_name="consumer/aware.workspace.toml", package_address=("Consumer", "main", "consumer"),
            plan_only=not execute)
        inspection, diagnostic, published = await _continue_direct_materialize_profile(proposal=proposal)
        assert diagnostic is None
        assert (inspection.graph_node_count, inspection.graph_edge_count) == (2, 2)
        if not execute:
            assert published is None
            assert [kind for kind, _, _ in calls] == ["source", "plan"]
            return
        assert published is not None
        result = published.result
        assert len(result.ordered_node_results) == 2
        supplier, consumer = result.ordered_node_results
        assert supplier.package_head_reread_evidence.head.result_coordinate.role == "attention_definition_manifest"
        assert supplier.package_head_reread_evidence.head.result_coordinate.contract == ATTENTION_DEFINITION_MANIFEST_REF
        assert consumer.package_head_reread_evidence.head.result_coordinate.role == "result"
        assert all(item.package_head_reread_evidence.materialization_head_revision == 1 for item in result.ordered_node_results)
        assert len(result.ordered_fulfilled_products) == 2
        assert all(item.consumed_body_coordinate == supplier.package_head_reread_evidence.head.result_coordinate
            for item in result.ordered_fulfilled_products)
        assert [kind for kind, _, _ in calls] == ["source", "plan", "execution_input", "execute"]
    assert {path.name: path.read_bytes() for path in HOME.iterdir()} == original
