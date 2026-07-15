// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'hosted_interface_namespace_model.freezed.dart';
part 'hosted_interface_namespace_model.g.dart';

/// Snapshot of one namespace hosted behind the local Interface daemon.
/// Transport-only contract:
/// - graph/ORM agnostic
/// - local-machine scoped
/// - safe for renderer and CLI clients
@freezed
abstract class HostedInterfaceNamespace with _$HostedInterfaceNamespace {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory HostedInterfaceNamespace.def({
    required String namespace,
    required String hostLabel,
    required bool started,
    @UuidValueConverter() UuidValue? actorId,
    @UuidValueConverter() UuidValue? interfaceId,
    @UuidValueConverter() UuidValue? interfaceSessionId,
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? environmentConfigId,
    @Default(const []) List<String> warnings,
  }) = _HostedInterfaceNamespace;

  factory HostedInterfaceNamespace({
    required String namespace,
    required String hostLabel,
    required bool started,
    UuidValue? actorId,
    UuidValue? interfaceId,
    UuidValue? interfaceSessionId,
    UuidValue? environmentId,
    UuidValue? environmentConfigId,
    List<String> warnings = const [],
  }) {
    return _HostedInterfaceNamespace(
      namespace: namespace,
      hostLabel: hostLabel,
      started: started,
      actorId: actorId,
      interfaceId: interfaceId,
      interfaceSessionId: interfaceSessionId,
      environmentId: environmentId,
      environmentConfigId: environmentConfigId,
      warnings: warnings,
    );
  }

  factory HostedInterfaceNamespace.fromJson(Map<String, dynamic> json) =>
      _$HostedInterfaceNamespaceFromJson(json);
}
