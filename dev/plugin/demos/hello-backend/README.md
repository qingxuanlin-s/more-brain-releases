# 最小后端

复制整个目录，修改 Manifest 的 ID、Python 类的 `id` 和 `ECHO` 的 name，使它们保持一致。不要只改目录名。工厂每次返回新实例，import/构造时没有外部副作用。

在开发中心目录运行（先安装 SDK）：

```bash
python -m more_brain_plugin_sdk validate demos/hello-backend
python tools/pack.py demos/hello-backend
```

导入 ZIP、启用后，访问已有 Host：

```bash
curl -fsS http://127.0.0.1:8000/api/plugins/demo-hello-backend/gateway/status
curl -fsS 'http://127.0.0.1:8000/api/plugins/demo-hello-backend/gateway/echo?text=hello'
```

端口替换为实际地址。返回 `message` 和当前 `generation_id`。这个 demo 只有后端，侧栏不会新增页面。

配置来自部署 Row 的 `config`，例如 `{"message":"我的插件"}`；修改后激活 Profile。`config.json` 不会自动覆盖 Row。若配置错误，候选 prepare 失败，已有活动组合继续工作。

同时安装并启用 `echo-consumer` 可以演示插件间调用。Capability 是 `example.echo/demo-hello-backend/1`，`echo(text: str)` 异步返回 `{text, message}`。它是 demo 自定义协议，不是宿主内置模型服务。
