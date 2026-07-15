from __future__ import annotations

from pathlib import Path

from aware_experience.view_contracts import load_view_state_model_contracts_from_sources


def test_load_view_state_model_contracts_from_sources_builds_view_fqns(
    tmp_path: Path,
) -> None:
    view_path = tmp_path / "views" / "identity_admission.aware"
    view_path.parent.mkdir(parents=True)
    view_path.write_text(
        "\n".join(
            [
                "class IdentityAdmissionViewState : inline_value {",
                "  admitted Bool = false",
                "  display_name String?",
                "}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    contracts = load_view_state_model_contracts_from_sources(
        package_root=tmp_path,
        source_files=(Path("views/identity_admission.aware"),),
        fqn_prefix="aware_control",
        package_name="aware-control",
    )

    assert len(contracts) == 1
    contract = contracts[0]
    assert (
        contract.state_model_ref
        == "aware_control.views.identity_admission.IdentityAdmissionViewState"
    )
    assert contract.source_path == "views/identity_admission.aware"
