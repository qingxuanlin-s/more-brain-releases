"""依赖只通过契约解析，不 import 另一个插件。"""

from typing import Any

from more_brain_plugin_sdk import CapabilityKey, PluginContext


class EchoConsumer:
    id = "demo-echo-consumer"

    async def prepare(self, context: PluginContext) -> None:
        provider = context.require(CapabilityKey("example.echo", "demo-hello-backend", 1))

        async def echo(request: Any) -> dict[str, Any]:
            result = await provider.echo(request.query_params.get("text", "来自另一个插件"))
            return {"consumer": self.id, "result": result}

        context.contribute_web("GET", "echo", echo)

    async def health(self) -> bool:
        return True


def create_plugin() -> EchoConsumer:
    return EchoConsumer()
