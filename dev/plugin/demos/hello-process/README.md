# 受限进程示例

这个 demo 展示现有 v1 子进程协议，适合确认纯 JSON 服务如何接入。优先学习进程内 demo，再使用它。

```bash
python -m more_brain_plugin_sdk validate demos/hello-process
python tools/pack.py demos/hello-process
```

在支持该 launcher 的已有 Host 中安装启用后，`GET /api/plugins/demo-hello-process/gateway/status` 返回 `{"ok":true,"plugin_id":"demo-hello-process"}`。

映射键必须与 Manifest 一致。子进程调用 `health/drain/dispose`，不会调用新式 `prepare`。不要将 `hello-backend` 的 isolation 改为 process 后直接运行。

限制：JSON 参数/结果、文本 body/asset、默认 3 秒超时、1 MiB 行帧、串行请求；不支持 `requires`、流式结果、二进制、完整 Request/ASGI，Web 不透传 query/Cookie/Authorization。stdout 专用于协议，当前 stderr 被丢弃。沿用宿主 Python，没有独立 venv 或 OS 沙箱。冻结桌面版 launcher 必须另外验收，静态检查无法证明它可用。

本目录的检查工具只在当前 Python 内检查映射和调用，不启动受管子进程，也不把它当作真实 launcher 验收。
