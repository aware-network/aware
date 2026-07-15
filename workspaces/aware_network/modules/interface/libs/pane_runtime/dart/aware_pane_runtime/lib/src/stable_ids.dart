import 'package:uuid/uuid.dart';

final Uuid _uuid = Uuid();
final String _interfaceNamespace = _uuid.v5(
  Namespace.url.value,
  'aware://interface/v1',
);

UuidValue stablePanePackageId({required String name}) {
  final nameNorm = name.toLowerCase().trim();
  final seed = 'aware:pane_package:$nameNorm';
  return UuidValue.fromString(_uuid.v5(_interfaceNamespace, seed));
}
