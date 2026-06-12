import { CheckCircle2, CircleDashed, Clock3, OctagonAlert, PauseCircle } from "lucide-react";
import type { StepStatus, TimelineStep } from "@/lib/types";

function iconFor(status: StepStatus) {
  if (status === "success") return <CheckCircle2 className="h-4 w-4 text-emerald-300" />;
  if (status === "failed") return <OctagonAlert className="h-4 w-4 text-red-300" />;
  if (status === "stopped") return <PauseCircle className="h-4 w-4 text-amber-300" />;
  if (status === "running") return <Clock3 className="h-4 w-4 text-sky-300" />;
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

export function ExecutionTimeline({ steps }: { steps: TimelineStep[] }) {
  return (
    <section className="rounded-lg border border-stroke bg-panel">
      <div className="border-b border-stroke px-4 py-3">
        <h2 className="text-sm font-semibold text-white">Execution Timeline</h2>
      </div>
      <div className="scrollbar-thin max-h-[470px] overflow-auto p-3">
        <div className="grid gap-2">
          {steps.map((step) => (
            <div key={step.id} className="grid grid-cols-[22px_1fr_auto] items-center gap-2 rounded-md border border-stroke bg-[#0b1424] p-3">
              {iconFor(step.status)}
              <div className="min-w-0">
                <div className="truncate text-sm text-slate-100">
                  #{step.index} {step.description}
                </div>
                <div className="mt-1 text-xs uppercase tracking-wide text-slate-500">{step.action}</div>
              </div>
              <div className="text-right text-xs text-slate-500">
                <div>{time(step.startedAt)}</div>
                <div>{duration(step.durationMs)}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

