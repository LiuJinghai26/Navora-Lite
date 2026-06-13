"use client";

import { Send, Square } from "lucide-react";
import { useState } from "react";
import { createRun, stopRun } from "@/lib/api";
import type { Run } from "@/lib/types";
import { ChatMessage } from "./chat-message";

export function ChatPanel({ run }: { run: Run }) {
  const [task, setTask] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    const trimmed = task.trim();
    if (!trimmed) return;
    setBusy(true);
    try {
      const response = await createRun(trimmed);
      window.location.href = `/runs/${response.run_id}`;
    } finally {
      setBusy(false);
    }
  };

  const stop = async () => {
    if (run.id !== "demo") {
      await stopRun(run.id);
    }
  };

  return (
    <section className="min-h-[260px] rounded-lg border-2 border-cyan-400/40 bg-panel p-4 shadow-glow">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">Task Chat</h2>
          <p className="text-sm text-slate-500">{run.status === "running" ? "Navora is controlling the browser" : `Status: ${run.status}`}</p>
        </div>
        <button
          className="inline-flex h-8 items-center gap-2 rounded-md border border-red-400/35 bg-red-500/10 px-3 text-xs font-semibold text-red-200 disabled:cursor-not-allowed disabled:opacity-45"
          onClick={stop}
          disabled={run.status !== "running"}
        >
          <Square className="h-3.5 w-3.5" />
          Stop Controlling
        </button>
      </div>

      <div className="scrollbar-thin grid max-h-[360px] min-h-[132px] gap-3 overflow-auto pr-1">
        {run.messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
      </div>

      <div className="mt-4 flex gap-2 rounded-lg border-2 border-cyan-400/30 p-2 theme-input">
        <input
          className="min-w-0 flex-1 bg-transparent px-3 text-base text-slate-100 outline-none placeholder:text-slate-500"
          value={task}
          onChange={(event) => setTask(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") submit();
          }}
          placeholder="Type a browser task for Navora..."
        />
        <button
          className="grid h-11 w-11 place-items-center rounded-md bg-cyan-500 text-slate-950 hover:bg-cyan-400 disabled:opacity-50"
          onClick={submit}
          disabled={busy}
          aria-label="Send task"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </section>
  );
}
