import clsx from "clsx";
import { CheckCircle2, CircleDashed, ImageIcon, OctagonAlert, PauseCircle } from "lucide-react";
import type { StepStatus, TimelineStep } from "@/lib/types";

function iconFor(status: StepStatus) {
  if (status === "success") return <CheckCircle2 className="h-4 w-4 text-emerald-300" />;
  if (status === "failed") return <OctagonAlert className="h-4 w-4 text-red-300" />;
  if (status === "stopped") return <PauseCircle className="h-4 w-4 text-amber-300" />;
  if (status === "running") return <CircleDashed className="h-4 w-4 animate-spin text-emerald-300" />;
  return <CircleDashed className="h-4 w-4 text-slate-500" />;
}

function time(value?: string) {
  if (!value) return "--";
  return new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", second: "2-digit" }).format(new Date(value));
}

function duration(ms?: number) {
  if (!ms) return "--";
  return `${(ms / 1000).toFixed(1)}s`;
}

export function ExecutionTimeline({
  steps,
  selectedStepId,
  onSelectStep
}: {
  steps: TimelineStep[];
  selectedStepId?: string | null;
  onSelectStep?: (step: TimelineStep) => void;
}) {
  return (
    <section className="min-w-0 rounded-lg border border-stroke bg-panel">
      <div className="border-b border-stroke px-4 py-3">
        <h2 className="text-sm font-semibold text-white">Execution Timeline</h2>
      </div>
      <div className="scrollbar-thin max-h-[470px] overflow-auto p-3">
        <div className="grid gap-2">
          {steps.map((step) => (
            <button
              key={step.id}
              className={clsx(
                "grid w-full grid-cols-[22px_minmax(0,1fr)_auto] items-center gap-2 rounded-md border p-3 text-left transition theme-message",
                step.screenshotUrl ? "hover:border-cyan-400/50" : "cursor-default",
                selectedStepId === step.id ? "border-cyan-400/70 shadow-glow" : "border-stroke"
              )}
              onClick={() => step.screenshotUrl && onSelectStep?.(step)}
              disabled={!step.screenshotUrl}
              title={step.screenshotUrl ? "Show this step screenshot" : "Screenshot is not ready yet"}
            >
              {iconFor(step.status)}
              <div className="min-w-0">
                <div className="truncate text-sm text-slate-100">
                  #{step.index} {step.description}
                </div>
                <div className="mt-1 flex items-center gap-2 text-xs uppercase tracking-wide text-slate-500">
                  <span>{step.action}</span>
                  {step.screenshotUrl ? <ImageIcon className="h-3.5 w-3.5" /> : null}
                </div>
              </div>
              <div className="text-right text-xs text-slate-500">
                <div>{time(step.startedAt)}</div>
                <div>{duration(step.durationMs)}</div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
