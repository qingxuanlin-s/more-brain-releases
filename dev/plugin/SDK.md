# 公共 SDK

公开开发资料包含两份从实际实现导出的 SDK。它们提供契约与开发工具；真实插件运行时由 More Brain 注入上下文，不需要把 SDK 再复制进插件 ZIP。

## Python 公共 SDK

路径：`sdk/python/`，包名 `more-brain-plugin-sdk`，导入名 `more_brain_plugin_sdk`。要求 Python 3.11+，当前版本 1.0.0，无第三方运行依赖。

```bash
python -m pip install -e sdk/python
python -m more_brain_plugin_sdk validate demos/hello-backend
```

主要导出：

| 分组 | 类型和工具 |
| --- | --- |
| 插件结构协议 | PluginContext、RuntimePlugin |
| 能力键 | CapabilityKey |
| 资源与事件 | EffectScope、LiveEvent |
| 错误 | PluginUnavailable、PluginGenerationMismatch、ManifestError |
| 清单模型 | PluginManifest、ClientManifest、CapabilityDeclaration |
| 清单工具 | parse_manifest、parse_manifest_toml、resolve_manifest_order、validate_plugin_directory |
| 版本常量 | HOST_API_VERSION、CLIENT_SDK_API_VERSION、__version__ |
| CLI | more-brain-plugin validate DIR 或 python -m more_brain_plugin_sdk validate DIR |

这个包不包含 Host 的 Registry、数据库、FastAPI 服务或业务 Runtime/LLM 实现。Context 是 Protocol，具体对象由 Host 提供。validate 只做静态检查，不执行插件。详见 [接口参考](REFERENCE.md)。

SDK 源码可用 hatchling 构建 wheel/sdist；尚未承诺上传 PyPI。安装使用目录或实际分发的 wheel，不假设公共包名已经可在线下载。目标 Host 也需要带上这版 SDK。

## 浏览器 TypeScript / React SDK

路径：`sdk/client/`，源文件入口 `index.ts`，运行时模块标识 `@more-brain/plugin-sdk`。目前公开包附的是源码和开发类型依赖配置，不是 npm 上已发布的独立运行库。

```bash
cd sdk/client
npm install
```

业务项目通过 TypeScript paths 或 demo 的 `sdk.d.ts` 转发，读取这里的真实类型：

```typescript
import type { ClientPlugin, PluginContext, PluginPanelProps } from "@more-brain/plugin-sdk";
```

构建插件时将 `@more-brain/plugin-sdk`、React 和 React DOM external。More Brain 浏览器运行环境通过 import map 提供对应模块，不要把 `sdk/client` 当成 Node 后端 SDK，也不要在插件打包时复制另一套 React。

主要导出：

| 分组 | 类型和工具 |
| --- | --- |
| 生命周期 | ClientPlugin、PluginContext、PluginScope |
| UI | PluginPanelProps、UiContribution、OwnedContribution、ExecutionDetailProps / Context |
| 面板与状态 | PanelPresentation、PanelLayoutState / Source、ExternalStore、useExternalSnapshot |
| 调用与错误 | ApiClient、ResourceClient、CommandHandler、CommandError、CommandCode |
| 实时 | RuntimeEvent、RealtimeScope、PluginResourceScope |
| 输入引用 | registerComposerReferenceSource、useComposerReferenceSources 及引用类型 |
| 工作目录 | registerComposerWorkspaceSource、useComposerWorkspaceSources 及来源类型 |
| 完整消息 | requestRoundtableMessage、ROUNDTABLE_MESSAGE_REQUEST_EVENT、RoundtableMessageRequest |
| React | 宿主共享的 React 导出 |

具体参数以附带的 `.ts` 源码为准；复制 hello-react 就能看到正确的构建与引用方式。SDK 类型允许注册不代表每个 Host 页面都有对应 UI 消费者，Slot 支持范围见 [能力清单](CAPABILITIES.md)。

## 版本与维护

插件 version、SDK 包版本、Host API、Client SDK API、Capability api 是独立维度。发布时应记录目标 Host 发行版本并完成实际验收。

源码仓库使用根 `sdk/python` 和 `frontend/packages/plugin-sdk/src`。导出工具将它们放入公开开发资料的 `sdk/`，并更新 demo 的类型转发路径。`SDK-SOURCE.md` 记录导出基线；不要手工修改公开副本后忘记回到原 SDK 更新，否则会产生两套行为不同的契约。
