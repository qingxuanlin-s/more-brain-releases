# More Brain 桌面版发布

本仓库用于公开分发 More Brain 桌面安装包、更新公告及插件开发资料，不包含应用核心源码。

## 插件开发

[插件开发中心](dev/plugin/README.md) 提供详细开发手册、加载原理、能力清单、接口参考、Agent 任务模板，以及四个 demo 和检查/打包工具。

公共 SDK 同步放在 [dev/plugin/sdk](dev/plugin/sdk/)：包含可独立安装的 Python SDK 和浏览器 TypeScript/React SDK 源码。开发者可以直接克隆本仓库开发插件，无需应用核心源码。按 [快速开始](dev/plugin/GUIDE.md#1-从零开始) 安装 SDK、复制 demo、构建并导入插件。

## 下载

请前往 [Releases](https://github.com/qingxuanlin-s/more-brain-releases/releases) 下载适合芯片架构的安装包。首次安装或更新时，请完全退出旧版应用后再替换安装。

目前尚未发布安装包；请以 Releases 页面实际发布的文件为准。

## 更新公告

支持更新检查的桌面版本会在启动后检查本仓库最新正式 Release。发现更高版本时，显示版本公告，并可打开下载页面。网络失败不会影响应用使用。

## 发布约定

- 标签使用 `vX.Y.Z`，与安装包内桌面版本一致。
- Release 正文为用户可见更新公告，可附国内镜像下载链接。
- 安装包作为 Release 附件上传，不提交到 Git 历史。
- 先创建草稿，上传并核对安装包后，再发布为最新正式版。
- 不上传应用核心源码、密钥、配置文件、授权文件或用户数据；`dev/plugin` 公开插件开发文档、公共 SDK 和示例源码。
