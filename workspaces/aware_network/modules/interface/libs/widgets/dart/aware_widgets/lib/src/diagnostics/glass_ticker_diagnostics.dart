/// Lightweight runtime counters for glass-related tickers.
///
/// These are intended for debug/profiling (e.g. `RefreshAudit`) to quickly
/// attribute unexpected frame production to common glass infrastructure:
/// - pointer/hover parallax tickers in `KinematicGlass`
/// - layout physics tickers in `GlassLayout`
///
/// The counters are best-effort and should never throw.
class GlassTickerDiagnostics {
  static int _activeKinematicPointerTickers = 0;
  static int _activeKinematicBreathingTickers = 0;
  static int _activeKinematicSettlingAnimations = 0;
  static int _activeGlassLayoutTickers = 0;

  static int get activeKinematicPointerTickers =>
      _activeKinematicPointerTickers;
  static int get activeKinematicBreathingTickers =>
      _activeKinematicBreathingTickers;
  static int get activeKinematicSettlingAnimations =>
      _activeKinematicSettlingAnimations;
  static int get activeGlassLayoutTickers => _activeGlassLayoutTickers;

  static void onKinematicPointerTickerStarted() {
    _activeKinematicPointerTickers += 1;
  }

  static void onKinematicPointerTickerStopped() {
    _activeKinematicPointerTickers = (_activeKinematicPointerTickers - 1).clamp(
      0,
      1 << 30,
    );
  }

  static void onKinematicBreathingTickerStarted() {
    _activeKinematicBreathingTickers += 1;
  }

  static void onKinematicBreathingTickerStopped() {
    _activeKinematicBreathingTickers = (_activeKinematicBreathingTickers - 1)
        .clamp(0, 1 << 30);
  }

  static void onKinematicSettlingStarted() {
    _activeKinematicSettlingAnimations += 1;
  }

  static void onKinematicSettlingStopped() {
    _activeKinematicSettlingAnimations =
        (_activeKinematicSettlingAnimations - 1).clamp(0, 1 << 30);
  }

  static void onGlassLayoutTickerStarted() {
    _activeGlassLayoutTickers += 1;
  }

  static void onGlassLayoutTickerStopped() {
    _activeGlassLayoutTickers = (_activeGlassLayoutTickers - 1).clamp(
      0,
      1 << 30,
    );
  }
}
