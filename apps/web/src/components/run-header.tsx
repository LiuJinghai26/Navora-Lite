"use client";

import { Code2, Download, RotateCw } from "lucide-react";
import { useState } from "react";
import { rerun } from "@/lib/api";
import type { Run } from "@/lib/types";
import { StatusBadge } from "./status-badge";

function formatDate(value?: string) {
  if (!value) return "Not started";
  return new Intl.DateTimeFormat("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit"
  }).format(new Date(value));
}

function formatDuration(ms?: number) {
  if (!ms) return "0s";
  const seconds = Math.round(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return minutes ? `${minutes}m ${rest}s` : `${rest}s`;
}

export function RunHeader({ run }: { run: Run }) {
  const [showApi, setShowApi] = useState(false);

  const exportRun = () => {
    const blob = new Blob([JSON.stringify(run, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${run.id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleRerun = async () => {
    const response = await rerun(run.id);
    window.location.href = `/runs/${response.run_id}`;
  };

  return (
    <header className="border-b border-stroke bg-[#081220]/90 px-6 py-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl font-semibold text-white">{run.title}</h1>
            <StatusBadge status={run.status} />
          </div>
          <div className="mt-2 grid gap-x-5 gap-y-1 text-xs text-slate-400 md:grid-cols-2 xl:grid-cols-4">
            <span>Run ID: {run.id}</span>
            <span>Started: {formatDate(run.startedAt)}</span>
            <span>Finished: {formatDate(run.finishedAt)}</span>
            <span>Duration: {formatDuration(run.durationMs)}</span>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className="inline-flex h-9 items-center gap-2 rounded-md border border-stroke bg-panelSoft px-3 text-sm text-slate-200 hover:border-cyan-400/50"
            onClick={() => setShowApi(true)}
          >
            <Code2 className="h-4 w-4" />
            API & Webhooks
          </button>
          <button
            className="inline-flex h-9 items-center gap-2 rounded-md border border-stroke bg-panelSoft px-3 text-sm text-slate-200 hover:border-cyan-400/50"
            onClick={exportRun}
          >
            <Download className="h-4 w-4" />
            Export
          </button>
          <button
            className="inline-flex h-9 items-center gap-2 rounded-md bg-cyan-500 px-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
            onClick={handleRerun}
          >
            <RotateCw className="h-4 w-4" />
            Rerun
          </button>
        </div>
      </div>

      {showApi ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-5" onClick={() => setShowApi(false)}>
          <div
            className="w-full max-w-2xl rounded-lg border border-stroke bg-panel p-5 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">API & Webhooks</h2>
              <button className="rounded-md border border-stroke px-3 py-1 text-sm text-slate-300" onClick={() => setShowApi(false)}>
                Close
              </button>
            </div>
            <pre className="overflow-auto rounded-md bg-[#050b14] p-4 text-xs text-cyan-100">
{`curl -X POST http://localhost:8000/api/runs \\
  -H "Content-Type: application/json" \\
  -d '{"task":"${run.task}","url":"${run.url}"}'`}
            </pre>
          </div>
        </div>
      ) : null}
    </header>
  );
}

