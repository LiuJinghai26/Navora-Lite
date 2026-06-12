"use client";

import { Maximize2, Square } from "lucide-react";
import { useMemo, useState } from "react";
import { API_BASE, stopRun } from "@/lib/api";
import type { Run } from "@/lib/types";
import { FullscreenPreviewDialog } from "./fullscreen-preview-dialog";
import { StatusBadge } from "./status-badge";

function absoluteImageUrl(url?: string) {
  // Backend screenshots are served from /artifacts, while demo assets are local to Next.
  if (!url) return "/assets/browser-preview-placeholder.png";
  if (url.startsWith("http") || url.startsWith("/assets")) return url;
  return `${API_BASE}${url}`;
}

export function BrowserPreview({ run }: { run: Run }) {
  const [fullscreen, setFullscreen] = useState(false);
  const latest = run.screenshots[run.screenshots.length - 1];
  const imageUrl = useMemo(() => absoluteImageUrl(latest?.imageUrl), [latest?.imageUrl]);

  const stop = async () => {
    if (run.id !== "demo") {
      await stopRun(run.id);
    }
  };

  return (
    <section className="rounded-lg border border-stroke bg-panel">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-stroke px-4 py-3">
        <h2 className="text-sm font-semibold text-white">Browser Preview</h2>
        <div className="flex flex-wrap items-center gap-2">
          <button
            className="grid h-8 w-8 place-items-center rounded-md border border-stroke bg-panelSoft text-slate-200 hover:border-cyan-400/50"
            onClick={() => setFullscreen(true)}
            aria-label="Fullscreen browser preview"
          >
            <Maximize2 className="h-4 w-4" />
          </button>
          <StatusBadge status={run.controlStatus === "controlling" ? "controlling" : run.status} />
          <button
            className="inline-flex h-8 items-center gap-1.5 rounded-md border border-red-400/35 bg-red-500/10 px-2.5 text-xs font-semibold text-red-200 disabled:cursor-not-allowed disabled:opacity-45"
            onClick={stop}
            disabled={run.status !== "running"}
          >
            <Square className="h-3.5 w-3.5" />
            Stop Controlling
          </button>
        </div>
      </div>
      <div className="aspect-video bg-[#050b14] p-3">
        <img className="h-full w-full rounded-md object-cover" src={imageUrl} alt="Browser preview screenshot" />
      </div>
      <FullscreenPreviewDialog open={fullscreen} imageUrl={imageUrl} onClose={() => setFullscreen(false)} />
    </section>
  );
}
