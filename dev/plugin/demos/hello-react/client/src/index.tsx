import React, { useEffect, useState } from "react";
import type { ClientPlugin, PluginContext, PluginPanelProps } from "@more-brain/plugin-sdk";

type Echo = { text: string; generation_id: string | number };
const COMMAND = "demo-hello-react.echo";

function HelloPanel({ context, visible }: PluginPanelProps) {
  const [text, setText] = useState(() => context.recovery.get<string>("echo-draft", 1) ?? "你好");
  const [result, setResult] = useState("等待后端响应");

  useEffect(() => {
    if (!visible) return;
    const controller = new AbortController();
    const stop = () => controller.abort();
    context.scope.signal.addEventListener("abort", stop, { once: true });
    if (context.scope.signal.aborted) controller.abort();
    void context.commands.execute<string, Echo>(COMMAND, text, { signal: controller.signal })
      .then((value) => {
        if (!controller.signal.aborted) setResult(`${value.text} · generation ${value.generation_id}`);
      })
      .catch((error: unknown) => {
        if (!controller.signal.aborted) setResult(String(error));
      });
    return () => {
      controller.abort();
      context.scope.signal.removeEventListener("abort", stop);
    };
  }, [context, visible, text]);

  return <section className="demo-hello-react" style={{ padding: 24 }}>
    <h2>我的第一个 React 插件</h2>
    <label htmlFor="demo-hello-react-input">输入内容，读取后端 echo 接口</label>
    <p><input id="demo-hello-react-input" value={text} maxLength={200} onChange={(event) => {
      const value = event.target.value;
      setText(value);
      context.recovery.set("echo-draft", 1, value);
    }} /></p>
    <p role="status">{result}</p>
  </section>;
}

const plugin: ClientPlugin = {
  activate(context: PluginContext) {
    context.commands.register<string, Echo>(COMMAND, (text, { signal }) =>
      context.api.request<Echo>(`echo?text=${encodeURIComponent(text)}`, { signal }));
    context.ui.register({ kind: "navigation", id: "demo-hello-react.nav",
      viewId: "demo-hello-react", label: "React 开发示例", order: 900 });
    context.ui.register({ kind: "workspace", id: "demo-hello-react.workspace",
      viewId: "demo-hello-react", label: "React 开发示例", component: HelloPanel });
  },
};

export default plugin;
