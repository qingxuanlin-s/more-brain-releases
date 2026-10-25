# Manifest 与接口参考

字段来自当前 SDK 和运行时实现。公开包中 Python 校验源位于 `sdk/python/src/more_brain_plugin_sdk/manifest.py`，浏览器类型位于 `sdk/client/index.ts`；Host 源码仓库的对应位置见 [加载原理](LOADING.md#10-源码导航)。

## 1. Manifest 完整示意

以下是字段说明，不是可直接安装的 demo：provides/requires 及所有客户端制品必须有实际实现。想立即开始请复制 demos。

```toml
[plugin]
id = "my-plugin"
name = "我的插件"
version = "0.1.0"
description = "插件用途"
entrypoint = "plugin.py:create_plugin"
host_api = ">=1.0,<2.0"
isolation = "in-process"
enabled_by_default = false

[[provides]]
kind = "example.echo"
name = "my-plugin"
api = 1
exclusive = true

[[requires]]
kind = "host.service"
name = "llm-models"
api = 1
optional = true

[client]
entry = "dist/client.js"
styles = []
sdk_api = ">=1.0,<2.0"
renderer = "react"
slots = ["global.navigation", "global.workspace"]
commands = ["my-plugin.refresh"]
requires = []
optional_requires = []
```

无 UI 时整个 `[client]` 省略，不要声明不存在的入口。没有服务依赖则省略对应数组表。Python 和客户端两个 requires 的语义不同。

| 字段 | 缺省 / 约束 |
| --- | --- |
| plugin.id | 必填；正则 `^[a-z][a-z0-9-]{0,62}$` |
| plugin.name | 缺省为 ID，不能为空 |
| plugin.version | 必填 SemVer，如 0.1.0；不是 SDK 或 Capability 版本 |
| plugin.description | 可选说明文本 |
| plugin.entrypoint | 默认 plugin.py:create_plugin；制品内 .py:对象，禁止绝对/上级路径 |
| plugin.host_api | 默认 >=1.0,<2.0；逗号连接比较范围，不支持任意 npm 的 ^/~ 写法 |
| plugin.isolation | 默认 in-process；另一值 process 使用受限映射协议 |
| plugin.enabled_by_default | 解析器默认 true；demo 明确 false，发布时应主动选择 |
| provides[].kind/name/api | Capability 键，api 正整数；actual provide 必须完全匹配 |
| provides[].exclusive | 可选，常用 true；不是授权声明；当前不支持同 key 多 provider 选择 |
| requires[].kind/name/api | 依赖的能力键，不是插件 ID |
| requires[].optional | 默认 false；true 仍应配 optional() 和缺失分支 |
| client.entry | dist/ 内 .js 文件，构建后必须存在 |
| client.styles | dist/ 内 .css 路径数组，默认 []；不要漏掉实际 CSS |
| client.sdk_api | 默认 >=1.0,<2.0；与后端 host_api 独立 |
| client.renderer | 当前仅 react |
| client.slots | 当前允许的 Slot，无重复；完整表见能力清单 |
| client.commands | 自己注册的命令 ID，无重复；建议 plugin-id.command |
| client.requires / optional_requires | 客户端插件 ID 数组，不能互相重复；不是 Capability |

解析器目前不严格拒绝所有未知键，所以不要用“清单校验通过”证明一个自行增加的字段生效。例如 `runtime="node"` 不会带来 Node 后端支持。`[ui] icon` 是部分旧导航读取 SVG 的附加元数据，不是新的 React 挂载系统。

## 2. Python 结构协议

```python
from more_brain_plugin_sdk import (
    CapabilityKey, PluginContext, RuntimePlugin, LiveEvent, EffectScope,
    PluginUnavailable, PluginGenerationMismatch,
    parse_manifest, parse_manifest_toml, resolve_manifest_order,
    validate_plugin_directory,
)
```

不要从 Host 的旧兼容路径导入通用 SDK 类型。PluginContext/RuntimePlugin 是用于类型注解的 Protocol，不需要实例化或继承。

| 生命周期 | 签名 / 含义 |
| --- | --- |
| factory | 同步 `def create_plugin()`；每次返回新实例 |
| prepare | `async def prepare(self, context: PluginContext) -> None` |
| health | `async def health(self) -> bool`；候选健康检查 |
| drain，可选 | `async def drain(self, deadline: float)`；停止内部新工作，遵守宿主给定时间预算 |
| dispose，可选 | `async def dispose(self)`；释放尚未由 effects 管理的资源 |

进程内 Context 速查：

```python
context.plugin_id                    # str
context.generation_id                # int；传浏览器建议转字符串
context.is_active                    # bool，只读
context.config                       # Mapping[str, Any]，当前 Row 配置
context.provide(key, provider)       # None
context.require(key)                 # provider，缺失抛 PluginUnavailable
context.optional(key)                # provider | None
context.contribute_web("GET", "status", handler)
context.contribute_asset("hello.txt", "你好", "text/plain; charset=utf-8")
url = context.asset_url("hello.txt")
context.contribute_ui(
    contribution_id="my-plugin.nav", view="my-plugin", label="我的插件",
    view_path="/api/plugins/my-plugin/gateway/view", root_id="my-plugin-root", order=500,
)
context.effects.add("client", client.aclose)
context.spawn_task("poll", poll())
context.subscribe("my-domain.changed", on_change)
context.notify_resource_changed("items")
```

上面 handler/client/poll/on_change 是插件提供的实现，不是 SDK 内置。支持 Web methods：GET / POST / PUT / PATCH / DELETE。handler 接收 Request，可同步或异步返回 dict / Response；精确 path，写入需主动验证 JSON/body/query 和权限。单个普通 asset 最大 5 MiB。

`EffectScope.add(name, disposer)` 的 disposer 无参，可同步/异步。`dispose()` 幂等，逆序执行并返回错误列表。需要清理的资源应在获取后立即登记。

## 3. 浏览器结构协议

```typescript
import type { ClientPlugin, PluginContext, PluginPanelProps } from "@more-brain/plugin-sdk";
```

| 对象 | 主要签名 |
| --- | --- |
| ClientPlugin | activate(context): void 或 Promise<void>；default export |
| PluginPanelProps | context、visible，另有可选 presentation、singleColumn |
| context | pluginId: string，generationId: string 或兼容旧版 number |
| api | request<T>(path, RequestInit & {signal?}): Promise<T> |
| ui | register(UiContribution): () => void |
| commands | register<Request,Result>(id,handler): () => void；execute(id,request,{signal?}): Promise<Result> |
| command handler | (request, {signal: AbortSignal}) => Result 或 Promise<Result> |
| services | provide<T>(key:string,service:T): () => void；get<T>(key): T 或 undefined |
| events | emit(event)；subscribe(type 或 scope,handler): () => void；可选 isConnected() |
| resources | read<T>(key,load:(signal)=>Promise<T>): Promise<T>；invalidate(key) |
| scope | signal；add(cleanup): () => void；dispose(): Promise<void>（通常由宿主调用） |
| dock | activate(id)、close(id) |
| recovery | get<T>(contextKey,schemaVersion)、set<T>(contextKey,schemaVersion,value)、clear(contextKey) |

`scope.add()` 返回的是取消注册该 cleanup 的函数，不能假定调用它会立即执行 cleanup。具体语义以当前 SDK/运行时实现为准。

资源订阅例子，放在 activate 或带正确 cleanup 的 effect 中：

```typescript
const unsubscribe = context.events.subscribe({ pluginResources: [{
  plugin_id: context.pluginId,
  generation_id: String(context.generationId),
  resource_id: "items",
}] }, () => {
  // 标记缓存失效，并通过自己的 Gateway 重新加载。
  context.resources.invalidate(`${context.pluginId}:items`);
});
context.scope.add(unsubscribe);
```

API 错误 code 包括 `plugin/generation-mismatch`、`plugin/unavailable`、`plugin/error`；命令还有 unavailable / invalid-argument / forbidden / cancelled。应读取 CommandError.code 并显示可恢复状态，不按错误字符串猜控制流。

## 4. 管理接口

这些是宿主管理 API，不是插件任意远程管理其他插件的授权。下面路径基于已有 Host。

| 方法与路径 | 请求 / 用途 |
| --- | --- |
| GET /api/plugins | 状态、发现错误、代际、Registry 诊断 |
| GET /api/plugin-contributions | 前端客户端描述与贡献 |
| POST /api/plugins/install | multipart `file` 为 ZIP；首次安装或同 ID 更新 |
| POST /api/plugins/{id}/enabled | form `enabled`；兼容开关，有 active Profile 时不能隐式改它 |
| GET /api/plugins/{id}/config | 私有目录配置，不等同 Row.config |
| PATCH /api/plugins/{id}/config | JSON 配置更新，需插件自己明确读取和优先级 |
| POST /api/plugins/reload-changed | 检查目录变化 |
| POST /api/plugins/reload | 强制重建活动组合 |
| DELETE /api/plugins/{id} | 卸载第三方目录插件，排空/备份、保留数据 |
| GET /api/plugin-profiles | 读取现有部署组合 |
| PUT /api/plugin-profiles | 保存 deployment JSON；保留已有 Bundle/Profile/Row |
| POST /api/plugin-profiles/{id}/activate | 显式激活 Profile；realm_key 默认 host |
| GET /api/plugin-profiles/revisions | 部署修订记录 |
| GET /api/plugin-operations?realm_key=host&limit=50 | 组合操作记录 |

Profile 最小结构示意：

```json
{
  "bundles": [{"bundle": {"id": "development", "version": 1}, "rows": [
    {"id": "service.my-plugin", "plugin": "my-plugin", "version": "0.1.0",
     "enabled": true, "isolation": "in-process", "config": {"message": "你好"}}
  ]}],
  "profiles": [{"profile": {"id": "development", "bundles": ["development"]}, "patch": []}],
  "active_profile_id": "development"
}
```

这只说明 schema，不是覆盖现有部署的命令。应先读取、保留现有内容后追加自己的 Row；process Row 的 isolation 也要与 Manifest 一致。

## 5. 开发工具

| 命令 | 实际执行什么 |
| --- | --- |
| python -m more_brain_plugin_sdk validate DIR | 只读静态检查，不 import 插件 |
| python tools/check.py | import 并检查本资料包的可信 demo，React 未构建可跳过 |
| python tools/check.py --require-client | 所有 demo 必须已具备声明制品；依赖顺序/工厂/prepare/health/handler/映射冒烟检查 |
| python tools/pack.py DIR [--output DIR] [--include RELPATH] | 白名单制品 ZIP、解压再静态验证、生成 SHA256；不安装依赖、不启用插件 |
| python tools/export.py --output DIR | 仅 Host 源码环境：导出资料 + 两种真实 SDK，不推送 Git |

工具不代替真实 Host 的 Registry、Gateway、React 挂载、子进程 launcher 和目标桌面版验收。默认 pack 包含 plugin.toml / plugin.py / dist / src / templates / assets / vendor / README.md / LICENSE / requirements-vendor.txt；非默认入口或其他运行文件显式 --include。
