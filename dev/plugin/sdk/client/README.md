# 浏览器 TypeScript / React SDK

源码入口 `index.ts`，运行时模块标识 `@more-brain/plugin-sdk`。先运行 `npm install` 安装源码的类型依赖。插件编译时读取本目录类型，React / React DOM / SDK 保持 external，由 More Brain 的 import map 提供运行模块。

这不是 Node 服务端 SDK，也尚未承诺发布到 npm。完整 API 与接入见 [SDK 说明](../../SDK.md) 和 [React demo](../../demos/hello-react/)。
