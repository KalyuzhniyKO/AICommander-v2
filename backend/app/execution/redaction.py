import re


class Redactor:
    """Best effort patterns plus explicit literals, not arbitrary-secret discovery."""

    def __init__(self, secrets=()):
        self.secrets = tuple(sorted({s for s in secrets if s}, key=len, reverse=True))
        if any(len(s) > 4096 for s in self.secrets):
            raise ValueError("Redaction literals must be at most 4096 characters")

    def __call__(self, value: str) -> str:
        for secret in self.secrets:
            value = value.replace(secret, "[REDACTED]")
        value = re.sub(r"(?i)\bBearer\s+[^\s\"']+", "Bearer [REDACTED]", value)
        value = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[REDACTED]", value)
        return re.sub(
            r'''(?ix)(["']?[\w-]*(?:api[_-]?key|token|password|secret|authorization)["']?\s*[:=]\s*)("[^"\r\n]*"|'[^'\r\n]*'|[^\s,;}]+)''',
            lambda match: match[1] + "[REDACTED]",
            value,
        )
