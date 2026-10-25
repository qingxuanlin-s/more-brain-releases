"""generation-aware 的进程内 LiveEvent。"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class LiveEvent:
    type: str
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.type or not self.type.replace(".", "").replace("-", "").isalnum():
            raise ValueError("LiveEvent type 必须是安全标识")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
