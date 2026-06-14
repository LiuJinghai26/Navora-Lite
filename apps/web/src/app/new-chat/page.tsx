"use client";

import { AppSidebar } from "@/components/app-sidebar";
import { createRun } from "@/lib/api";
import { AlertCircle, Loader2, Send } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function NewChatPage() {
  const router = useRouter();
  const [task, setTask] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    const trimmed = task.trim();
    if (!trimmed || busy) return;
    setBusy(true);
    setError("");
    try {
      const response = await createRun(trimmed);
      router.push(`/runs/${response.run_id}`);
    } catch {
      setError("Could not start the task. Check that the API server is running.");
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-surface md:flex-row">
      <AppSidebar />
      <main className="min-w-0 flex-1 px-5 py-5 md:px-8 md:py-7">
        <div className="mx-auto grid max-w-3xl gap-5">
          <header className="border-b border-stroke pb-4">
            <h1 className="text-xl font-semibold text-white">New Chat</h1>
          </header>

          <section className="rounded-lg border border-cyan-400/40 bg-panel p-4 shadow-glow">
            <label htmlFor="new-chat-task" className="sr-only">
              Browser task
            </label>
            <textarea
              id="new-chat-task"
              data-testid="new-chat-task-input"
              className="min-h-[168px] w-full resize-none rounded-md border border-stroke bg-panelSoft px-4 py-3 text-base leading-7 text-slate-100 outline-none placeholder:text-slate-500 focus:border-cyan-400/60"
              value={task}
              onChange={(event) => setTask(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void submit();
                }
              }}
              placeholder="Enter a browser task"
            />
            <div className="mt-3 flex items-center justify-between gap-3">
              {error ? (
                <p className="inline-flex items-center gap-2 text-sm text-red-200">
                  <AlertCircle className="h-4 w-4" />
                  {error}
                </p>
              ) : (
                <span />
              )}
              <button
                data-testid="new-chat-submit"
                className="inline-flex h-10 items-center gap-2 rounded-md bg-cyan-500 px-4 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
                onClick={submit}
                disabled={busy || !task.trim()}
              >
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Start
              </button>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
