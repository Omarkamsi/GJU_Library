"""Whitelist of accepted bucket strings — never interpolate user input into SQL."""
_ALLOWED = {"10s", "30s", "1m", "5m", "15m", "1h", "6h", "1d"}

def safe_bucket(b: str) -> str:
    if b not in _ALLOWED:
        raise ValueError(f"bucket must be one of {sorted(_ALLOWED)}")
    return b
