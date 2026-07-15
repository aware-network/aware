from __future__ import annotations

from pathlib import Path
from hashlib import sha256
from typing import cast
from uuid import UUID

import pytest

from aware_code.builder import build_code_from_content, build_code_from_file
from aware_code.grammar_anchor.render_delta import (
    resolve_code_grammar_anchor_render_delta,
)
from aware_code.language.registry import CodeLanguagePluginRegistry
from aware_code.segment.render_policy import (
    digest_matches as _segment_render_digest_matches,
)
from aware_code.segment.render_policy import (
    resolve_code_segment_render_policy,
    sha256_text_digest as _segment_render_sha256_digest,
)
from aware_code.segment.scanner import CodeSegmentScanner
from aware_code.section.builder_index import CodeSectionBuilderIndex
from aware_code.setup_language_plugins import setup_code_plugins
from aware_code.symbol_table import CodeSymbolTable
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType
from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_meta.fqn_resolver import NamespacePath
from aware_meta.graph.config.builder import build_object_config_graph_from_code
from aware_meta.language_plugin_registry import MetaLanguagePluginRegistry
from aware_meta.materialization.deltas.code_dto import (
    CodeGeneratedMaterializationDeltaEntry,
    CodeGeneratedMaterializationDeltaMode,
    CodeGeneratedMaterializationDeltaRequest,
    CodeGeneratedMaterializationDeltaResult,
    CodePackageDeltaAuthorityKind,
    CodePackageDeltaPath,
    CodeSectionDeltaEntry,
    CodeSectionDeltaOperationKind,
    CodeSectionDeltaSet,
    CodeSegmentRef,
    CodeLanguage as ServiceCodeLanguage,
)
from aware_meta.materialization.deltas.language_renderer_contracts import (
    MetaLanguageGeneratedMaterializationDeltaContext,
    MetaLanguageGeneratedMaterializationDeltaRenderRequest,
    MetaLanguageGeneratedMaterializationTargetHint,
)
from aware_meta.materialization.deltas.renderer_completeness import (
    compare_generated_materialization_package_delta_final_state,
    compare_generated_materialization_package_delta_path_content_map,
)
from aware_meta.materialization.deltas.source_projection import (
    _meta_attribute_create_typed_operation_from_semantic_source_operation,
)
from aware_meta.materialization.deltas.target_profiles import (
    ORM_RUNTIME_TARGET_PROFILE,
)
from aware_meta.materialization.deltas.typed_operation_contracts import (
    MetaProviderDeltaTypedOperation,
)
from aware_meta.materialization.language_service import (
    LanguagePluginMaterializationRequest,
    materialize_object_config_graph_via_language_plugin,
)
from aware_code_service_dto.code.features.package_delta import (
    CodePackageDelta,
    CodePackageDeltaKind,
)
from python_grammar.meta_language_plugin import (
    ONTOLOGY_ORM_MODELS_RENDERER_PROFILE,
    PYTHON_META_PLUGIN,
)
from python_grammar.renderer_delta_orm_runtime import (
    PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME,
    PYTHON_ORM_MATERIALIZATION_SOURCE,
    PYTHON_ORM_RENDERER_PROFILE,
    PythonOrmRuntimeGeneratedDeltaRenderer,
)


@pytest.mark.asyncio
async def test_python_orm_class_create_deltas_match_full_package_render(
    tmp_path: Path,
) -> None:
    package = _python_package_create_delta_fixture(
        tmp_path,
        baseline_files={
            "home/controls.aware": """
class TvChannel {
}
""",
            "devices/local.aware": """
class DeviceGroup {
}
""",
        },
        target_files={
            "home/controls.aware": """
class TvChannel {
}

class RemoteControl {
}
""",
            "devices/local.aware": """
class DeviceGroup {
}

class LocalDevice {
}
""",
        },
        create_operations=(
            _class_create_operation(
                class_fqn="aware_home.default.home.RemoteControl",
                class_name="RemoteControl",
                relative_path="home/controls.py",
                source_ref="home/controls.aware",
            ),
            _class_create_operation(
                class_fqn="aware_home.default.devices.LocalDevice",
                class_name="LocalDevice",
                relative_path="devices/local.py",
                source_ref="devices/local.aware",
            ),
        ),
    )

    package_deltas = await _resolved_python_package_deltas(
        package_root=cast(Path, package["baseline_package_root"]),
        sources_root=cast(str, package["sources_root"]),
        operations=cast(
            tuple[MetaProviderDeltaTypedOperation, ...], package["operations"]
        ),
    )
    comparison = compare_generated_materialization_package_delta_path_content_map(
        expected_by_path=cast(dict[str, str], package["expected_by_path"]),
        package_deltas=package_deltas,
    )

    assert comparison.equivalent, comparison.summary()
    assert sorted(comparison.actual_by_path) == [
        "devices/local.py",
        "home/controls.py",
    ]
    assert comparison.actual_by_path["home/controls.py"].index(
        "class RemoteControl(ORMModel):"
    ) < comparison.actual_by_path["home/controls.py"].index(
        "class TvChannel(ORMModel):"
    )
    assert (
        "class DeviceGroup(ORMModel):" in comparison.actual_by_path["devices/local.py"]
    )
    assert (
        "class LocalDevice(ORMModel):" in comparison.actual_by_path["devices/local.py"]
    )


@pytest.mark.asyncio
async def test_python_orm_same_file_class_and_attribute_create_deltas_match_full_render(
    tmp_path: Path,
) -> None:
    package = _python_package_create_delta_fixture(
        tmp_path,
        baseline_files={
            "home/controls.aware": """
class TvChannel {
}
""",
        },
        target_files={
            "home/controls.aware": """
class TvChannel {
}

class RemoteControl {
    remote_id String key
    label String
}
""",
        },
        create_operations=(
            _class_create_operation(
                class_fqn="aware_home.default.home.RemoteControl",
                class_name="RemoteControl",
                relative_path="home/controls.py",
                source_ref="home/controls.aware",
            ),
            _attribute_create_operation(
                owner_key="aware_home.default.home.RemoteControl",
                attribute_name="remote_id",
                relative_path="home/controls.py",
                source_ref="home/controls.aware",
            ),
            _attribute_create_operation(
                owner_key="aware_home.default.home.RemoteControl",
                attribute_name="label",
                relative_path="home/controls.py",
                source_ref="home/controls.aware",
            ),
        ),
    )

    package_deltas = await _resolved_python_package_deltas(
        package_root=cast(Path, package["baseline_package_root"]),
        sources_root=cast(str, package["sources_root"]),
        operations=cast(
            tuple[MetaProviderDeltaTypedOperation, ...], package["operations"]
        ),
    )
    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path=cast(dict[str, str], package["expected_by_path"]),
        baseline_by_path=cast(dict[str, str], package["baseline_by_path"]),
        package_deltas=package_deltas,
    )

    assert comparison.equivalent, comparison.summary()
    [relative_path] = sorted(comparison.actual_by_path)
    assert relative_path == "home/controls.py"
    assert comparison.actual_by_path[relative_path].index(
        "class RemoteControl(ORMModel):"
    ) < comparison.actual_by_path[relative_path].index("class TvChannel(ORMModel):")
    assert (
        "    remote_id: str\n    label: str\n"
        in comparison.actual_by_path[relative_path]
    )


@pytest.mark.asyncio
async def test_python_orm_class_delete_delta_matches_full_render_final_state(
    tmp_path: Path,
) -> None:
    package = _python_package_create_delta_fixture(
        tmp_path,
        baseline_files={
            "home/controls.aware": """
class RemoteControl {
    remote_id String key
}

class TvChannel {
    channel_id String key
}
""",
        },
        target_files={
            "home/controls.aware": """
class TvChannel {
    channel_id String key
}
""",
        },
        create_operations=(
            _class_delete_operation(
                class_fqn="aware_home.default.home.RemoteControl",
                class_name="RemoteControl",
                relative_path="home/controls.py",
                source_ref="home/controls.aware",
            ),
        ),
    )

    package_deltas = await _resolved_python_package_deltas(
        package_root=cast(Path, package["baseline_package_root"]),
        sources_root=cast(str, package["sources_root"]),
        operations=cast(
            tuple[MetaProviderDeltaTypedOperation, ...], package["operations"]
        ),
    )
    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path=cast(dict[str, str], package["expected_by_path"]),
        baseline_by_path=cast(dict[str, str], package["baseline_by_path"]),
        package_deltas=package_deltas,
    )

    assert comparison.equivalent, comparison.summary()
    [relative_path] = sorted(comparison.actual_by_path)
    assert relative_path == "home/controls.py"
    actual = comparison.actual_by_path[relative_path]
    assert "class TvChannel(ORMModel):" in actual
    assert "class RemoteControl(ORMModel):" not in actual
    assert actual == comparison.expected_by_path[relative_path]


@pytest.mark.asyncio
async def test_python_orm_same_file_attribute_update_delete_create_deltas_match_full_render(
    tmp_path: Path,
) -> None:
    package = _python_package_create_delta_fixture(
        tmp_path,
        baseline_files={
            "home/controls.aware": """
class RemoteControl {
    remote_id String key
    label String
    firmware_version String
}
""",
        },
        target_files={
            "home/controls.aware": """
class RemoteControl {
    remote_id String key
    label Int
    nickname String
}
""",
        },
        create_operations=(
            _attribute_type_update_operation(
                owner_key="aware_home.default.home.RemoteControl",
                attribute_name="label",
                baseline_primitive_base_type="string",
                current_primitive_base_type="integer",
                relative_path="home/controls.py",
                source_ref="home/controls.aware",
            ),
            _attribute_delete_operation(
                owner_key="aware_home.default.home.RemoteControl",
                attribute_name="firmware_version",
                primitive_base_type="string",
                relative_path="home/controls.py",
                source_ref="home/controls.aware",
            ),
            _attribute_create_operation(
                owner_key="aware_home.default.home.RemoteControl",
                attribute_name="nickname",
                relative_path="home/controls.py",
                source_ref="home/controls.aware",
            ),
        ),
    )

    package_deltas = await _resolved_python_package_deltas(
        package_root=cast(Path, package["baseline_package_root"]),
        sources_root=cast(str, package["sources_root"]),
        operations=cast(
            tuple[MetaProviderDeltaTypedOperation, ...], package["operations"]
        ),
    )
    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path=cast(dict[str, str], package["expected_by_path"]),
        baseline_by_path=cast(dict[str, str], package["baseline_by_path"]),
        package_deltas=package_deltas,
    )

    assert comparison.equivalent, comparison.summary()
    [relative_path] = sorted(comparison.actual_by_path)
    assert relative_path == "home/controls.py"
    actual = comparison.actual_by_path[relative_path]
    assert "    remote_id: str\n    label: int\n    nickname: str\n" in actual
    assert "firmware_version" not in actual


@pytest.mark.asyncio
async def test_python_orm_same_file_default_optionality_delete_create_deltas_match_full_render(
    tmp_path: Path,
) -> None:
    package = _python_package_create_delta_fixture(
        tmp_path,
        baseline_files={
            "home/controls.aware": """
class RemoteControl {
    remote_id String key
    volume Int = 7
    selected_channel Int?
    firmware_version String
}
""",
        },
        target_files={
            "home/controls.aware": """
class RemoteControl {
    remote_id String key
    volume Int = 11
    selected_channel Int
    nickname String
}
""",
        },
        create_operations=(
            _attribute_default_value_update_operation(
                owner_key="aware_home.default.home.RemoteControl",
                attribute_name="volume",
                primitive_base_type="integer",
                baseline_default_value="7",
                current_default_value="11",
                relative_path="home/controls.py",
                source_ref="home/controls.aware",
            ),
            _attribute_type_update_operation(
                owner_key="aware_home.default.home.RemoteControl",
                attribute_name="selected_channel",
                baseline_primitive_base_type="integer",
                current_primitive_base_type="integer",
                relative_path="home/controls.py",
                source_ref="home/controls.aware",
                baseline_is_required=False,
                current_is_required=True,
            ),
            _attribute_delete_operation(
                owner_key="aware_home.default.home.RemoteControl",
                attribute_name="firmware_version",
                primitive_base_type="string",
                relative_path="home/controls.py",
                source_ref="home/controls.aware",
            ),
            _attribute_create_operation(
                owner_key="aware_home.default.home.RemoteControl",
                attribute_name="nickname",
                relative_path="home/controls.py",
                source_ref="home/controls.aware",
            ),
        ),
    )

    package_deltas = await _resolved_python_package_deltas(
        package_root=cast(Path, package["baseline_package_root"]),
        sources_root=cast(str, package["sources_root"]),
        operations=cast(
            tuple[MetaProviderDeltaTypedOperation, ...], package["operations"]
        ),
    )
    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path=cast(dict[str, str], package["expected_by_path"]),
        baseline_by_path=cast(dict[str, str], package["baseline_by_path"]),
        package_deltas=package_deltas,
    )

    assert comparison.equivalent, comparison.summary()
    [relative_path] = sorted(comparison.actual_by_path)
    assert relative_path == "home/controls.py"
    actual = comparison.actual_by_path[relative_path]
    assert "    volume: int = Field(default=11)\n" in actual
    assert "    selected_channel: int\n" in actual
    assert "    nickname: str\n" in actual
    assert "firmware_version" not in actual


@pytest.mark.asyncio
async def test_python_orm_enum_option_delete_create_reorder_deltas_match_full_render(
    tmp_path: Path,
) -> None:
    package = _python_package_create_delta_fixture(
        tmp_path,
        baseline_files={
            "content/content_enums.aware": """
enum ContentKind {
    text
    image
    legacy
}
""",
        },
        target_files={
            "content/content_enums.aware": """
enum ContentKind {
    image
    video
    text
}
""",
        },
        create_operations=(
            _enum_option_delete_operation(
                enum_fqn="aware_home.default.content.ContentKind",
                enum_name="ContentKind",
                option_value="legacy",
                baseline_position=2,
                relative_path="content/content_enums.py",
                source_ref="content/content_enums.aware",
            ),
            _enum_option_create_operation(
                enum_fqn="aware_home.default.content.ContentKind",
                enum_name="ContentKind",
                option_value="video",
                current_position=1,
                relative_path="content/content_enums.py",
                source_ref="content/content_enums.aware",
            ),
            _enum_option_position_update_operation(
                enum_fqn="aware_home.default.content.ContentKind",
                enum_name="ContentKind",
                option_value="text",
                baseline_position=0,
                current_position=2,
                relative_path="content/content_enums.py",
                source_ref="content/content_enums.aware",
            ),
        ),
    )

    package_deltas = await _resolved_python_package_deltas(
        package_root=cast(Path, package["baseline_package_root"]),
        sources_root=cast(str, package["sources_root"]),
        operations=cast(
            tuple[MetaProviderDeltaTypedOperation, ...], package["operations"]
        ),
    )
    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path=cast(dict[str, str], package["expected_by_path"]),
        baseline_by_path=cast(dict[str, str], package["baseline_by_path"]),
        package_deltas=package_deltas,
    )

    assert comparison.equivalent, comparison.summary()
    [relative_path] = sorted(comparison.actual_by_path)
    assert relative_path == "content/content_enums.py"
    actual = comparison.actual_by_path[relative_path]
    assert actual == comparison.expected_by_path[relative_path]
    assert '    image = "image"\n    video = "video"\n    text = "text"\n' in actual
    assert "legacy" not in actual


@pytest.mark.asyncio
async def test_python_orm_relationship_load_policy_delta_matches_full_render_final_state(
    tmp_path: Path,
) -> None:
    package = _python_package_create_delta_fixture(
        tmp_path,
        baseline_files={
            "home/controls.aware": """
class TvChannel {
    channel_id String key
}

class RemoteControl {
    remote_id String key
    selected_channel TvChannel
}
""",
        },
        target_files={
            "home/controls.aware": """
class TvChannel {
    channel_id String key
}

class RemoteControl {
    remote_id String key
    selected_channel TvChannel
}

ann default.RemoteControl::selected_channel load forward eager
""",
        },
        create_operations=(
            _relationship_load_policy_update_operation(
                source_class_fqn="aware_home.default.home.RemoteControl",
                target_class_fqn="aware_home.default.home.TvChannel",
                relationship_key="selected_channel",
                baseline_forward_loading_strategy="lazy",
                current_forward_loading_strategy="eager",
                relative_path="home/controls.py",
                source_ref="home/controls.aware",
            ),
        ),
    )

    package_deltas = await _resolved_python_package_deltas(
        package_root=cast(Path, package["baseline_package_root"]),
        sources_root=cast(str, package["sources_root"]),
        operations=cast(
            tuple[MetaProviderDeltaTypedOperation, ...], package["operations"]
        ),
    )
    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path=cast(dict[str, str], package["expected_by_path"]),
        baseline_by_path=cast(dict[str, str], package["baseline_by_path"]),
        package_deltas=package_deltas,
    )

    assert comparison.equivalent, comparison.summary()
    [relative_path] = sorted(comparison.actual_by_path)
    assert relative_path == "home/controls.py"
    actual = comparison.actual_by_path[relative_path]
    assert actual == comparison.expected_by_path[relative_path]
    assert "    selected_channel: TvChannel\n" in actual
    assert (
        "    selected_channel_id: UUID | None = "
        'Field(default=None, description="Foreign key for RemoteControl.selected_channel")\n'
    ) in actual
    assert "selected_channel: TvChannel | None = Field" not in actual


@pytest.mark.asyncio
async def test_python_orm_relationship_create_delta_matches_full_render_final_state(
    tmp_path: Path,
) -> None:
    package = _python_package_create_delta_fixture(
        tmp_path,
        baseline_files={
            "home/model.aware": """
class Device {
    name String
}

class Room {
    room_name String
}
""",
        },
        target_files={
            "home/model.aware": """
class Device {
    name String
}

class Room {
    room_name String
    primary_device Device
}

ann default.Room::primary_device load forward eager
""",
        },
        create_operations=(
            _relationship_create_operation(
                source_class_fqn="aware_home.default.home.Room",
                target_class_fqn="aware_home.default.home.Device",
                relationship_key="primary_device",
                forward_loading_strategy="eager",
                relative_path="home/model.py",
                source_ref="home/model.aware",
            ),
        ),
    )

    package_deltas = await _resolved_python_package_deltas(
        package_root=cast(Path, package["baseline_package_root"]),
        sources_root=cast(str, package["sources_root"]),
        operations=cast(
            tuple[MetaProviderDeltaTypedOperation, ...], package["operations"]
        ),
    )
    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path=cast(dict[str, str], package["expected_by_path"]),
        baseline_by_path=cast(dict[str, str], package["baseline_by_path"]),
        package_deltas=package_deltas,
    )

    assert comparison.equivalent, comparison.summary()
    [relative_path] = sorted(comparison.actual_by_path)
    assert relative_path == "home/model.py"
    actual = comparison.actual_by_path[relative_path]
    assert actual == comparison.expected_by_path[relative_path]
    assert "# Relationships\n    primary_device: Device\n" in actual
    assert (
        "    primary_device_id: UUID | None = "
        'Field(default=None, description="Foreign key for Room.primary_device")\n'
    ) in actual


@pytest.mark.asyncio
async def test_python_orm_relationship_delete_delta_matches_full_render_final_state(
    tmp_path: Path,
) -> None:
    package = _python_package_create_delta_fixture(
        tmp_path,
        baseline_files={
            "home/model.aware": """
class Device {
    name String
}

class Room {
    room_name String
    primary_device Device
}

ann default.Room::primary_device load forward eager
""",
        },
        target_files={
            "home/model.aware": """
class Device {
    name String
}

class Room {
    room_name String
}
""",
        },
        create_operations=(
            _relationship_delete_operation(
                source_class_fqn="aware_home.default.home.Room",
                target_class_fqn="aware_home.default.home.Device",
                relationship_key="primary_device",
                forward_loading_strategy="eager",
                relative_path="home/model.py",
                source_ref="home/model.aware",
            ),
        ),
    )

    package_deltas = await _resolved_python_package_deltas(
        package_root=cast(Path, package["baseline_package_root"]),
        sources_root=cast(str, package["sources_root"]),
        operations=cast(
            tuple[MetaProviderDeltaTypedOperation, ...], package["operations"]
        ),
    )
    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path=cast(dict[str, str], package["expected_by_path"]),
        baseline_by_path=cast(dict[str, str], package["baseline_by_path"]),
        package_deltas=package_deltas,
    )

    assert comparison.equivalent, comparison.summary()
    [relative_path] = sorted(comparison.actual_by_path)
    assert relative_path == "home/model.py"
    actual = comparison.actual_by_path[relative_path]
    assert actual == comparison.expected_by_path[relative_path]
    assert "primary_device" not in actual
    assert "from uuid import UUID" not in actual
    assert "from pydantic import Field" not in actual


@pytest.mark.asyncio
async def test_python_orm_function_create_constructor_delta_matches_full_runtime_render(
    tmp_path: Path,
) -> None:
    owner_key = "aware_home.default.home.TvChannel"
    package = _python_package_create_delta_fixture(
        tmp_path,
        baseline_files={
            "home/tv_channel.aware": """
class TvChannel {
    name String
    number Int key
}
""",
        },
        target_files={
            "home/tv_channel.aware": """
class TvChannel {
    name String
    number Int key

    fn create construct(name String, number Int key) -> TvChannel {
        \"\"\"
        Create a Tv channel.
        \"\"\"
    }
}
""",
        },
        create_operations=(
            _function_create_operation(
                owner_key=owner_key,
                function_name="create",
                is_constructor=True,
                description="Create a Tv channel.",
                relative_path="home/tv_channel.py",
                source_ref="home/tv_channel.aware",
                inputs=(
                    _function_attribute_payload(
                        name="name",
                        primitive_base_type="string",
                        position=0,
                    ),
                    _function_attribute_payload(
                        name="number",
                        primitive_base_type="integer",
                        position=1,
                    ),
                ),
                outputs=(
                    _function_attribute_payload(
                        name="value",
                        class_fqn=owner_key,
                        position=0,
                    ),
                ),
            ),
        ),
        renderer_profile=PYTHON_ORM_RENDERER_PROFILE,
    )

    package_deltas = await _resolved_python_package_deltas(
        package_root=cast(Path, package["baseline_package_root"]),
        sources_root=cast(str, package["sources_root"]),
        operations=cast(
            tuple[MetaProviderDeltaTypedOperation, ...], package["operations"]
        ),
    )
    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path=cast(dict[str, str], package["expected_by_path"]),
        baseline_by_path=cast(dict[str, str], package["baseline_by_path"]),
        package_deltas=package_deltas,
    )

    assert comparison.equivalent, comparison.summary()
    [relative_path] = sorted(comparison.actual_by_path)
    assert relative_path == "home/tv_channel.py"
    actual = comparison.actual_by_path[relative_path]
    assert "from pydantic import BaseModel" in actual
    assert "from aware_orm.runtime.invocation import invoke_constructor" in actual
    assert "async def create(cls, name: str, number: int) -> TvChannel:" in actual
    assert "class TvChannelCreateInput(BaseModel):" in actual
    assert "class TvChannelCreateOutput(BaseModel):" in actual
    assert "FUNCTIONS = {" in actual
    assert '"create": {' in actual


@pytest.mark.asyncio
async def test_python_orm_storage_style_function_and_attribute_deltas_match_full_render(
    tmp_path: Path,
) -> None:
    bucket_owner_key = "aware_home.default.bucket.StorageBucket"
    package = _python_package_create_delta_fixture(
        tmp_path,
        baseline_files={
            "bucket/storage_bucket.aware": """
enum StorageBackend {
    local
}

class StorageBucket {
}
""",
        },
        target_files={
            "bucket/storage_bucket.aware": """
enum StorageBackend {
    local
}

class StorageBucket {
    allowed_mime_types String[]
    backend StorageBackend = "local"
    config JsonObject?
    name String key

    fn build construct(
        name String key,
        backend StorageBackend = "local",
        allowed_mime_types String[] = [],
        config JsonObject? = null,
    ) -> StorageBucket {
        \"\"\"
        Create a deterministic storage bucket metadata root.

        Contract:
        - Identity is deterministic from `(name)`.
        - Backend/config values are mutable policy metadata.
        \"\"\"
    }
}
""",
        },
        create_operations=(
            _attribute_create_operation(
                owner_key=bucket_owner_key,
                attribute_name="allowed_mime_types",
                relative_path="bucket/storage_bucket.py",
                source_ref="bucket/storage_bucket.aware",
                type_descriptor={
                    "kind": "collection",
                    "collection_kind": "list",
                    "child_descriptors": (
                        {
                            "kind": "primitive",
                            "primitive_base_type": "string",
                        },
                    ),
                    "element_primitive_base_type": "string",
                },
                default_value=[],
            ),
            _attribute_create_operation(
                owner_key=bucket_owner_key,
                attribute_name="backend",
                relative_path="bucket/storage_bucket.py",
                source_ref="bucket/storage_bucket.aware",
                type_descriptor={
                    "kind": "enum",
                    "enum_fqn": "aware_home.default.bucket.StorageBackend",
                },
                default_value="local",
            ),
            _attribute_create_operation(
                owner_key=bucket_owner_key,
                attribute_name="config",
                relative_path="bucket/storage_bucket.py",
                source_ref="bucket/storage_bucket.aware",
                type_descriptor={
                    "kind": "primitive",
                    "primitive_base_type": "json",
                },
                is_required=False,
            ),
            _attribute_create_operation(
                owner_key=bucket_owner_key,
                attribute_name="name",
                relative_path="bucket/storage_bucket.py",
                source_ref="bucket/storage_bucket.aware",
            ),
            _function_create_operation(
                owner_key=bucket_owner_key,
                function_name="build",
                is_constructor=True,
                description=(
                    "Create a deterministic storage bucket metadata root.\n\n"
                    "Contract:\n"
                    "- Identity is deterministic from `(name)`.\n"
                    "- Backend/config values are mutable policy metadata."
                ),
                relative_path="bucket/storage_bucket.py",
                source_ref="bucket/storage_bucket.aware",
                inputs=(
                    _function_attribute_payload(
                        name="name",
                        primitive_base_type="string",
                        position=0,
                    ),
                    _function_attribute_payload(
                        name="backend",
                        enum_fqn="aware_home.default.bucket.StorageBackend",
                        position=1,
                        default_value="local",
                    ),
                    _function_attribute_payload(
                        name="allowed_mime_types",
                        collection_child={
                            "kind": "primitive",
                            "primitive_base_type": "string",
                        },
                        position=2,
                        default_value=[],
                    ),
                    _function_attribute_payload(
                        name="config",
                        primitive_base_type="json",
                        position=3,
                        is_required=False,
                        default_value=None,
                    ),
                ),
                outputs=(
                    _function_attribute_payload(
                        name="value",
                        class_fqn=bucket_owner_key,
                        position=0,
                    ),
                ),
            ),
        ),
        renderer_profile=PYTHON_ORM_RENDERER_PROFILE,
    )

    package_deltas = await _resolved_python_package_deltas(
        package_root=cast(Path, package["baseline_package_root"]),
        sources_root=cast(str, package["sources_root"]),
        operations=cast(
            tuple[MetaProviderDeltaTypedOperation, ...], package["operations"]
        ),
    )
    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path=cast(dict[str, str], package["expected_by_path"]),
        baseline_by_path=cast(dict[str, str], package["baseline_by_path"]),
        package_deltas=package_deltas,
    )

    assert comparison.equivalent, comparison.summary()
    actual = comparison.actual_by_path["bucket/storage_bucket.py"]
    assert "allowed_mime_types: list[str] = Field(default_factory=list)" in actual
    assert "backend: StorageBackend = Field(default=StorageBackend.local)" in actual
    assert "config: JsonObject | None = Field(default=None)" in actual
    assert "async def build(" in actual
    assert "from aware_types import JsonObject" in actual


@pytest.mark.asyncio
async def test_python_orm_storage_style_relationship_and_function_deltas_emit_product_shape(
    tmp_path: Path,
) -> None:
    bucket_owner_key = "aware_home.default.bucket.StorageBucket"
    blob_owner_key = "aware_home.default.blob.StorageBlob"
    package = _python_package_create_delta_fixture(
        tmp_path,
        baseline_files={
            "bucket/storage_bucket.aware": """
class StorageBucket {
    name String
}
""",
            "blob/storage_blob.aware": """
class StorageBlob {
    mime_type String
    sha String
    size_bytes Int
}
""",
        },
        target_files={
            "bucket/storage_bucket.aware": """
class StorageBucket {
    name String
}
""",
            "blob/storage_blob.aware": """
class StorageBlob {
    bucket StorageBucket
    mime_type String
    sha String
    size_bytes Int

    fn create construct(sha String, mime_type String, size_bytes Int) -> StorageBlob {
        \"\"\"
        Registers a StorageBlob metadata record for already-uploaded bytes.

        Contract:
        - Commits must never include raw bytes.
        - Bytes are uploaded out-of-band (HTTP data-plane).
        - This constructor records the immutable metadata required to resolve and validate bytes.
        \"\"\"
    }
}
""",
        },
        create_operations=(
            _relationship_create_operation(
                source_class_fqn=blob_owner_key,
                target_class_fqn=bucket_owner_key,
                relationship_key="bucket",
                forward_loading_strategy="lazy",
                relative_path="blob/storage_blob.py",
                source_ref="blob/storage_blob.aware",
            ),
            _function_create_operation(
                owner_key=blob_owner_key,
                function_name="create",
                is_constructor=True,
                description=(
                    "Registers a StorageBlob metadata record for already-uploaded "
                    "bytes.\n\n"
                    "Contract:\n"
                    "- Commits must never include raw bytes.\n"
                    "- Bytes are uploaded out-of-band (HTTP data-plane).\n"
                    "- This constructor records the immutable metadata required "
                    "to resolve and validate bytes."
                ),
                relative_path="blob/storage_blob.py",
                source_ref="blob/storage_blob.aware",
                inputs=(
                    _function_attribute_payload(
                        name="sha",
                        primitive_base_type="string",
                        position=0,
                    ),
                    _function_attribute_payload(
                        name="mime_type",
                        primitive_base_type="string",
                        position=1,
                    ),
                    _function_attribute_payload(
                        name="size_bytes",
                        primitive_base_type="integer",
                        position=2,
                    ),
                ),
                outputs=(
                    _function_attribute_payload(
                        name="value",
                        class_fqn=blob_owner_key,
                        position=0,
                    ),
                ),
            ),
        ),
        renderer_profile=PYTHON_ORM_RENDERER_PROFILE,
    )

    package_deltas = await _resolved_python_package_deltas(
        package_root=cast(Path, package["baseline_package_root"]),
        sources_root=cast(str, package["sources_root"]),
        operations=cast(
            tuple[MetaProviderDeltaTypedOperation, ...], package["operations"]
        ),
    )
    comparison = compare_generated_materialization_package_delta_final_state(
        expected_by_path=cast(dict[str, str], package["expected_by_path"]),
        baseline_by_path=cast(dict[str, str], package["baseline_by_path"]),
        package_deltas=package_deltas,
    )

    actual = comparison.actual_by_path["blob/storage_blob.py"]
    assert "from typing import TYPE_CHECKING" in actual
    assert "from uuid import UUID" in actual
    assert "if TYPE_CHECKING:" in actual
    assert "from aware_home_ontology.default.bucket.storage_bucket import StorageBucket" in actual
    assert (
        "    bucket_id: UUID | None = "
        'Field(default=None, description="Foreign key for StorageBlob.bucket")'
    ) in actual
    assert (
        "async def create(cls, sha: str, mime_type: str, size_bytes: int) "
        "-> StorageBlob:"
    ) in actual


def test_meta_attribute_create_source_operation_preserves_storage_descriptors() -> None:
    operation = {
        "operation_key": (
            "aware_kernel.storage_ontology_genesis."
            "aware_storage.bucket.StorageBucket.allowed_mime_types.create"
        ),
        "operation_family": "create",
        "semantic_operation_type": "aware_meta.object_config_graph.attribute.create",
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "semantic_key": (
            "ocg:aware_storage/node:aware_storage.bucket.StorageBucket/"
            "attribute:allowed_mime_types"
        ),
        "field_path": "definition",
        "source_refs": ("bucket/storage_bucket.aware",),
        "after_payload": {
            "class_name": "StorageBucket",
            "class_fqn": "aware_storage.bucket.StorageBucket",
            "owner_key": "aware_storage.bucket.StorageBucket",
            "attribute_config_id": "attribute-allowed-mime-types",
            "attribute_name": "allowed_mime_types",
            "attribute_signature": {
                "owner_key": "aware_storage.bucket.StorageBucket",
                "name": "allowed_mime_types",
                "is_required": True,
                "is_public": True,
                "type_descriptor": {
                    "kind": "collection",
                    "collection_kind": "list",
                    "element_primitive_base_type": "string",
                    "child_descriptors": (
                        {
                            "kind": "primitive",
                            "primitive_base_type": "string",
                        },
                    ),
                },
                "default_value": [],
            },
        },
    }

    payload = _meta_attribute_create_typed_operation_from_semantic_source_operation(
        operation,
        default_source_refs=("bucket/storage_bucket.aware",),
        semantic_key=cast(str, operation["semantic_key"]),
        generated_materialization_target_profile=ORM_RUNTIME_TARGET_PROFILE,
    )
    current = cast(dict[str, object], payload["current"])
    signature = cast(dict[str, object], current["attribute_signature"])
    descriptor = cast(dict[str, object], signature["type_descriptor"])

    assert descriptor["kind"] == "collection"
    assert descriptor["collection_kind"] == "list"
    assert signature["default_value"] == []


async def _resolved_python_package_deltas(
    *,
    package_root: Path,
    sources_root: str,
    operations: tuple[MetaProviderDeltaTypedOperation, ...],
) -> tuple[CodePackageDelta, ...]:
    package_deltas: list[CodePackageDelta] = []

    for operation in operations:
        evidence = PythonOrmRuntimeGeneratedDeltaRenderer().render_generated_materialization_delta(
            MetaLanguageGeneratedMaterializationDeltaRenderRequest(
                operation=operation,
                context=MetaLanguageGeneratedMaterializationDeltaContext(
                    package_name="aware-home-ontology-python",
                    package_root=package_root.as_posix(),
                    sources_root=sources_root,
                    target_language="python",
                    renderer_profile=PYTHON_ORM_RENDERER_PROFILE,
                    materialization_source=PYTHON_ORM_MATERIALIZATION_SOURCE,
                    product_intent="orm_runtime",
                    target_hints=(
                        MetaLanguageGeneratedMaterializationTargetHint(
                            descriptor_key="orm_runtime",
                            capability_key=PYTHON_ORM_GENERATED_DELTA_RENDERER_NAME,
                            target_language="python",
                            renderer_profile=PYTHON_ORM_RENDERER_PROFILE,
                            materialization_source=PYTHON_ORM_MATERIALIZATION_SOURCE,
                            owner_key=_operation_owner_key(operation),
                            relative_path=_operation_relative_path(operation),
                        ),
                    ),
                ),
            )
        )

        assert evidence.handled is True
        assert evidence.delta_request is not None
        assert evidence.result is not None
        assert evidence.result.mode in {
            CodeGeneratedMaterializationDeltaMode.package_delta_ready,
            CodeGeneratedMaterializationDeltaMode.grammar_anchor_render_ready,
            CodeGeneratedMaterializationDeltaMode.section_delta_ready,
        }

        resolved_delta = _resolve_generated_materialization_package_delta_for_test(
            delta_request=evidence.delta_request,
            result=evidence.result,
        )

        package_deltas.append(resolved_delta)
        _apply_package_delta_to_generated_package(
            package_root=package_root,
            sources_root=sources_root,
            package_delta=resolved_delta,
        )

    return tuple(package_deltas)


def _resolve_generated_materialization_package_delta_for_test(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    result: CodeGeneratedMaterializationDeltaResult,
) -> CodePackageDelta:
    assert result.available is True
    resolved_deltas = [
        _resolve_generated_materialization_entry_for_test(
            delta_request=delta_request,
            entry=entry,
        )
        for entry in result.entries
    ]
    assert resolved_deltas
    return _merge_package_deltas_for_test(
        delta_request=delta_request,
        result=result,
        deltas=resolved_deltas,
    )


def _resolve_generated_materialization_entry_for_test(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    entry: CodeGeneratedMaterializationDeltaEntry,
) -> CodePackageDelta:
    if entry.package_delta is not None:
        return _package_delta_with_identity_defaults(
            package_delta=entry.package_delta,
            delta_request=delta_request,
            entry=entry,
        )
    if entry.grammar_anchor_render_delta is not None:
        grammar_request = entry.grammar_anchor_render_delta.model_copy(
            update={
                "package_name": (
                    entry.grammar_anchor_render_delta.package_name
                    or entry.target.package_name
                    or delta_request.package_name
                ),
                "package_root": (
                    entry.grammar_anchor_render_delta.package_root
                    or entry.target.package_root
                    or delta_request.package_root
                ),
                "sources_root": (
                    entry.grammar_anchor_render_delta.sources_root
                    or entry.target.sources_root
                    or delta_request.sources_root
                ),
                "baseline_fingerprint": (
                    entry.grammar_anchor_render_delta.baseline_fingerprint
                    or delta_request.baseline_fingerprint
                ),
                "baseline_fingerprint_algorithm": (
                    entry.grammar_anchor_render_delta.baseline_fingerprint_algorithm
                    or delta_request.baseline_fingerprint_algorithm
                    or "sha256"
                ),
            }
        )
        response = resolve_code_grammar_anchor_render_delta(request=grammar_request)
        assert response.success is True, response.diagnostics
        assert response.resolved is True, response.diagnostics
        assert response.package_delta is not None
        return _package_delta_with_identity_defaults(
            package_delta=response.package_delta,
            delta_request=delta_request,
            entry=entry,
        )
    if entry.section_delta is not None:
        return _resolve_section_delta_set_for_test(
            entry.section_delta.model_copy(
                update={
                    "package_name": (
                        entry.section_delta.package_name
                        or entry.target.package_name
                        or delta_request.package_name
                    ),
                    "package_root": (
                        entry.section_delta.package_root
                        or entry.target.package_root
                        or delta_request.package_root
                    ),
                    "sources_root": (
                        entry.section_delta.sources_root
                        or entry.target.sources_root
                        or delta_request.sources_root
                    ),
                    "baseline_fingerprint": (
                        entry.section_delta.baseline_fingerprint
                        or delta_request.baseline_fingerprint
                    ),
                }
            )
        )
    raise AssertionError(
        "Generated materialization entry must include package_delta, "
        "grammar_anchor_render_delta, or section_delta evidence."
    )


def _resolve_section_delta_set_for_test(
    delta_set: CodeSectionDeltaSet,
) -> CodePackageDelta:
    assert delta_set.package_root is not None
    base_path = Path(delta_set.package_root)
    if delta_set.sources_root:
        base_path = base_path / delta_set.sources_root
    file_text_by_path: dict[str, str] = {}
    original_text_by_path: dict[str, str] = {}

    for entry in sorted(delta_set.entries, key=_section_delta_entry_sort_key):
        relative_path = entry.section_ref.relative_path
        assert relative_path and not Path(relative_path).is_absolute()
        if relative_path not in file_text_by_path:
            source_path = base_path / relative_path
            assert source_path.is_file(), source_path
            text = source_path.read_text(encoding="utf-8")
            file_text_by_path[relative_path] = text
            original_text_by_path[relative_path] = text
        file_text_by_path[relative_path] = _apply_section_delta_entry_for_test(
            entry=entry,
            current_text=file_text_by_path[relative_path],
        )

    assert file_text_by_path
    return CodePackageDelta(
        package_name=delta_set.package_name,
        package_root=delta_set.package_root,
        sources_root=delta_set.sources_root,
        authority=CodePackageDeltaAuthorityKind.code_package_delta,
        authority_kind=CodePackageDeltaAuthorityKind.code_package_delta.value,
        production=delta_set.production,
        paths=[
            CodePackageDeltaPath(
                relative_path=relative_path,
                kind=CodePackageDeltaKind.update,
                content_text=updated_text,
                before_hash=_sha256_digest(original_text_by_path[relative_path]),
                after_hash=_sha256_digest(updated_text),
                size_bytes=len(updated_text.encode("utf-8")),
                language=ServiceCodeLanguage.python,
                is_structural=True,
            )
            for relative_path, updated_text in sorted(file_text_by_path.items())
        ],
        warnings=list(delta_set.warnings),
    )


def _apply_section_delta_entry_for_test(
    *,
    entry: CodeSectionDeltaEntry,
    current_text: str,
) -> str:
    assert entry.operation is CodeSectionDeltaOperationKind.replace_segment
    assert entry.segment_ref is not None
    assert entry.content_text is not None
    section_type = CodeSectionType(entry.section_ref.section_type)
    language = CodeLanguage(entry.section_ref.language or "python")
    hydrated_entry = _hydrated_section_delta_entry_for_test(
        entry=entry,
        current_text=current_text,
        language=language,
        section_type=section_type,
    )
    segment_ref = hydrated_entry.segment_ref
    assert segment_ref is not None
    assert segment_ref.byte_start is not None
    assert segment_ref.byte_end is not None
    current_bytes = current_text.encode("utf-8")
    before_text = current_bytes[segment_ref.byte_start : segment_ref.byte_end].decode(
        "utf-8"
    )
    assert _segment_render_digest_matches(
        segment_ref.before_segment_hash,
        _sha256_digest(before_text),
    )
    replacement_text = hydrated_entry.content_text
    assert replacement_text is not None
    updated_bytes = (
        current_bytes[: segment_ref.byte_start]
        + replacement_text.encode("utf-8")
        + current_bytes[segment_ref.byte_end :]
    )
    return updated_bytes.decode("utf-8")


def _hydrated_section_delta_entry_for_test(
    *,
    entry: CodeSectionDeltaEntry,
    current_text: str,
    language: CodeLanguage,
    section_type: CodeSectionType,
) -> CodeSectionDeltaEntry:
    segment_ref = entry.segment_ref
    assert segment_ref is not None
    if segment_ref.byte_start is not None and segment_ref.byte_end is not None:
        return entry

    setup_code_plugins()
    code = build_code_from_content(
        sections_index=CodeSectionBuilderIndex(),
        content=current_text,
        code_key=entry.section_ref.relative_path,
        language=language,
        symbol_table=CodeSymbolTable(),
    )
    candidates = [
        section
        for section in code.code_sections
        if section.type == section_type
        and (
            not entry.section_ref.identity_hash
            or section.identity_hash == entry.section_ref.identity_hash
        )
        and (
            not entry.section_ref.qualname
            or section.qualname == entry.section_ref.qualname
        )
    ]
    assert len(candidates) == 1
    segment = CodeSegmentScanner.get_segment_from_section(
        candidates[0],
        segment_ref.segment_name,
    )
    assert segment is not None
    assert segment.byte_start is not None
    assert segment.byte_end is not None

    current_bytes = current_text.encode("utf-8")
    segment_text = current_bytes[segment.byte_start : segment.byte_end].decode("utf-8")
    segment_payload = segment_ref.model_dump(mode="json")
    segment_payload["byte_start"] = segment.byte_start
    segment_payload["byte_end"] = segment.byte_end
    segment_payload["before_segment_hash"] = (
        segment_ref.before_segment_hash or _sha256_digest(segment_text)
    )
    content_text = entry.content_text
    if content_text is not None:
        policy = resolve_code_segment_render_policy(
            language=language.value,
            section_type=section_type.value,
            segment_name=segment_ref.segment_name,
        )
        if policy is not None and not policy.raw_segment_is_policy_owned(
            content_text,
        ):
            requested_semantic_text = policy.semantic_text_from_content_text(
                content_text
            )
            requested_semantic_hash = _segment_render_sha256_digest(
                requested_semantic_text
            )
            current_semantic_text = policy.semantic_text_from_raw_segment(segment_text)
            current_semantic_hash = _segment_render_sha256_digest(current_semantic_text)
            current_raw_hash = _sha256_digest(segment_text)
            if _segment_render_digest_matches(
                segment_ref.before_segment_hash,
                current_semantic_hash,
            ) or _segment_render_digest_matches(
                segment_ref.before_segment_hash,
                current_raw_hash,
            ):
                content_text = policy.render_raw_segment(
                    semantic_text=requested_semantic_text,
                    current_raw_segment=segment_text,
                )
                segment_payload["before_segment_hash"] = current_raw_hash
                assert _segment_render_digest_matches(
                    entry.after_hash,
                    requested_semantic_hash,
                )

    return entry.model_copy(
        update={
            "segment_ref": CodeSegmentRef.model_validate(segment_payload),
            "content_text": content_text,
            "after_hash": (
                _sha256_digest(content_text) if content_text is not None else None
            ),
        }
    )


def _package_delta_with_identity_defaults(
    *,
    package_delta: CodePackageDelta,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    entry: CodeGeneratedMaterializationDeltaEntry,
) -> CodePackageDelta:
    return package_delta.model_copy(
        update={
            "package_name": (
                package_delta.package_name
                or entry.target.package_name
                or delta_request.package_name
            ),
            "package_root": (
                package_delta.package_root
                or entry.target.package_root
                or delta_request.package_root
            ),
            "sources_root": (
                package_delta.sources_root
                or entry.target.sources_root
                or delta_request.sources_root
            ),
            "authority": CodePackageDeltaAuthorityKind.code_package_delta,
            "authority_kind": CodePackageDeltaAuthorityKind.code_package_delta.value,
        }
    )


def _merge_package_deltas_for_test(
    *,
    delta_request: CodeGeneratedMaterializationDeltaRequest,
    result: CodeGeneratedMaterializationDeltaResult,
    deltas: list[CodePackageDelta],
) -> CodePackageDelta:
    _ = result
    paths_by_relative_path: dict[str, CodePackageDeltaPath] = {}
    warnings: list[str] = []
    for delta in deltas:
        warnings.extend(delta.warnings)
        for path in delta.paths:
            existing = paths_by_relative_path.get(path.relative_path)
            assert existing is None or existing.model_dump(
                mode="json"
            ) == path.model_dump(mode="json")
            paths_by_relative_path[path.relative_path] = path
    return CodePackageDelta(
        package_name=deltas[0].package_name or delta_request.package_name,
        package_root=deltas[0].package_root or delta_request.package_root,
        sources_root=deltas[0].sources_root or delta_request.sources_root,
        authority=CodePackageDeltaAuthorityKind.code_package_delta,
        authority_kind=CodePackageDeltaAuthorityKind.code_package_delta.value,
        paths=[paths_by_relative_path[path] for path in sorted(paths_by_relative_path)],
        warnings=sorted(set(warnings)),
    )


def _section_delta_entry_sort_key(entry: CodeSectionDeltaEntry) -> tuple[str, ...]:
    section = entry.section_ref
    segment = entry.segment_ref
    return (
        entry.operation.value,
        section.relative_path,
        section.section_type,
        section.qualname or "",
        segment.segment_name if segment is not None else "",
        entry.semantic_key or "",
        entry.event_ref or "",
    )


def _sha256_digest(text: str) -> str:
    return "sha256:" + sha256(text.encode("utf-8")).hexdigest()


def _python_package_create_delta_fixture(
    tmp_path: Path,
    *,
    baseline_files: dict[str, str],
    target_files: dict[str, str],
    create_operations: tuple[dict[str, object], ...],
    renderer_profile: str = ONTOLOGY_ORM_MODELS_RENDERER_PROFILE,
) -> dict[str, object]:
    sources_root = "aware_home_ontology"
    baseline_package_root = tmp_path / "baseline" / "python" / "orm_runtime"
    target_package_root = tmp_path / "target" / "python" / "orm_runtime"

    baseline_by_path = _render_python_orm_models_package(
        tmp_path / "baseline_sources",
        output_root=baseline_package_root / sources_root,
        files=baseline_files,
        renderer_profile=renderer_profile,
    )
    expected_by_path = _render_python_orm_models_package(
        tmp_path / "target_sources",
        output_root=target_package_root / sources_root,
        files=target_files,
        renderer_profile=renderer_profile,
    )

    return {
        "baseline_package_root": baseline_package_root,
        "sources_root": sources_root,
        "baseline_by_path": baseline_by_path,
        "expected_by_path": expected_by_path,
        "operations": tuple(_typed_operation(payload) for payload in create_operations),
    }


def _render_python_orm_models_package(
    source_root: Path,
    *,
    output_root: Path,
    files: dict[str, str],
    renderer_profile: str = ONTOLOGY_ORM_MODELS_RENDERER_PROFILE,
) -> dict[str, str]:
    CodeLanguagePluginRegistry.register(AWARE_CODE_PLUGIN)
    file_codes = tuple(
        (
            relative_path,
            _build_code(source_root, relative_path, content.strip()),
        )
        for relative_path, content in sorted(files.items())
    )
    namespace_by_code_id, _domains = _namespace_by_code_id(
        fqn_prefix="aware_home",
        namespace="default",
        code_ids=[code.id for _relative_path, code in file_codes],
    )
    graph = build_object_config_graph_from_code(
        name="aware-home-test",
        description="Aware Home test package.",
        fqn_prefix="aware_home",
        file_codes=list(file_codes),
        namespace_by_code_id=namespace_by_code_id,
    ).graph

    MetaLanguagePluginRegistry.register(PYTHON_META_PLUGIN)
    result = materialize_object_config_graph_via_language_plugin(
        LanguagePluginMaterializationRequest(
            source_graph=graph,
            target_language_plugin_id=CodeLanguage.python,
            output_root=output_root,
            renderer_kind="default",
            renderer_profile=renderer_profile,
            emit_files=True,
        )
    )

    return {
        generated.path.as_posix(): (output_root / generated.path).read_text(
            encoding="utf-8"
        )
        for generated in result.generated_files
    }


def _build_code(source_root: Path, relative_path: str, content: str):
    path = source_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return build_code_from_file(
        sections_index=CodeSectionBuilderIndex(),
        file_path=str(path),
        language=CodeLanguage.aware,
        symbol_table=CodeSymbolTable(),
    )


def _namespace_by_code_id(
    *,
    fqn_prefix: str,
    namespace: str,
    code_ids: list[UUID],
):
    return {
        code_id: NamespacePath(package=fqn_prefix, namespace=namespace)
        for code_id in code_ids
    }, []


def _class_create_operation(
    *,
    class_fqn: str,
    class_name: str,
    relative_path: str,
    source_ref: str,
) -> dict[str, object]:
    semantic_key = f"ocg:aware_home/node:{class_fqn}"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.class.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.class.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "class",
        "source_refs": (source_ref,),
        "baseline": {"object": {}},
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "class",
            "class_fqn": class_fqn,
            "class_name": class_name,
            "name": class_name,
            "entity_name": class_name,
            "generated_materialization": _python_orm_runtime_targets(
                relative_path,
                owner_key=class_fqn,
            ),
        },
    }


def _class_delete_operation(
    *,
    class_fqn: str,
    class_name: str,
    relative_path: str,
    source_ref: str,
) -> dict[str, object]:
    semantic_key = f"ocg:aware_home/node:{class_fqn}"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.class.delete:{semantic_key}",
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.class.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ObjectConfigGraphNode",
        "ontology_subject_kind": "class",
        "source_refs": (source_ref,),
        "baseline": {
            "object": {
                "class_fqn": class_fqn,
                "class_name": class_name,
                "name": class_name,
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "class",
            "class_fqn": class_fqn,
            "class_name": class_name,
            "name": class_name,
            "entity_name": class_name,
            "generated_materialization": _python_orm_runtime_targets(
                relative_path,
                owner_key=class_fqn,
            ),
        },
    }


def _attribute_create_operation(
    *,
    owner_key: str,
    attribute_name: str,
    relative_path: str,
    source_ref: str,
    type_descriptor: dict[str, object] | None = None,
    is_required: bool = True,
    default_value: object | None = None,
) -> dict[str, object]:
    semantic_key = f"ocg:aware_home/node:{owner_key}/attribute:{attribute_name}"
    payload: dict[str, object] = {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.attribute.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.attribute.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": (source_ref,),
        "baseline": {"object": {}},
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "attribute",
            "owner_key": owner_key,
            "owner_semantic_key": f"ocg:aware_home/node:{owner_key}",
            "attribute_name": attribute_name,
            "attribute_signature": {
                "name": attribute_name,
                "description": f"{attribute_name} field.",
                "is_required": is_required,
                "is_public": True,
                "type_descriptor": type_descriptor
                or {
                    "kind": "primitive",
                    "primitive_base_type": "string",
                },
            },
            "generated_materialization": _python_orm_runtime_targets(
                relative_path,
                owner_key=owner_key,
            ),
        },
    }
    if default_value is not None:
        current = cast(dict[str, object], payload["current"])
        signature = cast(dict[str, object], current["attribute_signature"])
        signature["default_value"] = default_value
    return payload


def _attribute_type_update_operation(
    *,
    owner_key: str,
    attribute_name: str,
    baseline_primitive_base_type: str,
    current_primitive_base_type: str,
    relative_path: str,
    source_ref: str,
    is_required: bool | None = True,
    baseline_is_required: bool | None = None,
    current_is_required: bool | None = None,
) -> dict[str, object]:
    semantic_key = f"ocg:aware_home/node:{owner_key}/attribute:{attribute_name}"
    baseline_required = (
        is_required if baseline_is_required is None else baseline_is_required
    )
    current_required = (
        is_required if current_is_required is None else current_is_required
    )
    assert baseline_required is not None
    assert current_required is not None
    baseline_signature = _attribute_signature_payload(
        owner_key=owner_key,
        attribute_name=attribute_name,
        primitive_base_type=baseline_primitive_base_type,
        is_required=baseline_required,
    )
    current_signature = _attribute_signature_payload(
        owner_key=owner_key,
        attribute_name=attribute_name,
        primitive_base_type=current_primitive_base_type,
        is_required=current_required,
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.attribute.update:{semantic_key}:type",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.attribute.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": (source_ref,),
        "baseline": {
            "object": {
                "attribute_name": attribute_name,
                "attribute_signature": baseline_signature,
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "attribute",
            "owner_key": owner_key,
            "owner_semantic_key": f"ocg:aware_home/node:{owner_key}",
            "attribute_name": attribute_name,
            "attribute_signature": current_signature,
            "generated_materialization": _python_orm_runtime_targets(
                relative_path,
                owner_key=owner_key,
            ),
        },
    }


def _attribute_default_value_update_operation(
    *,
    owner_key: str,
    attribute_name: str,
    primitive_base_type: str,
    baseline_default_value: object,
    current_default_value: object,
    relative_path: str,
    source_ref: str,
    is_required: bool = True,
) -> dict[str, object]:
    semantic_key = f"ocg:aware_home/node:{owner_key}/attribute:{attribute_name}"
    baseline_signature = _attribute_signature_payload(
        owner_key=owner_key,
        attribute_name=attribute_name,
        primitive_base_type=primitive_base_type,
        is_required=is_required,
        default_value=baseline_default_value,
    )
    current_signature = _attribute_signature_payload(
        owner_key=owner_key,
        attribute_name=attribute_name,
        primitive_base_type=primitive_base_type,
        is_required=is_required,
        default_value=current_default_value,
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.attribute.update:{semantic_key}:default_value",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.attribute.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": (source_ref,),
        "baseline": {
            "object": {
                "attribute_name": attribute_name,
                "attribute_signature": baseline_signature,
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "attribute",
            "owner_key": owner_key,
            "owner_semantic_key": f"ocg:aware_home/node:{owner_key}",
            "attribute_name": attribute_name,
            "attribute_signature": current_signature,
            "generated_materialization": _python_orm_runtime_targets(
                relative_path,
                owner_key=owner_key,
            ),
        },
    }


def _attribute_delete_operation(
    *,
    owner_key: str,
    attribute_name: str,
    primitive_base_type: str,
    relative_path: str,
    source_ref: str,
    is_required: bool = True,
) -> dict[str, object]:
    semantic_key = f"ocg:aware_home/node:{owner_key}/attribute:{attribute_name}"
    baseline_signature = _attribute_signature_payload(
        owner_key=owner_key,
        attribute_name=attribute_name,
        primitive_base_type=primitive_base_type,
        is_required=is_required,
    )
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.attribute.delete:{semantic_key}",
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.attribute.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.AttributeConfig",
        "ontology_subject_kind": "attribute",
        "source_refs": (source_ref,),
        "baseline": {
            "object": {
                "owner_key": owner_key,
                "owner_semantic_key": f"ocg:aware_home/node:{owner_key}",
                "attribute_name": attribute_name,
                "attribute_signature": baseline_signature,
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "attribute",
            "owner_key": owner_key,
            "owner_semantic_key": f"ocg:aware_home/node:{owner_key}",
            "attribute_name": attribute_name,
            "generated_materialization": _python_orm_runtime_targets(
                relative_path,
                owner_key=owner_key,
            ),
        },
    }


def _function_create_operation(
    *,
    owner_key: str,
    function_name: str,
    is_constructor: bool,
    description: str,
    relative_path: str,
    source_ref: str,
    inputs: tuple[dict[str, object], ...],
    outputs: tuple[dict[str, object], ...],
) -> dict[str, object]:
    semantic_key = f"ocg:aware_home/node:{owner_key}/function:{function_name}"
    signature = {
        "name": function_name,
        "owner_key": owner_key,
        "description": description,
        "is_async": True,
        "is_constructor": is_constructor,
        "inputs": inputs,
        "outputs": outputs,
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.function.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.function.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.FunctionConfig",
        "ontology_subject_kind": "function",
        "source_refs": (source_ref,),
        "baseline": {"object": {}},
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "function",
            "owner_key": owner_key,
            "owner_semantic_key": f"ocg:aware_home/node:{owner_key}",
            "function_name": function_name,
            "is_constructor": is_constructor,
            "function_signature": signature,
            "generated_materialization": _python_orm_runtime_targets(
                relative_path,
                owner_key=owner_key,
            ),
        },
    }


def _function_attribute_payload(
    *,
    name: str,
    position: int,
    primitive_base_type: str | None = None,
    class_fqn: str | None = None,
    enum_fqn: str | None = None,
    collection_child: dict[str, object] | None = None,
    is_required: bool = True,
    default_value: object | None = None,
) -> dict[str, object]:
    if primitive_base_type is not None:
        type_descriptor: dict[str, object] = {
            "kind": "primitive",
            "primitive_base_type": primitive_base_type,
        }
    elif enum_fqn is not None:
        type_descriptor = {
            "kind": "enum",
            "enum_fqn": enum_fqn,
        }
    elif collection_child is not None:
        type_descriptor = {
            "kind": "collection",
            "collection_kind": "list",
            "child_descriptors": (collection_child,),
        }
    else:
        assert class_fqn is not None
        type_descriptor = {
            "kind": "class",
            "class_fqn": class_fqn,
        }
    payload: dict[str, object] = {
        "name": name,
        "position": position,
        "is_required": is_required,
        "type_descriptor": type_descriptor,
    }
    if default_value is not None:
        payload["default_value"] = default_value
    return payload


def _relationship_load_policy_update_operation(
    *,
    source_class_fqn: str,
    target_class_fqn: str,
    relationship_key: str,
    baseline_forward_loading_strategy: str,
    current_forward_loading_strategy: str,
    relative_path: str,
    source_ref: str,
) -> dict[str, object]:
    semantic_key = (
        f"ocg:aware_home/node:{source_class_fqn}:relationship:{relationship_key}"
    )
    baseline_signature = {
        "relationship_key": relationship_key,
        "relationship_type": "many_to_one",
        "source_class_fqn": source_class_fqn,
        "target_class_fqn": target_class_fqn,
        "forward_loading_strategy": baseline_forward_loading_strategy,
    }
    current_signature = {
        **baseline_signature,
        "forward_loading_strategy": current_forward_loading_strategy,
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.relationship.update:{semantic_key}:load_policy",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.relationship.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ClassConfigRelationship",
        "ontology_subject_kind": "relationship",
        "source_refs": (source_ref,),
        "baseline": {
            "object": {
                "relationship_key": relationship_key,
                "relationship_signature": baseline_signature,
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "relationship",
            "relationship_key": relationship_key,
            "source_class_fqn": source_class_fqn,
            "target_class_fqn": target_class_fqn,
            "relationship_type": "many_to_one",
            "forward_loading_strategy": current_forward_loading_strategy,
            "relationship_signature": current_signature,
            "generated_materialization": _python_orm_runtime_targets(
                relative_path,
                owner_key=source_class_fqn,
            ),
        },
    }


def _relationship_create_operation(
    *,
    source_class_fqn: str,
    target_class_fqn: str,
    relationship_key: str,
    forward_loading_strategy: str,
    relative_path: str,
    source_ref: str,
) -> dict[str, object]:
    semantic_key = (
        f"ocg:aware_home/node:{source_class_fqn}:relationship:{relationship_key}"
    )
    current_signature = {
        "relationship_key": relationship_key,
        "relationship_type": "many_to_one",
        "source_class_fqn": source_class_fqn,
        "target_class_fqn": target_class_fqn,
        "forward_loading_strategy": forward_loading_strategy,
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.relationship.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.relationship.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ClassConfigRelationship",
        "ontology_subject_kind": "relationship",
        "source_refs": (source_ref,),
        "baseline": {"object": {}},
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "relationship",
            "relationship_key": relationship_key,
            "source_class_fqn": source_class_fqn,
            "target_class_fqn": target_class_fqn,
            "relationship_type": "many_to_one",
            "forward_loading_strategy": forward_loading_strategy,
            "relationship_signature": current_signature,
            "generated_materialization": _python_orm_runtime_targets(
                relative_path,
                owner_key=source_class_fqn,
            ),
        },
    }


def _relationship_delete_operation(
    *,
    source_class_fqn: str,
    target_class_fqn: str,
    relationship_key: str,
    forward_loading_strategy: str,
    relative_path: str,
    source_ref: str,
) -> dict[str, object]:
    semantic_key = (
        f"ocg:aware_home/node:{source_class_fqn}:relationship:{relationship_key}"
    )
    baseline_signature = {
        "relationship_key": relationship_key,
        "relationship_type": "many_to_one",
        "source_class_fqn": source_class_fqn,
        "target_class_fqn": target_class_fqn,
        "forward_loading_strategy": forward_loading_strategy,
    }
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.relationship.delete:{semantic_key}",
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.relationship.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.ClassConfigRelationship",
        "ontology_subject_kind": "relationship",
        "source_refs": (source_ref,),
        "baseline": {
            "object": {
                "relationship_key": relationship_key,
                "relationship_signature": baseline_signature,
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "relationship",
            "relationship_key": relationship_key,
            "source_class_fqn": source_class_fqn,
            "target_class_fqn": target_class_fqn,
            "relationship_type": "many_to_one",
            "relationship_signature": baseline_signature,
            "generated_materialization": _python_orm_runtime_targets(
                relative_path,
                owner_key=source_class_fqn,
            ),
        },
    }


def _enum_option_create_operation(
    *,
    enum_fqn: str,
    enum_name: str,
    option_value: str,
    current_position: int,
    relative_path: str,
    source_ref: str,
) -> dict[str, object]:
    semantic_key = f"ocg:aware_home/node:{enum_fqn}/option:{option_value}"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.enum_option.create:{semantic_key}",
        "operation_family": "create",
        "provider_operation_type": "meta_ocg.enum_option.create",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumOption",
        "ontology_subject_kind": "enum_option",
        "source_refs": (source_ref,),
        "baseline": {"object": {}},
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "enum_option",
            "enum_fqn": enum_fqn,
            "enum_name": enum_name,
            "value": option_value,
            "position": current_position,
            "generated_materialization": _python_orm_runtime_targets(
                relative_path,
                owner_key=enum_fqn,
            ),
        },
    }


def _enum_option_delete_operation(
    *,
    enum_fqn: str,
    enum_name: str,
    option_value: str,
    baseline_position: int,
    relative_path: str,
    source_ref: str,
) -> dict[str, object]:
    semantic_key = f"ocg:aware_home/node:{enum_fqn}/option:{option_value}"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.enum_option.delete:{semantic_key}",
        "operation_family": "delete",
        "provider_operation_type": "meta_ocg.enum_option.delete",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumOption",
        "ontology_subject_kind": "enum_option",
        "source_refs": (source_ref,),
        "baseline": {
            "object": {
                "enum_fqn": enum_fqn,
                "enum_name": enum_name,
                "value": option_value,
                "position": baseline_position,
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "enum_option",
            "enum_fqn": enum_fqn,
            "enum_name": enum_name,
            "value": option_value,
            "generated_materialization": _python_orm_runtime_targets(
                relative_path,
                owner_key=enum_fqn,
            ),
        },
    }


def _enum_option_position_update_operation(
    *,
    enum_fqn: str,
    enum_name: str,
    option_value: str,
    baseline_position: int,
    current_position: int,
    relative_path: str,
    source_ref: str,
) -> dict[str, object]:
    semantic_key = f"ocg:aware_home/node:{enum_fqn}/option:{option_value}"
    return {
        "operation_kind": "meta_ocg_provider_delta_typed_operation",
        "operation_key": f"meta_ocg.enum_option.update:{semantic_key}:position",
        "operation_family": "update",
        "provider_operation_type": "meta_ocg.enum_option.update",
        "semantic_key": semantic_key,
        "semantic_subject_type": "aware_meta.EnumOption",
        "ontology_subject_kind": "enum_option",
        "source_refs": (source_ref,),
        "baseline": {
            "object": {
                "enum_fqn": enum_fqn,
                "enum_name": enum_name,
                "value": option_value,
                "position": baseline_position,
            },
        },
        "current": {
            "semantic_key": semantic_key,
            "object_kind": "enum_option",
            "enum_fqn": enum_fqn,
            "enum_name": enum_name,
            "value": option_value,
            "position": current_position,
            "generated_materialization": _python_orm_runtime_targets(
                relative_path,
                owner_key=enum_fqn,
            ),
        },
    }


def _attribute_signature_payload(
    *,
    owner_key: str,
    attribute_name: str,
    primitive_base_type: str,
    is_required: bool,
    default_value: object | None = None,
) -> dict[str, object]:
    signature: dict[str, object] = {
        "owner_key": owner_key,
        "name": attribute_name,
        "description": f"{attribute_name} field.",
        "is_required": is_required,
        "is_public": True,
        "type_descriptor": {
            "kind": "primitive",
            "primitive_base_type": primitive_base_type,
        },
    }
    if default_value is not None:
        signature["default_value"] = default_value
    return signature


def _python_orm_runtime_targets(
    relative_path: str,
    **target_payload: object,
) -> dict[str, object]:
    target: dict[str, object] = {
        **ORM_RUNTIME_TARGET_PROFILE.target_metadata(),
        "relative_path": relative_path,
    }
    target.update(target_payload)
    return {
        "targets": {
            ORM_RUNTIME_TARGET_PROFILE.target_key: target,
        },
    }


def _typed_operation(payload: dict[str, object]) -> MetaProviderDeltaTypedOperation:
    operation = MetaProviderDeltaTypedOperation.from_payload(payload)
    assert operation is not None
    return operation


def _apply_package_delta_to_generated_package(
    *,
    package_root: Path,
    sources_root: str,
    package_delta: CodePackageDelta,
) -> None:
    for path_delta in package_delta.paths:
        target_path = package_root / sources_root / path_delta.relative_path
        if path_delta.kind is CodePackageDeltaKind.delete:
            if target_path.exists():
                target_path.unlink()
            continue
        assert path_delta.content_text is not None
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(path_delta.content_text, encoding="utf-8")


def _operation_owner_key(operation: MetaProviderDeltaTypedOperation) -> str:
    value = (
        operation.current.get("class_fqn")
        or operation.current.get("owner_key")
        or operation.current.get("enum_fqn")
        or operation.current.get("source_class_fqn")
    )
    assert isinstance(value, str)
    return value


def _class_fqn(operation: MetaProviderDeltaTypedOperation) -> str:
    value = operation.current.get("class_fqn")
    assert isinstance(value, str)
    return value


def _operation_relative_path(operation: MetaProviderDeltaTypedOperation) -> str:
    generated_materialization = operation.current.get("generated_materialization")
    assert isinstance(generated_materialization, dict)
    targets = generated_materialization.get("targets")
    assert isinstance(targets, dict)
    target = targets.get(ORM_RUNTIME_TARGET_PROFILE.target_key)
    assert isinstance(target, dict)
    relative_path = target.get("relative_path")
    assert isinstance(relative_path, str)
    return relative_path
