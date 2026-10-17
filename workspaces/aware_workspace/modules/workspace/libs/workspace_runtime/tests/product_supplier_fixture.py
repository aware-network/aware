"""Neutral executable fixture owner, admitted before original host assembly.

This is test meaning, not an API/Meta/Ontology implementation or installed origin.
All source, catalog, execution and publisher checks are production entrances.
"""

from dataclasses import dataclass, fields, replace

from aware_code_semantic_contract_runtime import (
    CodeSemanticMaterializationIntent,
    CodeSemanticMaterializationProfileBinding,
    CodeSemanticRequiredResultProduct,
    ConsumedRoleDeclaration,
    ContentDigest,
    PreparedSemanticEffectEnvelope,
    ProfileInputDeclaration,
    ProviderDerivation,
    ProviderExecutionBinding,
    RoleBinding,
    SemanticBody,
    SemanticBodyCodecBinding,
    SemanticConfigurationCoordinate,
    SemanticContractInvocation,
    SemanticContractResult,
    SemanticDependencyDemand,
    SemanticDependencyDemandSet,
    SemanticImpactCoordinate,
    SemanticImplementationCoordinate,
    SemanticTransitionEnvelope,
    SemanticValueCoordinate,
    TerminalStatus,
    TypedEmptyCoordinate,
    canonical_json_bytes,
)
from aware_code_semantic_contract_runtime import selected_provider as selected
from aware_code_semantic_contract_runtime.dependency_input_codec import (
    SemanticDependencyProductInputCodec,
)
from aware_code_semantic_contract_runtime.dependency_inputs import (
    SemanticAuthoredDependency,
    SemanticDependencyPlanningInput,
)
from aware_code_semantic_contract_runtime.product_contribution import (
    read_selected_provider_product_contribution,
)
from aware_code_semantic_contract_runtime.product_execution_input_plan import (
    ProductExecutionInputPlan,
    ProductExecutionInputSourceScope,
    ProductExecutionInputStep,
)
from aware_code_semantic_contract_runtime.retained_input_projection_codec import (
    DeclarationTargetInventoryCodec,
    DependencyPlanningInputCodec,
    PackageContextInputCodec,
)
from aware_code_semantic_contract_runtime.runtime import SemanticContractRuntime
from aware_code_semantic_contract_runtime.semantic_input_producer import (
    SemanticInputContextContract,
    SemanticInputProducerDeclaration,
    SemanticInputSourceContract,
)
from test_direct_cli_dependency_planning import RAW, ROOT_KEY, SUPPLIER_KEY, Catalog
from test_materialization_graph_planner import _code_binding
from test_semantic_materialization_publication import _JsonCodec


@dataclass(frozen=True)
class Input:
    invocation: SemanticContractInvocation
    input_bodies: tuple[SemanticBody, ...]
    predecessor_body: SemanticBody | None = None


def body(role, contract, payload):
    digest = ContentDigest.of_bytes(payload)
    return SemanticBody(SemanticValueCoordinate(role, contract, "fixture:" + role + ":" + digest.value, digest, len(payload)), payload)


def supplier_factory(calls, *, consumer=False, dependency_role="semantic_dependencies"):
    key = ROOT_KEY if consumer else SUPPLIER_KEY
    template = _code_binding("example", key)
    declaration = replace(template.profile_declaration.providers[0], output_roles=(), allows_typed_empty=True)
    source_input = template.profile_declaration.inputs[0]
    profile_inputs, steps = template.profile_declaration.inputs, template.profile_declaration.steps
    if consumer:
        dependency = SemanticDependencyProductInputCodec.contract
        declaration = replace(declaration, consumed_roles=(
            ConsumedRoleDeclaration(dependency_role, (dependency,)), *declaration.consumed_roles))
        profile_inputs = (ProfileInputDeclaration(dependency_role, dependency), *profile_inputs)
        steps = (replace(steps[0], bindings=(RoleBinding(dependency_role, dependency_role), *steps[0].bindings)),)
    profile = replace(template.profile_declaration, inputs=profile_inputs, steps=steps,
        providers=(declaration,), terminal_output_roles=())
    usage = {}
    artifact, configuration = canonical_json_bytes({"fixture": key}), canonical_json_bytes({"configuration": key})
    binding = ProviderExecutionBinding(key,
        SemanticImplementationCoordinate(key, ContentDigest.of_bytes(artifact)),
        SemanticConfigurationCoordinate(key, ContentDigest.of_bytes(configuration)))
    values = {field.name: getattr(template, field.name) for field in fields(template) if field.name != "binding_digest"}
    values.update(package_families=("example",), package_roles=("example",),
        profile_declaration=profile, provider_execution_bindings=(binding,),
        dependency_planner_implementation=SemanticImplementationCoordinate(key + ".planner", ContentDigest.of_bytes(key.encode())),
        dependency_planner_configuration=binding.configuration,
        result_product_contracts=tuple(sorted((CodeSemanticRequiredResultProduct.create(role=role.role, contract=role.contract)
            for role in (declaration.result_role, declaration.effect_role)), key=lambda item: item.role)))
    entry = CodeSemanticMaterializationProfileBinding.create(**values)
    contracts = {*(item.contract for item in profile.inputs), declaration.result_role.contract,
        declaration.transition_contract, declaration.effect_contract}
    codecs = {contract: _JsonCodec(contract) for contract in contracts}
    if consumer:
        codecs[SemanticDependencyProductInputCodec.contract] = SemanticDependencyProductInputCodec()

    class Provider:
        @property
        def declaration(self):
            return declaration

        async def derive(self, step):
            return self.result(step)

        def result(self, step):
            calls.append(("execute", step.invocation.target_package.package_ref, key))
            source = next(item for item in step.inputs if item.target_role == "source")
            dependencies = ()
            if consumer:
                admitted = next(item for item in step.inputs if item.target_role == dependency_role).value
                assert len(admitted.products) == 2
                assert admitted.products[0].coordinate == admitted.products[1].coordinate
                assert admitted.products[0].body == admitted.products[1].body
                dependencies = tuple(item.body.coordinate.digest.value for item in admitted.products)
            candidate = body("result", declaration.result_role.contract, canonical_json_bytes({
                "package": step.invocation.target_package.package_ref,
                "input": source.value,
                "dependencies": list(dependencies),
            }))
            transition_body = body("transition", declaration.transition_contract, b'{"created":true}')
            impacts = (SemanticImpactCoordinate("supplier", "definition", step.invocation.target_package.package_ref),)
            transition = SemanticTransitionEnvelope(key, declaration.result_role.contract, declaration.transition_contract,
                step.invocation.predecessor, candidate.coordinate, transition_body.coordinate, impacts, step.input_closure_digest)
            effect_body = body("effect", declaration.effect_contract, b'{"retained":true}')
            effect = PreparedSemanticEffectEnvelope(key, declaration.effect_contract, transition.digest,
                step.invocation.predecessor, candidate.coordinate, effect_body.coordinate, (), impacts, ())
            return ProviderDerivation(SemanticContractResult(TerminalStatus.DELTA, step.invocation.digest,
                transition=transition, effect=effect), tuple(sorted((candidate, transition_body, effect_body),
                    key=lambda item: canonical_json_bytes(item.coordinate.to_wire()))))

        def execute(self, step, value):
            closure = self.input_closure(value)
            assert step.invocation is closure.invocation
            return self.result(step)

        def input_closure(self, value):
            assert type(value) is Input
            return selected.SelectedProviderInvocationClosure(value.invocation, value.input_bodies, value.predecessor_body)

    class Planner:
        async def plan(self, *, package, intent, selected_match, planning_input):
            calls.append(("plan", package.package_ref, key))
            assert consumer or not planning_input.dependencies
            demands = tuple(SemanticDependencyDemand.create(
                consumer_semantic_role=role, authored_dependency_kind=item.dependency_kind,
                authored_dependency_ref=item.dependency_ref, target_constraints=item.target_constraints,
                required_result_role="result", result_product_contract=declaration.result_role.contract,
                target_intent=CodeSemanticMaterializationIntent.create(operation_kind="materialize",
                    requested_semantic_root_refs=item.targets[0].semantic_root_refs,
                    requested_terminal_output_roles=("result",), semantic_configuration_coordinate=None), cardinality="required",
            ) for item in planning_input.dependencies for role in ("first", "second")
                if consumer and usage[package.package_ref, planning_input.source_identity_digest.value])
            return SemanticDependencyDemandSet.create(package=package, intent=intent,
                profile_ref=profile.profile_ref, profile_digest=profile.digest, contract_profile_binding_digest=entry.binding_digest,
                planner_implementation_ref=entry.dependency_planner_implementation.implementation_ref,
                planner_implementation_digest=entry.dependency_planner_implementation.closure_digest,
                planner_configuration=entry.dependency_planner_configuration,
                demands=tuple(sorted(demands, key=lambda item: item.demand_digest.value)))

    def planning_input(value):
        calls.append(("source", value.package_identity.package.package_ref, key))
        inventory = DeclarationTargetInventoryCodec().decode(value.context_bodies[0].canonical_body)
        context = PackageContextInputCodec().decode(value.context_bodies[1].canonical_body)
        assert inventory.package == context.package == value.package_identity.package
        usage[context.package.package_ref, context.source_identity_digest.value] = any(
            b"requires:target" in item.canonical_body for item in value.sources)
        value = SemanticDependencyPlanningInput(context.package, context.source_identity_digest,
            tuple(SemanticAuthoredDependency(item.dependency_kind, item.dependency_ref, item.targets, item.target_constraints)
                for item in inventory.entries))
        return body("planning_input", DependencyPlanningInputCodec.contract, DependencyPlanningInputCodec().encode(value))

    def execution_input(value):
        calls.append(("execution_input", value.package_identity.package.package_ref, key))
        return body("source", source_input.contract, canonical_json_bytes({
            "original_paths": [[source.source.relative_path, source.source.coordinate.digest.value] for source in value.sources],
        }))

    def assemble(value):
        dependencies = () if value.dependency_body is None else tuple(sorted(
            {item.coordinate for item in SemanticDependencyProductInputCodec().decode(value.dependency_body.canonical_body).products},
            key=lambda item: canonical_json_bytes(item.to_wire())))
        invocation = SemanticContractInvocation(value.invocation_ref, value.idempotency_key,
            profile.profile_ref, profile.digest, value.package, "materialize",
            tuple(sorted((item.coordinate for item in value.input_bodies), key=lambda item: item.role)),
            TypedEmptyCoordinate(declaration.result_role.contract), dependencies,
            tuple(SemanticBodyCodecBinding(contract, codec.implementation) for contract, codec in sorted(codecs.items(),
                key=lambda item: canonical_json_bytes(item[0].to_wire()))), (binding,), ())
        return Input(invocation, value.input_bodies)

    def recipe(original):
        assert read_selected_provider_product_contribution(original).profile == profile
        declared = SemanticInputProducerDeclaration(key + ".execution-input", profile.profile_ref,
            binding.implementation, binding.configuration, (SemanticInputSourceContract("raw", RAW),), "source", source_input.contract)
        return ProductExecutionInputPlan((ProductExecutionInputStep("source", declared, execution_input,
            (ProductExecutionInputSourceScope("raw"),)),), (0,), assemble,
            dependency_input_role=dependency_role if consumer else "")

    def factory():
        provider = Provider()
        runtime = SemanticContractRuntime(profile, {key: provider}, codecs)

        def catalog(original):
            admitted = read_selected_provider_product_contribution(original)
            return Catalog(original, (entry,), ((binding.implementation, binding.configuration, admitted.executable),), Planner())

        return selected._SelectedProviderFactoryProduct(runtime, provider, binding, provider.execute, provider.input_closure,
            artifact, configuration, catalog_contribution_producer=catalog,
            planning_input_declaration=SemanticInputProducerDeclaration(key + ".planning-input", profile.profile_ref,
                binding.implementation, binding.configuration, (SemanticInputSourceContract("raw", RAW),),
                "planning_input", DependencyPlanningInputCodec.contract, context_contracts=(
                    SemanticInputContextContract("declaration_inventory", DeclarationTargetInventoryCodec.contract),
                    SemanticInputContextContract("package_context", PackageContextInputCodec.contract))),
            planning_input_producer=planning_input, execution_input_contribution_producer=recipe)

    return selected._admit_selected_provider_factory(factory_ref=key, provider_key=key, selection_factory=factory), profile
