# 插件开发手册

本文命令默认从 `dev/plugin/` 执行。Python 使用已安装 SDK 的 Python 3.11+ 虚拟环境；`python` 指该环境解释器。资料适用版本见 [README](README.md)。

## 1. 从零开始

### 1.1 选择模板

| 需求 | 复制目录 | 最后得到什么 |
| --- | --- | --- |
| 自定义工具、接口、业务逻辑 | `demos/hello-backend` | Python + JSON Gateway + Capability |
| 增加主导航和 React 页面 | `demos/hello-react` | Python Gateway + 浏览器 React ESM |
| 依赖另一个插件提供的服务 | `demos/echo-consumer` | `requires` + `context.require()` |
| 只需 JSON / 文本且想放到子进程 | `demos/hello-process` | 当前受限的映射协议 |

例如：

```bash
cp -R demos/hello-backend /tmp/my-plugin
```

改永久 ID：Manifest `plugin.id`、Python `id`、能力 name、客户端 contribution/command/view ID 和相关 URL。ID 如 `my-plugin`，小写字母开头，可包含数字和短横线，最长 63 字符。目录名不是插件身份。发布后不要随意修改 ID，否则是另一个插件，旧配置和数据不会自动迁移。

### 1.2 安装开发 SDK

公开开发包包含 `sdk/python`：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e sdk/python
source .venv/bin/activate
python -m more_brain_plugin_sdk validate /tmp/my-plugin
```

在 Host 源码仓库时，SDK 在仓库根的 `sdk/python`，从 `dev/plugin` 应使用 `../../sdk/python`。也可以先在仓库根安装。SDK 只依赖标准库；其构建工具由 pip 在安装时准备。离线环境需事先准备 SDK wheel 及所需构建依赖。SDK 尚未上传 PyPI，不要假定直接按包名安装可用。

静态校验不执行插件代码，检查 Manifest、Host / Client SDK 范围、入口语法、文件和 dist 存在性。它不证明依赖可导入、工厂正确、业务正确、健康检查通过或目标 Host 支持全部特性。

### 1.3 修改业务

保留 `create_plugin()` 同步工厂，每次返回新实例。实现普通类即可，无需继承基类。

```python
from typing import Any
from more_brain_plugin_sdk import PluginContext

class MyPlugin:
    id = "my-plugin"

    async def prepare(self, context: PluginContext) -> None:
        async def status(request: Any):
            return {"ok": True, "generation_id": context.generation_id}
        context.contribute_web("GET", "status", status)

    async def health(self) -> bool:
        return True

def create_plugin() -> MyPlugin:
    return MyPlugin()
```

Manifest 必须同步改为 `id="my-plugin"`。如果从 echo demo 改成上面的代码，需要删除不再使用的 `[[provides]]`：实际 provide 集必须与声明完全一致。状态请求最终访问 `/api/plugins/my-plugin/gateway/status`，不是 `/status`。

import 和构造函数只做本地初始化。不要在此打开连接、启动线程、进程、watcher 或 asyncio task：宿主在发现时就可能 import 并调用工厂，插件未启用也可能发生这些步骤。

### 1.4 打包与导入

```bash
python tools/pack.py /tmp/my-plugin
```

生成 `out/my-plugin-0.1.0.zip` 及 `.zip.sha256`。ZIP 根有 `plugin.toml` 和入口；完整 React dist、实现包、模板和静态资源按需一并发布。

在已运行的 More Brain「设置 → 插件」导入 ZIP，再启用。默认停用是 demo 的显式配置。**导入成功、已发现、已启用、ACTIVE 是不同阶段。** 有 active Profile 时，编辑其 Bundle/Row 并显式激活，不能只调用兼容开关。

如果还没有 Host 运行，应先征得启动许可并说明命令和端口；不需要为写插件专门启动第二个服务。客户端 dist 在构建期生成，运行时不启动 Vite。

### 1.5 看结果

仅访问已有 Host，地址换成实际地址：

```bash
curl -fsS http://127.0.0.1:8000/api/plugins
curl -fsS http://127.0.0.1:8000/api/plugins/my-plugin/gateway/status
```

应看到插件 ACTIVE 和接口 `{ok:true,generation_id:...}`。后端插件不一定有 UI；需要界面时选择 React demo。

## 2. 为插件加 React 界面

复制 `hello-react`。先构建再 validate / pack；当前不支持省略 Python 入口，可以让 `prepare` 为空，但 Manifest 仍须指向 Python 文件。

在公开包里，先为 SDK 源码提供其 React 类型依赖：

```bash
cd sdk/client
npm install
cd ../../demos/hello-react/client
npm install
npm run typecheck
npm run build
cd ../../..
python tools/check.py --require-client
python tools/pack.py demos/hello-react
```

在 Host 源码中，客户端 SDK 的类型依赖由 `frontend/node_modules` 提供；先在 frontend 安装其依赖，然后直接进入 demo 的 client 执行安装和构建。导出工具会调整 `client/sdk.d.ts`，让公开包引用自己的 SDK。把 demo 复制到其他地方后也需修正这个相对路径。

客户端入口 `export default { activate(context) { ... } }`。`activate` 注册贡献，不直接访问宿主私有 DOM、不自己 `createRoot()`。新主页面通常注册同一个 `viewId` 的 navigation 和 workspace；Manifest 同时声明 `global.navigation` 和 `global.workspace`。

客户端与后端用 `context.api.request("echo?text=...")` 通信，自动构造当前插件 Gateway URL 并携带 `X-Plugin-Generation`。不要硬编码 generation，不将后端 Provider 对象传入前端。需要写入 JSON 时显式设置 `method`、`Content-Type` 和 `body`；不要把 GET 当作修改接口。

组件 effect 使用 AbortController，组件隐藏/卸载时终止请求；也响应 `context.scope.signal`。`visible=false` 不代表 React 组件已经 unmount。命令名必须在 Manifest 的 `commands` 中声明，contribution ID 必须以 `pluginId.` 开头。

构建保持 `react`、`react/*`、`react-dom`、`react-dom/*`、`@more-brain/plugin-sdk` 为 external，由 Host import map 提供单例。业务依赖可在构建期打包。不要把开发机的 `node_modules` 放入 ZIP。增加 CSS 后将实际输出文件写进 `client.styles`，选择插件前缀作用域，使用宿主主题变量。新的插件不需要改 Host Vite 插件 ID 白名单。

## 3. 能力协作和专用扩展

### 3.1 自定义 Capability

Capability 的永久契约键是 `kind/name/api`，例如 `example.echo/demo-hello-backend/1`。`plugin.version` 是制品版本，`api` 是这个服务协议的主版本，二者独立。

Provider 在 Manifest 声明 `[[provides]]`，prepare 中调用 `context.provide(CapabilityKey(...), service)`。Consumer 在 Manifest 声明 `[[requires]]`，prepare 中 `context.require(key)`；可选依赖同时使用 `optional=true` 和 `context.optional(key)`。不要 import 另一个插件的实现模块。

运行流程可直接比较 `hello-backend` 和 `echo-consumer`。维护一份契约说明：方法名、同步/异步、参数、返回值、错误、取消和版本升级规则。Registry 按 key 找对象，不会自动检查每个业务方法的类型。

一般选择唯一 provider。当前组合运行时仍拒绝重复 key；`exclusive=false` 不等于获得一套可选择的多 provider 列表。兼容修改提升插件小版本，不兼容方法变更引入新的 Capability api，并迁移消费者。

### 3.2 专用业务契约

- 模型供应商：`llm.provider/<provider-id>/1`，需实现 Host 的 LLM Provider definition 与流式接口；仅注册同名 key 不够。
- Agent 执行引擎：`runtime.adapter/<runtime-key>/2`，需实现对应业务命令、事件和取消协议；不要照旧 api=1 教程接入。
- MCP：`host.mcp/<plugin-id>/1`，Provider 提供 ASGI `app`，Host 挂载 `/plugin-mcp/{id}/`；当前仅进程内。
- 模型目录消费：`host.service/llm-models/1`，有版本化 Host service 协议。

这些业务类型还没有全部抽离到通用 SDK。公开包不含 Host 私有业务模块；开发这类插件需先取得目标 Host 对应的契约说明或兼容源码，不能在 agent 中猜方法签名。通用 Gateway/React/自定义 Capability demo 可以完全仓外开发。具体能力及源码定位见 [能力清单](CAPABILITIES.md)。

## 4. 配置、资源和持久化

`context.config` 是本次组合 Row 的配置。准备期间校验字段和范围，非法值应令候选失败；不要等到发布后才发现必需配置错误。`config.json` 是安装容器的私有配置文件，管理 API 可读写，但不会自动合并进所有 Row，插件必须主动定义读取、合并和优先级。

凭据放插件私有凭据存储，避免进入 Manifest、Profile、URL、前端 bundle 或日志。目录会升级、备份、卸载，不适合作为唯一业务数据存储位置。通用 SDK 没有内置 SQL/文件/密钥 API；使用自己的依赖或有文档的 Host 契约，明确状态目录和迁移策略。

有资源需要回收时，在 prepare 成功获取后立即登记：

```python
# client 是插件自行创建的异步客户端；此段放在 prepare 内。
context.effects.add("http-client", client.aclose)
context.spawn_task("poll", poll())
context.subscribe("my-domain.changed", on_change)
```

其中 client/poll/on_change 需由插件实现。`spawn_task` 会立刻创建任务，后台消费应在 `context.is_active` 后才处理真实工作，否则候选失败也可能已经产生业务副作用。effects 按逆序释放并尽量完成其他清理；不要再在 `dispose()` 重复关闭同一资源。可选 `drain(deadline)` 停止新投递，`dispose()` 释放未登记的私有资源。

`context.notify_resource_changed("items")` 只发失效通知，前端订阅当前 plugin/generation/resource 后重新请求权威数据。它不携带业务正文，也不负责数据持久化，错过通知后要能重新读取。

HTML Gateway 返回真正的 HTMLResponse；直接返回字符串会被当成 JSON 字符串。普通 assets 用 `contribute_asset` + `asset_url`。React dist 走客户端制品归档，两种地址与保留策略不同，见 [加载原理](LOADING.md)。

## 5. 本地迭代、升级与卸载

- `dev/plugin/demos` 不在扫描目录。源码 Host 扫描根 `plugins/` 及受管插件目录；桌面版从设置打开实际目录。
- 源码调试优先在仓外构建、生成 ZIP 再覆盖安装；放入受管源码目录的内容会参与 digest，不要放 node_modules 或构建缓存。
- watcher 默认每 2 秒检查，也可请求 `POST /api/plugins/reload-changed`；`POST /api/plugins/reload` 强制重建活动组合。
- 修改配置、制品或 Provider 会计算换代影响集；候选 prepare / health 成功才发布，失败保留旧组合。
- 同 ID ZIP 可直接覆盖升级，不需先卸载。更新是否激活取决于现有启用状态和 Profile；停用插件不会因上传更新被擅自启用。
- 卸载使用设置页或 DELETE 管理接口，先撤下、drain、备份文件，保留业务数据。不要手工删除活动插件目录。
- wheel entry point 适用于普通 Python 部署，更新后以重启 Host 为稳妥路径；不要把 wheel 热更新等同于目录插件换代。

## 6. 排错

| 现象 | 检查顺序 |
| --- | --- |
| 不在插件列表 | 是否在真实扫描目录、ZIP 根、ID 和 Manifest、发现错误 |
| 已发现但没运行 | 默认关闭、保存开关、active Profile 是否含启用 Row、缺失 requires |
| prepare 失败 | 工厂同步且 id 正确、依赖可导入、配置合法、实际 provide 与清单一致 |
| health 失败 | 运行依赖与配置；失败只撤销候选，查看旧代是否还 ACTIVE |
| Gateway 503 | 插件是否 ACTIVE、精确 method/path 是否存在、是否已停用 |
| Gateway 409 | 请求 generation 与当前代不同；刷新描述，不盲重放写入 |
| Gateway 422 | generation 不是正整数；业务输入也可能由插件主动报 422 |
| React 无法加载 | dist 存在、default.activate、共享 React、SDK 范围、声明 slots/commands |
| 能加载但没有页面 | contribution 的 kind/viewId、当前宿主页面是否挂载该 Slot |
| 修改没生效 | 是否编辑了实际活动 release、受管同 ID 覆盖、模块缓存/全局单例、watcher 是否发现 |
| 进程插件不可用 | 是否误用 prepare、launcher 是否支持冻结环境、stdout 杂音、JSON/帧/超时限制 |
| 开关被拒绝 | 已有 active Profile，需要修改部署组合并显式激活 |

## 7. 交付检查

1. 记录目标 Host 发行版本、SDK API 和插件 version。变更 ID 时同步所有代码、能力、UI 和路径。
2. 安装 SDK，运行静态校验；构建 UI 后执行 `python tools/check.py --require-client`，本脚本会 import 并执行这几个可信 demo。
3. React 执行 typecheck/build。检查 ESM external，保留所有 chunks，styles 中每个文件都存在。
4. `pack.py` 默认只打包约定路径。业务目录若名为 `lib` 等，显式加 `--include lib`，查看 ZIP 文件清单；打包工具不会猜动态 import、生成 vendor 或扫描秘密内容。
5. 在实际目标 Host 验证导入、启用、调用、配置、失败候选回退、升级、停用和卸载；检查旧请求/流的排空。冻结版和源码版分别验证，不能互相替代。
6. ZIP 无 .env、config.json、凭据、用户数据、数据库、缓存、node_modules 或宿主管理指针。第三方依赖和授权许可齐备。
7. 提供 README：用途、配置字段、前提依赖、权限/数据位置、入口、已知限制、升级/迁移/卸载行为和验证结果。保留 lockfile 与 SHA256。

`pack.py` 是小型制品工具，不会运行 pip/npm。Python 依赖需要构建时准备 vendor；源码仓库的 `scripts/build_plugin_vendor.py` / `scripts/build_plugin_zips.py` 可处理 `requirements-vendor.txt`，当前自动 vendor 只接受通用纯 Python wheel。运行时不执行 .pth，同进程 Host 依赖优先；原生扩展按平台与 ABI 验证，插件间没有通用依赖版本隔离。
