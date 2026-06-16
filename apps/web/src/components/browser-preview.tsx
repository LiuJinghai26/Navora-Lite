"use client";

import { Maximize2, Square } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
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

export function BrowserPreview({
  run,
  imageUrl,
  imageTitle,
  live = true
}: {
  run: Run;
  imageUrl?: string;
  imageTitle?: string;
  live?: boolean;
}) {
  const [fullscreen, setFullscreen] = useState(false);
  const latest = run.screenshots[run.screenshots.length - 1];
  const runningStep = [...run.timeline].reverse().find((step) => step.status === "running");
  const resolvedImageUrl = useMemo(() => absoluteImageUrl(imageUrl || latest?.imageUrl), [imageUrl, latest?.imageUrl]);
  const [displayedImageUrl, setDisplayedImageUrl] = useState(resolvedImageUrl);

  useEffect(() => {
    let cancelled = false;
    const image = new Image();
    image.onload = () => {
      if (!cancelled) setDisplayedImageUrl(resolvedImageUrl);
    };
    image.onerror = () => {
      if (!cancelled) setDisplayedImageUrl(resolvedImageUrl);
    };
    image.src = resolvedImageUrl;
    return () => {
      cancelled = true;
    };
  }, [resolvedImageUrl]);

  const stop = async () => {
    // The bundled demo run is read-only; real runs are controlled through the API.
    if (run.id !== "demo") {
      await stopRun(run.id);
    }
  };

  return (
    <section id="browser-preview" className="min-w-0 rounded-lg border border-stroke bg-panel">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-stroke px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold text-white">Browser Preview</h2>
          <p className="mt-1 text-xs text-slate-500">
            {runningStep && live ? `Running: ${runningStep.description}` : live ? "Live latest screenshot" : imageTitle || "Selected timeline screenshot"}
          </p>
        </div>
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
      <div className="relative aspect-video overflow-hidden p-3 theme-input">
        <img
          className="h-full w-full rounded-md object-contain transition-opacity duration-200"
          src={displayedImageUrl}
          alt="Browser preview screenshot"
          loading="eager"
        />
        {runningStep && live ? (
          <div className="pointer-events-none absolute left-5 top-5 max-w-[calc(100%-2.5rem)] rounded-md border border-cyan-400/35 bg-slate-950/80 px-3 py-2 text-xs text-cyan-100 shadow-glow">
            <span className="mr-2 inline-block h-2 w-2 animate-pulse rounded-full bg-cyan-300" />
            {runningStep.description}
          </div>
        ) : null}
      </div>
      <FullscreenPreviewDialog open={fullscreen} imageUrl={displayedImageUrl} onClose={() => setFullscreen(false)} />
    </section>
  );
}
