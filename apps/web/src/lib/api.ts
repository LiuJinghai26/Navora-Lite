import type { CreateRunResponse, Run } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    }
  });
  if (!response.ok) {
    let message = `Request failed: ${response.status}`;
    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string") {
        message = payload.detail;
      }
    } catch {
      // Keep the status-only message when the response has no JSON body.
    }
    throw new Error(message);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export async function getRun(runId: string): Promise<Run> {
  return request<Run>(`/api/runs/${runId}`);
}

export async function getTasks(): Promise<Run[]> {
  return request<Run[]>("/api/tasks");
}

export async function deleteTask(runId: string): Promise<void> {
  await request<void>(`/api/tasks/${runId}`, { method: "DELETE" });
}

export async function createRun(
  task: string,
  url = "http://localhost:8000/mock/findparts",
  presetId?: string
): Promise<CreateRunResponse> {
  return request<CreateRunResponse>("/api/runs", {
    method: "POST",
    body: JSON.stringify({ task, url, preset_id: presetId })
  });
}

export async function stopRun(runId: string): Promise<Run> {
  return request<Run>(`/api/runs/${runId}/stop`, { method: "POST" });
}

export async function rerun(runId: string): Promise<CreateRunResponse> {
  return request<CreateRunResponse>(`/api/runs/${runId}/rerun`, { method: "POST" });
}

export async function getSettings(): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>("/api/settings");
}

export async function saveSettings(payload: Record<string, unknown>): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>("/api/settings", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
