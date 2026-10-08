"""Typed software prompt-composition helpers for workspace bootstrap."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

_TOKEN_PATTERN = re.compile(r"\{([a-zA-Z0-9_]+)\}")
_ASSET_URI_PREFIX = "asset://"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SoftwarePromptProfile(_StrictModel):
    profile_id: str
    template_id: str
    strict_unresolved: bool = False
    replacements: dict[str, str] = Field(default_factory=dict)


class SoftwareComposedFile(_StrictModel):
    name: str
    template_text: str
    rendered_text: str
    unresolved_tokens: list[str] = Field(default_factory=list)


class SoftwarePromptComposeResult(_StrictModel):
    template_id: str
    profile_id: str
    strict_unresolved: bool = False
    files: list[SoftwareComposedFile] = Field(default_factory=list)
    unresolved_tokens: list[str] = Field(default_factory=list)
    unresolved_by_file: dict[str, list[str]] = Field(default_factory=dict)


def load_software_template_files(*, template_root: Path) -> dict[str, str]:
    template_files = sorted(
        path for path in template_root.glob("*.md") if path.is_file()
    )
    if not template_files:
        raise FileNotFoundError(
            f"No software template files found under: {template_root.as_posix()}"
        )
    return {path.name: path.read_text(encoding="utf-8") for path in template_files}


def load_software_prompt_profile(
    *,
    profile_path: Path,
    profile_id: str,
    assets_root: Path | None = None,
) -> SoftwarePromptProfile:
    raw = tomllib.loads(profile_path.read_text(encoding="utf-8"))
    template_id = str(raw.get("template_id", "")).strip()
    if not template_id:
        raise ValueError(
            f"Software profile {profile_id!r} is missing template_id: "
            f"{profile_path.as_posix()}"
        )
    replacements_raw = raw.get("replacements", {})
    if replacements_raw is None:
        replacements_raw = {}
    if not isinstance(replacements_raw, dict):
        raise ValueError(
            f"Software profile replacements must be a table: {profile_path.as_posix()}"
        )
    replacements: dict[str, str] = {}
    for key, value in replacements_raw.items():
        token = str(key).strip()
        if not token:
            continue
        replacement_value = str(value)
        if replacement_value.startswith(_ASSET_URI_PREFIX):
            replacement_value = _load_profile_asset_value(
                profile_path=profile_path,
                assets_root=assets_root,
                asset_uri=replacement_value,
            )
        replacements[token] = replacement_value

    return SoftwarePromptProfile(
        profile_id=profile_id,
        template_id=template_id,
        strict_unresolved=bool(raw.get("strict_unresolved", False)),
        replacements=replacements,
    )


def _load_profile_asset_value(
    *,
    profile_path: Path,
    assets_root: Path | None,
    asset_uri: str,
) -> str:
    if assets_root is None:
        raise ValueError(
            "Software profile uses asset replacement but no assets_root was provided: "
            f"{profile_path.as_posix()}"
        )
    relative = asset_uri[len(_ASSET_URI_PREFIX) :].strip()
    if not relative:
        raise ValueError(
            "Software profile asset replacement must include a relative path: "
            f"{profile_path.as_posix()}"
        )
    normalized_assets_root = assets_root.resolve()
    asset_path = (normalized_assets_root / relative).resolve()
    try:
        asset_path.relative_to(normalized_assets_root)
    except Exception as exc:
        raise ValueError(
            "Software profile asset replacement escapes assets root: "
            f"{asset_uri!r} ({profile_path.as_posix()})"
        ) from exc
    if not asset_path.exists() or not asset_path.is_file():
        raise FileNotFoundError(
            "Software profile asset replacement not found: "
            f"{asset_path.as_posix()} ({profile_path.as_posix()})"
        )
    return asset_path.read_text(encoding="utf-8")


def compose_software_templates(
    *,
    template_id: str,
    profile: SoftwarePromptProfile,
    template_files: dict[str, str],
) -> SoftwarePromptComposeResult:
    expected_template_id = str(template_id).strip()
    profile_template_id = str(profile.template_id).strip()
    if expected_template_id != profile_template_id:
        raise ValueError(
            "Software profile/template mismatch: "
            f"template_id={expected_template_id!r} "
            f"profile.template_id={profile_template_id!r}"
        )

    files: list[SoftwareComposedFile] = []
    unresolved_by_file: dict[str, list[str]] = {}
    unresolved_all: set[str] = set()

    for filename in sorted(template_files.keys()):
        template_text = str(template_files[filename])
        unresolved_tokens_for_file: set[str] = set()

        def _replace(match: re.Match[str]) -> str:
            token = match.group(1)
            replacement = profile.replacements.get(token)
            if replacement is None:
                unresolved_tokens_for_file.add(token)
                return match.group(0)
            return replacement

        rendered_text = _TOKEN_PATTERN.sub(_replace, template_text)
        unresolved_list = sorted(unresolved_tokens_for_file)
        unresolved_all.update(unresolved_tokens_for_file)
        unresolved_by_file[filename] = unresolved_list
        files.append(
            SoftwareComposedFile(
                name=filename,
                template_text=template_text,
                rendered_text=rendered_text,
                unresolved_tokens=unresolved_list,
            )
        )

    unresolved_tokens = sorted(unresolved_all)
    if profile.strict_unresolved and unresolved_tokens:
        unresolved_text = ", ".join(unresolved_tokens)
        raise ValueError(
            "Software prompt composition failed due to unresolved template tokens: "
            f"{unresolved_text}"
        )

    return SoftwarePromptComposeResult(
        template_id=expected_template_id,
        profile_id=profile.profile_id,
        strict_unresolved=profile.strict_unresolved,
        files=files,
        unresolved_tokens=unresolved_tokens,
        unresolved_by_file=unresolved_by_file,
    )


__all__ = [
    "SoftwareComposedFile",
    "SoftwarePromptComposeResult",
    "SoftwarePromptProfile",
    "compose_software_templates",
    "load_software_prompt_profile",
    "load_software_template_files",
]
