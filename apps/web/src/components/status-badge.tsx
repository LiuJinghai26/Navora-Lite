import clsx from "clsx";
import { CheckCircle2, CircleDashed, OctagonAlert, PauseCircle } from "lucide-react";
import type { RunStatus, StepStatus } from "@/lib/types";

const styles: Record<string, string> = {
  idle: "border-stroke bg-panelSoft text-slate-400",
  pending: "border-stroke bg-panelSoft text-slate-400",
  running: "border-sky-500/50 bg-sky-500/15 text-sky-200",
  completed: "border-emerald-500/50 bg-emerald-500/15 text-emerald-200",
  success: "border-emerald-500/50 bg-emerald-500/15 text-emerald-200",
  failed: "border-red-500/50 bg-red-500/15 text-red-200",
  stopped: "border-amber-500/50 bg-amber-500/15 text-amber-200",
  skipped: "border-stroke bg-panelSoft text-slate-400"
};

export function StatusBadge({ status }: { status: RunStatus | StepStatus | "controlling" }) {
  // "controlling" is a UI-specific state that visually behaves like running.
  const normalized = status === "controlling" ? "running" : status;
  const Icon =
    normalized === "completed" || normalized === "success"
      ? CheckCircle2
      : normalized === "failed"
        ? OctagonAlert
        : normalized === "stopped"
          ? PauseCircle
          : CircleDashed;

  return (
    <span
      className={clsx(
        "inline-flex h-7 items-center gap-1.5 rounded-md border px-2.5 text-xs font-semibold capitalize",
        styles[normalized]
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {status}
    </span>
  );
}
