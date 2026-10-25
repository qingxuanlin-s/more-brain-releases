/** 插件组织完整消息，圆桌宿主只处理发送，不解释文件或选区。 */
export type RoundtableMessageRequest = {
  content: string;
  workingDirectory: string;
  agentId?: number;
};

export const ROUNDTABLE_MESSAGE_REQUEST_EVENT = "more-rag:roundtable-message-request";

/** 返回宿主是否接收请求；未接收时由插件保留输入供重试。 */
export function requestRoundtableMessage(detail: RoundtableMessageRequest): boolean {
  const event = new CustomEvent<RoundtableMessageRequest>(ROUNDTABLE_MESSAGE_REQUEST_EVENT, { cancelable: true, detail });
  window.dispatchEvent(event);
  return event.defaultPrevented;
}
