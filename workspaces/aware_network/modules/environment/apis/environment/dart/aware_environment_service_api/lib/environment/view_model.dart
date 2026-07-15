// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint
// ignore_for_file: unused_element, deprecated_member_use, deprecated_member_use_from_same_package, use_function_type_syntax_for_parameters, unnecessary_const, avoid_init_to_null, invalid_override_different_default_values_named, prefer_expression_function_bodies, annotate_overrides, invalid_annotation_target, unnecessary_question_mark

import 'package:aware_model_helpers/converters.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:uuid/uuid.dart';

part 'view_model.freezed.dart';
part 'view_model.g.dart';

/// API-owned view-state contracts for Environment navigation surfaces.
/// Public API view keys:
/// - environment.navigator
/// - environment.process_workspace
/// - environment.thread_layout
@freezed
abstract class EnvironmentStatusBlockSummaryV1
    with _$EnvironmentStatusBlockSummaryV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentStatusBlockSummaryV1.def({
    required String name,
    required bool available,
    String? authorityKind,
    String? unavailableReason,
    required Map<String, dynamic> payload,
  }) = _EnvironmentStatusBlockSummaryV1;

  factory EnvironmentStatusBlockSummaryV1({
    required String name,
    bool? available,
    String? authorityKind,
    String? unavailableReason,
    Map<String, dynamic>? payload,
  }) {
    return _EnvironmentStatusBlockSummaryV1(
      name: name,
      available: available ?? true,
      authorityKind: authorityKind,
      unavailableReason: unavailableReason,
      payload: payload ?? {},
    );
  }

  factory EnvironmentStatusBlockSummaryV1.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentStatusBlockSummaryV1FromJson({
        ...json,
        if (!json.containsKey('available')) 'available': true,
        if (!json.containsKey('payload')) 'payload': {},
      });
}

@freezed
abstract class EnvironmentThreadNavigationItemV1
    with _$EnvironmentThreadNavigationItemV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentThreadNavigationItemV1.def({
    @UuidValueConverter() UuidValue? threadId,
    String? threadKey,
    required String title,
    String? description,
    required int attachmentCount,
    required int activeAttachmentCount,
    required bool isSelected,
  }) = _EnvironmentThreadNavigationItemV1;

  factory EnvironmentThreadNavigationItemV1({
    UuidValue? threadId,
    String? threadKey,
    String? title,
    String? description,
    int? attachmentCount,
    int? activeAttachmentCount,
    bool? isSelected,
  }) {
    return _EnvironmentThreadNavigationItemV1(
      threadId: threadId,
      threadKey: threadKey,
      title: title ?? 'Thread',
      description: description,
      attachmentCount: attachmentCount ?? 0,
      activeAttachmentCount: activeAttachmentCount ?? 0,
      isSelected: isSelected ?? false,
    );
  }

  factory EnvironmentThreadNavigationItemV1.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentThreadNavigationItemV1FromJson({
    ...json,
    if (!json.containsKey('title')) 'title': 'Thread',
    if (!json.containsKey('attachment_count')) 'attachment_count': 0,
    if (!json.containsKey('active_attachment_count'))
      'active_attachment_count': 0,
    if (!json.containsKey('is_selected')) 'is_selected': false,
  });
}

@freezed
abstract class EnvironmentProcessNavigationItemV1
    with _$EnvironmentProcessNavigationItemV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentProcessNavigationItemV1.def({
    @UuidValueConverter() UuidValue? processId,
    String? processKey,
    required String title,
    String? description,
    required int threadCount,
    required bool isSelected,
    @Default(const []) List<EnvironmentThreadNavigationItemV1> threads,
  }) = _EnvironmentProcessNavigationItemV1;

  factory EnvironmentProcessNavigationItemV1({
    UuidValue? processId,
    String? processKey,
    String? title,
    String? description,
    int? threadCount,
    bool? isSelected,
    List<EnvironmentThreadNavigationItemV1> threads = const [],
  }) {
    return _EnvironmentProcessNavigationItemV1(
      processId: processId,
      processKey: processKey,
      title: title ?? 'Process',
      description: description,
      threadCount: threadCount ?? 0,
      isSelected: isSelected ?? false,
      threads: threads,
    );
  }

  factory EnvironmentProcessNavigationItemV1.fromJson(
    Map<String, dynamic> json,
  ) => _$EnvironmentProcessNavigationItemV1FromJson({
    ...json,
    if (!json.containsKey('title')) 'title': 'Process',
    if (!json.containsKey('thread_count')) 'thread_count': 0,
    if (!json.containsKey('is_selected')) 'is_selected': false,
  });
}

@freezed
abstract class EnvironmentNavigatorViewStateV1
    with _$EnvironmentNavigatorViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory EnvironmentNavigatorViewStateV1.def({
    @UuidValueConverter() UuidValue? environmentId,
    required String title,
    required String status,
    required bool ready,
    @UuidValueConverter() UuidValue? selectedProcessId,
    String? selectedProcessKey,
    @UuidValueConverter() UuidValue? selectedThreadId,
    String? selectedThreadKey,
    @Default(const []) List<EnvironmentProcessNavigationItemV1> processes,
    @Default(const []) List<EnvironmentStatusBlockSummaryV1> statusBlocks,
    required String emptyMessage,
    required Map<String, dynamic> provenance,
  }) = _EnvironmentNavigatorViewStateV1;

  factory EnvironmentNavigatorViewStateV1({
    UuidValue? environmentId,
    String? title,
    String? status,
    bool? ready,
    UuidValue? selectedProcessId,
    String? selectedProcessKey,
    UuidValue? selectedThreadId,
    String? selectedThreadKey,
    List<EnvironmentProcessNavigationItemV1> processes = const [],
    List<EnvironmentStatusBlockSummaryV1> statusBlocks = const [],
    String? emptyMessage,
    Map<String, dynamic>? provenance,
  }) {
    return _EnvironmentNavigatorViewStateV1(
      environmentId: environmentId,
      title: title ?? 'Environment',
      status: status ?? 'waiting',
      ready: ready ?? false,
      selectedProcessId: selectedProcessId,
      selectedProcessKey: selectedProcessKey,
      selectedThreadId: selectedThreadId,
      selectedThreadKey: selectedThreadKey,
      processes: processes,
      statusBlocks: statusBlocks,
      emptyMessage: emptyMessage ?? 'No environment topology available',
      provenance: provenance ?? {},
    );
  }

  factory EnvironmentNavigatorViewStateV1.fromJson(Map<String, dynamic> json) =>
      _$EnvironmentNavigatorViewStateV1FromJson({
        ...json,
        if (!json.containsKey('title')) 'title': 'Environment',
        if (!json.containsKey('status')) 'status': 'waiting',
        if (!json.containsKey('ready')) 'ready': false,
        if (!json.containsKey('empty_message'))
          'empty_message': 'No environment topology available',
        if (!json.containsKey('provenance')) 'provenance': {},
      });
}

@freezed
abstract class ProcessWorkspaceThreadViewStateV1
    with _$ProcessWorkspaceThreadViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ProcessWorkspaceThreadViewStateV1.def({
    @UuidValueConverter() UuidValue? threadId,
    String? threadKey,
    required String title,
    String? description,
    required int attachmentCount,
    required int activeAttachmentCount,
    required int laneCount,
    required int layoutCount,
    required bool isSelected,
  }) = _ProcessWorkspaceThreadViewStateV1;

  factory ProcessWorkspaceThreadViewStateV1({
    UuidValue? threadId,
    String? threadKey,
    String? title,
    String? description,
    int? attachmentCount,
    int? activeAttachmentCount,
    int? laneCount,
    int? layoutCount,
    bool? isSelected,
  }) {
    return _ProcessWorkspaceThreadViewStateV1(
      threadId: threadId,
      threadKey: threadKey,
      title: title ?? 'Thread',
      description: description,
      attachmentCount: attachmentCount ?? 0,
      activeAttachmentCount: activeAttachmentCount ?? 0,
      laneCount: laneCount ?? 0,
      layoutCount: layoutCount ?? 0,
      isSelected: isSelected ?? false,
    );
  }

  factory ProcessWorkspaceThreadViewStateV1.fromJson(
    Map<String, dynamic> json,
  ) => _$ProcessWorkspaceThreadViewStateV1FromJson({
    ...json,
    if (!json.containsKey('title')) 'title': 'Thread',
    if (!json.containsKey('attachment_count')) 'attachment_count': 0,
    if (!json.containsKey('active_attachment_count'))
      'active_attachment_count': 0,
    if (!json.containsKey('lane_count')) 'lane_count': 0,
    if (!json.containsKey('layout_count')) 'layout_count': 0,
    if (!json.containsKey('is_selected')) 'is_selected': false,
  });
}

@freezed
abstract class ProcessWorkspaceViewStateV1 with _$ProcessWorkspaceViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ProcessWorkspaceViewStateV1.def({
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? processId,
    String? processKey,
    required String title,
    String? description,
    required String status,
    @UuidValueConverter() UuidValue? selectedThreadId,
    String? selectedThreadKey,
    @Default(const []) List<ProcessWorkspaceThreadViewStateV1> threads,
    required String emptyMessage,
    required Map<String, dynamic> provenance,
  }) = _ProcessWorkspaceViewStateV1;

  factory ProcessWorkspaceViewStateV1({
    UuidValue? environmentId,
    UuidValue? processId,
    String? processKey,
    String? title,
    String? description,
    String? status,
    UuidValue? selectedThreadId,
    String? selectedThreadKey,
    List<ProcessWorkspaceThreadViewStateV1> threads = const [],
    String? emptyMessage,
    Map<String, dynamic>? provenance,
  }) {
    return _ProcessWorkspaceViewStateV1(
      environmentId: environmentId,
      processId: processId,
      processKey: processKey,
      title: title ?? 'Process',
      description: description,
      status: status ?? 'waiting',
      selectedThreadId: selectedThreadId,
      selectedThreadKey: selectedThreadKey,
      threads: threads,
      emptyMessage: emptyMessage ?? 'No threads available',
      provenance: provenance ?? {},
    );
  }

  factory ProcessWorkspaceViewStateV1.fromJson(Map<String, dynamic> json) =>
      _$ProcessWorkspaceViewStateV1FromJson({
        ...json,
        if (!json.containsKey('title')) 'title': 'Process',
        if (!json.containsKey('status')) 'status': 'waiting',
        if (!json.containsKey('empty_message'))
          'empty_message': 'No threads available',
        if (!json.containsKey('provenance')) 'provenance': {},
      });
}

@freezed
abstract class ThreadLayoutLaneViewStateV1 with _$ThreadLayoutLaneViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ThreadLayoutLaneViewStateV1.def({
    required String laneHash,
    @UuidValueConverter() UuidValue? opgId,
    String? opgName,
  }) = _ThreadLayoutLaneViewStateV1;

  factory ThreadLayoutLaneViewStateV1({
    required String laneHash,
    UuidValue? opgId,
    String? opgName,
  }) {
    return _ThreadLayoutLaneViewStateV1(
      laneHash: laneHash,
      opgId: opgId,
      opgName: opgName,
    );
  }

  factory ThreadLayoutLaneViewStateV1.fromJson(Map<String, dynamic> json) =>
      _$ThreadLayoutLaneViewStateV1FromJson(json);
}

@freezed
abstract class ThreadLayoutAttachmentViewStateV1
    with _$ThreadLayoutAttachmentViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ThreadLayoutAttachmentViewStateV1.def({
    @UuidValueConverter() UuidValue? attachmentId,
    String? title,
    required bool isActive,
    @UuidValueConverter() UuidValue? objectInstanceGraphBranchId,
    @UuidValueConverter() UuidValue? objectInstanceGraphIdentityId,
    @UuidValueConverter() UuidValue? domainBranchId,
    @Default(const []) List<ThreadLayoutLaneViewStateV1> lanes,
  }) = _ThreadLayoutAttachmentViewStateV1;

  factory ThreadLayoutAttachmentViewStateV1({
    UuidValue? attachmentId,
    String? title,
    bool? isActive,
    UuidValue? objectInstanceGraphBranchId,
    UuidValue? objectInstanceGraphIdentityId,
    UuidValue? domainBranchId,
    List<ThreadLayoutLaneViewStateV1> lanes = const [],
  }) {
    return _ThreadLayoutAttachmentViewStateV1(
      attachmentId: attachmentId,
      title: title,
      isActive: isActive ?? true,
      objectInstanceGraphBranchId: objectInstanceGraphBranchId,
      objectInstanceGraphIdentityId: objectInstanceGraphIdentityId,
      domainBranchId: domainBranchId,
      lanes: lanes,
    );
  }

  factory ThreadLayoutAttachmentViewStateV1.fromJson(
    Map<String, dynamic> json,
  ) => _$ThreadLayoutAttachmentViewStateV1FromJson({
    ...json,
    if (!json.containsKey('is_active')) 'is_active': true,
  });
}

@freezed
abstract class ThreadLayoutSectionViewStateV1
    with _$ThreadLayoutSectionViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ThreadLayoutSectionViewStateV1.def({
    required String sectionKey,
    required String title,
    String? description,
    required int order,
    required double flex,
    required bool isVisible,
    @UuidValueConverter() UuidValue? focusScopeId,
    String? viewRef,
    String? viewKey,
    String? packageName,
    String? paneKey,
  }) = _ThreadLayoutSectionViewStateV1;

  factory ThreadLayoutSectionViewStateV1({
    required String sectionKey,
    String? title,
    String? description,
    int? order,
    double? flex,
    bool? isVisible,
    UuidValue? focusScopeId,
    String? viewRef,
    String? viewKey,
    String? packageName,
    String? paneKey,
  }) {
    return _ThreadLayoutSectionViewStateV1(
      sectionKey: sectionKey,
      title: title ?? 'Section',
      description: description,
      order: order ?? 0,
      flex: flex ?? 1.0,
      isVisible: isVisible ?? true,
      focusScopeId: focusScopeId,
      viewRef: viewRef,
      viewKey: viewKey,
      packageName: packageName,
      paneKey: paneKey,
    );
  }

  factory ThreadLayoutSectionViewStateV1.fromJson(Map<String, dynamic> json) =>
      _$ThreadLayoutSectionViewStateV1FromJson({
        ...json,
        if (!json.containsKey('title')) 'title': 'Section',
        if (!json.containsKey('order')) 'order': 0,
        if (!json.containsKey('flex')) 'flex': 1.0,
        if (!json.containsKey('is_visible')) 'is_visible': true,
      });
}

@freezed
abstract class ThreadLayoutCandidateViewStateV1
    with _$ThreadLayoutCandidateViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ThreadLayoutCandidateViewStateV1.def({
    @UuidValueConverter() UuidValue? layoutId,
    String? layoutKey,
    required String title,
    String? description,
    required bool isActive,
    @Default(const []) List<ThreadLayoutSectionViewStateV1> sections,
  }) = _ThreadLayoutCandidateViewStateV1;

  factory ThreadLayoutCandidateViewStateV1({
    UuidValue? layoutId,
    String? layoutKey,
    String? title,
    String? description,
    bool? isActive,
    List<ThreadLayoutSectionViewStateV1> sections = const [],
  }) {
    return _ThreadLayoutCandidateViewStateV1(
      layoutId: layoutId,
      layoutKey: layoutKey,
      title: title ?? 'Layout',
      description: description,
      isActive: isActive ?? false,
      sections: sections,
    );
  }

  factory ThreadLayoutCandidateViewStateV1.fromJson(
    Map<String, dynamic> json,
  ) => _$ThreadLayoutCandidateViewStateV1FromJson({
    ...json,
    if (!json.containsKey('title')) 'title': 'Layout',
    if (!json.containsKey('is_active')) 'is_active': false,
  });
}

@freezed
abstract class ThreadLayoutViewStateV1 with _$ThreadLayoutViewStateV1 {
  @JsonSerializable(explicitToJson: true, fieldRename: FieldRename.snake)
  factory ThreadLayoutViewStateV1.def({
    @UuidValueConverter() UuidValue? environmentId,
    @UuidValueConverter() UuidValue? processId,
    String? processKey,
    @UuidValueConverter() UuidValue? threadId,
    String? threadKey,
    required String title,
    String? description,
    required String status,
    @UuidValueConverter() UuidValue? activeLayoutId,
    String? activeLayoutKey,
    @Default(const []) List<ThreadLayoutCandidateViewStateV1> layouts,
    @Default(const []) List<ThreadLayoutSectionViewStateV1> sections,
    @Default(const []) List<ThreadLayoutAttachmentViewStateV1> attachments,
    required String emptyMessage,
    required Map<String, dynamic> provenance,
  }) = _ThreadLayoutViewStateV1;

  factory ThreadLayoutViewStateV1({
    UuidValue? environmentId,
    UuidValue? processId,
    String? processKey,
    UuidValue? threadId,
    String? threadKey,
    String? title,
    String? description,
    String? status,
    UuidValue? activeLayoutId,
    String? activeLayoutKey,
    List<ThreadLayoutCandidateViewStateV1> layouts = const [],
    List<ThreadLayoutSectionViewStateV1> sections = const [],
    List<ThreadLayoutAttachmentViewStateV1> attachments = const [],
    String? emptyMessage,
    Map<String, dynamic>? provenance,
  }) {
    return _ThreadLayoutViewStateV1(
      environmentId: environmentId,
      processId: processId,
      processKey: processKey,
      threadId: threadId,
      threadKey: threadKey,
      title: title ?? 'Thread',
      description: description,
      status: status ?? 'waiting',
      activeLayoutId: activeLayoutId,
      activeLayoutKey: activeLayoutKey,
      layouts: layouts,
      sections: sections,
      attachments: attachments,
      emptyMessage: emptyMessage ?? 'No thread layout available',
      provenance: provenance ?? {},
    );
  }

  factory ThreadLayoutViewStateV1.fromJson(Map<String, dynamic> json) =>
      _$ThreadLayoutViewStateV1FromJson({
        ...json,
        if (!json.containsKey('title')) 'title': 'Thread',
        if (!json.containsKey('status')) 'status': 'waiting',
        if (!json.containsKey('empty_message'))
          'empty_message': 'No thread layout available',
        if (!json.containsKey('provenance')) 'provenance': {},
      });
}
