# More Brain 插件开发中心

这里面向第一次开发插件的人和 coding agent：复制 demo → 检查 → 打包 → 在 More Brain 中导入。**资料以 2026-10-26 核对的源码为准**，Host API / Client SDK API 为 `1.0.0`，Python SDK 为 `1.0.0`。目标桌面版本必须包含这一版插件 SDK；API 范围相同不保证旧桌面版具备全部功能。

公开发行入口：[more-brain-releases](https://github.com/qingxuanlin-s/more-brain-releases)。安装包以其 Releases 实际附件为准。这个公开仓库不包含 Host 源码；不要把私有应用源码作为开发插件的前提。

## 从这里读

| 要做什么 | 入口 |
| --- | --- |
| 十分钟做出可导入插件 | [开发手册](GUIDE.md#1-从零开始) |
| 理解插件如何发现、加载、换代和卸载 | [加载原理](LOADING.md) |
| 判断能扩展什么、哪些尚不可用 | [能力清单](CAPABILITIES.md) |
| 查询 Manifest、Python / TS API、管理接口 | [接口参考](REFERENCE.md) |
| 安装和使用附带的公共 SDK | [Python / 浏览器 SDK](SDK.md) |
| 交给 agent 直接执行 | [Agent 开发任务模板](AGENT.md) |
| 查看已验证内容与验收边界 | [验证记录](VALIDATION.md) |
| 最小后端与配置、JSON 接口、Capability | [hello-backend](demos/hello-backend/) |
| React 页面、命令、恢复草稿、后端调用 | [hello-react](demos/hello-react/) |
| 通过版本化能力调用另一插件 | [echo-consumer](demos/echo-consumer/) |
| 受限 Python 子进程协议 | [hello-process](demos/hello-process/) |

## 两种开发环境

**在 Host 源码仓库中**，工作目录为仓库根目录：

```bash
python3 -m venv dev/plugin/.venv
dev/plugin/.venv/bin/python -m pip install -e sdk/python
dev/plugin/.venv/bin/python dev/plugin/tools/check.py
dev/plugin/.venv/bin/python dev/plugin/tools/pack.py dev/plugin/demos/hello-backend
```

**拿到公开开发资料包后**，`dev/plugin` 内含导出时附带的 `sdk/python` 和 `sdk/client`，不需要 Host 源码。从 `dev/plugin` 运行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e sdk/python
.venv/bin/python tools/check.py
.venv/bin/python tools/pack.py demos/hello-backend
```

以上命令不启动应用、不占用端口。检查脚本默认跳过尚未构建的 React demo；它会明确输出跳过原因，不把跳过算成验证成功。完整检查方式见开发手册。

`pack.py` 输出 ZIP 和 SHA256 到 `dev/plugin/out/`。通过**已经运行**的 More Brain「设置 → 插件 → 导入插件」导入，再启用。demo 均默认关闭，放在这里不会被宿主自动扫描。已有 active Deployment Profile 时，需要把插件加入对应 Bundle 的 Row，再激活 Profile；依赖示例还需要同时启用 provider。

## 发布公开开发资料

维护者在 Host 源码仓库根目录执行：

```bash
python3 dev/plugin/tools/export.py --output /tmp/more-brain-plugin-kit
```

得到 `/tmp/more-brain-plugin-kit/dev/plugin/`：文档、demo、工具、独立 Python SDK 和浏览器 SDK 源码。该目录可整体放进公开发布仓库的 `dev/plugin/`。导出使用白名单，只复制插件开发所需 SDK，不复制 `app/`、凭据、运行配置或数据库；SDK 示例文档会换成公开开发包说明，避免依赖私有文档链接。

公开包 SDK 的位置：`sdk/python/src/more_brain_plugin_sdk/` 是完整 Python 公共包，`sdk/client/` 是完整浏览器 SDK TypeScript 源码。Host 源码仓库中复用原有 SDK，导出时再附入开发中心；不手工维护第二套实现。浏览器 SDK 附带类型依赖安装配置，仍通过宿主 import map 在运行时共享，不是已发布到 npm 的独立运行包。

导出工具不提交或推送 Git，不上传 Release。SDK 文件从当前实现导出，避免手工维护两套协议。公开目录生成后应按 [开发手册的发布检查](GUIDE.md#7-交付检查) 在仓外验证，再与目标 Host 一同发布。

## 当前边界

- 新插件首选 Python `prepare(context)` + 同步工厂，公共类型从 `more_brain_plugin_sdk` 导入。
- UI 使用 TS/TSX 编译后的浏览器 ESM，共享宿主 React 和客户端 SDK。
- 纯 Node/TypeScript 后端、无 Python 入口的 client-only Manifest、跨进程流式能力和跨进程 `requires` 尚未实现。
- Python 进程内和浏览器插件属于可信代码；`isolation="process"` 也不是 OS 安全沙箱。
- 本目录不启动宿主或预览服务。需要启动时先遵守所在仓库的 `AGENTS.md` 和用户授权要求。
