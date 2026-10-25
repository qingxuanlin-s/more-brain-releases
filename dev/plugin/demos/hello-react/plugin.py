"""React 通过相对 Gateway 路径读取此后端。"""

from typing import Any

from more_brain_plugin_sdk import PluginContext


class HelloReact:
    id = "demo-hello-react"

    async def prepare(self, context: PluginContext) -> None:
        async def echo(request: Any) -> dict[str, Any]:
            return {"text": request.query_params.get("text", "hello"),
                    "generation_id": str(context.generation_id)}

        context.contribute_web("GET", "echo", echo)

    async def health(self) -> bool:
        return True


def create_plugin() -> HelloReact:
    return HelloReact()
