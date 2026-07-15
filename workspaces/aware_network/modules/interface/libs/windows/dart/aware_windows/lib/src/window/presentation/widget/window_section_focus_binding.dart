import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../domain/model/window_config.dart';
import '../../domain/provider/window_focus_provider.dart';
import '../../domain/presenter/window_pane_presenter.dart';

class WindowSectionFocusBinding extends ConsumerStatefulWidget {
  const WindowSectionFocusBinding({
    super.key,
    required this.windowId,
    required this.section,
    required this.child,
    this.focusConfig,
  });

  final String windowId;
  final WindowSectionConfig section;
  final Widget child;
  final PaneFocusConfig? focusConfig;

  @override
  ConsumerState<WindowSectionFocusBinding> createState() =>
      _WindowSectionFocusBindingState();
}

class _WindowSectionFocusBindingState
    extends ConsumerState<WindowSectionFocusBinding> {
  late FocusScopeNode _focusScope;
  late FocusNode _sectionFocusNode;
  bool _claimedFocus = false;

  FocusScopeNode get focusScope => _focusScope;

  @override
  void initState() {
    super.initState();
    _focusScope = FocusScopeNode(
      debugLabel:
          'window:${widget.windowId}/section:${widget.section.id}/focus_scope',
    );
    _sectionFocusNode = FocusNode(
      debugLabel:
          'window:${widget.windowId}/section:${widget.section.id}/focus_node',
      canRequestFocus: widget.focusConfig?.canRequestFocus ?? true,
    );
    _maybeAutofocus();
  }

  @override
  void dispose() {
    _sectionFocusNode.dispose();
    _focusScope.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant WindowSectionFocusBinding oldWidget) {
    super.didUpdateWidget(oldWidget);
    final canRequestFocus = widget.focusConfig?.canRequestFocus ?? true;
    if (_sectionFocusNode.canRequestFocus != canRequestFocus) {
      _sectionFocusNode.canRequestFocus = canRequestFocus;
    }
    if (!(oldWidget.focusConfig?.autofocus ?? false) &&
        (widget.focusConfig?.autofocus ?? false)) {
      _maybeAutofocus();
    }
  }

  void _handleFocusChange(bool focused) {
    final controller = ref.read(
      windowFocusControllerProvider(widget.windowId).notifier,
    );
    if (focused) {
      controller.setSectionFocus(
        sectionId: widget.section.id,
        paneId: widget.section.paneId,
      );
      _claimedFocus = true;
      return;
    }

    if (!_claimedFocus) {
      return;
    }

    final focusState = ref.read(windowFocusControllerProvider(widget.windowId));
    if (focusState.isSuspended &&
        focusState.overlayCapture != null &&
        focusState.activeSectionId == widget.section.id) {
      // Overlay is capturing focus; keep the last active section.
      return;
    }

    controller.clearSectionFocus(widget.section.id);
    _claimedFocus = false;
  }

  void _maybeAutofocus() {
    if (!(widget.focusConfig?.autofocus ?? false)) {
      return;
    }
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      if (!_sectionFocusNode.hasFocus) {
        _focusScope.requestFocus(_sectionFocusNode);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return FocusScope(
      node: _focusScope,
      onFocusChange: _handleFocusChange,
      child: _PaneSectionFocusInherited(
        windowId: widget.windowId,
        sectionId: widget.section.id,
        focusScope: _focusScope,
        focusNode: _sectionFocusNode,
        child: Focus(
          focusNode: _sectionFocusNode,
          autofocus: widget.focusConfig?.autofocus ?? false,
          canRequestFocus: widget.focusConfig?.canRequestFocus ?? true,
          onFocusChange: _handleFocusChange,
          child: widget.child,
        ),
      ),
    );
  }
}

class PaneFocusHandle {
  const PaneFocusHandle._(this._data);

  final _PaneSectionFocusInherited _data;

  static PaneFocusHandle? maybeOf(BuildContext context) {
    final data = context
        .dependOnInheritedWidgetOfExactType<_PaneSectionFocusInherited>();
    return data == null ? null : PaneFocusHandle._(data);
  }

  String get windowId => _data.windowId;

  String get sectionId => _data.sectionId;

  bool get hasFocus => _data.focusScope.hasFocus || _data.focusNode.hasFocus;

  void requestFocus() {
    if (_data.focusNode.canRequestFocus) {
      _data.focusScope.requestFocus(_data.focusNode);
    }
  }
}

class _PaneSectionFocusInherited extends InheritedWidget {
  const _PaneSectionFocusInherited({
    required this.windowId,
    required this.sectionId,
    required this.focusScope,
    required this.focusNode,
    required super.child,
  });

  final String windowId;
  final String sectionId;
  final FocusScopeNode focusScope;
  final FocusNode focusNode;

  @override
  bool updateShouldNotify(covariant _PaneSectionFocusInherited oldWidget) {
    return windowId != oldWidget.windowId ||
        sectionId != oldWidget.sectionId ||
        focusScope != oldWidget.focusScope ||
        focusNode != oldWidget.focusNode;
  }
}
