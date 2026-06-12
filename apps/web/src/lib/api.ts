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
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getRun(runId: string): Promise<Run> {
  return request<Run>(`/api/runs/${runId}`);
}

export async function createRun(task: string, url = "http://localhost:8000/mock/findparts"): Promise<CreateRunResponse> {
  return request<CreateRunResponse>("/api/runs", {
    method: "POST",
    body: JSON.stringify({ task, url })
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

