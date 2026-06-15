"use client";

import { create } from "zustand";
import { sampleRun } from "./sample-run";
import type { Run, RunEvent, TimelineStep } from "./types";

interface RunState {
  run: Run;
  activeTab: string;
  apiOnline: boolean;
  setRun: (run: Run) => void;
  applyEvent: (event: RunEvent) => void;
  setActiveTab: (tab: string) => void;
  setApiOnline: (online: boolean) => void;
}

function replaceStep(steps: TimelineStep[], step: TimelineStep) {
  // The backend first publishes a running step, then publishes the same id with final status.
  const existing = steps.findIndex((item) => item.id === step.id);
  if (existing === -1) {
    return [...steps, step];
  }
  return steps.map((item, index) => (index === existing ? step : item));
}

export const useRunStore = create<RunState>((set) => ({
  // sampleRun gives the UI an immediate, valid shape before a real run loads.
  run: sampleRun,
  activeTab: "Overview",
  apiOnline: true,
  setRun: (run) => set({ run }),
  applyEvent: (event) =>
    set((state) => {
      if (event.run) {
        // Snapshot events are authoritative and simplify reconnect behavior.
        return { run: event.run };
      }
      const run = { ...state.run };
      if (event.type === "chat_message" && event.message) {
        run.messages = [...run.messages, event.message];
      }
      if (event.type === "timeline_step" && event.step) {
        run.timeline = replaceStep(run.timeline, event.step);
      }
      if (event.type === "status" && event.status) {
        // Keep browser control status aligned with backend terminal states.
        run.status = event.status;
        run.controlStatus =
          event.status === "running"
            ? "controlling"
            : event.status === "completed"
              ? "completed"
              : event.status === "stopped"
                ? "stopped"
                : event.status === "failed"
                  ? "failed"
                  : run.controlStatus;
      }
      if (event.type === "extracted") {
        run.extracted = event.data;
      }
      return { run };
    }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setApiOnline: (apiOnline) => set({ apiOnline })
}));
