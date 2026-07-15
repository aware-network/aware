from __future__ import annotations

import pytest

from aware_interface.manifest import (
    AwareAppSourceError,
    load_aware_app_source_spec_from_text,
)


def test_app_aware_source_loader_lowers_screens_to_experience_layout_tokens() -> None:
    apps = load_aware_app_source_spec_from_text(
        source_text="""\
app aware_home {
    title "Aware Home"
    description "Control-first Home app."

    screen control {
        projection aware_control_identity layout personal
    }

    screen home {
        projection home_story layout configuration_map
    }
}
""",
        source_path="app.aware",
    )

    assert len(apps) == 1
    app = apps[0]
    assert app.name == "aware_home"
    assert app.title == "Aware Home"
    assert app.description == "Control-first Home app."
    assert [screen.screen_key for screen in app.screens] == ["control", "home"]
    assert app.screens[0].projection_experience == "aware_control_identity"
    assert app.screens[0].projection_experience_layout == "personal"
    assert app.screens[1].projection_experience == "home_story"
    assert app.screens[1].projection_experience_layout == "configuration_map"


def test_app_aware_source_loader_rejects_duplicate_screen_keys() -> None:
    with pytest.raises(AwareAppSourceError, match="duplicates screen 'home'"):
        load_aware_app_source_spec_from_text(
            source_text="""\
app aware_home {
    screen home {
        projection home_story layout configuration_map
    }

    screen home {
        projection home_story layout configuration_map
    }
}
""",
            source_path="app.aware",
        )


def test_app_aware_source_loader_requires_one_projection_layout_per_screen() -> None:
    with pytest.raises(AwareAppSourceError, match="must declare exactly one"):
        load_aware_app_source_spec_from_text(
            source_text="""\
app aware_home {
    screen home {
    }
}
""",
            source_path="app.aware",
        )
