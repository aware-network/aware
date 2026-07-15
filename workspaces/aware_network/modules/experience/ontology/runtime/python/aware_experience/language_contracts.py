from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
import shutil
from typing import Any

from aware_experience.compiler.workspace import ExperienceWorkspaceSnapshot
from aware_experience.projection.compiler import (
    load_projection_experience_ownership_from_sources,
)
from aware_experience.view_contracts import (
    ExperienceViewStateModelContract,
    load_view_state_model_contracts_from_sources,
)
from aware_experience.manifest.spec import AwareExperienceTomlLanguageTargetSpec
from aware_meta_ontology.attribute.attribute_type_descriptor import (
    AttributeTypeDescriptor,
)


SUPPORTED_LANGUAGE_CONTRACT_TARGETS = ("dart", "python")


@dataclass(frozen=True, slots=True)
class ExperienceLanguageContractPackage:
    language: str
    package_name: str
    import_root: str
    package_root: Path
    relpath: str
    manifest_relative_path: str
    sources_root_relpath: str
    materialized_package_paths: tuple[str, ...]
    file_count: int
    contract_count: int


@dataclass(frozen=True, slots=True)
class ExperienceLanguageContractMaterializationResult:
    packages: tuple[ExperienceLanguageContractPackage, ...]


@dataclass(frozen=True, slots=True)
class _ViewBinding:
    experience_name: str
    observable_key: str
    view_key: str
    view_ref: str
    projection_view_key: str
    version: str
    is_default: bool
    state_model_ref: str
    state_provider_ref: str | None


@dataclass(frozen=True, slots=True)
class _ViewContract:
    model: ExperienceViewStateModelContract
    binding: _ViewBinding
    attributes: tuple["_ViewAttribute", ...]
    models: tuple["_ViewContractModel", ...]


@dataclass(frozen=True, slots=True)
class _ViewContractModel:
    model: ExperienceViewStateModelContract
    attributes: tuple["_ViewAttribute", ...]


@dataclass(frozen=True, slots=True)
class _ViewAttribute:
    wire_name: str
    dart_name: str
    python_name: str
    dart_type: str
    python_type: str
    default_value: Any
    has_default: bool
    is_nullable: bool


class _MissingDefault:
    pass


_MISSING = _MissingDefault()


def materialize_experience_language_contracts(
    *,
    snapshot: ExperienceWorkspaceSnapshot,
    languages: tuple[str, ...] | None = None,
) -> ExperienceLanguageContractMaterializationResult:
    requested_languages = _normalize_languages(
        languages=languages, spec_targets=frozenset(snapshot.spec.targets)
    )
    contracts = _load_bound_view_contracts(snapshot=snapshot)
    if not contracts:
        return ExperienceLanguageContractMaterializationResult(packages=())
    packages: list[ExperienceLanguageContractPackage] = []
    for language in requested_languages:
        target = _target_for_language(snapshot=snapshot, language=language)
        package_root = (
            snapshot.package_root / target.root_dir / target.package_dir
        ).resolve()
        _assert_within(
            base=snapshot.package_root,
            candidate=package_root,
            label=f"[targets.{language}]",
        )
        if language == "dart":
            packages.append(
                _materialize_dart_package(
                    snapshot=snapshot,
                    target=target,
                    package_root=package_root,
                    contracts=contracts,
                )
            )
            continue
        if language == "python":
            packages.append(
                _materialize_python_package(
                    snapshot=snapshot,
                    target=target,
                    package_root=package_root,
                    contracts=contracts,
                )
            )
            continue
        raise ValueError(
            f"Unsupported experience language contract target: {language!r}"
        )
    return ExperienceLanguageContractMaterializationResult(packages=tuple(packages))


def _normalize_languages(
    *, languages: tuple[str, ...] | None, spec_targets: frozenset[str]
) -> tuple[str, ...]:
    if languages is None:
        languages = (
            tuple(sorted(spec_targets))
            if spec_targets
            else SUPPORTED_LANGUAGE_CONTRACT_TARGETS
        )
    normalized: list[str] = []
    for item in languages:
        language = (item or "").strip().casefold()
        if language == "all":
            normalized.extend(SUPPORTED_LANGUAGE_CONTRACT_TARGETS)
            continue
        if language not in SUPPORTED_LANGUAGE_CONTRACT_TARGETS:
            raise ValueError(
                f"Unsupported experience language contract target: {item!r}"
            )
        normalized.append(language)
    return tuple(dict.fromkeys(normalized))


def _target_for_language(
    *,
    snapshot: ExperienceWorkspaceSnapshot,
    language: str,
) -> AwareExperienceTomlLanguageTargetSpec:
    target = snapshot.spec.targets.get(language)
    if target is not None:
        return target
    return AwareExperienceTomlLanguageTargetSpec(
        language=language,
        root_dir=f"languages/{language}",
        package_dir=snapshot.spec.experience.fqn_prefix,
    )


def _load_bound_view_contracts(
    *, snapshot: ExperienceWorkspaceSnapshot
) -> tuple[_ViewContract, ...]:
    model_contracts = load_view_state_model_contracts_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
        fqn_prefix=(snapshot.spec.experience.fqn_prefix or "").strip(),
        package_name=(snapshot.spec.experience.package_name or "").strip(),
    )
    models_by_ref = {model.state_model_ref: model for model in model_contracts}
    models_by_class_config_id = {
        str(model.class_config_id): model for model in model_contracts
    }
    bindings_by_state_model_ref = _load_view_bindings_by_state_model_ref(
        snapshot=snapshot
    )
    bound: list[_ViewContract] = []
    for binding in bindings_by_state_model_ref.values():
        model = models_by_ref.get(binding.state_model_ref)
        if model is None:
            raise ValueError(
                "Experience view-state model "
                f"{binding.state_model_ref!r} has no matching view contract source in {snapshot.spec_path}"
            )
        contract_models = _contract_models_for_root(
            root_model=model,
            models_by_class_config_id=models_by_class_config_id,
        )
        bound.append(
            _ViewContract(
                model=model,
                binding=binding,
                attributes=_attributes_for_model(
                    model=model,
                    models_by_class_config_id=models_by_class_config_id,
                ),
                models=contract_models,
            )
        )
    return tuple(sorted(bound, key=lambda item: item.binding.view_ref.casefold()))


def _contract_models_for_root(
    *,
    root_model: ExperienceViewStateModelContract,
    models_by_class_config_id: dict[str, ExperienceViewStateModelContract],
) -> tuple[_ViewContractModel, ...]:
    ordered: list[ExperienceViewStateModelContract] = []
    seen: set[str] = set()
    visiting: set[str] = set()

    def visit(model: ExperienceViewStateModelContract) -> None:
        model_key = str(model.class_config_id)
        if model_key in seen:
            return
        if model_key in visiting:
            return
        visiting.add(model_key)
        for dependency_id in _model_dependency_class_config_ids(model=model):
            dependency = models_by_class_config_id.get(dependency_id)
            if dependency is not None:
                visit(dependency)
        visiting.remove(model_key)
        seen.add(model_key)
        ordered.append(model)

    visit(root_model)
    return tuple(
        _ViewContractModel(
            model=model,
            attributes=_attributes_for_model(
                model=model,
                models_by_class_config_id=models_by_class_config_id,
            ),
        )
        for model in ordered
    )


def _model_dependency_class_config_ids(
    *, model: ExperienceViewStateModelContract
) -> tuple[str, ...]:
    dependency_ids: list[str] = []
    for edge in getattr(model.class_config, "class_config_attribute_configs", ()) or ():
        attribute_config = getattr(edge, "attribute_config", None)
        if attribute_config is None:
            continue
        dependency_ids.extend(
            _descriptor_class_config_ids(attribute_config.type_descriptor)
        )
    return tuple(dict.fromkeys(dependency_ids))


def _descriptor_class_config_ids(
    descriptor: AttributeTypeDescriptor | None,
) -> tuple[str, ...]:
    if descriptor is None:
        return ()
    out: list[str] = []
    if _enum_value(getattr(descriptor, "kind", "")) == "class":
        class_config_id = _descriptor_class_config_id(descriptor)
        if class_config_id is not None:
            out.append(class_config_id)
    for link in getattr(descriptor, "child_links", ()) or ():
        child = getattr(link, "child", None)
        out.extend(_descriptor_class_config_ids(child))
    return tuple(dict.fromkeys(out))


def _descriptor_class_config_id(descriptor: AttributeTypeDescriptor) -> str | None:
    class_config_id = getattr(descriptor, "class_config_id", None)
    if class_config_id is not None:
        return str(class_config_id)
    class_config = getattr(descriptor, "class_config", None)
    if class_config is None:
        return None
    raw_id = getattr(class_config, "id", None)
    return str(raw_id) if raw_id is not None else None


def _load_view_bindings_by_state_model_ref(
    *,
    snapshot: ExperienceWorkspaceSnapshot,
) -> dict[str, _ViewBinding]:
    experiences = load_projection_experience_ownership_from_sources(
        package_root=snapshot.package_root,
        source_files=snapshot.source_files,
    )
    bindings: dict[str, _ViewBinding] = {}
    for experience in experiences:
        for observable in experience.observables:
            for view in observable.views:
                if view.api_view_ref is not None:
                    continue
                if view.state_model_ref is None:
                    raise ValueError(
                        "Experience language contract view must declare state_model_ref "
                        + (
                            f"(experience={experience.name!r}, observable={observable.key!r}, "
                            f"view={view.key!r})"
                        )
                    )
                projection_view_key = f"{observable.key}.{view.key}"
                binding = _ViewBinding(
                    experience_name=experience.name,
                    observable_key=observable.key,
                    view_key=view.key,
                    view_ref=f"{experience.name}.{projection_view_key}",
                    projection_view_key=projection_view_key,
                    version=_view_version(view_key=view.key),
                    is_default=view.is_default,
                    state_model_ref=view.state_model_ref,
                    state_provider_ref=view.state_provider_ref,
                )
                previous = bindings.setdefault(view.state_model_ref, binding)
                if previous is not binding:
                    raise ValueError(
                        "Experience state model "
                        f"{view.state_model_ref!r} is bound to multiple views: "
                        f"{previous.view_ref!r}, {binding.view_ref!r}"
                    )
    return bindings


def _view_version(*, view_key: str) -> str:
    tail = (view_key or "").strip().split(".")[-1]
    if re.fullmatch(r"v[0-9]+", tail):
        return tail
    if re.fullmatch(r"[0-9]+", tail):
        return f"v{tail}"
    return "unversioned"


def _attributes_for_model(
    *,
    model: ExperienceViewStateModelContract,
    models_by_class_config_id: dict[str, ExperienceViewStateModelContract],
) -> tuple[_ViewAttribute, ...]:
    rows: list[_ViewAttribute] = []
    for edge in sorted(
        model.class_config.class_config_attribute_configs,
        key=lambda item: (int(getattr(item, "position", 0) or 0), str(item.id)),
    ):
        attribute_config = edge.attribute_config
        if attribute_config is None:
            continue
        type_info = _type_info(
            attribute_config.type_descriptor,
            models_by_class_config_id=models_by_class_config_id,
        )
        default_value, has_default = _parse_default(attribute_config.default_value)
        rows.append(
            _ViewAttribute(
                wire_name=attribute_config.name,
                dart_name=_snake_to_camel(attribute_config.name),
                python_name=attribute_config.name,
                dart_type=type_info["dart_type"],
                python_type=type_info["python_type"],
                default_value=default_value,
                has_default=has_default,
                is_nullable=type_info["is_nullable"],
            )
        )
    return tuple(rows)


def _type_info(
    descriptor: AttributeTypeDescriptor,
    *,
    models_by_class_config_id: dict[str, ExperienceViewStateModelContract],
) -> dict[str, Any]:
    kind = _enum_value(getattr(descriptor, "kind", ""))
    collection_kind = _enum_value(getattr(descriptor, "collection_kind", "single"))
    if kind == "collection" or collection_kind == "list":
        element = _collection_element_descriptor(descriptor)
        if element is None:
            return {
                "dart_type": "List<dynamic>",
                "python_type": "list[Any]",
                "is_nullable": False,
            }
        element_info = _type_info(
            element,
            models_by_class_config_id=models_by_class_config_id,
        )
        return {
            "dart_type": f"List<{_dart_non_nullable_type(str(element_info['dart_type']))}>",
            "python_type": f"list[{_python_non_nullable_type(str(element_info['python_type']))}]",
            "is_nullable": False,
        }
    if kind == "union":
        children = [
            link.child for link in getattr(descriptor, "child_links", ()) if link.child
        ]
        non_null_children = [
            child for child in children if _primitive_kind(child) != "null"
        ]
        if not non_null_children:
            mapped: dict[str, Any] = {
                "dart_type": "dynamic",
                "python_type": "Any",
                "is_nullable": True,
            }
        else:
            mapped = dict(
                _type_info(
                    non_null_children[0],
                    models_by_class_config_id=models_by_class_config_id,
                )
            )
        mapped["is_nullable"] = True
        dart_type = str(mapped["dart_type"])
        python_type = str(mapped["python_type"])
        if not dart_type.endswith("?"):
            mapped["dart_type"] = f"{dart_type}?"
        if "| None" not in python_type:
            mapped["python_type"] = f"{python_type} | None"
        return mapped
    if kind == "class":
        model = models_by_class_config_id.get(
            _descriptor_class_config_id(descriptor) or ""
        )
        if model is not None:
            return {
                "dart_type": model.class_config.name,
                "python_type": model.class_config.name,
                "is_nullable": False,
            }
    return _primitive_type_info(_primitive_kind(descriptor))


def _collection_element_descriptor(
    descriptor: AttributeTypeDescriptor,
) -> AttributeTypeDescriptor | None:
    for link in getattr(descriptor, "child_links", ()) or ():
        child = getattr(link, "child", None)
        if child is not None:
            return child
    return None


def _primitive_kind(descriptor: AttributeTypeDescriptor) -> str:
    primitive_config = getattr(descriptor, "primitive_config", None)
    primitive_type = getattr(primitive_config, "primitive_type", None)
    base_type = _enum_value(getattr(primitive_type, "base_type", ""))
    constraints = getattr(primitive_type, "constraints", None)
    if (
        base_type == "json"
        and isinstance(constraints, dict)
        and constraints.get("json_kind") == "object"
    ):
        return "json_object"
    if base_type:
        return base_type
    kind = _enum_value(getattr(descriptor, "kind", ""))
    return kind or "any"


def _primitive_type_info(kind: str) -> dict[str, Any]:
    if kind == "string":
        return {"dart_type": "String", "python_type": "str", "is_nullable": False}
    if kind == "uuid":
        return {"dart_type": "String", "python_type": "str", "is_nullable": False}
    if kind == "bool":
        return {"dart_type": "bool", "python_type": "bool", "is_nullable": False}
    if kind in {"int", "integer"}:
        return {"dart_type": "int", "python_type": "int", "is_nullable": False}
    if kind in {"float", "number"}:
        return {"dart_type": "double", "python_type": "float", "is_nullable": False}
    if kind == "json_object":
        return {
            "dart_type": "Map<String, dynamic>",
            "python_type": "dict[str, Any]",
            "is_nullable": False,
        }
    if kind == "null":
        return {"dart_type": "dynamic", "python_type": "Any", "is_nullable": True}
    return {"dart_type": "dynamic", "python_type": "Any", "is_nullable": False}


def _dart_non_nullable_type(value: str) -> str:
    return value.removesuffix("?")


def _python_non_nullable_type(value: str) -> str:
    return value.replace(" | None", "").replace("None | ", "")


def _enum_value(value: object) -> str:
    if hasattr(value, "value"):
        return str(getattr(value, "value"))
    return str(value or "")


def _parse_default(default_value: str | None) -> tuple[Any, bool]:
    if default_value is None:
        return _MISSING, False
    raw = default_value.strip()
    if not raw:
        return _MISSING, False
    try:
        return json.loads(raw), True
    except json.JSONDecodeError:
        if raw.startswith('"') and raw.endswith('"'):
            return raw[1:-1], True
        return raw, True


def _materialize_dart_package(
    *,
    snapshot: ExperienceWorkspaceSnapshot,
    target: AwareExperienceTomlLanguageTargetSpec,
    package_root: Path,
    contracts: tuple[_ViewContract, ...],
) -> ExperienceLanguageContractPackage:
    package_name = _package_import_root(target=target)
    lib_dir = package_root / "lib"
    _reset_generated_dir(path=lib_dir, base=snapshot.package_root)
    files: dict[Path, str] = {
        package_root
        / "pubspec.yaml": _render_dart_pubspec(
            package_name=package_name,
            description=snapshot.spec.experience.description,
        ),
        package_root / "analysis_options.yaml": _render_dart_analysis_options(),
        lib_dir
        / f"{package_name}.dart": _render_dart_library(
            package_name=package_name, contracts=contracts
        ),
        lib_dir
        / "view_model_registry.dart": _render_dart_registry(
            package_name=package_name,
            contracts=contracts,
        ),
    }
    for contract in contracts:
        files[lib_dir / _dart_contract_relpath(contract=contract)] = (
            _render_dart_contract(contract=contract)
        )
    _write_files(files=files)
    materialized_package_paths = _package_relative_file_paths(
        files=files,
        package_root=package_root,
    )
    return ExperienceLanguageContractPackage(
        language="dart",
        package_name=package_name,
        import_root=package_name,
        package_root=package_root,
        relpath=package_root.relative_to(snapshot.repo_root).as_posix(),
        manifest_relative_path=(package_root / "pubspec.yaml")
        .relative_to(snapshot.repo_root)
        .as_posix(),
        sources_root_relpath=lib_dir.relative_to(snapshot.repo_root).as_posix(),
        materialized_package_paths=materialized_package_paths,
        file_count=len(files),
        contract_count=len(contracts),
    )


def _materialize_python_package(
    *,
    snapshot: ExperienceWorkspaceSnapshot,
    target: AwareExperienceTomlLanguageTargetSpec,
    package_root: Path,
    contracts: tuple[_ViewContract, ...],
) -> ExperienceLanguageContractPackage:
    import_root = _package_import_root(target=target)
    package_dir = package_root / import_root
    _reset_generated_dir(path=package_dir, base=snapshot.package_root)
    files: dict[Path, str] = {
        package_root
        / "pyproject.toml": _render_python_pyproject(
            project_name=snapshot.spec.experience.package_name,
            import_root=import_root,
            description=snapshot.spec.experience.description,
        ),
        package_dir
        / "__init__.py": _render_python_init(
            import_root=import_root, contracts=contracts
        ),
        package_dir / "py.typed": "",
        package_dir
        / "view_model_registry.py": _render_python_registry(
            import_root=import_root,
            contracts=contracts,
        ),
    }
    for contract in contracts:
        files[package_dir / _python_contract_relpath(contract=contract)] = (
            _render_python_contract(
                contract=contract,
            )
        )
    _write_files(files=files)
    materialized_package_paths = _package_relative_file_paths(
        files=files,
        package_root=package_root,
    )
    return ExperienceLanguageContractPackage(
        language="python",
        package_name=snapshot.spec.experience.package_name,
        import_root=import_root,
        package_root=package_root,
        relpath=package_root.relative_to(snapshot.repo_root).as_posix(),
        manifest_relative_path=(package_root / "pyproject.toml")
        .relative_to(snapshot.repo_root)
        .as_posix(),
        sources_root_relpath=package_dir.relative_to(snapshot.repo_root).as_posix(),
        materialized_package_paths=materialized_package_paths,
        file_count=len(files),
        contract_count=len(contracts),
    )


def _package_relative_file_paths(
    *,
    files: dict[Path, str],
    package_root: Path,
) -> tuple[str, ...]:
    root = package_root.resolve()
    relpaths: list[str] = []
    for path in sorted(files, key=lambda item: item.as_posix()):
        relpaths.append(path.resolve().relative_to(root).as_posix())
    return tuple(relpaths)


def _render_dart_pubspec(*, package_name: str, description: str | None) -> str:
    return (
        f"name: {package_name}\n"
        f"description: {description or 'Aware experience view model contracts.'}\n"
        "version: 0.0.1\n"
        "publish_to: 'none'\n"
        "\n"
        "environment:\n"
        "  sdk: '>=3.2.0 <4.0.0'\n"
        "\n"
        "dev_dependencies:\n"
        "  lints: ^3.0.0\n"
    )


def _render_dart_analysis_options() -> str:
    return "include: package:lints/recommended.yaml\n"


def _render_dart_library(
    *, package_name: str, contracts: tuple[_ViewContract, ...]
) -> str:
    exports = [
        "export 'view_model_registry.dart';",
        *[
            f"export '{_dart_contract_relpath(contract=contract).as_posix()}';"
            for contract in contracts
        ],
    ]
    return _generated_header(language="dart") + "\n".join(exports) + "\n"


def _render_dart_registry(
    *, package_name: str, contracts: tuple[_ViewContract, ...]
) -> str:
    identifier_prefix = _snake_to_camel(package_name)
    imports = [
        f"import '{_dart_contract_relpath(contract=contract).as_posix()}';"
        for contract in contracts
    ]
    rows = []
    decoder_rows = []
    for contract in contracts:
        cls = contract.model.class_config.name
        rows.extend(
            [
                "  ExperienceViewModelContract(",
                f"    viewRef: {cls}.viewRef,",
                f"    viewKey: {cls}.viewKey,",
                f"    stateModelRef: {cls}.stateModelRef,",
                f"    version: {cls}.version,",
                f"    decode: {cls}.fromJson,",
                "  ),",
            ]
        )
        decoder_rows.append(f"  {cls}.viewRef: {cls}.fromJson,")
        decoder_rows.append(f"  {cls}.viewKey: {cls}.fromJson,")
    body = [
        _generated_header(language="dart").rstrip(),
        *imports,
        "",
        "typedef ExperienceViewModelDecoder = Object Function(Map<String, dynamic> json);",
        "",
        "class ExperienceViewModelContract {",
        "  const ExperienceViewModelContract({",
        "    required this.viewRef,",
        "    required this.viewKey,",
        "    required this.stateModelRef,",
        "    required this.version,",
        "    required this.decode,",
        "  });",
        "",
        "  final String viewRef;",
        "  final String viewKey;",
        "  final String stateModelRef;",
        "  final String version;",
        "  final ExperienceViewModelDecoder decode;",
        "}",
        "",
        f"const {identifier_prefix}ViewModelContracts = <ExperienceViewModelContract>[",
        *rows,
        "];",
        "",
        f"final {identifier_prefix}ViewModelDecoders =",
        "    <String, ExperienceViewModelDecoder>{",
        *decoder_rows,
        "};",
        "",
    ]
    return "\n".join(body)


def _render_dart_contract(*, contract: _ViewContract) -> str:
    helper_needs: set[str] = set()
    rendered_models: list[str] = []
    for contract_model in contract.models:
        helper_needs.update(
            helper
            for attr in contract_model.attributes
            for helper in _dart_helpers_for_attr(attr=attr)
        )
        rendered_models.append(
            _render_dart_contract_model(
                contract=contract,
                contract_model=contract_model,
                is_root=contract_model.model.class_config_id
                == contract.model.class_config_id,
            )
        )
    body = [_generated_header(language="dart").rstrip(), "\n\n".join(rendered_models)]
    body.extend(_render_dart_helpers(helper_needs=helper_needs))
    return "\n".join(body) + "\n"


def _render_dart_contract_model(
    *,
    contract: _ViewContract,
    contract_model: _ViewContractModel,
    is_root: bool,
) -> str:
    cls = contract_model.model.class_config.name
    constructor_rows = []
    field_rows = []
    from_json_rows = []
    to_json_rows = []
    for attr in contract_model.attributes:
        constructor_rows.append(_dart_constructor_param(attr=attr))
        field_rows.append(f"  final {attr.dart_type} {attr.dart_name};")
        from_json_rows.append(_dart_from_json_assignment(attr=attr))
        to_json_rows.append(_dart_to_json_assignment(attr=attr))
    body = [
        f"class {cls} {{",
        f"  const {cls}({{",
        *constructor_rows,
        "  });",
    ]
    if is_root:
        body.extend(
            [
                "",
                f"  static const String viewRef = '{contract.binding.view_ref}';",
                f"  static const String viewKey = '{contract.binding.projection_view_key}';",
                "  static const String stateModelRef =",
                f"      '{contract.model.state_model_ref}';",
                f"  static const String version = '{contract.binding.version}';",
                "",
            ]
        )
    else:
        body.append("")
    body.extend(
        [
            f"  factory {cls}.fromJson(Map<String, dynamic> json) {{",
            f"    return {cls}(",
            *from_json_rows,
            "    );",
            "  }",
            "",
            "  Map<String, dynamic> toJson() {",
            "    return <String, dynamic>{",
            *to_json_rows,
            "    };",
            "  }",
            "",
            *field_rows,
            "}",
        ]
    )
    return "\n".join(body)


def _dart_constructor_param(*, attr: _ViewAttribute) -> str:
    if attr.has_default:
        return f"    this.{attr.dart_name} = {_dart_literal(attr.default_value, dart_type=attr.dart_type)},"
    if attr.is_nullable:
        return f"    this.{attr.dart_name},"
    return f"    required this.{attr.dart_name},"


def _dart_from_json_assignment(*, attr: _ViewAttribute) -> str:
    value_expr = _dart_decode_expr(attr=attr, source=f"json['{attr.wire_name}']")
    if attr.has_default:
        if _dart_decode_expr_is_nullable(attr=attr):
            value_expr = f"{value_expr} ?? {_dart_literal(attr.default_value, dart_type=attr.dart_type)}"
    elif not attr.is_nullable:
        value_expr = f"{value_expr} ?? _missingRequiredField<{attr.dart_type}>('{attr.wire_name}')"
    if len(f"      {attr.dart_name}: {value_expr},") > 100 and " ?? " in value_expr:
        head, fallback = value_expr.split(" ?? ", 1)
        return f"      {attr.dart_name}: {head} ??\n          {fallback},"
    return f"      {attr.dart_name}: {value_expr},"


def _dart_decode_expr(*, attr: _ViewAttribute, source: str) -> str:
    base = attr.dart_type.removesuffix("?")
    if base == "String":
        return f"_stringValue({source})"
    if base == "bool":
        return f"_boolValue({source})"
    if base == "int":
        return f"_intValue({source})"
    if base == "double":
        return f"_doubleValue({source})"
    if base == "List<Map<String, dynamic>>":
        return f"_jsonObjectList({source})"
    if base == "Map<String, dynamic>":
        return f"_jsonObject({source})"
    if _dart_model_list_inner(base) is not None:
        inner = _dart_model_list_inner(base)
        return f"_modelList({source}, {inner}.fromJson)"
    if _is_dart_model_type(base):
        return f"_modelValue({source}, {base}.fromJson)"
    return source


def _dart_to_json_assignment(*, attr: _ViewAttribute) -> str:
    base = attr.dart_type.removesuffix("?")
    inner = _dart_model_list_inner(base)
    if inner is not None:
        return (
            f"      '{attr.wire_name}': "
            f"{attr.dart_name}.map((item) => item.toJson()).toList(growable: false),"
        )
    if _is_dart_model_type(base):
        expr = (
            f"{attr.dart_name}?.toJson()"
            if attr.is_nullable
            else f"{attr.dart_name}.toJson()"
        )
        return f"      '{attr.wire_name}': {expr},"
    return f"      '{attr.wire_name}': {attr.dart_name},"


def _dart_decode_expr_is_nullable(*, attr: _ViewAttribute) -> bool:
    base = attr.dart_type.removesuffix("?")
    if _dart_model_list_inner(base) is not None:
        return False
    return base not in {"List<Map<String, dynamic>>", "Map<String, dynamic>"}


def _dart_helpers_for_attr(*, attr: _ViewAttribute) -> set[str]:
    base = attr.dart_type.removesuffix("?")
    helpers: set[str] = set()
    if base == "String":
        helpers.add("string")
    elif base == "bool":
        helpers.add("bool")
    elif base == "int":
        helpers.add("int")
    elif base == "double":
        helpers.add("double")
    elif base == "List<Map<String, dynamic>>":
        helpers.add("json_object_list")
    elif base == "Map<String, dynamic>":
        helpers.add("json_object")
    elif _dart_model_list_inner(base) is not None:
        helpers.add("model_list")
    elif _is_dart_model_type(base):
        helpers.add("model_value")
    if not attr.is_nullable and not attr.has_default and base != "dynamic":
        helpers.add("required")
    return helpers


def _dart_model_list_inner(dart_type: str) -> str | None:
    inner = _dart_list_inner(dart_type)
    if inner is None:
        return None
    if inner in {"dynamic", "String", "bool", "int", "double", "Map<String, dynamic>"}:
        return None
    return inner or None


def _dart_list_inner(dart_type: str) -> str | None:
    if not dart_type.startswith("List<") or not dart_type.endswith(">"):
        return None
    return dart_type[len("List<") : -1].strip() or None


def _is_dart_model_type(dart_type: str) -> bool:
    if dart_type in {
        "dynamic",
        "String",
        "bool",
        "int",
        "double",
        "Map<String, dynamic>",
    }:
        return False
    return bool(re.fullmatch(r"[A-Z][A-Za-z0-9_]*", dart_type))


def _render_dart_helpers(*, helper_needs: set[str]) -> list[str]:
    helpers: list[str] = []
    if "string" in helper_needs:
        helpers.extend(
            [
                "",
                "String? _stringValue(Object? value) {",
                "  if (value == null) return null;",
                "  final text = value.toString().trim();",
                "  return text.isEmpty ? null : text;",
                "}",
            ]
        )
    if "bool" in helper_needs:
        helpers.extend(
            [
                "",
                "bool? _boolValue(Object? value) {",
                "  if (value is bool) return value;",
                "  if (value is String) return value.toLowerCase() == 'true';",
                "  return null;",
                "}",
            ]
        )
    if "int" in helper_needs:
        helpers.extend(
            [
                "",
                "int? _intValue(Object? value) {",
                "  if (value is int) return value;",
                "  if (value is num) return value.toInt();",
                "  if (value is String) return int.tryParse(value);",
                "  return null;",
                "}",
            ]
        )
    if "double" in helper_needs:
        helpers.extend(
            [
                "",
                "double? _doubleValue(Object? value) {",
                "  if (value is double) return value;",
                "  if (value is num) return value.toDouble();",
                "  if (value is String) return double.tryParse(value);",
                "  return null;",
                "}",
            ]
        )
    if "json_object" in helper_needs:
        helpers.extend(
            [
                "",
                "Map<String, dynamic> _jsonObject(Object? value) {",
                "  if (value is Map) return Map<String, dynamic>.from(value);",
                "  return const <String, dynamic>{};",
                "}",
            ]
        )
    if "json_object_list" in helper_needs:
        helpers.extend(
            [
                "",
                "List<Map<String, dynamic>> _jsonObjectList(Object? value) {",
                "  if (value is! List) return const <Map<String, dynamic>>[];",
                "  return <Map<String, dynamic>>[",
                "    for (final item in value)",
                "      if (item is Map) Map<String, dynamic>.from(item),",
                "  ];",
                "}",
            ]
        )
    if "model_list" in helper_needs:
        helpers.extend(
            [
                "",
                "List<T> _modelList<T>(",
                "  Object? value,",
                "  T Function(Map<String, dynamic> json) decode,",
                ") {",
                "  if (value is! List) return <T>[];",
                "  return <T>[",
                "    for (final item in value)",
                "      if (item is Map) decode(Map<String, dynamic>.from(item)),",
                "  ];",
                "}",
            ]
        )
    if "model_value" in helper_needs:
        helpers.extend(
            [
                "",
                "T? _modelValue<T>(",
                "  Object? value,",
                "  T Function(Map<String, dynamic> json) decode,",
                ") {",
                "  if (value is Map) return decode(Map<String, dynamic>.from(value));",
                "  return null;",
                "}",
            ]
        )
    if "required" in helper_needs:
        helpers.extend(
            [
                "",
                "T _missingRequiredField<T>(String fieldName) {",
                "  throw FormatException('Missing required view model field: $fieldName');",
                "}",
            ]
        )
    return helpers


def _render_python_pyproject(
    *, project_name: str, import_root: str, description: str | None
) -> str:
    return (
        "[project]\n"
        f'name = "{project_name}"\n'
        'version = "0.1.0"\n'
        f"description = \"{_escape_pyproject_string(description or 'Aware experience view model contracts.')}\"\n"
        'requires-python = ">=3.12"\n'
        "dependencies = [\n"
        '  "pydantic>=2.8.0,<3.0.0",\n'
        "]\n"
        "\n"
        "[build-system]\n"
        'requires = ["hatchling>=1.27.0"]\n'
        'build-backend = "hatchling.build"\n'
        "\n"
        "[tool.hatch.build.targets.wheel]\n"
        f'packages = ["{import_root}"]\n'
        f'include = ["{import_root}/py.typed"]\n'
    )


def _render_python_init(
    *, import_root: str, contracts: tuple[_ViewContract, ...]
) -> str:
    imports: list[str] = []
    all_items: list[str] = []
    for contract in contracts:
        names = tuple(
            dict.fromkeys(model.model.class_config.name for model in contract.models)
        )
        imports.append(
            f"from {import_root}.{_python_contract_module(contract=contract)} "
            f"import {', '.join(names)}"
        )
        all_items.extend(names)
    all_items = list(dict.fromkeys(all_items))
    all_items.extend(
        ["VIEW_MODEL_CONTRACTS", "VIEW_MODEL_DECODERS", "ExperienceViewModelContract"]
    )
    return (
        _generated_header(language="python")
        + "\n".join(imports)
        + "\nfrom .view_model_registry import ExperienceViewModelContract, VIEW_MODEL_CONTRACTS, VIEW_MODEL_DECODERS\n"
        + "\n__all__ = [\n"
        + "".join(f'    "{item}",\n' for item in all_items)
        + "]\n"
    )


def _render_python_registry(
    *, import_root: str, contracts: tuple[_ViewContract, ...]
) -> str:
    imports = [
        (
            f"from {import_root}.{_python_contract_module(contract=contract)} "
            f"import {contract.model.class_config.name}"
        )
        for contract in contracts
    ]
    rows = []
    decoder_rows = []
    for contract in contracts:
        cls = contract.model.class_config.name
        rows.append(
            "    ExperienceViewModelContract("
            f"view_ref={cls}.VIEW_REF, "
            f"view_key={cls}.VIEW_KEY, "
            f"state_model_ref={cls}.STATE_MODEL_REF, "
            f"version={cls}.VERSION, "
            f"model={cls}),"
        )
        decoder_rows.append(f"    {cls}.VIEW_REF: {cls}.model_validate,")
        decoder_rows.append(f"    {cls}.VIEW_KEY: {cls}.model_validate,")
    body = [
        _generated_header(language="python").rstrip(),
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass",
        "from typing import Any, Callable",
        "",
        "from pydantic import BaseModel",
        "",
        *imports,
        "",
        "",
        "@dataclass(frozen=True, slots=True)",
        "class ExperienceViewModelContract:",
        "    view_ref: str",
        "    view_key: str",
        "    state_model_ref: str",
        "    version: str",
        "    model: type[BaseModel]",
        "",
        "",
        "VIEW_MODEL_CONTRACTS: tuple[ExperienceViewModelContract, ...] = (",
        *rows,
        ")",
        "",
        "VIEW_MODEL_DECODERS: dict[str, Callable[[Any], BaseModel]] = {",
        *decoder_rows,
        "}",
        "",
    ]
    return "\n".join(body)


def _render_python_contract(*, contract: _ViewContract) -> str:
    body = [
        _generated_header(language="python").rstrip(),
        "from __future__ import annotations",
        "",
        "from typing import Any, ClassVar",
        "",
        "from pydantic import BaseModel, ConfigDict, Field",
        "",
        "",
    ]
    rendered_models = [
        _render_python_contract_model(
            contract=contract,
            contract_model=contract_model,
            is_root=contract_model.model.class_config_id
            == contract.model.class_config_id,
        )
        for contract_model in contract.models
    ]
    body.append("\n\n\n".join(rendered_models))
    return "\n".join(body) + "\n"


def _render_python_contract_model(
    *,
    contract: _ViewContract,
    contract_model: _ViewContractModel,
    is_root: bool,
) -> str:
    cls = contract_model.model.class_config.name
    field_rows = [_python_field_row(attr=attr) for attr in contract_model.attributes]
    body = [
        f"class {cls}(BaseModel):",
        "    model_config = ConfigDict(populate_by_name=True)",
        "",
    ]
    if is_root:
        body.extend(
            [
                f'    STATE_MODEL_REF: ClassVar[str] = "{contract.model.state_model_ref}"',
                f'    VIEW_REF: ClassVar[str] = "{contract.binding.view_ref}"',
                f'    VIEW_KEY: ClassVar[str] = "{contract.binding.projection_view_key}"',
                f'    VERSION: ClassVar[str] = "{contract.binding.version}"',
                "",
            ]
        )
    body.extend(
        [
            *field_rows,
            "",
            "    def to_json(self) -> dict[str, Any]:",
            '        return self.model_dump(mode="json")',
        ]
    )
    return "\n".join(body)


def _python_field_row(*, attr: _ViewAttribute) -> str:
    if attr.has_default:
        if isinstance(attr.default_value, list):
            return f"    {attr.python_name}: {attr.python_type} = Field(default_factory=list)"
        if isinstance(attr.default_value, dict):
            return f"    {attr.python_name}: {attr.python_type} = Field(default_factory=dict)"
        return f"    {attr.python_name}: {attr.python_type} = Field(default={attr.default_value!r})"
    if attr.is_nullable:
        return f"    {attr.python_name}: {attr.python_type} = Field(default=None)"
    return f"    {attr.python_name}: {attr.python_type}"


def _dart_contract_relpath(*, contract: _ViewContract) -> Path:
    return (
        Path("views")
        .joinpath(
            contract.binding.observable_key,
            *[part for part in contract.binding.view_key.split(".") if part],
        )
        .with_suffix(".dart")
    )


def _python_contract_relpath(*, contract: _ViewContract) -> Path:
    return (
        Path("views")
        .joinpath(
            contract.binding.observable_key,
            *[part for part in contract.binding.view_key.split(".") if part],
        )
        .with_suffix(".py")
    )


def _python_contract_module(*, contract: _ViewContract) -> str:
    return (
        _python_contract_relpath(contract=contract)
        .with_suffix("")
        .as_posix()
        .replace("/", ".")
    )


def _package_import_root(*, target: AwareExperienceTomlLanguageTargetSpec) -> str:
    return Path(target.package_dir).parts[-1]


def _snake_to_camel(value: str) -> str:
    parts = [part for part in value.split("_") if part]
    if not parts:
        return value
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _dart_literal(value: Any, *, dart_type: str | None = None) -> str:
    if value is _MISSING:
        return "null"
    if value is None:
        return "null"
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, list):
        if not value:
            list_inner = _dart_list_inner(dart_type or "")
            return f"const <{list_inner or 'Map<String, dynamic>'}>[]"
        return json.dumps(value)
    if isinstance(value, dict):
        return "const <String, dynamic>{}" if not value else json.dumps(value)
    return json.dumps(value)


def _escape_pyproject_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _generated_header(*, language: str) -> str:
    if language == "dart":
        return "// Generated by aware_experience language contracts. Do not edit by hand.\n"
    return "# Generated by aware_experience language contracts. Do not edit by hand.\n"


def _reset_generated_dir(*, path: Path, base: Path) -> None:
    if path.exists():
        _assert_within(
            base=base, candidate=path, label="generated language contract path"
        )
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _write_files(*, files: dict[Path, str]) -> None:
    for path, content in sorted(files.items(), key=lambda item: item[0].as_posix()):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def _assert_within(*, base: Path, candidate: Path, label: str) -> None:
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    if (
        candidate_resolved == base_resolved
        or base_resolved in candidate_resolved.parents
    ):
        return
    raise ValueError(
        f"{label} resolved outside package boundary: base={base_resolved} candidate={candidate_resolved}"
    )


__all__ = [
    "ExperienceLanguageContractMaterializationResult",
    "ExperienceLanguageContractPackage",
    "SUPPORTED_LANGUAGE_CONTRACT_TARGETS",
    "materialize_experience_language_contracts",
]
