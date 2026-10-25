# 给开发 Agent 的执行说明

先读 [README](README.md)、[能力清单](CAPABILITIES.md)，再选一个 demo。需要改生命周期或诊断加载问题时读 [加载原理](LOADING.md)，查字段/签名读 [接口参考](REFERENCE.md)。不要把设计提案当已发布功能。

## 可复制任务模板

```text
为 More Brain 开发一个插件。

插件用途：<具体用户操作与结果>
永久 ID：<小写 kebab-case>
目标 Host 发行版本：<实际版本，未知则记录并核对>
UI 入口：<无 / 主导航 workspace / 右 dock / 圆桌 workbench / 执行明细>
配置字段：<字段、类型、默认值、秘密存放方式>
数据来源与存储：<API / 文件 / 自有数据库，明确读写>
依赖能力：<kind/name/api，必需或可选>
交付目录：<路径>

先以 dev/plugin/README.md 为入口，选最接近的 demo，按现有 SDK 实现。
交付完整源码、Manifest、构建配置、README 和 ZIP，不修改 Host 核心实现。
静态检查与短时构建可以执行；不自行启动应用、预览服务器或长期 worker。
需要启动时遵守工作区 AGENTS.md，先说明目的、命令、端口并取得授权。
报告已执行的验证和未覆盖部分，不将校验通过等同实际桌面验收通过。
```

## 实施顺序

1. 明确用户操作和验收结果，查能力清单确定当前能支持。只有未知信息会影响实际实现时再询问，不凭空补 Host API。
2. Python 后端选 hello-backend；UI 选 hello-react；插件依赖参考 echo-consumer。除非理解受限协议，不选择 process。
3. 同步修改 Manifest ID、Python id、能力声明、UI/command ID、viewId 和 URL。同步 factory 每次返回新实例；通用类型从 SDK 导入。
4. 后端只注册 Context 贡献，不 import app.main/app.bootstrap、不修改全局 Router/Host 模板、不导入另一个插件实现。专用 LLM/Runtime 契约先取得对应版本定义。
5. prepare 建资源并立即登记 effects，后台消费等 is_active；实现输入校验、取消、错误状态和配置校验。不要在 import/构造中启动任何外部资源。
6. UI 使用真实 SDK 类型，不伪造 .d.ts 接口；修正 SDK 路径，ESM external React/React DOM/SDK；Slot/command 与清单一致，所有异步操作清理。
7. 在仓外开发环境安装 SDK。执行 validate、Python 语法检查、UI typecheck/build、必要业务验证、pack，查看 ZIP 内容和 SHA256。
8. 生成用户可读的 README，包括配置、安装启用、Profile、API、存储、依赖、限制、升级与卸载。报告目标 Host 验收边界。

## 不应猜测的接口

- 不存在通用的 context.db / context.fs / context.llm / register_retriever。
- 不支持 Manifest runtime=node/none、Node server SDK 或任意 shell launcher。
- 进程插件不执行 prepare，不支持 requires、流或完整 Request；不能只改 isolation。
- 通用 Gateway 是精确 path，不是 FastAPI 动态路由。普通 api.request 读 JSON，不是任意二进制/流客户端。
- SDK 没有从 PyPI/npm 正式发布的保证；使用本包附带源码或实际发布的 wheel，不执行未经核实的按名称安装命令。
- enabled_by_default 不强制覆盖已有 Profile，导入不等于启用；不以只含本插件的部署 JSON 覆盖用户现有配置。
- generationId 当不透明字符串传浏览器，不转换为不安全的 JS number。
- 不在 ZIP 中打包开发 SDK、node_modules、秘密、用户数据或宿主管理指针。

## 交付回执模板

```text
已交付：<源码目录、ZIP、SHA256>
行为：<用户怎么进入、怎么操作、得到什么>
安装：<导入、启用、Profile 依赖>
配置/数据：<字段、存放位置、迁移影响>
验证通过：<实际命令和结果>
尚未验证：<如真实桌面 Host 的启用/升级/卸载、冻结 launcher>
已知限制：<当前实现真实限制>
```
