import { useSyncExternalStore } from "react";
import type { PluginContext } from "./index";

/** 输入框工作目录挂载点：插件提供默认目录，宿主仍允许用户手动修改。 */
export type ComposerWorkspaceSource = {
  id: string;
  getSnapshot(): string | null;
  subscribe(listener: () => void): () => void;
};
const sources = new Map<string, ComposerWorkspaceSource>();
const listeners = new Set<() => void>();
let snapshot: readonly ComposerWorkspaceSource[] = [];
const emit = () => { snapshot = [...sources.values()]; listeners.forEach((listener) => listener()); };
export function registerComposerWorkspaceSource(context: PluginContext, source: ComposerWorkspaceSource): () => void {
  if (!source.id.startsWith(`${context.pluginId}.`)) throw new Error("工作目录源 ID 必须带所属插件前缀");
  if (sources.has(source.id)) throw new Error(`重复工作目录源：${source.id}`);
  sources.set(source.id, source);
  const unsubscribe = source.subscribe(emit);
  emit();
  let disposed = false;
  const dispose = () => { if (disposed) return; disposed = true; unsubscribe(); sources.delete(source.id); emit(); };
  context.scope.add(dispose);
  return dispose;
}
export function useComposerWorkspaceSources(): readonly ComposerWorkspaceSource[] {
  return useSyncExternalStore((listener) => { listeners.add(listener); return () => listeners.delete(listener); }, () => snapshot, () => snapshot);
}
