import 'dart:typed_data';

import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

import 'package:aware_models/converters.dart';

part 'agent_identity_freezed.freezed.dart';
part 'agent_identity_freezed.g.dart';

/// Simple Identity model in freezed style
@freezed
abstract class Identity with _$Identity {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory Identity.def({
    @UuidValueConverter() required UuidValue id,
    required String publicKey,
    required String type,
    required DateTime createdAt,
    DateTime? updatedAt,
  }) = _Identity;

  factory Identity({
    UuidValue? id,
    required String publicKey,
    required String type,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    return _Identity(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      publicKey: publicKey,
      type: type,
      createdAt: createdAt ?? DateTime.timestamp(),
      updatedAt: updatedAt,
    );
  }

  factory Identity.fromJson(Map<String, dynamic> json) => 
      _$IdentityFromJson(json);
}

/// Simple Agent model in freezed style with Identity relationship
@freezed
abstract class Agent with _$Agent {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory Agent.def({
    @UuidValueConverter() required UuidValue id,
    @UuidValueConverter() required UuidValue identityId,
    required String name,
    required DateTime createdAt,
    DateTime? updatedAt,
    required Identity identity,
    @Default([]) List<Agent>? childAgents,
  }) = _Agent;

  factory Agent({
    UuidValue? id,
    required UuidValue identityId,
    required String name,
    DateTime? createdAt,
    DateTime? updatedAt,
    required Identity identity,
    List<Agent>? childAgents,
  }) {
    return _Agent(
      id: id ?? UuidValue.fromString(Uuid().v4()),
      identityId: identityId,
      name: name,
      createdAt: createdAt ?? DateTime.timestamp(),
      updatedAt: updatedAt,
      identity: identity,
      childAgents: childAgents ?? [],
    );
  }

  factory Agent.fromJson(Map<String, dynamic> json) => 
      _$AgentFromJson(json);
}