"""Best-effort masking of configured literals and documented text patterns.

No file/credential discovery. This is not arbitrary-secret detection or DLP.
"""
import os
import re


def redact(value):
    if isinstance(value, dict):
        # Preserve every value if sanitizing a key collides with another key.
        # Reserve unchanged names first so a secret cannot overwrite real fields.
        names = {key: redact(key) if isinstance(key, str) else key for key in value}
        occupied = {key for key, name in names.items() if key == name}
        result = {}
        for key, item in value.items():
            name = names[key]
            if name != key:
                candidate, suffix = name, 2
                while candidate in occupied:
                    candidate = f"{name}_{suffix}"
                    suffix += 1
                name = candidate
                occupied.add(name)
            result[name] = redact(item)
        return result
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    if not isinstance(value, str):
        return value
    secrets = {os.environ.get(name, "") for name in ("OPENROUTER_API_KEY", "OMNIROUTE_API_KEY", "PANEL_PASSWORD")}
    # A shorter configured credential must not partially replace a longer one
    # before the complete value can be masked.
    for secret in sorted(secrets - {""}, key=len, reverse=True):
        value = value.replace(secret, "[REDACTED]")
    value = re.sub(r"(?i)\b(Bearer\s+)[^\s\"']+", r"\1[REDACTED]", value)
    value = re.sub(r"\bsk-[\w-]+", "[REDACTED]", value)
    return re.sub(
        r'''(?ix)(["']?\b(?:[a-z_]*api_key|[a-z_]*token|password|secret|client_secret|authorization)\b["']?\s*[=:]\s*)(?:"[^"\n]*"|'[^'\n]*'|[^\s,;}]+)''',
        r"\1[REDACTED]", value,
    )


