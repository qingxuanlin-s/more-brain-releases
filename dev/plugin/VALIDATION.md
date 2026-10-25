# 验证记录

2026-10-26 在 macOS 开发环境验证。Node `22.16.0`，npm `10.9.2`，Python SDK `1.0.0`。本记录区分源码 Host 内核验证、公开资料独立验证和需要目标桌面环境的人工验收。

## 公开资料独立验证：通过

将资料导出到仓库外的临时目录，新建独立 Python 虚拟环境，安装附带的 `sdk/python`。在此环境确认 `app` 不可导入，插件开发不依赖 Host 源码。

在公开资料的 `dev/plugin` 运行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e sdk/python
cd sdk/client
npm install --ignore-scripts --no-audit --no-fund
cd ../../demos/hello-react/client
npm install --ignore-scripts --no-audit --no-fund
npm run typecheck
npm run build
cd ../../..
.venv/bin/python tools/check.py --require-client
.venv/bin/python tools/pack.py demos/hello-backend
.venv/bin/python tools/pack.py demos/hello-react
.venv/bin/python tools/pack.py demos/echo-consumer
.venv/bin/python tools/pack.py demos/hello-process
```

结果：SDK 安装、React typecheck/build、4 个 demo 的清单/工厂/handler/能力检查与 ZIP 打包全部通过。hello-process 只检查映射和本地方法调用，未启动受管子进程。构建 React 后才执行 require-client，没有把跳过算作验证成功。

## 源码 Host 内核验证：通过

使用已有 Host Python 依赖环境，直接调用运行时类，不启动 FastAPI 服务、端口或后台 worker：

- 三个进程内 demo 经真实目录加载器注册，组合激活通过。
- consumer 的 requires 正确解析，真实 PluginWebGateway 调用得到 provider 结果。
- 修改 Row 配置并 reconcile：新调用得到新结果，旧 lease 保持原实例；最后归还后旧代变 DISPOSED。
- 无效配置使候选 prepare 失败，原 Registry 对象与已有接口继续可用。
- 四个 ZIP 均通过真实 stage_plugin_archive 安装器的临时目录校验。
- `python -m compileall -q app dev/plugin` 通过。

## 尚未覆盖

- 实际桌面 Host 的 UI 导入、启用和 React 页面呈现。
- 真实账号、外部业务 API、数据库持久化和模型调用；demo 不需要这些服务。
- 真实受管 process launcher、冻结版解释器和进程通信。
- 目标发行版跨版本升级、长期运行、断网重连与卸载的端到端体验。

这些仍应按目标 Host 发行版本验收，不能用静态检查或源码内核通过代替。需要启动实际 Host 时先遵守对应工作区的 AGENTS.md 和用户授权。
