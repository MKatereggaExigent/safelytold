from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SanitisedDerivative:
    bytes_value: bytes
    media_type: str
    transformation_log: list[str]


class ContentSanitiser(Protocol):
    async def sanitise(self, data: bytes, media_type: str) -> SanitisedDerivative: ...


class DisabledSanitiser:
    async def sanitise(self, data: bytes, media_type: str) -> SanitisedDerivative:
        raise RuntimeError('Configure a sandboxed metadata-removal/content-disarm provider before enabling sanitisation')
