from __future__ import annotations

from aware_code.semantic_capability import SemanticCapabilityChangePreview
from aware_code.semantic_materialization import (
    SEMANTIC_SOURCE_SESSION_SOURCE_INDEX_CACHE_KIND,
    SemanticSourceSessionCacheRef,
    SemanticSourceSessionContext,
)
from aware_code.semantic_source_meaning import (
    CODE_SEMANTIC_SOURCE_MEANING_BINDING_CONTRACT_VERSION,
    CodeSemanticSourceIndexRef,
    CodeSemanticSourceMeaningBinding,
    CodeSemanticSourceMeaningContract,
    clear_code_semantic_source_index_cache_for_tests,
    resolve_code_semantic_source_delta_meaning,
    resolve_code_semantic_source_meaning,
)
from aware_code.source_index import (
    CodeGrammarGraphSelector,
    CodeGrammarSource,
    CodeGrammarSourceIndex,
)
from aware_code_ontology.code.code_plan import (
    CodePackageDelta,
    CodePackageDeltaKind,
    CodePackageDeltaPath,
)


def test_meaning_binding_emits_semantic_update_from_grammar_anchor_diff() -> None:
    baseline = _source_index(
        "class TvChannel {\n    channel_number Int key\n}\n",
    )
    current = _source_index(
        "class TvChannel {\n    channel_number String key\n}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_home_attribute_type_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.binding_count == 1
    assert resolution.resolved_binding_count == 1
    assert resolution.changed_binding_count == 1
    assert resolution.diagnostics == ()
    assert resolution.source_index_evidence["parse_count"] == 1
    assert resolution.source_index_evidence["source_count"] == 1

    [delta] = resolution.semantic_deltas
    assert delta.verb == "update"
    assert delta.semantic_key == "meta.attribute:TvChannel.channel_number"
    assert delta.subject_type == "ClassConfigAttributeConfig"
    assert delta.source == "aware_code.semantic_source_meaning"
    assert delta.source_refs == ("home.aware",)
    before_payload = _payload(delta.before_payload)
    after_payload = _payload(delta.after_payload)
    assert before_payload["type"] == "Int"
    assert str(before_payload["text_hash"]).startswith("sha256:")
    assert str(before_payload["source_hash"]).startswith("sha256:")
    assert after_payload["type"] == "String"
    assert str(after_payload["text_hash"]).startswith("sha256:")
    assert str(after_payload["source_hash"]).startswith("sha256:")
    assert delta.metadata["contract_version"] == (
        CODE_SEMANTIC_SOURCE_MEANING_BINDING_CONTRACT_VERSION
    )
    assert delta.metadata["binding_key"] == "meta.attribute.type"
    assert delta.metadata["semantic_field"] == "type"

    [event] = resolution.semantic_events
    assert event.event_key == "meta.attribute:TvChannel.channel_number:type:update"
    assert event.semantic_key == delta.semantic_key
    assert event.delta_keys == (delta.delta_key,)
    assert event.payload["before"] == "Int"
    assert event.payload["after"] == "String"


def test_meaning_binding_derives_template_values_for_generic_attribute_binding() -> (
    None
):
    baseline = _source_index(
        "class TvChannel {\n" "    name String\n" "    channel_number Int key\n" "}\n",
    )
    current = _source_index(
        "class TvChannel {\n"
        "    name String\n"
        "    channel_number String key\n"
        "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_attribute_type_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.binding_count == 1
    assert resolution.resolved_binding_count == 1
    assert resolution.changed_binding_count == 1
    [delta] = resolution.semantic_deltas
    assert delta.semantic_key == "meta.attribute:TvChannel.channel_number"
    assert delta.before_payload is not None
    assert delta.after_payload is not None
    assert delta.before_payload["type"] == "Int"
    assert delta.after_payload["type"] == "String"
    graph_selector = _payload(delta.metadata["graph_selector"])
    assert graph_selector["class_name"] == "TvChannel"
    assert graph_selector["attribute_name"] == "channel_number"
    source_index = _payload(delta.metadata["source_index"])
    template_values = _payload(source_index["template_values"])
    assert template_values["class_name"] == "TvChannel"
    assert template_values["attribute_name"] == "channel_number"


def test_meaning_binding_derives_attribute_membership_identity_key_update() -> None:
    baseline = _source_index(
        "class TvChannel {\n" "    channel_number Int\n" "}\n",
    )
    current = _source_index(
        "class TvChannel {\n" "    channel_number Int key\n" "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_attribute_membership_identity_key_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.changed_binding_count == 1
    [delta] = resolution.semantic_deltas
    assert delta.verb == "update"
    assert delta.semantic_key == (
        "meta.attribute:TvChannel.channel_number/membership:class_config"
    )
    assert delta.subject_type == "aware_meta.ClassConfigAttributeConfig"
    before_payload = _payload(delta.before_payload)
    after_payload = _payload(delta.after_payload)
    assert before_payload["is_identity_key"] is False
    assert after_payload["is_identity_key"] is True
    assert _payload(after_payload["attribute_membership_signature"]) == {
        "owner_kind": "class",
        "is_identity_key": True,
    }
    [operation] = resolution.typed_operations
    assert operation.operation_family == "update"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.attribute.membership.update"
    )
    assert operation.field_path == "is_identity_key"


def test_meaning_binding_ignores_non_membership_attr_text_change() -> None:
    baseline = _source_index(
        "class TvChannel {\n" "    channel_number Int key\n" "}\n",
    )
    current = _source_index(
        "class TvChannel {\n" "    channel_number String key\n" "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_attribute_membership_identity_key_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.changed_binding_count == 0
    assert resolution.semantic_deltas == ()
    assert resolution.typed_operations == ()


def test_meaning_binding_derives_function_create_from_generic_fn_binding() -> None:
    baseline = _source_index(
        "class TvChannel {\n" "    name String\n" "    channel_number Int key\n" "}\n",
    )
    current = _source_index(
        "class TvChannel {\n"
        "    name String\n"
        "    channel_number Int key\n"
        "\n"
        "    fn rename(display_name String) -> TvChannel {\n"
        '        """\n'
        "        Rename the channel display label for humans and assistants.\n"
        '        """\n'
        "    }\n"
        "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_function_create_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.binding_count == 1
    assert resolution.resolved_binding_count == 1
    assert resolution.changed_binding_count == 1
    [delta] = resolution.semantic_deltas
    assert delta.verb == "upsert"
    assert delta.semantic_key == "meta.function:TvChannel.rename"
    assert delta.subject_type == "aware_meta.FunctionConfig"
    assert delta.before_payload is None
    after_payload = _payload(delta.after_payload)
    assert after_payload["name"] == "rename"
    assert after_payload["class_name"] == "TvChannel"
    assert after_payload["function_name"] == "rename"
    assert after_payload["function_path"] == "TvChannel.rename"
    assert after_payload["function_description"] == (
        "Rename the channel display label for humans and assistants."
    )
    [event] = resolution.semantic_events
    assert event.event_key == "meta.function:TvChannel.rename:name:upsert"
    [operation] = resolution.typed_operations
    assert operation.operation_family == "create"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.function.create"
    )
    assert operation.semantic_key == delta.semantic_key
    assert operation.semantic_subject_type == "aware_meta.FunctionConfig"
    assert operation.field_path == "name"
    assert operation.before_payload is None
    assert operation.after_payload is not None
    assert operation.after_payload["function_name"] == "rename"


def test_meaning_binding_derives_attribute_create_from_generic_attr_binding() -> None:
    baseline = _source_index(
        "class ContentLayout {\n" "    name String\n" "}\n",
    )
    current = _source_index(
        "class ContentLayout {\n"
        "    name String\n"
        "    title String\n"
        "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_attribute_structural_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.binding_count == 1
    assert resolution.resolved_binding_count == 1
    assert resolution.changed_binding_count == 1
    [delta] = resolution.semantic_deltas
    assert delta.verb == "upsert"
    assert delta.semantic_key == "meta.attribute:ContentLayout.title"
    assert delta.subject_type == "aware_meta.AttributeConfig"
    assert delta.before_payload is None
    after_payload = _payload(delta.after_payload)
    assert after_payload["definition"] == "title String"
    assert after_payload["class_name"] == "ContentLayout"
    assert after_payload["attribute_name"] == "title"
    assert after_payload["type"] == "String"
    [operation] = resolution.typed_operations
    assert operation.operation_family == "create"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.attribute.create"
    )
    assert operation.semantic_key == delta.semantic_key
    assert operation.semantic_subject_type == "aware_meta.AttributeConfig"
    assert operation.field_path == "definition"
    assert operation.before_payload is None
    assert operation.after_payload is not None
    assert operation.after_payload["attribute_name"] == "title"
    assert operation.after_payload["type"] == "String"
    assert operation.requires_baseline_object_identity is False


def test_meaning_binding_derives_attribute_delete_from_generic_attr_binding() -> None:
    baseline = _source_index(
        "class ContentLayout {\n"
        "    name String\n"
        "    title String\n"
        "}\n",
    )
    current = _source_index(
        "class ContentLayout {\n" "    name String\n" "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_attribute_structural_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.changed_binding_count == 1
    [delta] = resolution.semantic_deltas
    assert delta.verb == "delete"
    assert delta.semantic_key == "meta.attribute:ContentLayout.title"
    assert delta.subject_type == "aware_meta.AttributeConfig"
    assert delta.before_payload is not None
    assert delta.after_payload is None
    before_payload = _payload(delta.before_payload)
    assert before_payload["definition"] == "title String"
    assert before_payload["class_name"] == "ContentLayout"
    assert before_payload["attribute_name"] == "title"
    assert before_payload["type"] == "String"
    [operation] = resolution.typed_operations
    assert operation.operation_family == "delete"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.attribute.delete"
    )
    assert operation.semantic_key == delta.semantic_key
    assert operation.semantic_subject_type == "aware_meta.AttributeConfig"
    assert operation.field_path == "definition"
    assert operation.requires_baseline_object_identity is True


def test_meaning_binding_emits_attribute_identity_rename_when_policy_opts_in() -> (
    None
):
    baseline = _source_index(
        "class ContentLayout {\n" "    title String\n" "}\n",
    )
    current = _source_index(
        "class ContentLayout {\n" "    slug String\n" "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_attribute_identity_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.changed_binding_count == 1
    [delta] = resolution.semantic_deltas
    assert delta.verb == "rename"
    assert delta.semantic_key == "meta.attribute:ContentLayout.slug"
    assert delta.metadata["before_semantic_key"] == (
        "meta.attribute:ContentLayout.title"
    )
    before_payload = _payload(delta.before_payload)
    after_payload = _payload(delta.after_payload)
    assert before_payload["name"] == "title"
    assert before_payload["attribute_name"] == "title"
    assert after_payload["name"] == "slug"
    assert after_payload["attribute_name"] == "slug"

    [operation] = resolution.typed_operations
    assert operation.operation_family == "rename"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.attribute.identity.rename"
    )
    assert operation.semantic_key == "meta.attribute:ContentLayout.slug"
    assert operation.semantic_subject_type == "aware_meta.AttributeConfig"
    assert operation.field_path == "name"
    assert operation.before_payload is not None
    assert operation.after_payload is not None
    assert operation.metadata["fallback_required"] is True
    assert operation.requires_baseline_object_identity is True


def test_meaning_binding_derives_function_impl_body_update_from_fn_body_anchor() -> (
    None
):
    baseline = _source_index(
        "class TvChannel {\n"
        "    name String\n"
        "    channel_number String key\n"
        "\n"
        "    fn rename(display_name String) -> TvChannel {\n"
        '        """\n'
        "        Rename the channel display label for humans and assistants.\n"
        '        """\n'
        "    }\n"
        "}\n",
    )
    current = _source_index(
        "class TvChannel {\n"
        "    name String\n"
        "    channel_number String key\n"
        "\n"
        "    fn rename(display_name String) -> TvChannel {\n"
        '        """\n'
        "        Rename the channel display label for humans and assistants.\n"
        '        """\n'
        "        set name = display_name\n"
        "    }\n"
        "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_function_impl_body_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.binding_count == 1
    assert resolution.resolved_binding_count == 1
    assert resolution.changed_binding_count == 1
    [delta] = resolution.semantic_deltas
    assert delta.verb == "update"
    assert delta.semantic_key == "meta.function_impl:TvChannel.rename:default"
    assert delta.subject_type == "aware_meta.FunctionImpl"
    assert delta.before_payload is not None
    assert delta.after_payload is not None
    assert "set name = display_name" not in str(delta.before_payload["body_text"])
    assert "set name = display_name" in str(delta.after_payload["body_text"])
    assert delta.after_payload["function_name"] == "rename"
    assert delta.after_payload["function_path"] == "TvChannel.rename"
    [operation] = resolution.typed_operations
    assert operation.operation_family == "update"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.function_impl.body.update"
    )
    assert operation.semantic_key == delta.semantic_key
    assert operation.semantic_subject_type == "aware_meta.FunctionImpl"
    assert operation.field_path == "body_text"
    assert operation.requires_baseline_object_identity is True


def test_meaning_binding_derives_class_description_from_doc_comment_anchor() -> None:
    baseline = _source_index(
        "class TvChannel {\n" "    name String\n" "}\n",
    )
    current = _source_index(
        "/// A media channel available to the home assistant.\n"
        "class TvChannel {\n"
        "    name String\n"
        "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_class_description_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.binding_count == 1
    assert resolution.resolved_binding_count == 1
    assert resolution.changed_binding_count == 1
    [delta] = resolution.semantic_deltas
    assert delta.verb == "upsert"
    assert delta.semantic_key == "meta.class:TvChannel"
    assert delta.subject_type == "aware_meta.ClassConfig"
    assert delta.before_payload is None
    after_payload = _payload(delta.after_payload)
    assert after_payload["description"] == (
        "A media channel available to the home assistant."
    )
    assert after_payload["class_name"] == "TvChannel"
    assert after_payload["class_description"] == (
        "A media channel available to the home assistant."
    )
    source_index = _payload(delta.metadata["source_index"])
    template_values = _payload(source_index["template_values"])
    assert template_values["class_name"] == "TvChannel"
    assert template_values["field_path"] == "TvChannel.description"
    assert template_values["class_description"] == (
        "A media channel available to the home assistant."
    )
    [operation] = resolution.typed_operations
    assert operation.operation_family == "update"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.class.description.update"
    )
    assert operation.semantic_key == "meta.class:TvChannel"
    assert operation.semantic_subject_type == "aware_meta.ClassConfig"
    assert operation.field_path == "description"
    assert operation.before_payload is None
    assert operation.after_payload is not None
    assert operation.after_payload["description"] == (
        "A media channel available to the home assistant."
    )
    assert operation.requires_baseline_object_identity is True


def test_meaning_binding_derives_enum_description_from_doc_comment_anchor() -> None:
    baseline = _source_index(
        "/// Playback state.\n"
        "enum PlaybackState {\n"
        "    paused\n"
        "    playing\n"
        "}\n",
    )
    current = _source_index(
        "/// Playback state visible to assistants.\n"
        "enum PlaybackState {\n"
        "    paused\n"
        "    playing\n"
        "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_enum_description_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.binding_count == 1
    assert resolution.resolved_binding_count == 1
    assert resolution.changed_binding_count == 1
    [delta] = resolution.semantic_deltas
    assert delta.verb == "update"
    assert delta.semantic_key == "meta.enum:PlaybackState"
    assert delta.subject_type == "aware_meta.EnumConfig"
    assert delta.before_payload is not None
    after_payload = _payload(delta.after_payload)
    assert after_payload["description"] == "Playback state visible to assistants."
    assert after_payload["enum_name"] == "PlaybackState"
    assert after_payload["enum_description"] == (
        "Playback state visible to assistants."
    )
    source_index = _payload(delta.metadata["source_index"])
    template_values = _payload(source_index["template_values"])
    assert template_values["enum_name"] == "PlaybackState"
    assert template_values["field_path"] == "PlaybackState.description"
    assert template_values["enum_description"] == (
        "Playback state visible to assistants."
    )
    [operation] = resolution.typed_operations
    assert operation.operation_family == "update"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.enum.description.update"
    )
    assert operation.semantic_key == "meta.enum:PlaybackState"
    assert operation.semantic_subject_type == "aware_meta.EnumConfig"
    assert operation.field_path == "description"
    assert operation.before_payload is not None
    assert operation.after_payload is not None
    assert operation.after_payload["description"] == (
        "Playback state visible to assistants."
    )
    assert operation.requires_baseline_object_identity is True


def test_meaning_binding_emits_enum_identity_rename_when_policy_opts_in() -> None:
    baseline = _source_index(
        "enum PlaybackState {\n" "    paused\n" "}\n",
    )
    current = _source_index(
        "enum PlaybackStatus {\n" "    paused\n" "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_enum_identity_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.changed_binding_count == 1
    [delta] = resolution.semantic_deltas
    assert delta.verb == "rename"
    assert delta.semantic_key == "meta.enum:PlaybackStatus"
    assert delta.metadata["before_semantic_key"] == "meta.enum:PlaybackState"
    assert delta.before_payload is not None
    assert delta.after_payload is not None
    assert delta.before_payload["name"] == "PlaybackState"
    assert delta.after_payload["name"] == "PlaybackStatus"
    assert delta.before_payload["enum_name"] == "PlaybackState"
    assert delta.after_payload["enum_name"] == "PlaybackStatus"

    [event] = resolution.semantic_events
    assert event.verb == "rename"
    assert event.payload["before"] == "PlaybackState"
    assert event.payload["after"] == "PlaybackStatus"

    [operation] = resolution.typed_operations
    assert operation.operation_family == "rename"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.enum.identity.rename"
    )
    assert operation.semantic_key == "meta.enum:PlaybackStatus"
    assert operation.semantic_subject_type == "aware_meta.EnumConfig"
    assert operation.field_path == "name"
    assert operation.before_payload is not None
    assert operation.after_payload is not None
    assert operation.before_payload["name"] == "PlaybackState"
    assert operation.after_payload["name"] == "PlaybackStatus"
    assert operation.requires_baseline_object_identity is True
    assert operation.metadata["fallback_required"] is True


def test_meaning_binding_derives_relationship_load_policy_from_annotation() -> None:
    baseline = _source_index(
        "class TvChannel {\n"
        "    channel_number Int key\n"
        "}\n"
        "\n"
        "class RemoteControl {\n"
        "    selected_channel TvChannel\n"
        "}\n",
    )
    current = _source_index(
        "class TvChannel {\n"
        "    channel_number Int key\n"
        "}\n"
        "\n"
        "class RemoteControl {\n"
        "    selected_channel TvChannel\n"
        "}\n"
        "\n"
        "ann home.RemoteControl::selected_channel load forward eager\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_relationship_load_policy_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.binding_count == 1
    assert resolution.resolved_binding_count == 1
    assert resolution.changed_binding_count == 1
    [delta] = resolution.semantic_deltas
    assert delta.verb == "upsert"
    assert delta.semantic_key == "meta.relationship:RemoteControl.selected_channel"
    assert delta.subject_type == "aware_meta.ClassConfigRelationship"
    assert delta.before_payload is None
    assert delta.after_payload is not None
    after_payload = _payload(delta.after_payload)
    assert after_payload["load_policy_args"] == "forward eager"
    assert after_payload["ann_path"] == "home.RemoteControl::selected_channel"
    assert after_payload["ann_verb"] == "load"
    assert after_payload["class_fqn"] == "home.RemoteControl"
    assert after_payload["class_name"] == "RemoteControl"
    assert after_payload["relationship_key"] == "selected_channel"
    assert after_payload["relationship_path"] == "RemoteControl.selected_channel"
    assert after_payload["relationship_type"] == "many_to_one"
    assert after_payload["target_class_name"] == "TvChannel"
    assert after_payload["target_class_fqn"] == "home.TvChannel"
    source_index = _payload(delta.metadata["source_index"])
    template_values = _payload(source_index["template_values"])
    assert template_values["relationship_key"] == "selected_channel"
    assert template_values["target_class_fqn"] == "home.TvChannel"
    [operation] = resolution.typed_operations
    assert operation.operation_family == "update"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.relationship.load_policy.update"
    )
    assert operation.semantic_key == delta.semantic_key
    assert operation.semantic_subject_type == ("aware_meta.ClassConfigRelationship")
    assert operation.field_path == "load_policy_args"
    assert operation.before_payload is None
    assert operation.after_payload is not None
    assert operation.after_payload["load_policy_args"] == "forward eager"
    assert operation.requires_baseline_object_identity is True


def test_meaning_binding_derives_relationship_create_from_class_typed_attr() -> None:
    baseline = _source_index(
        "class ContentPlacement {\n"
        "    key String key\n"
        "}\n"
        "\n"
        "class ContentLayout {\n"
        "    name String key\n"
        "}\n",
    )
    current = _source_index(
        "class ContentPlacement {\n"
        "    key String key\n"
        "}\n"
        "\n"
        "class ContentLayout {\n"
        "    name String key\n"
        "    placements ContentPlacement[]\n"
        "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_relationship_structural_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.binding_count == 1
    assert resolution.resolved_binding_count == 1
    assert resolution.changed_binding_count == 1
    [delta] = resolution.semantic_deltas
    assert delta.verb == "upsert"
    assert delta.semantic_key == "meta.relationship:ContentLayout.placements"
    assert delta.subject_type == "aware_meta.ClassConfigRelationship"
    assert delta.before_payload is None
    after_payload = _payload(delta.after_payload)
    assert after_payload["definition"] == "placements ContentPlacement[]"
    assert after_payload["class_name"] == "ContentLayout"
    assert after_payload["relationship_key"] == "placements"
    assert after_payload["relationship_path"] == "ContentLayout.placements"
    assert after_payload["target_class_name"] == "ContentPlacement"
    assert after_payload["target_class_fqn"] == "ContentPlacement"
    assert after_payload["relationship_type"] == "one_to_many"
    [operation] = resolution.typed_operations
    assert operation.operation_family == "create"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.relationship.create"
    )
    assert operation.semantic_key == delta.semantic_key
    assert operation.semantic_subject_type == "aware_meta.ClassConfigRelationship"
    assert operation.field_path == "definition"
    assert operation.before_payload is None
    assert operation.after_payload is not None
    assert operation.after_payload["relationship_key"] == "placements"
    assert operation.after_payload["relationship_type"] == "one_to_many"
    assert operation.requires_baseline_object_identity is False


def test_meaning_binding_derives_relationship_delete_from_class_typed_attr() -> None:
    baseline = _source_index(
        "class ContentPlacement {\n"
        "    key String key\n"
        "}\n"
        "\n"
        "class ContentLayout {\n"
        "    name String key\n"
        "    placements ContentPlacement[]\n"
        "}\n",
    )
    current = _source_index(
        "class ContentPlacement {\n"
        "    key String key\n"
        "}\n"
        "\n"
        "class ContentLayout {\n"
        "    name String key\n"
        "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_relationship_structural_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.changed_binding_count == 1
    [delta] = resolution.semantic_deltas
    assert delta.verb == "delete"
    assert delta.semantic_key == "meta.relationship:ContentLayout.placements"
    assert delta.subject_type == "aware_meta.ClassConfigRelationship"
    assert delta.before_payload is not None
    assert delta.after_payload is None
    before_payload = _payload(delta.before_payload)
    assert before_payload["definition"] == "placements ContentPlacement[]"
    assert before_payload["relationship_key"] == "placements"
    assert before_payload["relationship_type"] == "one_to_many"
    [operation] = resolution.typed_operations
    assert operation.operation_family == "delete"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.relationship.delete"
    )
    assert operation.semantic_key == delta.semantic_key
    assert operation.semantic_subject_type == "aware_meta.ClassConfigRelationship"
    assert operation.field_path == "definition"
    assert operation.requires_baseline_object_identity is True


def test_meaning_binding_skips_primitive_attrs_for_relationship_structural() -> None:
    baseline = _source_index("class ContentLayout {\n    name String key\n}\n")
    current = _source_index(
        "class ContentLayout {\n"
        "    name String key\n"
        "    title String\n"
        "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_relationship_structural_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.resolved_binding_count == 0
    assert resolution.changed_binding_count == 0
    assert resolution.semantic_deltas == ()
    assert resolution.typed_operations == ()


def test_meaning_binding_skips_relationship_attrs_for_attribute_structural() -> None:
    baseline = _source_index(
        "class ContentPlacement {\n"
        "    key String key\n"
        "}\n"
        "\n"
        "class ContentLayout {\n"
        "    name String key\n"
        "}\n",
    )
    current = _source_index(
        "class ContentPlacement {\n"
        "    key String key\n"
        "}\n"
        "\n"
        "class ContentLayout {\n"
        "    name String key\n"
        "    placements ContentPlacement[]\n"
        "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_attribute_structural_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    assert resolution.changed_binding_count == 0
    assert resolution.semantic_deltas == ()
    assert resolution.typed_operations == ()


def test_meaning_binding_blocks_duplicate_generic_semantic_keys() -> None:
    baseline = CodeGrammarSourceIndex.from_sources(
        (
            CodeGrammarSource(
                source_key="home_a.aware",
                source_text="class TvChannel {\n    channel_number Int key\n}\n",
                relative_path="home_a.aware",
            ),
            CodeGrammarSource(
                source_key="home_b.aware",
                source_text="class TvChannel {\n    channel_number Int key\n}\n",
                relative_path="home_b.aware",
            ),
        )
    )
    current = CodeGrammarSourceIndex.from_sources(
        (
            CodeGrammarSource(
                source_key="home_a.aware",
                source_text="class TvChannel {\n    channel_number String key\n}\n",
                relative_path="home_a.aware",
            ),
            CodeGrammarSource(
                source_key="home_b.aware",
                source_text="class TvChannel {\n    channel_number String key\n}\n",
                relative_path="home_b.aware",
            ),
        )
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_attribute_type_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is False
    assert resolution.semantic_deltas == ()
    assert "ambiguous baseline semantic key" in resolution.diagnostics[0]


def test_meaning_binding_emits_upsert_without_baseline_source_index() -> None:
    current = _source_index(
        "class TvChannel {\n    channel_number Int key\n}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_home_attribute_type_contract(),
        current_source_index=current,
    )

    assert resolution.resolved is True
    [delta] = resolution.semantic_deltas
    assert delta.verb == "upsert"
    assert delta.before_payload is None
    assert delta.after_payload is not None
    assert delta.after_payload["type"] == "Int"


def test_delta_meaning_hydrates_and_reuses_source_index_session_cache() -> None:
    clear_code_semantic_source_index_cache_for_tests()
    baseline_ref = _source_index_ref("semantic-source-index:home:baseline")
    current_ref = _source_index_ref("semantic-source-index:home:current")
    session_context = _source_session_context(baseline_ref, current_ref)
    baseline_source = _meaning_source(
        "class TvChannel {\n    channel_number Int key\n}\n",
    )
    current_source = _meaning_source(
        "class TvChannel {\n    channel_number String key\n}\n",
    )

    first = resolve_code_semantic_source_delta_meaning(
        contract=_home_attribute_type_contract(),
        code_package_delta=_code_delta("home.aware"),
        baseline_sources=(baseline_source,),
        current_sources=(current_source,),
        baseline_source_index_ref=baseline_ref,
        current_source_index_ref=current_ref,
        session_context=session_context,
    )
    second = resolve_code_semantic_source_delta_meaning(
        contract=_home_attribute_type_contract(),
        code_package_delta=_code_delta("home.aware"),
        baseline_sources=(baseline_source,),
        current_sources=(current_source,),
        baseline_source_index_ref=baseline_ref,
        current_source_index_ref=current_ref,
        session_context=session_context,
    )

    assert first.resolved is True
    assert first.source_index_evidence["cache_miss_count"] == 2
    assert first.source_index_evidence["cache_hit_count"] == 0
    assert second.resolved is True
    assert second.source_index_evidence["cache_hit_count"] == 2
    assert second.source_index_evidence["cache_miss_count"] == 0
    assert _payload(second.source_index_evidence["baseline"])["parse_count"] == 0
    assert _payload(second.source_index_evidence["current"])["parse_count"] == 0


def test_delta_meaning_resolves_ref_only_from_hydrated_source_index_cache() -> None:
    clear_code_semantic_source_index_cache_for_tests()
    baseline_ref = _source_index_ref("semantic-source-index:home:baseline-ref")
    current_ref = _source_index_ref("semantic-source-index:home:current-ref")
    session_context = _source_session_context(baseline_ref, current_ref)

    hydrated = resolve_code_semantic_source_delta_meaning(
        contract=_home_attribute_type_contract(),
        code_package_delta=_code_delta("home.aware"),
        baseline_sources=(
            _meaning_source("class TvChannel {\n    channel_number Int key\n}\n"),
        ),
        current_sources=(
            _meaning_source("class TvChannel {\n    channel_number String key\n}\n"),
        ),
        baseline_source_index_ref=baseline_ref,
        current_source_index_ref=current_ref,
        session_context=session_context,
    )
    ref_only = resolve_code_semantic_source_delta_meaning(
        contract=_home_attribute_type_contract(),
        code_package_delta=_code_delta("home.aware", content_text=None),
        baseline_source_index_ref=baseline_ref,
        current_source_index_ref=current_ref,
        session_context=session_context,
    )

    assert hydrated.resolved is True
    assert ref_only.resolved is True
    assert ref_only.meaning_resolution_mode == "delta_with_index_ref"
    assert ref_only.source_index_evidence["cache_hit_count"] == 2
    assert ref_only.source_index_evidence["cache_miss_count"] == 0
    [delta] = ref_only.semantic_deltas
    assert delta.verb == "update"
    assert delta.after_payload is not None
    assert delta.after_payload["type"] == "String"


def test_delta_meaning_blocks_ref_only_without_hydrated_source_index_cache() -> None:
    clear_code_semantic_source_index_cache_for_tests()
    baseline_ref = _source_index_ref("semantic-source-index:missing:baseline")
    current_ref = _source_index_ref("semantic-source-index:missing:current")

    resolution = resolve_code_semantic_source_delta_meaning(
        contract=_home_attribute_type_contract(),
        code_package_delta=_code_delta("home.aware", content_text=None),
        baseline_source_index_ref=baseline_ref,
        current_source_index_ref=current_ref,
        session_context=_source_session_context(baseline_ref, current_ref),
    )

    assert resolution.resolved is False
    assert resolution.status == "blocked"
    assert resolution.required_context == (
        "baseline_source_index_ref_hydration",
        "current_source_index_ref_hydration",
    )
    assert resolution.source_index_evidence["cache_hit_count"] == 0
    assert resolution.source_index_evidence["cache_miss_count"] == 0


def test_meaning_binding_change_preview_uses_existing_semantic_capability_shape() -> (
    None
):
    baseline = _source_index(
        "class TvChannel {\n    channel_number Int key\n}\n",
    )
    current = _source_index(
        "class TvChannel {\n    channel_number String key\n}\n",
    )

    preview = resolve_code_semantic_source_meaning(
        contract=_home_attribute_type_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    ).change_preview()

    assert isinstance(preview, SemanticCapabilityChangePreview)
    assert preview.changed_source_files == ("home.aware",)
    assert preview.affected_semantic_keys == (
        "meta.attribute:TvChannel.channel_number",
    )
    assert len(preview.semantic_deltas) == 1
    assert len(preview.semantic_events) == 1
    assert preview.metadata["source"] == "aware_code.semantic_source_meaning"


def test_meaning_binding_emits_action_bindings_from_contract_metadata() -> None:
    baseline = _source_index(
        "class TvChannel {\n    channel_number Int key\n}\n",
    )
    current = _source_index(
        "class TvChannel {\n    channel_number String key\n}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_home_attribute_type_contract_with_action(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    [action] = resolution.action_bindings
    assert action.action_key == (
        "aware_meta.object_config_graph.attribute.type:"
        "TvChannel.channel_number:update_primitive"
    )
    assert action.event_key == ("meta.attribute:TvChannel.channel_number:type:update")
    assert action.action_type == "function_call"
    assert action.function_call_binding is not None
    assert action.function_call_binding.function_ref == (
        "aware_meta_ontology.attribute.attribute_config."
        "AttributeConfig.update_primitive"
    )
    assert action.function_call_binding.receiver_semantic_key_template == (
        "semantic_key"
    )
    assert action.function_call_binding.argument_bindings == {
        "primitive_base_type": "payload.after"
    }

    preview = resolution.change_preview()
    assert preview.action_bindings == resolution.action_bindings


def test_meaning_binding_emits_typed_operations_from_contract_metadata() -> None:
    baseline = _source_index(
        "class TvChannel {\n    channel_number Int key\n}\n",
    )
    current = _source_index(
        "class TvChannel {\n    channel_number String key\n}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_home_attribute_type_contract_with_typed_operation(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    [operation] = resolution.typed_operations
    assert operation.operation_key == (
        "aware_meta.object_config_graph.attribute.type:"
        "TvChannel.channel_number:update"
    )
    assert operation.operation_family == "update"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.attribute.type.update"
    )
    assert operation.semantic_key == "meta.attribute:TvChannel.channel_number"
    assert operation.semantic_subject_type == "ClassConfigAttributeConfig"
    assert operation.field_path == "type"
    assert operation.event_key == (
        "meta.attribute:TvChannel.channel_number:type:update"
    )
    assert operation.source == "aware_code.semantic_source_meaning"
    assert operation.source_refs == ("home.aware",)
    assert operation.before_payload is not None
    assert operation.after_payload is not None
    assert operation.before_payload["type"] == "Int"
    assert operation.after_payload["type"] == "String"
    assert operation.requires_baseline_object_identity is True
    assert "function_ref" not in operation.evidence_payload()

    preview = resolution.change_preview()
    assert preview.typed_operations == resolution.typed_operations


def test_meaning_binding_emits_function_membership_constructor_update_from_verb() -> (
    None
):
    baseline = _source_index(
        "class ContentLayout {\n"
        "    name String key\n"
        "    fn rename(display_name String) -> ContentLayout\n"
        "}\n",
    )
    current = _source_index(
        "class ContentLayout {\n"
        "    name String key\n"
        "    fn rename construct(display_name String) -> ContentLayout\n"
        "}\n",
    )

    resolution = resolve_code_semantic_source_meaning(
        contract=_generic_function_membership_constructor_contract(),
        baseline_source_index=baseline,
        current_source_index=current,
    )

    assert resolution.resolved is True
    [delta] = resolution.semantic_deltas
    assert delta.verb == "upsert"
    assert delta.semantic_key == "meta.function:ContentLayout.rename"
    assert delta.before_payload is None
    after_payload = _payload(delta.after_payload)
    assert after_payload["is_constructor"] is True
    assert after_payload["function_verb"] == "construct"
    assert after_payload["function_membership_signature"] == {
        "is_constructor": True,
    }

    [operation] = resolution.typed_operations
    assert operation.operation_key == (
        "aware_meta.object_config_graph.function.membership."
        "constructor:ContentLayout.rename:update"
    )
    assert operation.operation_family == "update"
    assert operation.semantic_operation_type == (
        "aware_meta.object_config_graph.function.signature.update"
    )
    assert operation.semantic_key == "meta.function:ContentLayout.rename"
    assert operation.semantic_subject_type == "aware_meta.FunctionConfig"
    assert operation.field_path == "is_constructor"
    assert operation.before_payload is None
    assert operation.after_payload is not None
    assert operation.after_payload["is_constructor"] is True
    assert operation.requires_baseline_object_identity is True


def test_meaning_binding_blocks_when_required_anchor_does_not_resolve() -> None:
    current = _source_index("class TvChannel {\n    name String\n}\n")

    resolution = resolve_code_semantic_source_meaning(
        contract=_home_attribute_type_contract(),
        current_source_index=current,
    )

    assert resolution.resolved is False
    assert resolution.status == "blocked"
    assert resolution.semantic_deltas == ()
    assert "meta.attribute.type" in resolution.diagnostics[0]


def _home_attribute_type_contract() -> CodeSemanticSourceMeaningContract:
    return CodeSemanticSourceMeaningContract(
        provider_key="aware_meta",
        semantic_owner="aware_meta.provider",
        grammar_profile_key="code.grammar_profile.aware_kernel",
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key="meta.attribute.type",
                grammar_rule_name="attr_def",
                anchor_field_path="type",
                graph_selector=CodeGrammarGraphSelector(
                    provider_key="aware_meta",
                    semantic_owner="aware_meta.provider",
                    class_name="TvChannel",
                    attribute_name="channel_number",
                    attribute_path="TvChannel.channel_number.type",
                ),
                semantic_subject_type="ClassConfigAttributeConfig",
                semantic_key_template=("meta.attribute:{class_name}.{attribute_name}"),
                semantic_field="type",
                value_domain="aware_type_descriptor",
            ),
        ),
    )


def _home_attribute_type_contract_with_action() -> CodeSemanticSourceMeaningContract:
    contract = _home_attribute_type_contract()
    binding = contract.bindings[0]
    return CodeSemanticSourceMeaningContract(
        provider_key=contract.provider_key,
        semantic_owner=contract.semantic_owner,
        grammar_profile_key=contract.grammar_profile_key,
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key=binding.binding_key,
                grammar_rule_name=binding.grammar_rule_name,
                anchor_field_path=binding.anchor_field_path,
                graph_selector=binding.graph_selector,
                semantic_subject_type=binding.semantic_subject_type,
                semantic_key_template=binding.semantic_key_template,
                semantic_field=binding.semantic_field,
                value_domain=binding.value_domain,
                metadata={
                    "action_bindings": [
                        {
                            "action_key_template": (
                                "aware_meta.object_config_graph.attribute.type:"
                                "{class_name}.{attribute_name}:update_primitive"
                            ),
                            "event_verbs": ["update"],
                            "action_type": "function_call",
                            "function_call_binding": {
                                "binding_key": (
                                    "aware_meta.object_config_graph.attribute."
                                    "type.update_primitive"
                                ),
                                "function_ref": (
                                    "aware_meta_ontology.attribute."
                                    "attribute_config."
                                    "AttributeConfig.update_primitive"
                                ),
                                "receiver_semantic_key_template": ("semantic_key"),
                                "argument_bindings": {
                                    "primitive_base_type": "payload.after"
                                },
                            },
                        },
                    ],
                },
            ),
        ),
    )


def _home_attribute_type_contract_with_typed_operation() -> (
    CodeSemanticSourceMeaningContract
):
    contract = _home_attribute_type_contract()
    binding = contract.bindings[0]
    return CodeSemanticSourceMeaningContract(
        provider_key=contract.provider_key,
        semantic_owner=contract.semantic_owner,
        grammar_profile_key=contract.grammar_profile_key,
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key=binding.binding_key,
                grammar_rule_name=binding.grammar_rule_name,
                anchor_field_path=binding.anchor_field_path,
                graph_selector=binding.graph_selector,
                semantic_subject_type=binding.semantic_subject_type,
                semantic_key_template=binding.semantic_key_template,
                semantic_field=binding.semantic_field,
                value_domain=binding.value_domain,
                metadata={
                    "typed_operation_bindings": [
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.attribute.type:"
                                "{class_name}.{attribute_name}:update"
                            ),
                            "event_verbs": ["update"],
                            "operation_family": "update",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.attribute."
                                "type.update"
                            ),
                            "semantic_subject_type": ("ClassConfigAttributeConfig"),
                            "field_path": "type",
                            "requires_baseline_object_identity": True,
                            "metadata": {"source": "aware_meta.semantic_contract"},
                        },
                    ],
                },
            ),
        ),
    )


def _generic_attribute_type_contract() -> CodeSemanticSourceMeaningContract:
    return CodeSemanticSourceMeaningContract(
        provider_key="aware_meta",
        semantic_owner="aware_meta.provider",
        grammar_profile_key="code.grammar_profile.aware_kernel",
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key="meta.attribute.type",
                grammar_rule_name="attr_def",
                anchor_field_path="type",
                graph_selector=CodeGrammarGraphSelector(
                    provider_key="aware_meta",
                    semantic_owner="aware_meta.provider",
                ),
                semantic_subject_type="ClassConfigAttributeConfig",
                semantic_key_template=("meta.attribute:{class_name}.{attribute_name}"),
                semantic_field="type",
                value_domain="aware_type_descriptor",
            ),
        ),
    )


def _generic_attribute_membership_identity_key_contract() -> (
    CodeSemanticSourceMeaningContract
):
    return CodeSemanticSourceMeaningContract(
        provider_key="aware_meta",
        semantic_owner="aware_meta.object_config_graph",
        grammar_profile_key="code.grammar_profile.aware_kernel",
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key="meta.attribute.membership.identity_key",
                grammar_rule_name="attr_def",
                anchor_field_path="__node__",
                graph_selector=CodeGrammarGraphSelector(
                    provider_key="aware_meta",
                    semantic_owner="aware_meta.object_config_graph",
                ),
                semantic_subject_type="aware_meta.ClassConfigAttributeConfig",
                semantic_key_template=(
                    "meta.attribute:{class_name}.{attribute_name}"
                    "/membership:class_config"
                ),
                semantic_field="is_identity_key",
                value_domain="aware_attribute_membership_identity_key",
                metadata={
                    "change_detection_template_fields": ["is_identity_key"],
                    "excluded_template_values": ["relationship_key"],
                    "typed_operation_bindings": [
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.attribute."
                                "membership.identity_key:"
                                "{class_name}.{attribute_name}:update"
                            ),
                            "event_verbs": ["update"],
                            "operation_family": "update",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.attribute."
                                "membership.update"
                            ),
                            "semantic_subject_type": (
                                "aware_meta.ClassConfigAttributeConfig"
                            ),
                            "field_path": "is_identity_key",
                            "requires_baseline_object_identity": True,
                            "metadata": {"source": "aware_meta.semantic_contract"},
                        },
                    ],
                },
            ),
        ),
    )


def _generic_function_create_contract() -> CodeSemanticSourceMeaningContract:
    return CodeSemanticSourceMeaningContract(
        provider_key="aware_meta",
        semantic_owner="aware_meta.object_config_graph",
        grammar_profile_key="code.grammar_profile.aware_kernel",
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key="meta.function.create",
                grammar_rule_name="fn_def",
                anchor_field_path="name",
                graph_selector=CodeGrammarGraphSelector(
                    provider_key="aware_meta",
                    semantic_owner="aware_meta.object_config_graph",
                ),
                semantic_subject_type="aware_meta.FunctionConfig",
                semantic_key_template="meta.function:{class_name}.{function_name}",
                semantic_field="name",
                value_domain="aware_function_name",
                metadata={
                    "include_template_values_in_payload": True,
                    "typed_operation_bindings": [
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.function:"
                                "{class_name}.{function_name}:create"
                            ),
                            "event_verbs": ["upsert"],
                            "operation_family": "create",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.function.create"
                            ),
                            "semantic_subject_type": "aware_meta.FunctionConfig",
                            "field_path": "name",
                        },
                    ],
                },
            ),
        ),
    )


def _generic_attribute_structural_contract() -> CodeSemanticSourceMeaningContract:
    return CodeSemanticSourceMeaningContract(
        provider_key="aware_meta",
        semantic_owner="aware_meta.object_config_graph",
        grammar_profile_key="code.grammar_profile.aware_kernel",
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key="meta.attribute.structural",
                grammar_rule_name="attr_def",
                anchor_field_path="__node__",
                graph_selector=CodeGrammarGraphSelector(
                    provider_key="aware_meta",
                    semantic_owner="aware_meta.object_config_graph",
                ),
                semantic_subject_type="aware_meta.AttributeConfig",
                semantic_key_template=(
                    "meta.attribute:{class_name}.{attribute_name}"
                ),
                semantic_field="definition",
                value_domain="aware_attribute_definition",
                metadata={
                    "include_template_values_in_payload": True,
                    "excluded_template_values": ["relationship_key"],
                    "typed_operation_bindings": [
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.attribute:"
                                "{class_name}.{attribute_name}:create"
                            ),
                            "event_verbs": ["upsert"],
                            "operation_family": "create",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.attribute.create"
                            ),
                            "semantic_subject_type": "aware_meta.AttributeConfig",
                            "field_path": "definition",
                            "requires_baseline_object_identity": False,
                        },
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.attribute:"
                                "{class_name}.{attribute_name}:delete"
                            ),
                            "event_verbs": ["delete"],
                            "operation_family": "delete",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.attribute.delete"
                            ),
                            "semantic_subject_type": "aware_meta.AttributeConfig",
                            "field_path": "definition",
                            "requires_baseline_object_identity": True,
                        },
                    ],
                },
            ),
        ),
    )


def _generic_attribute_identity_contract() -> CodeSemanticSourceMeaningContract:
    return CodeSemanticSourceMeaningContract(
        provider_key="aware_meta",
        semantic_owner="aware_meta.object_config_graph",
        grammar_profile_key="code.grammar_profile.aware_kernel",
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key="meta.attribute.identity",
                grammar_rule_name="attr_def",
                anchor_field_path="name",
                graph_selector=CodeGrammarGraphSelector(
                    provider_key="aware_meta",
                    semantic_owner="aware_meta.object_config_graph",
                ),
                semantic_subject_type="aware_meta.AttributeConfig",
                semantic_key_template=("meta.attribute:{class_name}.{attribute_name}"),
                semantic_field="name",
                value_domain="aware_attribute_name",
                metadata={
                    "identity_rename_policy": "explicit_fallback_required",
                    "include_template_values_in_payload": True,
                    "excluded_template_values": ["relationship_key"],
                    "typed_operation_bindings": [
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.attribute.identity:"
                                "{class_name}.{attribute_name}:rename"
                            ),
                            "event_verbs": ["rename"],
                            "operation_family": "rename",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.attribute."
                                "identity.rename"
                            ),
                            "semantic_subject_type": "aware_meta.AttributeConfig",
                            "field_path": "name",
                            "requires_baseline_object_identity": True,
                            "metadata": {
                                "fallback_required": True,
                                "fallback_reason": (
                                    "meta_attribute_identity_rename_requires_"
                                    "explicit_replacement_policy"
                                ),
                            },
                        },
                    ],
                },
            ),
        ),
    )


def _generic_function_impl_body_contract() -> CodeSemanticSourceMeaningContract:
    return CodeSemanticSourceMeaningContract(
        provider_key="aware_meta",
        semantic_owner="aware_meta.object_config_graph",
        grammar_profile_key="code.grammar_profile.aware_kernel",
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key="meta.function_impl.body",
                grammar_rule_name="fn_def",
                anchor_field_path="body",
                graph_selector=CodeGrammarGraphSelector(
                    provider_key="aware_meta",
                    semantic_owner="aware_meta.object_config_graph",
                ),
                semantic_subject_type="aware_meta.FunctionImpl",
                semantic_key_template=(
                    "meta.function_impl:{class_name}.{function_name}:default"
                ),
                semantic_field="body_text",
                value_domain="aware_function_impl_body",
                metadata={
                    "include_template_values_in_payload": True,
                    "typed_operation_bindings": [
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.function_impl."
                                "body:{class_name}.{function_name}:update"
                            ),
                            "event_verbs": ["update", "upsert"],
                            "operation_family": "update",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph."
                                "function_impl.body.update"
                            ),
                            "semantic_subject_type": "aware_meta.FunctionImpl",
                            "field_path": "body_text",
                            "requires_baseline_object_identity": True,
                        },
                    ],
                },
            ),
        ),
    )


def _generic_function_membership_constructor_contract() -> (
    CodeSemanticSourceMeaningContract
):
    return CodeSemanticSourceMeaningContract(
        provider_key="aware_meta",
        semantic_owner="aware_meta.object_config_graph",
        grammar_profile_key="code.grammar_profile.aware_kernel",
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key="meta.function.membership.constructor",
                grammar_rule_name="fn_def",
                anchor_field_path="verb",
                graph_selector=CodeGrammarGraphSelector(
                    provider_key="aware_meta",
                    semantic_owner="aware_meta.object_config_graph",
                ),
                semantic_subject_type="aware_meta.FunctionConfig",
                semantic_key_template="meta.function:{class_name}.{function_name}",
                semantic_field="is_constructor",
                value_domain="aware_function_membership_constructor",
                metadata={
                    "include_template_values_in_payload": True,
                    "typed_operation_bindings": [
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.function.membership."
                                "constructor:{class_name}.{function_name}:update"
                            ),
                            "event_verbs": ["update", "upsert"],
                            "operation_family": "update",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.function."
                                "signature.update"
                            ),
                            "semantic_subject_type": "aware_meta.FunctionConfig",
                            "field_path": "is_constructor",
                            "requires_baseline_object_identity": True,
                        },
                    ],
                },
            ),
        ),
    )


def _generic_class_description_contract() -> CodeSemanticSourceMeaningContract:
    return CodeSemanticSourceMeaningContract(
        provider_key="aware_meta",
        semantic_owner="aware_meta.object_config_graph",
        grammar_profile_key="code.grammar_profile.aware_kernel",
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key="meta.class.description",
                grammar_rule_name="class_def",
                anchor_field_path="description_comment",
                graph_selector=CodeGrammarGraphSelector(
                    provider_key="aware_meta",
                    semantic_owner="aware_meta.object_config_graph",
                ),
                semantic_subject_type="aware_meta.ClassConfig",
                semantic_key_template="meta.class:{class_name}",
                semantic_field="description",
                value_domain="aware_doc_comment",
                metadata={
                    "include_template_values_in_payload": True,
                    "typed_operation_bindings": [
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.class."
                                "description:{class_name}:update"
                            ),
                            "event_verbs": ["update", "upsert"],
                            "operation_family": "update",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.class."
                                "description.update"
                            ),
                            "semantic_subject_type": "aware_meta.ClassConfig",
                            "field_path": "description",
                            "requires_baseline_object_identity": True,
                        },
                    ],
                },
            ),
        ),
    )


def _generic_enum_description_contract() -> CodeSemanticSourceMeaningContract:
    return CodeSemanticSourceMeaningContract(
        provider_key="aware_meta",
        semantic_owner="aware_meta.object_config_graph",
        grammar_profile_key="code.grammar_profile.aware_kernel",
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key="meta.enum.description",
                grammar_rule_name="enum_def",
                anchor_field_path="description_comment",
                graph_selector=CodeGrammarGraphSelector(
                    provider_key="aware_meta",
                    semantic_owner="aware_meta.object_config_graph",
                ),
                semantic_subject_type="aware_meta.EnumConfig",
                semantic_key_template="meta.enum:{enum_name}",
                semantic_field="description",
                value_domain="aware_doc_comment",
                metadata={
                    "include_template_values_in_payload": True,
                    "typed_operation_bindings": [
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.enum."
                                "description:{enum_name}:update"
                            ),
                            "event_verbs": ["update", "upsert"],
                            "operation_family": "update",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum."
                                "description.update"
                            ),
                            "semantic_subject_type": "aware_meta.EnumConfig",
                            "field_path": "description",
                            "requires_baseline_object_identity": True,
                        },
                    ],
                },
            ),
        ),
    )


def _generic_enum_identity_contract() -> CodeSemanticSourceMeaningContract:
    return CodeSemanticSourceMeaningContract(
        provider_key="aware_meta",
        semantic_owner="aware_meta.object_config_graph",
        grammar_profile_key="code.grammar_profile.aware_kernel",
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key="meta.enum.identity",
                grammar_rule_name="enum_def",
                anchor_field_path="name",
                graph_selector=CodeGrammarGraphSelector(
                    provider_key="aware_meta",
                    semantic_owner="aware_meta.object_config_graph",
                ),
                semantic_subject_type="aware_meta.EnumConfig",
                semantic_key_template="meta.enum:{enum_name}",
                semantic_field="name",
                value_domain="aware_enum_name",
                metadata={
                    "identity_rename_policy": "explicit_fallback_required",
                    "include_template_values_in_payload": True,
                    "typed_operation_bindings": [
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.enum.identity:"
                                "{enum_name}:rename"
                            ),
                            "event_verbs": ["rename"],
                            "operation_family": "rename",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.enum." "identity.rename"
                            ),
                            "semantic_subject_type": "aware_meta.EnumConfig",
                            "field_path": "name",
                            "requires_baseline_object_identity": True,
                            "metadata": {
                                "fallback_required": True,
                                "fallback_reason": (
                                    "meta_enum_identity_rename_requires_"
                                    "explicit_policy"
                                ),
                            },
                        },
                    ],
                },
            ),
        ),
    )


def _generic_relationship_load_policy_contract() -> CodeSemanticSourceMeaningContract:
    return CodeSemanticSourceMeaningContract(
        provider_key="aware_meta",
        semantic_owner="aware_meta.object_config_graph",
        grammar_profile_key="code.grammar_profile.aware_kernel",
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key="meta.relationship.load_policy",
                grammar_rule_name="ann_def",
                anchor_field_path="args",
                graph_selector=CodeGrammarGraphSelector(
                    provider_key="aware_meta",
                    semantic_owner="aware_meta.object_config_graph",
                ),
                semantic_subject_type="aware_meta.ClassConfigRelationship",
                semantic_key_template=(
                    "meta.relationship:{class_name}.{relationship_key}"
                ),
                semantic_field="load_policy_args",
                value_domain="aware_relationship_load_policy_args",
                metadata={
                    "include_template_values_in_payload": True,
                    "typed_operation_bindings": [
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.relationship."
                                "load_policy:{class_name}."
                                "{relationship_key}:update"
                            ),
                            "event_verbs": ["update", "upsert"],
                            "operation_family": "update",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.relationship."
                                "load_policy.update"
                            ),
                            "semantic_subject_type": (
                                "aware_meta.ClassConfigRelationship"
                            ),
                            "field_path": "load_policy_args",
                            "requires_baseline_object_identity": True,
                        },
                    ],
                },
            ),
        ),
    )


def _generic_relationship_structural_contract() -> CodeSemanticSourceMeaningContract:
    return CodeSemanticSourceMeaningContract(
        provider_key="aware_meta",
        semantic_owner="aware_meta.object_config_graph",
        grammar_profile_key="code.grammar_profile.aware_kernel",
        bindings=(
            CodeSemanticSourceMeaningBinding(
                binding_key="meta.relationship.structural",
                grammar_rule_name="attr_def",
                anchor_field_path="__node__",
                graph_selector=CodeGrammarGraphSelector(
                    provider_key="aware_meta",
                    semantic_owner="aware_meta.object_config_graph",
                ),
                semantic_subject_type="aware_meta.ClassConfigRelationship",
                semantic_key_template=(
                    "meta.relationship:{class_name}.{relationship_key}"
                ),
                semantic_field="definition",
                value_domain="aware_relationship_definition",
                required=False,
                metadata={
                    "include_template_values_in_payload": True,
                    "required_template_values": [
                        "relationship_key",
                        "target_class_name",
                        "relationship_type",
                    ],
                    "typed_operation_bindings": [
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.relationship:"
                                "{class_name}.{relationship_key}:create"
                            ),
                            "event_verbs": ["upsert"],
                            "operation_family": "create",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.relationship.create"
                            ),
                            "semantic_subject_type": (
                                "aware_meta.ClassConfigRelationship"
                            ),
                            "field_path": "definition",
                            "requires_baseline_object_identity": False,
                        },
                        {
                            "operation_key_template": (
                                "aware_meta.object_config_graph.relationship:"
                                "{class_name}.{relationship_key}:delete"
                            ),
                            "event_verbs": ["delete"],
                            "operation_family": "delete",
                            "semantic_operation_type": (
                                "aware_meta.object_config_graph.relationship.delete"
                            ),
                            "semantic_subject_type": (
                                "aware_meta.ClassConfigRelationship"
                            ),
                            "field_path": "definition",
                            "requires_baseline_object_identity": True,
                        },
                    ],
                },
            ),
        ),
    )


def _source_index(source_text: str) -> CodeGrammarSourceIndex:
    return CodeGrammarSourceIndex.from_sources(
        (
            CodeGrammarSource(
                source_key="home.aware",
                source_text=source_text,
                relative_path="home.aware",
            ),
        )
    )


def _meaning_source(source_text: str) -> CodeGrammarSource:
    return CodeGrammarSource(
        source_key="home.aware",
        source_text=source_text,
        relative_path="home.aware",
    )


def _code_delta(
    relative_path: str,
    *,
    content_text: str | None = "class TvChannel {\n    channel_number String key\n}\n",
) -> CodePackageDelta:
    return CodePackageDelta(
        package_name="home-ontology",
        package_root="modules/home/structure/ontology",
        paths=[
            CodePackageDeltaPath(
                relative_path=relative_path,
                kind=CodePackageDeltaKind.update,
                content_text=content_text,
            )
        ],
    )


def _source_index_ref(cache_key: str) -> CodeSemanticSourceIndexRef:
    return CodeSemanticSourceIndexRef(
        ref_kind="semantic_source_index_ref",
        cache_kind=SEMANTIC_SOURCE_SESSION_SOURCE_INDEX_CACHE_KIND,
        cache_key=cache_key,
        source_session_id="source-session-1",
        source_delta_fingerprint="sha256:delta-1",
        package_name="home-ontology",
        source_keys=("home.aware",),
    )


def _source_session_context(
    *refs: CodeSemanticSourceIndexRef,
) -> SemanticSourceSessionContext:
    return SemanticSourceSessionContext(
        source_session_id="source-session-1",
        branch_key="main",
        session_key="workspace-session-1",
        source_delta_fingerprint="sha256:delta-1",
        lifecycle_stages=("semantic_status", "semantic_apply"),
        cache_refs=tuple(
            SemanticSourceSessionCacheRef(
                cache_kind=ref.cache_kind or "",
                cache_key=ref.cache_key or "",
                signature=ref.source_delta_fingerprint,
                source="test",
            )
            for ref in refs
            if ref.cache_kind is not None and ref.cache_key is not None
        ),
    )


def _payload(payload: object) -> dict[str, object]:
    assert isinstance(payload, dict)
    return payload
