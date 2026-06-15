export type RunStatus = "idle" | "running" | "completed" | "failed" | "stopped";
export type ControlStatus = "idle" | "controlling" | "stopped" | "completed" | "failed";
export type StepStatus = "pending" | "running" | "success" | "failed" | "skipped" | "stopped";
export type FailureType = "recognition_failed" | "planning_failed" | "execution_failed";

export interface ChecklistItem {
  text: string;
  status: "pending" | "running" | "success" | "failed";
  time?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  createdAt: string;
  checklist?: ChecklistItem[];
}

export interface TimelineStep {
  id: string;
  index: number;
  action: string;
  description: string;
  status: StepStatus;
  startedAt?: string;
  endedAt?: string;
  durationMs?: number;
  screenshotUrl?: string;
  error?: string;
}

export interface ScreenshotItem {
  id: string;
  title: string;
  imageUrl: string;
  createdAt: string;
}

export interface Run {
  id: string;
  title: string;
  task: string;
  url: string;
  status: RunStatus;
  controlStatus: ControlStatus;
  startedAt?: string;
  finishedAt?: string;
  durationMs?: number;
  messages: ChatMessage[];
  timeline: TimelineStep[];
  screenshots: ScreenshotItem[];
  extracted?: unknown;
  inputs: Record<string, unknown>;
  fallbackReason?: string;
  failureType?: FailureType;
  stopRequested?: boolean;
}

export interface RunEvent {
  type: "snapshot" | "chat_message" | "timeline_step" | "screenshot" | "status" | "extracted" | "error";
  message?: ChatMessage;
  step?: TimelineStep;
  image_url?: string;
  status?: RunStatus;
  data?: unknown;
  error?: string;
  run?: Run;
}

export interface CreateRunResponse {
  run_id: string;
  status: RunStatus;
}
