"use client";

import { useEffect } from "react";
import { AppSidebar } from "@/components/app-sidebar";
import { ChatPanel } from "@/components/chat-panel";
import { RunHeader } from "@/components/run-header";
import { RunTabs } from "@/components/run-tabs";
import { getRun } from "@/lib/api";
import { subscribeToRun } from "@/lib/events";
import { useRunStore } from "@/lib/store";

export default function RunPage({ params }: { params: { runId: string } }) {
  const run = useRunStore((state) => state.run);
  const setRun = useRunStore((state) => state.setRun);
  const applyEvent = useRunStore((state) => state.applyEvent);
  const setApiOnline = useRunStore((state) => state.setApiOnline);

  useEffect(() => {
    let cleanup: (() => void) | undefined;
    if (params.runId === "demo") {
      // The demo route stays usable without the backend by reading the bundled sample run.
      return undefined;
    }
    // Load a fresh snapshot first, then rely on SSE for live run updates.
    getRun(params.runId)
      .then((loaded) => {
        setRun(loaded);
        setApiOnline(true);
        cleanup = subscribeToRun(params.runId, applyEvent, () => setApiOnline(false));
      })
      .catch(() => setApiOnline(false));
    return () => cleanup?.();
  }, [params.runId, setRun, applyEvent, setApiOnline]);

  return (
    <div className="flex min-h-screen flex-col bg-surface md:flex-row">
      <AppSidebar />
      <main className="min-w-0 flex-1">
        <RunHeader run={run} />
        <div className="grid gap-5 px-6 py-5">
          <ChatPanel run={run} />
          <RunTabs run={run} />
        </div>
      </main>
    </div>
  );
}
