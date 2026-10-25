# React + Python 完整示例

本插件展示主导航、workspace、客户端命令、Gateway、取消请求和恢复草稿。宿主负责 React root，插件只提供组件。无独立端口、无开发服务器、无 npm 运行时安装。

从本目录开始：

```bash
cd client
npm install
npm run typecheck
npm run build
cd ..
python -m more_brain_plugin_sdk validate .
python ../../tools/pack.py .
```

Python 需为已安装 SDK 的环境。构建输出 `dist/client.js`；`styles=[]` 因为 demo 没有 CSS 文件。如果增加 CSS import，需固定 CSS 输出名并将相应文件加入 `client.styles`。保留完整 dist，包括动态导入 chunks。

源码仓库的 `sdk.d.ts` 指向 Host 中的真实 SDK。公开包导出时会改为 `../../../sdk/client/index`。复制 demo 到任意新目录后，也要把该文件改为本机 SDK 的实际相对路径。SDK 自身位于别处时，TS 解析 React 类型可能需要 SDK 邻近的 node_modules；公开导出包已附 `sdk/client/package.json`，先在该目录运行 `npm install`。源码仓库使用已有 `frontend/node_modules`，缺失时先安装 frontend 依赖。

打包、导入并启用后，侧栏出现「React 开发示例」。输入文字应显示 echo 和 generation。切换页面或卸载会取消请求；输入草稿用于同一浏览器运行期间换代恢复，不承诺永久持久化。遇到代际 409 时 Host 会同步插件描述，不应自动重放写入请求。

`npm install` 的依赖版本用于此 demo，与当前宿主 React 19 匹配；生成的 lockfile 应随自己的插件项目提交。React / react-dom / SDK 保持 external，不能复制另一套 React。宿主源码的插件 Vite 配置有 ID 白名单，本示例独立构建，不需要修改白名单。
