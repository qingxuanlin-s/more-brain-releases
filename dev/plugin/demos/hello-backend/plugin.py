"""无需导入宿主 app 或 HTTP 框架的最小后端。"""

from typing import Any

from more_brain_plugin_sdk import CapabilityKey, PluginContext


ECHO = CapabilityKey("example.echo", "demo-hello-backend", 1)


class HelloBackend:
    id = "demo-hello-backend"

    async def prepare(self, context: PluginContext) -> None:
        message = context.config.get("message", "你好，More Brain 插件")
        if not isinstance(message, str) or len(message) > 200:
            raise ValueError("message 必须是最多 200 字的字符串")
        self.message = message
        context.provide(ECHO, self)

        async def status(request: Any) -> dict[str, Any]:
            return {"plugin_id": self.id, "generation_id": context.generation_id,
                    "message": self.message}

        async def echo(request: Any) -> dict[str, str]:
            return await self.echo(request.query_params.get("text", "hello"))

        context.contribute_web("GET", "status", status)
        context.contribute_web("GET", "echo", echo)

    async def echo(self, text: str) -> dict[str, str]:
        return {"text": text, "message": self.message}

    async def health(self) -> bool:
        return True


def create_plugin() -> HelloBackend:
    return HelloBackend()
