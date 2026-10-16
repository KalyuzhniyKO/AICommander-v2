"""Server-owned opt-in runtime configuration. No credentials or model calls."""
from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class HermesConfig:
    enabled: bool = False
    python: str = field(default='', repr=False)
    source: str = field(default='', repr=False)
    model: str = ''
    expected_commit: str = ''
    timeout_seconds: int = 90
    max_output_tokens: int = 768

    def __post_init__(self):
        if (type(self.enabled) is not bool or type(self.timeout_seconds) is not int
                or not 1 <= self.timeout_seconds <= 120 or type(self.max_output_tokens) is not int
                or not 64 <= self.max_output_tokens <= 2048):
            raise ValueError('Invalid Hermes configuration')

    @classmethod
    def from_env(cls):
        try:
            enabled = os.environ.get('HERMES_ENABLED','false').lower()
            if enabled not in {'true','false'}:
                raise ValueError
            return cls(enabled=enabled=='true', python=os.environ.get('HERMES_PYTHON',''),
                       source=os.environ.get('HERMES_SOURCE',''), model=os.environ.get('HERMES_MODEL',''),
                       expected_commit=os.environ.get('HERMES_EXPECTED_COMMIT',''),
                       timeout_seconds=int(os.environ.get('HERMES_TIMEOUT_SECONDS','90')),
                       max_output_tokens=int(os.environ.get('HERMES_MAX_OUTPUT_TOKENS','768')))
        except (TypeError,ValueError):
            raise ValueError('Invalid Hermes configuration') from None
