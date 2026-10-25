# 插件能力清单

“支持”指当前已实现的接缝，不意味着任意旧版桌面包都具有该能力。Host API 1.0.0 之外还需核对实际发行版本。入口与签名见 [接口参考](REFERENCE.md)，执行步骤见 [开发手册](GUIDE.md)。

## 1. 运行方式

| 方式 | 状态 | 适用场景 | 边界 / demo |
| --- | --- | --- | --- |
| Python 进程内 | 支持，首选 | 接口、业务服务、模型、Runtime、MCP | 同步工厂 + prepare；hello-backend |
| Python 独立进程 | 有限支持 | JSON 服务、文本接口，隔离部分故障 | v1 映射，不执行 prepare；hello-process |
| TS/TSX 浏览器 | 支持 | React 面板、导航、命令、浏览器协作 | ESM 制品 + Python 入口；hello-react |
| 只有 UI，Python 空入口 | 支持 | 没有服务端业务的 UI 扩展 | 仍须 plugin.py 和 factory |
| 无 Python 的纯 client Manifest | 尚未实现 | 未来的 client-only 插件 | 不要省略 entrypoint 或编造 runtime=none |
| TypeScript / Node 服务端 | 尚未实现 | 未来纯 TS 后端 | 无 Node runner / server SDK；不能把浏览器 SDK 当 Node SDK |
| wheel entry point | 支持 | 普通 Python 部署的包分发 | more_rag.plugins；更新后重启，不等同 ZIP 热更新 |

## 2. 后端通用能力

| 能力 | 如何实现 | Host 做什么 | 开发者负责什么 |
| --- | --- | --- | --- |
| JSON HTTP 接口 | contribute_web(method,path,handler) | 固定 Gateway、路由查找、handler lease、代际门禁 | 请求/响应 schema、输入检查、业务权限、错误码 |
| HTML 页面 | Gateway 返回 HTMLResponse，按需 contribute_ui | 控制台导航/页面入口 | HTML 转义、安全内容和 fragment 生命周期 |
| 二进制 / 自定义响应 | 进程内 handler 返回 Response | 返回 HTTP Response | Content-Type、大小、缓存、取消；process 不支持任意二进制 |
| 自定义服务 | Manifest provides + context.provide | Registry 绑定稳定 CapabilityKey | 明确方法契约、错误、主版本 |
| 插件依赖 | requires + require / optional | 强依赖校验、拓扑 prepare、Provider 变化影响消费者 | 处理可选服务缺失，不 import 插件实现 |
| 组合配置 | context.config | 按 Profile/Bundle/Row 注入 | 默认值、校验、迁移、秘密隔离 |
| 连接等资源清理 | effects.add(name,disposer) | 代际归属、逆序回收 | 获取后立即登记，避免重复关闭 |
| 异步后台工作 | spawn_task(name,awaitable) | generation 回收时取消任务 | 激活后才消费、背压、取消、可靠完成语义 |
| 后端事件订阅 | subscribe(type,handler) | 当前 Registry 定向投递、回调 lease | 事件契约、异常处理；通用 Context 没有 publish 方法 |
| 资源失效通知 | notify_resource_changed(resource_id) | 附加插件/代际身份，向 UI 推送失效 | 前端重新读取权威数据，处理断线重同步 |
| 普通静态文件 | contribute_asset + asset_url | 代际 URL 与有界历史缓存 | 内容类型、作用域、保留预期；单项当前至多 5 MiB |
| 热更新 | 工厂、prepare、health、scope/effects | 候选发布、Registry 切换、drain、lease 回收 | 无外部 import 副作用、代际资源、业务副作用补偿 |
| 安装 / 升级 / 卸载 | Manifest ZIP + 管理页/API | 制品验证、版本指针、回退、备份 | 正确制品、数据兼容与迁移说明 |

## 3. 宿主业务扩展点

这些是**特定服务协议**，并非通用 SDK 已经内置的全部实现。下列路径为 Host 源码定位，公开包不包含这些模块。

| 接缝 | Capability / 接口 | 能做什么 | 实现与参考 |
| --- | --- | --- | --- |
| LLM 服务商 | llm.provider/{provider-id}/1 | 新模型供应商、模型目录元信息、账号授权/文本与 agent 流 | `app/platform/llm/providers.py`、`plugins/llm-chatgpt/plugin.py`；Host `doc/49`、`doc/53` |
| Agent Runtime | runtime.adapter/{runtime-key}/2 | Agent 执行业务命令、事件、取消与运行表面 | `app/domains/research/runtime_adapters/`，`plugins/runtime-codex/plugin.py`；Host `doc/54-runtime-business-command-refactor.md` |
| Host 模型服务消费 | host.service/llm-models/1 | list_models、resolve_model、agent_stream | `app/platform/plugins/runtime/host_services.py` 的 LLMModelsService |
| MCP Provider | host.mcp/{plugin-id}/1 | 向 Agent 提供一套工具协议 ASGI app | `runtime/host_services.py` 的 PluginMcpService、`plugins/html-artifacts/plugin.py`；Host `doc/48` |
| 网页产物服务 | host.service/html-artifacts/1 | 按 run 发放产物访问授权 | HtmlArtifactsService；由可选插件提供，不能假定永远存在 |
| 圆桌输入引用 | registerComposerReferenceSource | 插入文件/外部资源引用、列举与读取引用 | 客户端 SDK composer-references；obsidian-bridge 示例 |
| 工作目录来源 | registerComposerWorkspaceSource | 插件提供当前工作目录 | 客户端 SDK composer-workspace；不是 Node 文件系统 API |
| 圆桌消息请求 | requestRoundtableMessage | 将完整 content、workingDirectory、可选 agentId 交给宿主 | 返回宿主是否接收，不代表消息执行完成 |

以上契约并不让插件通过 Registry 随意绕过业务授权。声明 `provides/requires` 表达结构依赖，不等于授予模型密钥、数据库、文件或网络权限。

当前没有独立、稳定的通用 SDK 用于注册任意检索器、embedding、reranker、任意数据库表或任意宿主菜单。可以在自有 Gateway / 面板实现业务，若要替换 Host 既有流程，需先找到真实消费者契约；不能编造 `register_retriever()`、`context.db`、`context.llm` 或 `context.fs`。

## 4. 浏览器 SDK 能力

| API | 用途 | 注意事项 |
| --- | --- | --- |
| context.api.request | 调用自己插件 Gateway | 自动 generation；返回 JSON，错误为 CommandError；非通用流/二进制客户端 |
| context.ui.register | 贡献 UI 元信息/React 组件 | 对应 Slot 必须声明，id 使用插件前缀；实际呈现取决于宿主挂载点 |
| context.commands.register / execute | 同页类型化命令 | 自己注册的 command 必须在 Manifest 列出；execute 需处理缺失和取消 |
| context.services.provide / get | 同页对象协作 | 浏览器运行时服务，不是后端 Capability 或跨进程代理 |
| context.events.subscribe(type,handler) | 订阅同页事件 | 返回取消函数；注册后按作用域回收 |
| context.events.subscribe(scope,handler) | 项目、圆桌、pluginResources 实时订阅 | 资源作用域须带当前 plugin ID / generation ID |
| context.events.emit | 发出客户端事件 | 不代表写入 Host 数据或广播至所有后端 |
| context.events.isConnected | 可选的连接状态读取 | 检查存在后调用；需要重新读取权威状态 |
| context.resources.read / invalidate | 资源读取缓存与失效 | key 应含插件等必要上下文；不要跨用户混用 |
| context.scope.signal / add | 活动上下文取消和清理 | 监听、timer、外部订阅登记清理；普通组件 effect 也要 cleanup |
| context.dock.activate / close | 右侧面板开关 | 与注册的 dock contribution ID 配合 |
| context.recovery.get / set / clear | 按 contextKey/schemaVersion 恢复草稿 | 面向 UI 换代恢复，不是数据库或永久存储保证 |
| useExternalSnapshot | 订阅外部状态源 | getSnapshot 在无变化时应返回同一引用 |
| registerComposerReferenceSource | 向输入区提供引用来源 | 在宿主支持的输入表面使用，注销函数交给 scope |
| registerComposerWorkspaceSource | 提供工作目录来源 | 不直接访问系统文件 |
| requestRoundtableMessage | 请求宿主接收完整消息 | 返回是否接收；未接收时保留输入 |

## 5. UI Slot 与 contribution 对照

Slot 是 Manifest 允许请求的挂载词汇；kind 是组件注册形式，不是同一字段。当前允许的 Slot 完整列表如下：

| Manifest slots | 注册的 contribution kind | 常见用途 |
| --- | --- | --- |
| global.navigation | navigation | 主导航入口；配 viewId |
| global.workspace | workspace | 主体页面，配同一 viewId + component |
| right-dock.tabs + right-dock.panel | dock-panel | 右侧 dock 标签与面板，需要同时声明两项 |
| global-overlay | settings-section | 设置区组件；具体呈现需宿主消费者支持 |
| execution-detail.panel | execution-detail | 回合执行明细，按 runtimes 认领，可 replace |
| roundtable.workbench | panel，slot="roundtable.workbench" | 圆桌业务面板，支持 layout/toolbar 等字段 |

SDK 还定义 message-action（command 字段），当前注册校验没有固定 Slot 要求；不能据此承诺每个宿主界面都有消息动作呈现。自定义字符串 Slot 目前会被 Manifest 校验器拒绝；不能凭空声明新布局区域。`panel` 的 slot 也必须是宿主真正挂载且清单允许的 Slot。

Panel 接收 `context`、`visible`，可选 presentation/singleColumn；执行明细接收 ExecutionDetailProps。普通 Slot 插件不创建 React root。旧 HTMX fragment 内 React 桥接是另外一种已有接入形态，需自行管理容器及 unmount，不应与新 Slot 生命周期混用。

## 6. 明确尚未提供的能力

| 想做的事 | 当前结论 | 可行方向 |
| --- | --- | --- |
| 用纯 TS 写 Node 后端 | 未实现 | 当前先用 Python 后端 + TS 浏览器 UI |
| 不带任何 Python 文件 | Manifest 仍需 Python 入口 | 使用空 prepare 工厂 |
| 任意 shell 命令作为 Manifest launcher | 不提供 | 使用已定义的受管运行方式 |
| process 消费 requires | 拒绝激活 | 使用进程内或等待双向协议 |
| process 提供流式 LLM / Runtime / MCP ASGI | 当前 JSON 代理不能承载 | 使用进程内对应契约 |
| SDK 自动安装 Python/npm 依赖 | 不提供 | 构建阶段打包 vendor / bundle |
| 自动独立 venv / OS 沙箱 | 不提供 | 可信插件；需要时另行设计隔离 |
| 任意 HTTP 路径参数匹配 | Gateway 精确键查找 | query/body 或单一 dispatch |
| 停用自动删除业务数据 | 不会 | 卸载说明与显式数据清理流程 |
| prepare 的外部业务写入自动回滚 | 不会 | 无副作用准备、幂等、补偿或激活后执行 |
| 无限保留旧 JS chunk 和旧 Python 模块隔离 | 不保证 | 有界缓存、兼容版本、独立命名空间 |
| 把 SDK 校验通过等同上线通过 | 不成立 | 目标 Host 安装/激活/升级/卸载验收 |

## 7. 已有插件可参考的实现

以下是当前 Host 源码中的实现目录，公开开发包只提供公共 SDK 和四个通用 demo，不随包分发这些业务插件。它们说明哪些业务已经通过插件接缝实现；安装包是否附带、是否启用仍以发行版本和用户配置为准。

| 插件 ID / 源码目录 plugins/{id} | 可参考的模式 |
| --- | --- |
| llm-chatgpt | llm.provider/chatgpt/1，账号授权、凭据引用、模型流 |
| llm-jev | llm.provider/jev/1，自定义模型供应商 |
| runtime-claude | runtime.adapter/claude/2，Agent Runtime 适配 |
| runtime-codex | runtime.adapter/codex/2，Runtime 配置和 Gateway |
| runtime-codex-pty | runtime.adapter/codex-pty/2，PTY 与执行明细 React 表面 |
| runtime-simple | runtime.adapter/simple/2，进程内骨架；核心 loop 尚未实现，不应作为完整 Agent 示例 |
| html-artifacts | ASGI MCP + host.service，工具会话与资源清理 |
| local-workbench | roundtable.workbench 面板、layout/toolbar、独立实现包 |
| obsidian-bridge | 外部笔记引用、工作目录来源、完整消息发送 |
| summary-index | 后端业务页面与旧控制台 React fragment 桥接 |
| document-relations | 文档关系业务 UI 与插件接口 |
| roundtable-scene | 工厂入口、多文件实现包 |
| desktop-pet | 本地桌面 UI 与专用配置 |
| mobile-tunnel | 手机访问入口、连接资源生命周期 |
| im-bridge | 即时通信平台接入、配置与后台连接 |
