import type { FailureType, Run, RunStatus, TimelineStep } from "./types";

export const failureLabels: Record<FailureType, string> = {
  recognition_failed: "识别",
  planning_failed: "规划",
  execution_failed: "执行"
};

export interface FailureRecord {
  run: Run;
  failureType: FailureType;
  failedStep?: TimelineStep;
  error: string;
  message: string;
  occurredAt?: string;
}

const terminalStatuses: RunStatus[] = ["completed", "failed", "stopped"];

export function failureTypeFor(run: Run): FailureType {
  // Older runs may only have a failed timeline action, so infer the failure bucket.
  if (run.failureType) return run.failureType;
  const failedStep = run.timeline.find((step) => step.status === "failed");
  if (failedStep?.action === "recognition") return "recognition_failed";
  if (failedStep?.action === "planning") return "planning_failed";
  return "execution_failed";
}

export function latestMessage(run: Run): string {
  return run.messages[run.messages.length - 1]?.content || run.task;
}

export function displayRunTitle(run: Run): string {
  if (run.task && run.title && run.task.startsWith(run.title) && run.task.length > run.title.length) {
    return run.task;
  }
  return run.title || run.task;
}

export function failedStepFor(run: Run): TimelineStep | undefined {
  return run.timeline.find((step) => step.status === "failed");
}

export function buildFailureRecords(tasks: Run[]): FailureRecord[] {
  return tasks
    .filter((task) => task.status === "failed")
    .map((run) => {
      const failedStep = failedStepFor(run);
      return {
        run,
        failureType: failureTypeFor(run),
        failedStep,
        error: failedStep?.error || run.fallbackReason || latestMessage(run),
        message: latestMessage(run),
        occurredAt: failedStep?.endedAt || run.finishedAt || run.startedAt
      };
    });
}

export function buildRunStats(tasks: Run[]) {
  // Success rate only counts terminal runs so active tasks do not distort the metric.
  const terminal = tasks.filter((task) => terminalStatuses.includes(task.status));
  const completed = terminal.filter((task) => task.status === "completed").length;
  const failedRecords = buildFailureRecords(tasks);
  const failures: Record<FailureType, number> = {
    recognition_failed: 0,
    planning_failed: 0,
    execution_failed: 0
  };
  for (const record of failedRecords) {
    failures[record.failureType] += 1;
  }
  return {
    total: terminal.length,
    completed,
    failed: failedRecords.length,
    stopped: terminal.filter((task) => task.status === "stopped").length,
    running: tasks.filter((task) => task.status === "running").length,
    idle: tasks.filter((task) => task.status === "idle").length,
    successRate: terminal.length ? Math.round((completed / terminal.length) * 100) : 0,
    failures,
    failureRecords: failedRecords
  };
}
