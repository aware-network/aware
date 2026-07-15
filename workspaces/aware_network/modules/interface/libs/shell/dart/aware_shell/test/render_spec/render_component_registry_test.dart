import 'package:aware_shell/aware_shell.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('resolves registered render components by canonical ref', () {
    final registry =
        RenderComponentRegistry.fromRegistrations(<RenderComponentRegistration>[
          RenderComponentRegistration(
            componentRef: 'aware.content.markdown_viewer',
            builder: (_, __) => const SizedBox.shrink(),
          ),
        ]);

    expect(registry.supports('aware.content.markdown_viewer'), isTrue);
    expect(registry.supports(' aware.content.markdown_viewer '), isTrue);
    expect(registry.supports('aware.content.code_editor'), isFalse);
    expect(
      registry.resolve('aware.content.markdown_viewer')?.componentRef,
      'aware.content.markdown_viewer',
    );
  });

  test('rejects duplicate component refs in one registry', () {
    expect(
      () => RenderComponentRegistry.fromRegistrations(
        <RenderComponentRegistration>[
          RenderComponentRegistration(
            componentRef: 'aware.content.markdown_viewer',
            builder: (_, __) => const SizedBox.shrink(),
          ),
          RenderComponentRegistration(
            componentRef: ' aware.content.markdown_viewer ',
            builder: (_, __) => const SizedBox.shrink(),
          ),
        ],
      ),
      throwsArgumentError,
    );
  });

  test('builder freezes registrations into immutable registry', () {
    final builder = RenderComponentRegistryBuilder()
      ..register(
        RenderComponentRegistration(
          componentRef: 'aware.content.markdown_viewer',
          builder: (_, __) => const SizedBox.shrink(),
        ),
      );

    final registry = builder.build();
    builder.register(
      RenderComponentRegistration(
        componentRef: 'aware.content.code_editor',
        builder: (_, __) => const SizedBox.shrink(),
      ),
    );

    expect(registry.supports('aware.content.markdown_viewer'), isTrue);
    expect(registry.supports('aware.content.code_editor'), isFalse);
    expect(builder.supports('aware.content.code_editor'), isTrue);
  });

  test('builder rejects duplicate component refs', () {
    final builder = RenderComponentRegistryBuilder()
      ..register(
        RenderComponentRegistration(
          componentRef: 'aware.content.markdown_viewer',
          builder: (_, __) => const SizedBox.shrink(),
        ),
      );

    expect(
      () => builder.register(
        RenderComponentRegistration(
          componentRef: ' aware.content.markdown_viewer ',
          builder: (_, __) => const SizedBox.shrink(),
        ),
      ),
      throwsArgumentError,
    );
  });
}
