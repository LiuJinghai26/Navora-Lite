import { API_BASE } from "./api";
import type { RunEvent } from "./types";

export function subscribeToRun(runId: string, onEvent: (event: RunEvent) => void, onError?: () => void) {
  // SSE is one-way, which is enough here because control actions still use HTTP endpoints.
  const source = new EventSource(`${API_BASE}/api/runs/${runId}/events`);
  source.onmessage = (message) => {
    try {
      onEvent(JSON.parse(message.data) as RunEvent);
    } catch {
      onError?.();
    }
  };
  source.onerror = () => {
    onError?.();
  };
  return () => source.close();
}
