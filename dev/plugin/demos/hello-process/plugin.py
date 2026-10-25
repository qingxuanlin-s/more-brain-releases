"""v1 子进程映射协议：没有 prepare(context)，stdout 不输出日志。"""

import json


class EchoService:
    async def echo(self, text: str) -> dict[str, str]:
        return {"text": text}


class HelloProcess:
    id = "demo-hello-process"

    def __init__(self) -> None:
        self.capabilities = {"example.echo/demo-hello-process/1": EchoService()}
        self.web = {"GET status": self.status}
        self.assets = {}
        self.ui = []

    async def status(self, body: str, headers: dict) -> dict:
        return {"status": 200, "content_type": "application/json",
                "body": json.dumps({"ok": True, "plugin_id": self.id})}

    async def health(self) -> bool:
        return True

    async def drain(self, deadline: float) -> None:
        pass

    async def dispose(self) -> None:
        pass


def create_plugin() -> HelloProcess:
    return HelloProcess()
