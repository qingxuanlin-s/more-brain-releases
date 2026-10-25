"""Generation 所有副作用的可逆生命周期。"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Callable
from typing import Any


class EffectScope:
    """按注册的反序释放资源；dispose 幂等。"""

    def __init__(self) -> None:
        self._disposers: list[tuple[str, Callable[[], Any]]] = []
        self._disposed = False

    @property
    def disposed(self) -> bool:
        return self._disposed

    @property
    def size(self) -> int:
        return len(self._disposers)

    def add(self, name: str, disposer: Callable[[], Any]) -> None:
        if self._disposed:
            raise RuntimeError("EffectScope 已释放")
        if not name:
            raise ValueError("Effect 必须有名称")
        self._disposers.append((name, disposer))

    def add_task(self, name: str, task: asyncio.Task[Any]) -> None:
        """把后台任务绑定到当前 generation；释放时取消并回收它。"""
        async def dispose_task() -> None:
            if not task.done():
                task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.add(f"task:{name}", dispose_task)

    async def dispose(self) -> list[BaseException]:
        if self._disposed:
            return []
        self._disposed = True
        errors: list[BaseException] = []
        while self._disposers:
            _, disposer = self._disposers.pop()
            try:
                result = disposer()
                if inspect.isawaitable(result):
                    await result
            except BaseException as exc:  # cleanup 必须尽量完成其余资源。
                errors.append(exc)
        return errors
