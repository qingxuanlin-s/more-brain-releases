# 能力消费者

先安装并启用 `hello-backend`，再安装并启用本插件；使用 Profile 时将两者加入同一活动组合。

```bash
python tools/pack.py demos/echo-consumer
curl -fsS 'http://127.0.0.1:8000/api/plugins/demo-echo-consumer/gateway/echo?text=hello'
```

预期响应为 `{"consumer":"demo-echo-consumer","result":{"text":"hello","message":"你好，More Brain 插件"}}`。这里的 curl 只适用于已经运行的 Host。

Host 根据 `requires` 排序，先 prepare provider，再将候选 provider 注入 consumer。依赖缺失时不能激活；provider 升级会把其消费者也列入换代影响集，因此当前 Context 绑定的依赖不会在一次工作中被随意替换。

改为可选依赖时，Manifest 增加 `optional = true`，Python 同时改用 `context.optional(key)` 并处理 `None`。不要只修改清单。
