import 'package:aware_shell/aware_shell.dart';
import 'package:flutter/material.dart';

const awareContentMarkdownViewerComponentRef = 'aware.content.markdown_viewer';
const awareContentCodeViewerComponentRef = 'aware.content.code_viewer';

void registerRenderComponents(RenderComponentRegistryBuilder registry) {
  registry.register(
    RenderComponentRegistration(
      componentRef: awareContentMarkdownViewerComponentRef,
      displayName: 'Markdown viewer',
      builder: _buildMarkdownViewer,
    ),
  );
  registry.register(
    RenderComponentRegistration(
      componentRef: awareContentCodeViewerComponentRef,
      displayName: 'Code viewer',
      builder: _buildCodeViewer,
    ),
  );
}

Widget _buildMarkdownViewer(
  BuildContext context,
  RenderComponentBuildData component,
) {
  final markdown = _stringInput(component.input('markdown'));
  return AwareContentMarkdownViewer(markdownText: markdown);
}

Widget _buildCodeViewer(
  BuildContext context,
  RenderComponentBuildData component,
) {
  return AwareContentCodeViewer(
    code: _stringInput(
      component.input('code') ??
          component.input('source') ??
          component.input('text'),
    ),
    language: _trimmedStringInput(component.input('language')),
    title: _trimmedStringInput(component.input('title')),
  );
}

class AwareContentMarkdownViewer extends StatelessWidget {
  const AwareContentMarkdownViewer({required this.markdownText, super.key});

  final String markdownText;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final blocks = _parseMarkdownBlocks(markdownText);
    if (blocks.isEmpty) {
      return _MarkdownEmptyState(theme: theme);
    }

    return SelectionArea(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          for (var index = 0; index < blocks.length; index += 1)
            _buildBlock(theme, blocks[index], index),
        ],
      ),
    );
  }

  Widget _buildBlock(ThemeData theme, _MarkdownBlock block, int index) {
    return Padding(
      padding: EdgeInsets.only(top: index == 0 ? 0 : block.topSpacing),
      child: switch (block) {
        _HeadingBlock(:final level, :final text) => _MarkdownHeading(
            level: level,
            text: text,
            theme: theme,
          ),
        _ParagraphBlock(:final text) => _MarkdownRichText(
            text: text,
            theme: theme,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: _withAlpha(theme.colorScheme.onSurface, 0.86),
              height: 1.45,
            ),
          ),
        _ListBlock(:final ordered, :final items) => _MarkdownList(
            ordered: ordered,
            items: items,
            theme: theme,
          ),
        _QuoteBlock(:final text) => _MarkdownQuote(text: text, theme: theme),
        _CodeBlock(:final code) => _MarkdownCodeBlock(code: code, theme: theme),
        _RuleBlock() => _MarkdownRule(theme: theme),
      },
    );
  }
}

class AwareContentCodeViewer extends StatelessWidget {
  const AwareContentCodeViewer({
    required this.code,
    super.key,
    this.language,
    this.title,
  });

  final String code;
  final String? language;
  final String? title;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    final normalizedCode = code.trimRight();
    if (normalizedCode.trim().isEmpty) {
      return Text(
        'No code yet',
        style: theme.textTheme.bodyMedium?.copyWith(
          color: _withAlpha(colorScheme.onSurface, 0.52),
          fontStyle: FontStyle.italic,
        ),
      );
    }

    final titleText = title?.trim();
    final languageText = language?.trim();
    final lines = normalizedCode.split('\n');
    return SelectionArea(
      child: Container(
        width: double.infinity,
        decoration: BoxDecoration(
          color: _withAlpha(colorScheme.surfaceContainerHighest, 0.34),
          border:
              Border.all(color: _withAlpha(colorScheme.outlineVariant, 0.6)),
          borderRadius: BorderRadius.circular(7),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            if ((titleText != null && titleText.isNotEmpty) ||
                (languageText != null && languageText.isNotEmpty))
              _CodeViewerHeader(
                title: titleText,
                language: languageText,
                theme: theme,
              ),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 8,
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: <Widget>[
                    for (var index = 0; index < lines.length; index += 1)
                      _CodeLine(
                        number: index + 1,
                        text: lines[index],
                        theme: theme,
                      ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _CodeViewerHeader extends StatelessWidget {
  const _CodeViewerHeader({
    required this.title,
    required this.language,
    required this.theme,
  });

  final String? title;
  final String? language;
  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    final colorScheme = theme.colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: _withAlpha(colorScheme.surface, 0.46),
        border: Border(bottom: BorderSide(color: colorScheme.outlineVariant)),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: Row(
          children: <Widget>[
            Expanded(
              child: Text(
                title == null || title!.isEmpty ? 'Code' : title!,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.labelMedium?.copyWith(
                  color: colorScheme.onSurface,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            if (language != null && language!.isNotEmpty)
              Text(
                language!,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: _withAlpha(colorScheme.onSurfaceVariant, 0.82),
                  fontFamily: 'monospace',
                  fontWeight: FontWeight.w700,
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _CodeLine extends StatelessWidget {
  const _CodeLine({
    required this.number,
    required this.text,
    required this.theme,
  });

  final int number;
  final String text;
  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    final colorScheme = theme.colorScheme;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        SizedBox(
          width: 32,
          child: SelectableText(
            number.toString().padLeft(2),
            textAlign: TextAlign.right,
            style: theme.textTheme.bodySmall?.copyWith(
              color: _withAlpha(colorScheme.onSurfaceVariant, 0.58),
              fontFamily: 'monospace',
              height: 1.42,
            ),
          ),
        ),
        const SizedBox(width: 10),
        SelectableText(
          text.isEmpty ? ' ' : text,
          style: theme.textTheme.bodySmall?.copyWith(
            color: _withAlpha(colorScheme.onSurface, 0.9),
            fontFamily: 'monospace',
            height: 1.42,
          ),
        ),
      ],
    );
  }
}

class _MarkdownEmptyState extends StatelessWidget {
  const _MarkdownEmptyState({required this.theme});

  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    return Text(
      'No content yet',
      style: theme.textTheme.bodyMedium?.copyWith(
        color: _withAlpha(theme.colorScheme.onSurface, 0.52),
        fontStyle: FontStyle.italic,
      ),
    );
  }
}

class _MarkdownHeading extends StatelessWidget {
  const _MarkdownHeading({
    required this.level,
    required this.text,
    required this.theme,
  });

  final int level;
  final String text;
  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    final colorScheme = theme.colorScheme;
    final style = switch (level) {
      1 => theme.textTheme.titleMedium,
      2 => theme.textTheme.titleSmall,
      _ => theme.textTheme.labelLarge,
    };
    final accentWidth = level == 1 ? 3.0 : 2.0;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Container(
          width: accentWidth,
          height: level == 1 ? 19 : 15,
          margin: const EdgeInsets.only(top: 2, right: 8),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(accentWidth),
            color: _withAlpha(colorScheme.primary, level == 1 ? 0.82 : 0.62),
          ),
        ),
        Expanded(
          child: SelectableText(
            text,
            style: style?.copyWith(
              color: colorScheme.onSurface,
              fontWeight: FontWeight.w700,
              height: 1.18,
            ),
          ),
        ),
      ],
    );
  }
}

class _MarkdownList extends StatelessWidget {
  const _MarkdownList({
    required this.ordered,
    required this.items,
    required this.theme,
  });

  final bool ordered;
  final List<String> items;
  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    final colorScheme = theme.colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        for (var index = 0; index < items.length; index += 1)
          Padding(
            padding: EdgeInsets.only(bottom: index == items.length - 1 ? 0 : 6),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                SizedBox(
                  width: 24,
                  child: ordered
                      ? Text(
                          '${index + 1}.',
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: colorScheme.primary,
                            fontWeight: FontWeight.w700,
                          ),
                        )
                      : Padding(
                          padding: const EdgeInsets.only(top: 7),
                          child: Align(
                            alignment: Alignment.centerLeft,
                            child: Container(
                              width: 6,
                              height: 6,
                              decoration: BoxDecoration(
                                color: colorScheme.primary,
                                shape: BoxShape.circle,
                              ),
                            ),
                          ),
                        ),
                ),
                Expanded(
                  child: _MarkdownRichText(
                    text: items[index],
                    theme: theme,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: _withAlpha(colorScheme.onSurface, 0.86),
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}

class _MarkdownQuote extends StatelessWidget {
  const _MarkdownQuote({required this.text, required this.theme});

  final String text;
  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    final colorScheme = theme.colorScheme;
    return Container(
      decoration: BoxDecoration(
        border: Border(left: BorderSide(color: colorScheme.primary, width: 3)),
      ),
      padding: const EdgeInsets.only(left: 12),
      child: _MarkdownRichText(
        text: text,
        theme: theme,
        style: theme.textTheme.bodyMedium?.copyWith(
          color: _withAlpha(colorScheme.onSurface, 0.74),
          fontStyle: FontStyle.italic,
          height: 1.42,
        ),
      ),
    );
  }
}

class _MarkdownCodeBlock extends StatelessWidget {
  const _MarkdownCodeBlock({required this.code, required this.theme});

  final String code;
  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    final colorScheme = theme.colorScheme;
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: _withAlpha(colorScheme.surfaceContainerHighest, 0.42),
        border: Border.all(color: _withAlpha(colorScheme.outlineVariant, 0.56)),
        borderRadius: BorderRadius.circular(6),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      child: SelectableText(
        code.trimRight(),
        style: theme.textTheme.bodySmall?.copyWith(
          color: _withAlpha(colorScheme.onSurface, 0.86),
          fontFamily: 'monospace',
          height: 1.42,
        ),
      ),
    );
  }
}

class _MarkdownRule extends StatelessWidget {
  const _MarkdownRule({required this.theme});

  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    return Divider(
      height: 1,
      thickness: 1,
      color: _withAlpha(theme.colorScheme.outlineVariant, 0.45),
    );
  }
}

class _MarkdownRichText extends StatelessWidget {
  const _MarkdownRichText({
    required this.text,
    required this.theme,
    required this.style,
  });

  final String text;
  final ThemeData theme;
  final TextStyle? style;

  @override
  Widget build(BuildContext context) {
    return SelectableText.rich(
      TextSpan(style: style, children: _inlineSpans(text, theme, style)),
    );
  }
}

List<InlineSpan> _inlineSpans(
  String text,
  ThemeData theme,
  TextStyle? baseStyle,
) {
  final spans = <InlineSpan>[];
  final pattern = RegExp(r'(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)');
  var cursor = 0;
  for (final match in pattern.allMatches(text)) {
    if (match.start > cursor) {
      spans.add(TextSpan(text: text.substring(cursor, match.start)));
    }
    final token = match.group(0)!;
    if (token.startsWith('`')) {
      spans.add(
        TextSpan(
          text: token.substring(1, token.length - 1),
          style: baseStyle?.copyWith(
            color: theme.colorScheme.onSurface,
            fontFamily: 'monospace',
            backgroundColor: _withAlpha(
              theme.colorScheme.surfaceContainerHighest,
              0.56,
            ),
          ),
        ),
      );
    } else if (token.startsWith('**')) {
      spans.add(
        TextSpan(
          text: token.substring(2, token.length - 2),
          style: baseStyle?.copyWith(fontWeight: FontWeight.w700),
        ),
      );
    } else {
      spans.add(
        TextSpan(
          text: token.substring(1, token.length - 1),
          style: baseStyle?.copyWith(fontStyle: FontStyle.italic),
        ),
      );
    }
    cursor = match.end;
  }
  if (cursor < text.length) {
    spans.add(TextSpan(text: text.substring(cursor)));
  }
  return spans;
}

List<_MarkdownBlock> _parseMarkdownBlocks(String markdown) {
  final normalized = markdown.replaceAll('\r\n', '\n').trim();
  if (normalized.isEmpty) {
    return const <_MarkdownBlock>[];
  }

  final lines = normalized.split('\n');
  final blocks = <_MarkdownBlock>[];
  final paragraph = <String>[];
  final quote = <String>[];
  final listItems = <String>[];
  var listOrdered = false;
  final codeLines = <String>[];
  var inCodeBlock = false;

  void flushParagraph() {
    if (paragraph.isEmpty) {
      return;
    }
    blocks.add(_ParagraphBlock(paragraph.join(' ').trim()));
    paragraph.clear();
  }

  void flushQuote() {
    if (quote.isEmpty) {
      return;
    }
    blocks.add(_QuoteBlock(quote.join('\n').trim()));
    quote.clear();
  }

  void flushList() {
    if (listItems.isEmpty) {
      return;
    }
    blocks.add(
        _ListBlock(ordered: listOrdered, items: List<String>.of(listItems)));
    listItems.clear();
  }

  void flushLooseBlocks() {
    flushParagraph();
    flushQuote();
    flushList();
  }

  for (final rawLine in lines) {
    final line = rawLine.trimRight();
    final trimmed = line.trim();

    if (trimmed.startsWith('```')) {
      flushLooseBlocks();
      if (inCodeBlock) {
        blocks.add(_CodeBlock(codeLines.join('\n')));
        codeLines.clear();
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      continue;
    }
    if (inCodeBlock) {
      codeLines.add(rawLine);
      continue;
    }

    if (trimmed.isEmpty) {
      flushLooseBlocks();
      continue;
    }

    final headingMatch = RegExp(r'^(#{1,6})\s+(.+)$').firstMatch(trimmed);
    if (headingMatch != null) {
      flushLooseBlocks();
      blocks.add(
        _HeadingBlock(
          level: headingMatch.group(1)!.length,
          text: headingMatch.group(2)!.trim(),
        ),
      );
      continue;
    }

    if (RegExp(r'^-{3,}$').hasMatch(trimmed) ||
        RegExp(r'^\*{3,}$').hasMatch(trimmed)) {
      flushLooseBlocks();
      blocks.add(const _RuleBlock());
      continue;
    }

    final quoteMatch = RegExp(r'^>\s?(.*)$').firstMatch(trimmed);
    if (quoteMatch != null) {
      flushParagraph();
      flushList();
      quote.add(quoteMatch.group(1)!.trimRight());
      continue;
    }

    final bulletMatch = RegExp(r'^[-*]\s+(.+)$').firstMatch(trimmed);
    final orderedMatch = RegExp(r'^\d+[.)]\s+(.+)$').firstMatch(trimmed);
    if (bulletMatch != null || orderedMatch != null) {
      flushParagraph();
      flushQuote();
      final ordered = orderedMatch != null;
      if (listItems.isNotEmpty && listOrdered != ordered) {
        flushList();
      }
      listOrdered = ordered;
      listItems.add((bulletMatch ?? orderedMatch)!.group(1)!.trim());
      continue;
    }

    flushQuote();
    flushList();
    paragraph.add(trimmed);
  }

  if (inCodeBlock) {
    blocks.add(_CodeBlock(codeLines.join('\n')));
  }
  flushLooseBlocks();
  return blocks;
}

sealed class _MarkdownBlock {
  const _MarkdownBlock();

  double get topSpacing => 12;
}

class _HeadingBlock extends _MarkdownBlock {
  const _HeadingBlock({required this.level, required this.text});

  final int level;
  final String text;

  @override
  double get topSpacing => level == 1 ? 12 : 10;
}

class _ParagraphBlock extends _MarkdownBlock {
  const _ParagraphBlock(this.text);

  final String text;

  @override
  double get topSpacing => 6;
}

class _ListBlock extends _MarkdownBlock {
  const _ListBlock({required this.ordered, required this.items});

  final bool ordered;
  final List<String> items;
}

class _QuoteBlock extends _MarkdownBlock {
  const _QuoteBlock(this.text);

  final String text;
}

class _CodeBlock extends _MarkdownBlock {
  const _CodeBlock(this.code);

  final String code;
}

class _RuleBlock extends _MarkdownBlock {
  const _RuleBlock();
}

String _stringInput(Object? value) {
  if (value == null) {
    return '';
  }
  if (value is String) {
    return value;
  }
  return value.toString();
}

String? _trimmedStringInput(Object? value) {
  final text = _stringInput(value).trim();
  return text.isEmpty ? null : text;
}

Color _withAlpha(Color color, double alpha) {
  return color.withValues(alpha: alpha);
}
