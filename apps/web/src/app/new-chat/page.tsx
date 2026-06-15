"use client";

import { AppSidebar } from "@/components/app-sidebar";
import { createRun, getSettings } from "@/lib/api";
import { AlertCircle, ArrowUp, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

const examples = [
  "Open Hacker News and extract the current top story with its source, score, age, and comments.",
  "Open the Wikipedia Python article and extract the lead summary, infobox language details, and page metadata.",
  "Open https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API and extract the page title, summary, and first four section headings."
];

function hasPlannerConfig(settings: Record<string, unknown>) {
  // Local providers use OpenAI-compatible endpoints but do not require API keys.
  const provider = String(settings.MODEL_PROVIDER || "").toLowerCase();
  const hasApiBase = Boolean(String(settings.API_BASE || "").trim());
  const hasApiKey = Boolean(String(settings.API_KEY || "").trim());
  const localProvider = ["ollama", "lmstudio", "vllm", "custom"].includes(provider);
  return hasApiBase && (hasApiKey || localProvider);
}

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
      // The backend enforces the same gate; checking here gives the user faster feedback.
      const settings = await getSettings();
      if (!hasPlannerConfig(settings)) {
        const message = "请先在 Settings 中配置模型 API，再启动浏览器任务。";
        window.alert(message);
        setError(message);
        setBusy(false);
        return;
      }
      const response = await createRun(trimmed);
      router.push(`/runs/${response.run_id}`);
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Could not start the task. Check that the API server is running.";
      setError(message);
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-surface md:flex-row">
      <AppSidebar />
      <main className="grid min-w-0 flex-1 place-items-center px-5 py-8 md:px-8">
        <div className="grid w-full max-w-3xl gap-5">
          <header className="text-center">
            <h1 className="text-5xl font-semibold text-white">Navora</h1>
          </header>

          <section className="rounded-lg border border-cyan-400/40 bg-panel shadow-glow">
            <label htmlFor="new-chat-task" className="sr-only">
              Browser task
            </label>
            <textarea
              id="new-chat-task"
              data-testid="new-chat-task-input"
              className="min-h-[132px] w-full resize-none bg-transparent px-5 py-4 text-base leading-7 text-slate-100 outline-none placeholder:text-slate-500"
              value={task}
              onChange={(event) => setTask(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  // Enter submits, while Shift+Enter keeps multiline task editing available.
                  event.preventDefault();
                  void submit();
                }
              }}
              placeholder="Ask Navora to control the browser..."
            />
            <div className="flex items-center justify-between gap-3 px-3 pb-3">
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
                className="grid h-10 w-10 place-items-center rounded-md bg-cyan-500 text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
                onClick={submit}
                disabled={busy || !task.trim()}
                aria-label="Start task"
              >
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" />}
              </button>
            </div>
          </section>

          <div className="grid gap-2 md:grid-cols-3">
            {examples.map((example) => (
              <button
                key={example}
                className="min-h-[108px] rounded-lg border border-stroke bg-panel/70 p-3 text-left text-sm leading-5 text-slate-300 transition hover:border-cyan-400/50 hover:bg-cyan-400/10 hover:text-slate-100"
                onClick={() => setTask(example)}
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
