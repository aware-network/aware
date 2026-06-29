from aware_grammar.formatter import format_aware_source


def test_formatter_preserves_discriminate_annotation_args() -> None:
    text = (
        "// Discriminated-union declarations (SSOT: attribute FQNs)\n"
        "ann comms.models.NetworkNodeOperationRequest::operation discriminate key\n"
        'ann comms.models.ProvisionEnvironmentRequest::operation discriminate tag "provision_environment"\n'
        'ann comms.models.GetEnvironmentStatusRequest::operation discriminate tag "get_environment_status"\n'
    )
    formatted = format_aware_source(text=text, indent_size=4)
    assert formatted == text


def test_formatter_does_not_insert_blank_lines_between_adjacent_annotations() -> None:
    text = (
        "ann comms.models.EnvironmentOperationContext::operation discriminate key\n"
        'ann comms.models.FetchCapabilitiesRequest::operation discriminate tag "fetch_capabilities"\n'
        'ann comms.models.DescribeEnvironmentRequest::operation discriminate tag "describe_environment"\n'
        'ann comms.models.InvokeFunctionRequest::operation discriminate tag "invoke_function"\n'
    )
    formatted = format_aware_source(text=text, indent_size=4)
    assert formatted == text


def test_formatter_wraps_long_function_signatures() -> None:
    text = (
        "class ServiceSubscription {\n"
        "    fn build construct (consumer_finance_entity_id UUID, service_id UUID, plan_id UUID, "
        "contract_id UUID, external_subscription_handle String? = null, status "
        "ServiceSubscriptionStatus = active, current_period_start DateTime? = null, "
        "current_period_end DateTime? = null, cancel_at_period_end Bool = false, "
        "metadata_json JsonObject? = null) -> ServiceSubscription {\n"
        "    }\n"
        "}\n"
    )
    formatted = format_aware_source(text=text, indent_size=4, max_line_length=120)
    assert formatted == (
        "class ServiceSubscription {\n"
        "    fn build construct (\n"
        "        consumer_finance_entity_id UUID,\n"
        "        service_id UUID,\n"
        "        plan_id UUID,\n"
        "        contract_id UUID,\n"
        "        external_subscription_handle String? = null,\n"
        "        status ServiceSubscriptionStatus = active,\n"
        "        current_period_start DateTime? = null,\n"
        "        current_period_end DateTime? = null,\n"
        "        cancel_at_period_end Bool = false,\n"
        "        metadata_json JsonObject? = null\n"
        "    ) -> ServiceSubscription {\n"
        "    }\n"
        "}\n"
    )
    assert max(map(len, formatted.splitlines())) <= 120


def test_formatter_wraps_long_return_tuples() -> None:
    text = (
        "class Terminal {\n"
        "    fn create construct (env String[], name String?, cwd String?, shell String = "
        '"/bin/bash") -> (thread_id UUID, descriptor_path String, terminal Terminal, '
        "session JsonObject, backend String?, cols Int?, rows Int?) {\n"
        "    }\n"
        "}\n"
    )
    formatted = format_aware_source(text=text, indent_size=4, max_line_length=120)
    assert formatted == (
        "class Terminal {\n"
        "    fn create construct (env String[], name String?, cwd String?, shell String = "
        '"/bin/bash") -> (\n'
        "        thread_id UUID,\n"
        "        descriptor_path String,\n"
        "        terminal Terminal,\n"
        "        session JsonObject,\n"
        "        backend String?,\n"
        "        cols Int?,\n"
        "        rows Int?\n"
        "    ) {\n"
        "    }\n"
        "}\n"
    )
    assert max(map(len, formatted.splitlines())) <= 120


def test_formatter_formats_projection_blocks() -> None:
    text = (
        "projection ActorFocus is_branchable{\n"
        "root actor.ActorFocus\n"
        "branch main{\n"
        '"""Primary branch."""\n'
        "}\n"
        "actor.ActorFocus::focus aware_identity.Identity\n"
        "}\n"
    )
    formatted = format_aware_source(text=text, indent_size=4)
    assert formatted == (
        "projection ActorFocus is_branchable {\n"
        "    root actor.ActorFocus\n"
        "    branch main {\n"
        '        """Primary branch."""\n'
        "    }\n"
        "    actor.ActorFocus::focus aware_identity.Identity\n"
        "}\n"
    )


def test_formatter_normalizes_projection_view_alias_to_observable() -> None:
    text = (
        "projection Identity {\n"
        "root identity.Identity\n"
        "view onboarding {\n"
        "view welcome construct default { }\n"
        "}\n"
        "}\n"
    )
    formatted = format_aware_source(text=text, indent_size=4)
    assert formatted == (
        "projection Identity {\n"
        "    root identity.Identity\n"
        "    observable onboarding {\n"
        "        observable welcome construct default {\n"
        "        }\n"
        "    }\n"
        "}\n"
    )


def test_formatter_formats_experience_observable_hierarchy() -> None:
    text = (
        "experience AgentMind on Agent{\n"
        "branch default default{\n"
        '"""Canonical default narrative."""\n'
        "}\n"
        "observable agent{\n"
        "view home default state Agent{\n"
        '"""Agent home."""\n'
        "}\n"
        "}\n"
        "}\n"
    )
    formatted = format_aware_source(text=text, indent_size=4)
    assert formatted == (
        "experience AgentMind on Agent {\n"
        "    branch default default {\n"
        '        """Canonical default narrative."""\n'
        "    }\n"
        "    observable agent {\n"
        "        view home default state Agent {\n"
        '            """Agent home."""\n'
        "        }\n"
        "    }\n"
        "}\n"
    )


def test_formatter_preserves_experience_nodes_and_identities() -> None:
    text = (
        "experience home_story on aware_home.home.Home{\n"
        "observable security{\n"
        "view door default state aware_home.home.Door{\n"
        '"""Door state view."""\n'
        "}\n"
        "}\n"
        "node home.Home{\n"
        "id home\n"
        "}\n"
        "node home.Home::doors{\n"
        "id front_door\n"
        "}\n"
        "}\n"
    )
    formatted = format_aware_source(text=text, indent_size=4)
    assert formatted == (
        "experience home_story on aware_home.home.Home {\n"
        "    observable security {\n"
        "        view door default state aware_home.home.Door {\n"
        '            """Door state view."""\n'
        "        }\n"
        "    }\n"
        "    node home.Home {\n"
        "        id home\n"
        "    }\n"
        "    node home.Home::doors {\n"
        "        id front_door\n"
        "    }\n"
        "}\n"
    )


def test_formatter_preserves_experience_section_surfaces() -> None:
    text = (
        "experience home_story on aware_home.home.Home{\n"
        "observable overview{\n"
        "view home default state aware_home.home.Home{}\n"
        "}\n"
        "node home.Home{\n"
        "id home\n"
        "}\n"
        "surface home.primary{\n"
        "section primary;\n"
        "view overview.home;\n"
        "graph home;\n"
        "}\n"
        "surface home.detail{\n"
        "section inspector;\n"
        "view overview.home;\n"
        "node home;\n"
        "source home.primary;\n"
        "}\n"
        "}\n"
    )
    formatted = format_aware_source(text=text, indent_size=4)
    assert formatted == (
        "experience home_story on aware_home.home.Home {\n"
        "    observable overview {\n"
        "        view home default state aware_home.home.Home {\n"
        "        }\n"
        "    }\n"
        "    node home.Home {\n"
        "        id home\n"
        "    }\n"
        "    surface home.primary {\n"
        "        section primary;\n"
        "        view overview.home;\n"
        "        graph home;\n"
        "    }\n"
        "    surface home.detail {\n"
        "        section inspector;\n"
        "        view overview.home;\n"
        "        node home;\n"
        "        source home.primary;\n"
        "    }\n"
        "}\n"
    )


def test_formatter_preserves_class_attribute_identity_key_marker() -> None:
    text = "class User {\n" "    identity_email String key\n" "}\n"
    formatted = format_aware_source(text=text, indent_size=4)
    assert formatted == text


def test_formatter_preserves_function_input_identity_key_marker() -> None:
    text = (
        "class Conversation {\n"
        "    fn build construct (title String? = null, description String? = null, "
        'key String key = "default") -> Conversation {\n'
        "    }\n"
        "}\n"
    )
    formatted = format_aware_source(text=text, indent_size=4)
    assert 'key String key = "default"' in formatted


def test_formatter_formats_binding_blocks() -> None:
    text = (
        "binding aware_home_api aware_home{\n"
        "map door_by_label door.DoorDevice home.Door.label{\n"
        '"""Resolve external door payload onto canonical Door.label."""\n'
        "template{\n"
        '"device_id::{device_id}_provider::{provider}_label::{door_label}"\n'
        "}\n"
        "}\n"
        "}\n"
    )
    formatted = format_aware_source(text=text, indent_size=4)
    assert formatted == (
        "binding aware_home_api aware_home {\n"
        "    map door_by_label door.DoorDevice home.Door.label {\n"
        '        """Resolve external door payload onto canonical Door.label."""\n'
        "        template {\n"
        '            "device_id::{device_id}_provider::{provider}_label::{door_label}"\n'
        "        }\n"
        "    }\n"
        "}\n"
    )


def test_formatter_formats_api_endpoint_contract_blocks() -> None:
    text = (
        "api home_devices{\n"
        "capability lock_door{\n"
        "endpoint lock_door aware_home_api.door.LockDoor{\n"
        '"""Lock a door by label."""\n'
        "response aware_home_api.door.LockDoorResult;\n"
        "stream server{\n"
        "event snapshot aware_home_api.door.DoorSnapshot;\n"
        "event delta aware_home_api.door.DoorDelta;\n"
        "}\n"
        "}\n"
        "}\n"
        "graph aware_home{\n"
        "capability lock_door{\n"
        "function lock aware_home.home.Door.lock;\n"
        "}\n"
        "}\n"
        "}\n"
    )
    formatted = format_aware_source(text=text, indent_size=4)
    assert formatted == (
        "api home_devices {\n"
        "    capability lock_door {\n"
        "        endpoint lock_door aware_home_api.door.LockDoor {\n"
        '            """Lock a door by label."""\n'
        "            response aware_home_api.door.LockDoorResult;\n"
        "            stream server {\n"
        "                event snapshot aware_home_api.door.DoorSnapshot;\n"
        "                event delta aware_home_api.door.DoorDelta;\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "    graph aware_home {\n"
        "        capability lock_door {\n"
        "            function lock aware_home.home.Door.lock;\n"
        "        }\n"
        "    }\n"
        "}\n"
    )


def test_formatter_formats_service_blocks() -> None:
    text = (
        "service workspace{\n"
        "api workspace_api;\n"
        "experience workspace_coordination;\n"
        "operation compile{\n"
        "endpoint workspace_api.compilation.compile;\n"
        "view workspace_coordination.compile_status{provider service_operation;}\n"
        "role identity.compiler{access operation;scope operation compile;}\n"
        "}\n"
        "operation diagnose{\n"
        "endpoint workspace_api.diagnostics.run;\n"
        "settlement reserve_and_finalize;\n"
        "price{\n"
        "coin USD;\n"
        "type fixed;\n"
        "fixed_amount 2.5;\n"
        'effective_from "2026-04-21T00:00:00Z";\n'
        "policy{\n"
        "fail_closed true;\n"
        "}\n"
        "}\n"
        "}\n"
        "contract default_subscription{\n"
        "kind subscription;\n"
        "projection_experience workspace_coordination;\n"
        "grant operation compile{access operation;}\n"
        "grant actor_role identity.compiler{access service;scope service default;role_assignment_binding_required true;}\n"
        "}\n"
        "}\n"
    )
    formatted = format_aware_source(text=text, indent_size=4)
    assert formatted == (
        "service workspace {\n"
        "    api workspace_api;\n"
        "    experience workspace_coordination;\n"
        "    operation compile {\n"
        "        endpoint workspace_api.compilation.compile;\n"
        "        view workspace_coordination.compile_status {\n"
        "            provider service_operation;\n"
        "        }\n"
        "        role identity.compiler {\n"
        "            access operation;\n"
        "            scope operation compile;\n"
        "        }\n"
        "    }\n"
        "    operation diagnose {\n"
        "        endpoint workspace_api.diagnostics.run;\n"
        "        settlement reserve_and_finalize;\n"
        "        price {\n"
        "            coin USD;\n"
        "            type fixed;\n"
        "            fixed_amount 2.5;\n"
        '            effective_from "2026-04-21T00:00:00Z";\n'
        "            policy {\n"
        "                fail_closed true;\n"
        "            }\n"
        "        }\n"
        "    }\n"
        "    contract default_subscription {\n"
        "        kind subscription;\n"
        "        projection_experience workspace_coordination;\n"
        "        grant operation compile {\n"
        "            access operation;\n"
        "        }\n"
        "        grant actor_role identity.compiler {\n"
        "            access service;\n"
        "            scope service default;\n"
        "            role_assignment_binding_required true;\n"
        "        }\n"
        "    }\n"
        "}\n"
    )
