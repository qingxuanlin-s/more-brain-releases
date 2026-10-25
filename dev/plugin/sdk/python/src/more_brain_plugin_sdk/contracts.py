"""仅描述宿主注入的上下文，不提供另一套插件运行时。"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Protocol, TypeVar

from .capabilities import CapabilityKey
from .effects import EffectScope
from .events import LiveEvent


T = TypeVar("T")


class PluginContext(Protocol):
    """进程内插件在 prepare 阶段使用；实例由 Host 创建。"""

    @property
    def plugin_id(self) -> str: ...

    @property
    def generation_id(self) -> int: ...

    @property
    def is_active(self) -> bool: ...

    @property
    def config(self) -> Mapping[str, Any]: ...

    @property
    def effects(self) -> EffectScope: ...

    def provide(self, key: CapabilityKey, provider: Any) -> None: ...
    def require(self, key: CapabilityKey) -> Any: ...
    def optional(self, key: CapabilityKey) -> Any | None: ...

    def contribute_web(self, method: str, path: str, handler: Callable[[Any], Any]) -> None: ...
    def contribute_asset(self, path: str, content: bytes | str, content_type: str) -> None: ...
    def asset_url(self, path: str) -> str: ...

    def contribute_ui(
        self, *, contribution_id: str, view: str, label: str,
        view_path: str, root_id: str | None = None, order: int = 500,
    ) -> None: ...

    def spawn_task(self, name: str, awaitable: Awaitable[T]) -> asyncio.Task[T]: ...
    def subscribe(self, event_type: str, handler: Callable[[LiveEvent], Any]) -> None: ...
    def notify_resource_changed(self, resource_id: str) -> None: ...


class RuntimePlugin(Protocol):
    """插件工厂返回的结构协议；无需继承，也无需装饰器。"""

    id: str

    async def prepare(self, context: PluginContext) -> None: ...
    async def health(self) -> bool: ...
