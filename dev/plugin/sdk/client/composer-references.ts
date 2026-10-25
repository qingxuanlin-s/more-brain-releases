import { useSyncExternalStore } from "react";
import type { PluginContext } from "./index";

/** 输入框外部引用源：可引用文件路径，正文预览按需读取。 */
export type ComposerReference = { key: string; title: string; quote?: string; path?: string; [key: string]: unknown };
export type ComposerReferenceCandidate = {
  id: string; title: string; detail?: string; current?: boolean;
  resolve(signal: AbortSignal): Promise<ComposerReference>;
  preview?(signal: AbortSignal): Promise<ComposerReference>;
};
export type ComposerReferenceSource = {
  id: string; label: string;
  getSnapshot(): readonly ComposerReferenceCandidate[];
  subscribe(listener: () => void): () => void;
};
const sources = new Map<string, ComposerReferenceSource>();
const listeners = new Set<() => void>();
let snapshot: readonly ComposerReferenceSource[] = [];
const emit = () => { snapshot = [...sources.values()]; listeners.forEach((listener) => listener()); };

export function registerComposerReferenceSource(context: PluginContext, source: ComposerReferenceSource): () => void {
  if (!source.id.startsWith(`${context.pluginId}.`)) throw new Error("引用源 ID 必须带所属插件前缀");
  if (sources.has(source.id)) throw new Error(`重复引用源：${source.id}`);
  sources.set(source.id, source);
  const unsubscribe = source.subscribe(emit);
  emit();
  let disposed = false;
  const dispose = () => {
    if (disposed) return;
    disposed = true;
    unsubscribe();
    sources.delete(source.id);
    emit();
  };
  context.scope.add(dispose);
  return dispose;
}

export function useComposerReferenceSources(): readonly ComposerReferenceSource[] {
  return useSyncExternalStore((listener) => { listeners.add(listener); return () => listeners.delete(listener); },
    () => snapshot, () => snapshot);
}
