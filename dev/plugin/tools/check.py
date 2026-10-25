"""可信 demo 的仓外冒烟检查；不启动 Web、进程插件或后台工作。"""

from __future__ import annotations

import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from more_brain_plugin_sdk import (
    EffectScope, resolve_manifest_order, validate_plugin_directory,
)


KIT = Path(__file__).resolve().parents[1]


class DemoContext:
    """只为本目录 demo 提供上下文替身，不代替真实 Host 生命周期测试。"""

    def __init__(self, plugin_id, providers):
        self.plugin_id = plugin_id
        self.generation_id = 1
        self.config = {}
        self.effects = EffectScope()
        self.providers = providers
        self.bindings = {}
        self.routes = {}

    def provide(self, key, provider):
        self.bindings[key] = provider

    def require(self, key):
        return self.providers[key]

    def contribute_web(self, method, path, handler):
        self.routes[(method, path)] = handler


async def check(require_client: bool) -> None:
    manifests = []
    roots = {}
    for root in sorted((KIT / "demos").iterdir()):
        if not (root / "plugin.toml").is_file():
            continue
        if root.name == "hello-react" and not (root / "dist/client.js").is_file() and not require_client:
            print("跳过 hello-react：尚无 dist/client.js；构建后用 --require-client 完整检查")
            continue
        manifest = validate_plugin_directory(root)
        manifests.append(manifest)
        roots[manifest.plugin_id] = root
    ordered = resolve_manifest_order(manifests)
    by_id = {manifest.plugin_id: manifest for manifest in manifests}
    providers = {}
    for plugin_id in ordered:
        manifest = by_id[plugin_id]
        root = roots[plugin_id]
        file, factory_name = manifest.entrypoint.split(":")
        spec = importlib.util.spec_from_file_location(plugin_id.replace("-", "_"), root / file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        factory = getattr(module, factory_name)
        plugin = factory()
        assert plugin is not factory(), f"{plugin_id} 工厂返回了同一个实例"
        assert plugin.id == plugin_id
        if manifest.isolation == "process":
            assert set(plugin.capabilities) == {f"{d.kind}/{d.name}/{d.api}" for d in manifest.provides}
            assert await plugin.capabilities["example.echo/demo-hello-process/1"].echo("检查") == {"text": "检查"}
            response = await plugin.web["GET status"](body="", headers={})
            assert response["status"] == 200 and json.loads(response["body"])["ok"]
            assert await plugin.health() is True
            await plugin.drain(1.0)
            await plugin.dispose()
            print(f"通过 {plugin_id}：映射和本地调用（未启动子进程）")
            continue
        context = DemoContext(plugin_id, providers)
        try:
            await plugin.prepare(context)
            assert await plugin.health() is True
            assert {str(key) for key in context.bindings} == {f"{d.kind}/{d.name}/{d.api}" for d in manifest.provides}
            providers.update(context.bindings)
            request = SimpleNamespace(query_params={"text": "检查"})
            if ("GET", "status") in context.routes:
                assert (await context.routes[("GET", "status")](request))["plugin_id"] == plugin_id
            result = await context.routes[("GET", "echo")](request)
            if plugin_id == "demo-echo-consumer":
                assert result["result"]["text"] == "检查"
            else:
                assert result["text"] == "检查"
        finally:
            assert await context.effects.dispose() == []
        print(f"通过 {plugin_id}：清单、工厂、prepare、health、Gateway handler 与能力")
    print(f"共检查 {len(manifests)} 个 demo；真实 Host 激活、前端挂载与 launcher 需另行验收")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-client", action="store_true", help="React 未构建时也必须报错")
    arguments = parser.parse_args()
    asyncio.run(check(arguments.require_client))
