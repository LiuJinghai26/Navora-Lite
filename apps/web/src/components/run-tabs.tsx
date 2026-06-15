"use client";

import clsx from "clsx";
import { useEffect, useMemo, useState } from "react";
import { API_BASE } from "@/lib/api";
import { useRunStore } from "@/lib/store";
import type { Run, TimelineStep } from "@/lib/types";
import { BrowserPreview } from "./browser-preview";
import { ExecutionTimeline } from "./execution-timeline";
import { ExtractedInformation } from "./extracted-information";

const tabs = ["Overview", "Output", "Inputs", "Recording", "Code"];

function JsonPanel({ data }: { data: unknown }) {
  // Shared JSON panel for raw output and input inspection tabs.
  return <pre className="overflow-auto rounded-lg border border-stroke bg-panel p-4 text-sm text-cyan-100">{JSON.stringify(data, null, 2)}</pre>;
}

function Recording({ run }: { run: Run }) {
  // Recording shows all captured screenshots instead of only the latest preview image.
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {run.screenshots.map((shot) => {
        const src = shot.imageUrl.startsWith("/artifacts") ? `${API_BASE}${shot.imageUrl}` : shot.imageUrl;
        return (
          <figure key={shot.id} className="rounded-lg border border-stroke bg-panel p-3">
            <img className="aspect-video w-full rounded-md object-cover" src={src} alt={shot.title} />
            <figcaption className="mt-2 text-xs text-slate-400">{shot.title}</figcaption>
          </figure>
        );
      })}
    </div>
  );
}

function CodePanel({ run }: { run: Run }) {
  // Code snippets mirror the current run so users can reproduce the task outside the UI.
  return (
    <div className="grid gap-4">
      <pre className="overflow-auto rounded-lg border border-stroke bg-panel p-4 text-sm text-cyan-100">
{`curl -X POST ${API_BASE}/api/runs \\
  -H "Content-Type: application/json" \\
  -d '{"task":"${run.task}","url":"${run.url}"}'`}
      </pre>
      <pre className="overflow-auto rounded-lg border border-stroke bg-panel p-4 text-sm text-cyan-100">
{`python scripts/run_demo.py \\
  --task "${run.task}" \\
  --url "${run.url}"`}
      </pre>
    </div>
  );
}

export function RunTabs({ run }: { run: Run }) {
  const activeTab = useRunStore((state) => state.activeTab);
  const setActiveTab = useRunStore((state) => state.setActiveTab);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const selectedStep = useMemo(
    () => run.timeline.find((step) => step.id === selectedStepId && step.screenshotUrl),
    [run.timeline, selectedStepId]
  );

  useEffect(() => {
    // Live runs should follow the latest screenshot rather than a stale selected step.
    if (run.status === "running") {
      setSelectedStepId(null);
    }
  }, [run.screenshots.length, run.status]);

  const selectTimelineStep = (step: TimelineStep) => {
    // Selecting a timeline row switches back to Overview where Browser Preview lives.
    setSelectedStepId(step.id);
    setActiveTab("Overview");
    document.getElementById("browser-preview")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <section className="grid gap-4">
      <div className="flex flex-wrap gap-1 border-b border-stroke">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={clsx(
              "h-10 rounded-t-md px-4 text-sm font-semibold",
              activeTab === tab ? "border border-b-0 border-stroke bg-panel text-cyan-100" : "text-slate-500 hover:text-slate-200"
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "Overview" ? (
        <div className="grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1.45fr)_minmax(360px,0.85fr)]">
          <div className="grid min-w-0 gap-4">
            <BrowserPreview
              run={run}
              imageUrl={selectedStep?.screenshotUrl}
              imageTitle={selectedStep?.description}
              live={!selectedStep}
            />
            <ExtractedInformation data={run.extracted} />
          </div>
          <ExecutionTimeline steps={run.timeline} selectedStepId={selectedStepId} onSelectStep={selectTimelineStep} />
        </div>
      ) : null}
      {activeTab === "Output" ? <JsonPanel data={run.extracted ?? {}} /> : null}
      {activeTab === "Inputs" ? <JsonPanel data={run.inputs} /> : null}
      {activeTab === "Recording" ? <Recording run={run} /> : null}
      {activeTab === "Code" ? <CodePanel run={run} /> : null}
    </section>
  );
}
