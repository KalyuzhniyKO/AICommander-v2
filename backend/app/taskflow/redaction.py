"""Best-effort redaction for the documented token/assignment patterns."""
import re


def redact(text: str) -> str:
    text = re.sub(r"(?i)\bBearer\s+[^\s,;]+", "Bearer [REDACTED]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[REDACTED]", text)
    return re.sub(
        r'''(?ix)(["']?\b(?:[a-z_]*api_key|[a-z_]*token|password|secret|client_secret|authorization)\b["']?\s*[=:]\s*)(?:"[^"\n]*"|'[^'\n]*'|[^\s,;}]+)''',
        r"\1[REDACTED]", text,
    )
