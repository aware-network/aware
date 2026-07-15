from __future__ import annotations

from pathlib import Path

from aware_experience.compiler.workspace import ExperienceWorkspace
from aware_experience.language_contracts import (
    materialize_experience_language_contracts,
)
from aware_experience.projection.compiler import (
    load_projection_experience_ownership_from_sources,
)


def test_materialize_experience_language_contracts_skips_api_view_mounts(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "aware.environment.toml").write_text("aware = 1\n", encoding="utf-8")
    (root / "aware.experience.toml").write_text(
        "\n".join(
            [
                "aware_experience = 1",
                "",
                "[experience]",
                'package_name = "aware-conversations"',
                'fqn_prefix = "aware_conversations"',
                "",
                "[build]",
                'environment_handle = "kernel"',
                'sources_dir = "."',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "force_fresh_scan = true",
                "",
                "[targets.dart]",
                'root_dir = "languages/dart"',
                'package_dir = "aware_conversations"',
                "",
                "[targets.python]",
                'root_dir = "languages/python"',
                'package_dir = "aware_conversations"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience aware_conversations on aware_conversation.conversation.Conversation {",
                "  observable chat {",
                "    view home.v1 default api_view conversation.home {}",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    view_path = root / "views" / "chat" / "home" / "v1.aware"
    view_path.parent.mkdir(parents=True)
    view_path.write_text(
        "\n".join(
            [
                "class ConversationChatMessageV1 : inline_value {",
                "  message_id UUID?",
                '  text String = "Message"',
                "  position Int?",
                "}",
                "",
                "class ConversationChatViewStateV1 : inline_value {",
                '  title String = "Conversation"',
                "  conversation_id UUID?",
                "  messages ConversationChatMessageV1[] = []",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    snapshot = ExperienceWorkspace.from_toml(
        toml_path=root / "aware.experience.toml"
    ).build_snapshot()
    result = materialize_experience_language_contracts(snapshot=snapshot)

    assert result.packages == ()
    assert not (root / "languages").exists()


def test_projection_experience_surface_accepts_dotted_view_key(tmp_path: Path) -> None:
    root = tmp_path
    (root / "experiences.aware").write_text(
        "\n".join(
            [
                "experience aware_conversations on aware_conversation.conversation.Conversation {",
                "  observable chat {",
                "    view home.v1 default api_view conversation.home {}",
                "  }",
                "  surface conversations.now {",
                "    section primary;",
                "    view chat.home.v1;",
                "    graph now;",
                "  }",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    ownership = load_projection_experience_ownership_from_sources(
        package_root=root,
        source_files=(Path("experiences.aware"),),
    )

    assert ownership[0].observables[0].views[0].key == "home.v1"
    assert ownership[0].section_surfaces[0].view_key == "home.v1"
