import base64
from os import urandom


def _normalize_b64(value: str) -> str:
    raw = value.strip()
    padding = (-len(raw)) % 4
    if padding:
        raw += "=" * padding
    return raw


def _decode_key_material(value: str) -> bytes:
    raw = value.strip()
    if not raw:
        raise ValueError("public_key cannot be empty")

    # Prefix support: ed25519:<b64|hex>, base64:<...>, b64:<...>, hex:<...>
    if ":" in raw:
        prefix, rest = raw.split(":", 1)
        prefix = prefix.strip().lower()
        rest = rest.strip()
        if prefix in {"ed25519", "base64", "b64"}:
            raw = rest
        elif prefix == "hex":
            try:
                return bytes.fromhex(rest)
            except ValueError as exc:
                raise ValueError("Invalid hex public_key material") from exc

    # Hex (common for Ed25519 keys)
    try:
        return bytes.fromhex(raw)
    except ValueError:
        pass

    # Base64 / URL-safe base64
    normalized = _normalize_b64(raw)
    for decoder in (base64.b64decode, base64.urlsafe_b64decode):
        try:
            return decoder(normalized)
        except Exception:
            continue

    raise ValueError("Unsupported public_key encoding; expected hex or base64")


def canonicalize_ed25519_public_key(public_key: str) -> tuple[str, bytes]:
    key_bytes = _decode_key_material(public_key)
    if len(key_bytes) != 32:
        raise ValueError(f"Invalid Ed25519 public key length: {len(key_bytes)} (expected 32)")
    return f"ed25519:{key_bytes.hex()}", key_bytes


def generate_ed25519_public_key() -> str:
    key_bytes = urandom(32)
    return f"ed25519:{key_bytes.hex()}"
