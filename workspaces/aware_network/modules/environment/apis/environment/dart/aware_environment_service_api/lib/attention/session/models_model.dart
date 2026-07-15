// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'models_model.freezed.dart';
part 'models_model.g.dart';

/// Canonical DTOs for Attention session transition reads.
/// Ownership:
/// - Attention API owns the transport read models.
/// - Attention ontology owns persisted AttentionSession and
/// AttentionFocusTransition truth.
/// - Identity owns actor membership/subscription checks.
@freezed
abstract class AttentionSessionPin with _$AttentionSessionPin {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory AttentionSessionPin.def({
    @UuidValueConverter() required UuidValue attentionSessionId,
    @UuidValueConverter() required UuidValue identitySessionId,
    @UuidValueConverter() UuidValue? activeLayoutId,
    String? key,
    String? title,
    String? description,
    String? purpose,
    required String status,
    String? sourceKind,
    String? sourceRef,
    required Map<String, dynamic> metadataJson,
  }) = _AttentionSessionPin;

  factory AttentionSessionPin({
    required UuidValue attentionSessionId,
    required UuidValue identitySessionId,
    UuidValue? activeLayoutId,
    String? key,
    String? title,
    String? description,
    String? purpose,
    String? status,
    String? sourceKind,
    String? sourceRef,
    Map<String, dynamic>? metadataJson,
  }) {
    return _AttentionSessionPin(
      attentionSessionId: attentionSessionId,
      identitySessionId: identitySessionId,
      activeLayoutId: activeLayoutId,
      key: key,
      title: title,
      description: description,
      purpose: purpose,
      status: status ?? 'active',
      sourceKind: sourceKind,
      sourceRef: sourceRef,
      metadataJson: metadataJson ?? {},
    );
  }

  factory AttentionSessionPin.fromJson(Map<String, dynamic> json) =>
      _$AttentionSessionPinFromJson({
        ...json,
        if (!json.containsKey('status')) 'status': 'active',
        if (!json.containsKey('metadata_json')) 'metadata_json': {},
      });
}

/// Read pin for one AttentionFocusTransition plus its parent session chain.
/// This is a DTO projection over Attention ontology rows. It is not a second
/// persisted frame model.
@freezed
abstract class AttentionFocusTransitionPin with _$AttentionFocusTransitionPin {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory AttentionFocusTransitionPin.def({
    @UuidValueConverter() required UuidValue attentionFocusTransitionId,
    @UuidValueConverter() required UuidValue attentionSessionSectionId,
    @UuidValueConverter() UuidValue? attentionSessionLayoutId,
    @UuidValueConverter() UuidValue? attentionSessionId,
    @UuidValueConverter() UuidValue? identitySessionId,
    @UuidValueConverter() UuidValue? layoutSectionId,
    @UuidValueConverter() UuidValue? sectionId,
    String? sectionKey,
    @UuidValueConverter() UuidValue? layoutId,
    @UuidValueConverter() UuidValue? layoutConfigId,
    @UuidValueConverter() UuidValue? previousTransitionId,
    @UuidValueConverter() required UuidValue focusScopeId,
    @UuidValueConverter() UuidValue? focusId,
    @UuidValueConverter() UuidValue? observableId,
    @UuidValueConverter() UuidValue? objectProjectionGraphIdentityId,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
    @UuidValueConverter() UuidValue? objectInstanceGraphCommitId,
    required String transitionKey,
    required int sequence,
    String? projectionHash,
    required String transitionKind,
    String? rationale,
    String? sourceKind,
    String? sourceRef,
    required Map<String, dynamic> metadataJson,
  }) = _AttentionFocusTransitionPin;

  factory AttentionFocusTransitionPin({
    required UuidValue attentionFocusTransitionId,
    required UuidValue attentionSessionSectionId,
    UuidValue? attentionSessionLayoutId,
    UuidValue? attentionSessionId,
    UuidValue? identitySessionId,
    UuidValue? layoutSectionId,
    UuidValue? sectionId,
    String? sectionKey,
    UuidValue? layoutId,
    UuidValue? layoutConfigId,
    UuidValue? previousTransitionId,
    required UuidValue focusScopeId,
    UuidValue? focusId,
    UuidValue? observableId,
    UuidValue? objectProjectionGraphIdentityId,
    UuidValue? objectInstanceGraphBranchId,
    UuidValue? objectInstanceGraphCommitId,
    required String transitionKey,
    int? sequence,
    String? projectionHash,
    String? transitionKind,
    String? rationale,
    String? sourceKind,
    String? sourceRef,
    Map<String, dynamic>? metadataJson,
  }) {
    return _AttentionFocusTransitionPin(
      attentionFocusTransitionId: attentionFocusTransitionId,
      attentionSessionSectionId: attentionSessionSectionId,
      attentionSessionLayoutId: attentionSessionLayoutId,
      attentionSessionId: attentionSessionId,
      identitySessionId: identitySessionId,
      layoutSectionId: layoutSectionId,
      sectionId: sectionId,
      sectionKey: sectionKey,
      layoutId: layoutId,
      layoutConfigId: layoutConfigId,
      previousTransitionId: previousTransitionId,
      focusScopeId: focusScopeId,
      focusId: focusId,
      observableId: observableId,
      objectProjectionGraphIdentityId: objectProjectionGraphIdentityId,
      objectInstanceGraphBranchId: objectInstanceGraphBranchId,
      objectInstanceGraphCommitId: objectInstanceGraphCommitId,
      transitionKey: transitionKey,
      sequence: sequence ?? 0,
      projectionHash: projectionHash,
      transitionKind: transitionKind ?? 'focus',
      rationale: rationale,
      sourceKind: sourceKind,
      sourceRef: sourceRef,
      metadataJson: metadataJson ?? {},
    );
  }

  factory AttentionFocusTransitionPin.fromJson(Map<String, dynamic> json) =>
      _$AttentionFocusTransitionPinFromJson({
        ...json,
        if (!json.containsKey('sequence')) 'sequence': 0,
        if (!json.containsKey('transition_kind')) 'transition_kind': 'focus',
        if (!json.containsKey('metadata_json')) 'metadata_json': {},
      });
}

@freezed
abstract class AttentionTransitionValidationResult
    with _$AttentionTransitionValidationResult {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory AttentionTransitionValidationResult.def({
    required bool exists,
    required bool valid,
    @Default(const []) List<String> failureReasons,
    AttentionFocusTransitionPin? transition,
  }) = _AttentionTransitionValidationResult;

  factory AttentionTransitionValidationResult({
    bool? exists,
    bool? valid,
    List<String> failureReasons = const [],
    AttentionFocusTransitionPin? transition,
  }) {
    return _AttentionTransitionValidationResult(
      exists: exists ?? false,
      valid: valid ?? false,
      failureReasons: failureReasons,
      transition: transition,
    );
  }

  factory AttentionTransitionValidationResult.fromJson(
    Map<String, dynamic> json,
  ) => _$AttentionTransitionValidationResultFromJson({
    ...json,
    if (!json.containsKey('exists')) 'exists': false,
    if (!json.containsKey('valid')) 'valid': false,
  });
}
