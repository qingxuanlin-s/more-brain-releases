"""宿主与插件共用的能力身份；不能在插件内复制该类型。"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CapabilityKey:
    kind: str
    name: str
    api_major: int = 1

    def __post_init__(self) -> None:
        if not self.kind or not self.name or self.api_major < 1:
            raise ValueError("CapabilityKey 必须包含 kind、name 和正 api_major")

    def __str__(self) -> str:
        return f"{self.kind}/{self.name}/{self.api_major}"


