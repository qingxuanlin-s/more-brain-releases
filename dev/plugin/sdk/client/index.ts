import React, { type ComponentType, useSyncExternalStore } from "react";

export type CommandCode =
  | "command/unavailable"
  | "command/invalid-argument"
  | "command/forbidden"
  | "command/cancelled"
  | "plugin/generation-mismatch"
  | "plugin/unavailable"
  | "plugin/error";

export class CommandError extends Error {
  readonly code: CommandCode;
  readonly detail?: unknown;

  constructor(code: CommandCode, message: string, detail?: unknown) {
    super(message);
    this.code = code;
    this.detail = detail;
  }
}

export type CommandHandler<Request, Result> = (
  request: Request,
  options: { signal: AbortSignal },
) => Result | Promise<Result>;

export type ServiceKey = string;

/** 主体区域的展示方式，由宿主授予；不暴露宿主内部控件或 DOM。 */
export type PanelPresentation = "embedded" | "immersive";

/** 插件拥有布局选择与持久化，宿主订阅快照并执行区域分配。 */
export type PanelLayoutState = {
  open: boolean;
  side: "left" | "right";
  presentation: PanelPresentation;
  width: number;
  minWidth: number;
  maxWidth: number;
  defaultWidth: number;
};

export type PanelLayoutSource = ExternalStore<PanelLayoutState> & {
  /** 拖拽过程中仅预览，结束时 commit=true，由插件保存。 */
  resize(width: number, commit?: boolean): void;
};

export type PluginPanelProps = {
  context: PluginContext;
  visible: boolean;
  presentation?: PanelPresentation;
  /** 窄窗口临时使用单栏，不改变插件已保存的展示偏好。 */
  singleColumn?: boolean;
};

type ContributionMeta = {
  id: string;
  label: string;
  order?: number;
  icon?: string;
};

/**
 * 回合执行明细的上下文。
 *
 * 宿主不判断「哪个插件该接管哪个 Runtime」——它只把事实交给插件，
 * 由插件在 `runtimes` 里自行声明认领范围。
 */
export type ExecutionDetailContext = {
  turnId: number;
  /** 本回合实际使用的 Runtime key（如 `codex-pty`）；未知时为空字符串。 */
  runtime: string;
  agentName: string;
  projectId: number | null;
  roundtableId: number | null;
  /** 回合是否仍在执行；面板据此决定是接管实时输出还是回看。 */
  running: boolean;
  /** 关闭所在弹窗。 */
  close(): void;
};

export type ExecutionDetailProps = {
  context: PluginContext;
  detail: ExecutionDetailContext;
};

export type UiContribution = ContributionMeta & (
  | { kind: "navigation"; viewId: string }
  | { kind: "workspace"; viewId: string; component: ComponentType<PluginPanelProps> }
  | { kind: "dock-panel"; component: ComponentType<PluginPanelProps> }
  | { kind: "message-action"; command: string }
  | { kind: "settings-section"; component: ComponentType<PluginPanelProps> }
  | {
      kind: "execution-detail";
      component: ComponentType<ExecutionDetailProps>;
      /** 认领的 Runtime key；省略表示任意 Runtime。 */
      runtimes?: string[];
      /** true 表示默认接管该表面，宿主仍保留切回内置事件列表的入口。 */
      replace?: boolean;
    }
  | {
      /**
       * 业务页面区域的通用面板：挂在宿主页面注册的挂载点上。
       * Slot 词汇（如 `roundtable.workbench`）属于宿主页面与 Manifest，
       * 不进 SDK——SDK 只固化 Shell 自有表面（上面这些 kind）的词汇。
       */
      kind: "panel";
      slot: string;
      component: ComponentType<PluginPanelProps>;
      /** 在用户选择沉浸展示时申请主体区域；退出入口及原界面恢复由宿主管理。 */
      presentation?: { immersive?: boolean };
      layout?: PanelLayoutSource;
      /** 由插件贡献入口；宿主决定工具栏的挂载位置。 */
      toolbar?: ComponentType<PluginPanelProps>;
    }
);

/**
 * 注册后由运行时附加 `owner` 的贡献记录。宿主用 `owner` 取 PluginContext，
 * 不从贡献 id 前缀反推（doc/41 §3.2：owner 由注册作用域附加，插件不能自选）。
 */
export type OwnedContribution = UiContribution & { owner: string };

export type RuntimeEvent = {
  type: string;
  [key: string]: unknown;
};

export type RealtimeScope = {
  projectIds?: number[];
  roundtableIds?: number[];
  pluginResources?: PluginResourceScope[];
};

export type PluginResourceScope = { plugin_id: string; generation_id: string; resource_id: string };

export type ApiClient = {
  request<T>(path: string, options?: RequestInit & { signal?: AbortSignal }): Promise<T>;
};

export type ResourceClient = {
  read<T>(key: string, load: (signal: AbortSignal) => Promise<T>): Promise<T>;
  invalidate(key: string): void;
};

export type PluginScope = {
  signal: AbortSignal;
  add(cleanup: () => void | Promise<void>): () => void;
  dispose(): Promise<void>;
};

export type PluginContext = {
  readonly pluginId: string;
  /** 新版宿主以字符串传输版本号，number 仅兼容旧版宿主。 */
  readonly generationId: string | number;
  readonly scope: PluginScope;
  readonly api: ApiClient;
  readonly resources: ResourceClient;
  ui: { register(contribution: UiContribution): () => void };
  commands: {
    register<Request, Result>(id: string, handler: CommandHandler<Request, Result>): () => void;
    execute<Request, Result>(id: string, request: Request, options?: { signal?: AbortSignal }): Promise<Result>;
  };
  services: {
    provide<T>(key: ServiceKey, service: T): () => void;
    get<T>(key: ServiceKey): T | undefined;
  };
  events: {
    isConnected?(): boolean;
    emit(event: RuntimeEvent): void;
    subscribe(type: string, handler: (event: RuntimeEvent) => void): () => void;
    subscribe(scope: RealtimeScope, handler: (event: RuntimeEvent) => void): () => void;
  };
  dock: { activate(id: string): void; close(id: string): void };
  recovery: {
    get<T>(contextKey: string, schemaVersion: number): T | undefined;
    set<T>(contextKey: string, schemaVersion: number, value: T): void;
    clear(contextKey: string): void;
  };
};

export type ClientPlugin = {
  activate(context: PluginContext): void | Promise<void>;
};

export type ExternalStore<T> = {
  subscribe(listener: () => void): () => void;
  getSnapshot(): T;
};

/** 仅在快照引用变更时让消费者更新；Store 必须缓存无变化快照。 */
export function useExternalSnapshot<T>(store: ExternalStore<T>): T {
  return useSyncExternalStore(store.subscribe, store.getSnapshot, store.getSnapshot);
}

export { React };
export { registerComposerReferenceSource, useComposerReferenceSources } from "./composer-references";
export type { ComposerReference, ComposerReferenceCandidate, ComposerReferenceSource } from "./composer-references";
export { registerComposerWorkspaceSource, useComposerWorkspaceSources } from "./composer-workspace";
export type { ComposerWorkspaceSource } from "./composer-workspace";
export { ROUNDTABLE_MESSAGE_REQUEST_EVENT, requestRoundtableMessage } from "./roundtable-message";
export type { RoundtableMessageRequest } from "./roundtable-message";
