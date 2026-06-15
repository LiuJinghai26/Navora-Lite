"use client";

import { AppSidebar } from "@/components/app-sidebar";
import { StatusBadge } from "@/components/status-badge";
import { createRun, deleteTask, getTasks } from "@/lib/api";
import { PRESET_TASKS, type PresetTask } from "@/lib/preset-tasks";
import type { Run, RunStatus } from "@/lib/types";
import clsx from "clsx";
import { BookOpen, Clock, ExternalLink, Filter, MessageSquare, Network, Newspaper, Play, RefreshCw, Search, Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

function formatDate(value?: string) {
  // Task cards need compact timestamps rather than full run header dates.
  if (!value) return "Not started";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(value));
}

function lastMessage(run: Run) {
  // Fall back to the task text for older runs that have no assistant messages.
  return run.messages[run.messages.length - 1]?.content || run.task;
}

const statusFilters: Array<"all" | RunStatus> = ["all", "running", "completed", "stopped", "failed", "idle"];
const presetIcons = {
  "hn-top-story": Newspaper,
  "wikipedia-python-summary": BookOpen,
  "mdn-api-research": Network
};

function matchesSearch(run: Run, query: string) {
  // Search combines identifiers, task text, status, and the latest visible message.
  const normalized = query.trim().toLowerCase();
  if (!normalized) return true;
  return [run.id, run.title, run.task, run.status, lastMessage(run)]
    .filter(Boolean)
    .some((value) => value.toLowerCase().includes(normalized));
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<"all" | RunStatus>("all");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [deletingAll, setDeletingAll] = useState(false);
  const [startingPresetId, setStartingPresetId] = useState<string | null>(null);

  const visibleTasks = useMemo(
    () => tasks.filter((task) => (statusFilter === "all" || task.status === statusFilter) && matchesSearch(task, query)),
    [tasks, query, statusFilter]
  );

  const loadTasks = async () => {
    // Refresh reads the backend's canonical local run history.
    setLoading(true);
    setError("");
    try {
      setTasks(await getTasks());
    } catch {
      setError("Could not load task history. Start the FastAPI backend and try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadTasks();
  }, []);

  const removeTask = async (task: Run) => {
    const confirmed = window.confirm(`Delete task "${task.title}"? This removes it from local history.`);
    if (!confirmed) return;
    setDeletingId(task.id);
    setError("");
    try {
      await deleteTask(task.id);
      setTasks((current) => current.filter((item) => item.id !== task.id));
    } catch {
      setError("Could not delete this task. Refresh and try again.");
    } finally {
      setDeletingId(null);
    }
  };

  const removeAllTasks = async () => {
    if (tasks.length === 0) return;
    const confirmed = window.confirm(`Delete all ${tasks.length} tasks? This removes local run history.`);
    if (!confirmed) return;
    setDeletingAll(true);
    setError("");
    try {
      // Deleting in parallel is acceptable because each request targets a different run id.
      await Promise.all(tasks.map((task) => deleteTask(task.id)));
      setTasks([]);
    } catch {
      setError("Could not delete all tasks. Refresh and try again.");
    } finally {
      setDeletingAll(false);
    }
  };

  const startPreset = async (preset: PresetTask) => {
    // Presets include a preset id so the backend can plan without a model call.
    setStartingPresetId(preset.id);
    setError("");
    try {
      const response = await createRun(preset.task, preset.url, preset.id);
      window.location.href = `/runs/${response.run_id}`;
    } catch {
      setError("Could not start this preset task. Start the FastAPI backend and try again.");
      setStartingPresetId(null);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-surface md:flex-row">
      <AppSidebar />
      <main className="min-w-0 flex-1 px-6 py-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-stroke pb-4">
          <div>
            <h1 className="text-xl font-semibold text-white">Tasks</h1>
            <p className="mt-1 text-sm text-slate-500">Run history with the chat messages, status, and captured outputs for each task.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button
              className="inline-flex h-9 items-center gap-2 rounded-md border border-stroke bg-panelSoft px-3 text-sm font-semibold text-slate-200 hover:border-cyan-400/50 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={loadTasks}
              disabled={loading || deletingAll}
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
            <button
              className="inline-flex h-9 items-center gap-2 rounded-md border border-red-400/35 bg-red-500/10 px-3 text-sm font-semibold text-red-200 hover:border-red-400/60 disabled:cursor-not-allowed disabled:opacity-50"
              onClick={removeAllTasks}
              disabled={loading || deletingAll || tasks.length === 0}
            >
              <Trash2 className="h-4 w-4" />
              {deletingAll ? "Deleting..." : "Delete All"}
            </button>
          </div>
        </div>

        <section className="mb-5 grid gap-3 rounded-lg border border-stroke bg-panel p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-sm font-semibold text-white">Preset website demos</h2>
              <p className="mt-1 text-xs text-slate-500">Run real Playwright browser tasks without a model API.</p>
            </div>
          </div>
          <div className="grid gap-3 lg:grid-cols-3">
            {PRESET_TASKS.map((preset) => {
              const Icon = presetIcons[preset.id as keyof typeof presetIcons] || Play;
              const isStarting = startingPresetId === preset.id;
              return (
                <article key={preset.id} className="rounded-lg border border-stroke bg-panelSoft p-3">
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-stroke bg-panel text-cyan-300">
                      <Icon className="h-4 w-4" />
                    </span>
                    <span className="rounded-md border border-stroke bg-panel px-2 py-1 text-[11px] font-semibold text-slate-500">
                      {preset.complexity}
                    </span>
                  </div>
                  <h3 className="line-clamp-2 min-h-[2.5rem] text-sm font-semibold text-white">{preset.title}</h3>
                  <p className="mt-2 line-clamp-2 min-h-[2.5rem] text-xs leading-5 text-slate-500">{preset.summary}</p>
                  <button
                    className="mt-3 inline-flex h-9 w-full items-center justify-center gap-2 rounded-md border border-cyan-400/50 bg-cyan-400/10 px-3 text-sm font-semibold text-cyan-100 transition hover:border-cyan-300 hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-60"
                    onClick={() => startPreset(preset)}
                    disabled={Boolean(startingPresetId)}
                  >
                    <Play className="h-4 w-4" />
                    {isStarting ? "Starting..." : "Run"}
                  </button>
                </article>
              );
            })}
          </div>
        </section>

        <section className="mb-5 grid gap-3 rounded-lg border border-stroke bg-panel p-4">
          <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_auto]">
            <label className="flex h-10 items-center gap-2 rounded-md border border-stroke px-3 theme-input">
              <Search className="h-4 w-4 text-slate-500" />
              <input
                className="min-w-0 flex-1 bg-transparent text-sm outline-none placeholder:text-slate-500"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search by title, message, run id, or status"
              />
            </label>
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <Filter className="h-3.5 w-3.5" />
                Status
              </span>
              {statusFilters.map((status) => (
                <button
                  key={status}
                  className={clsx(
                    "h-8 rounded-md border px-3 text-xs font-semibold capitalize transition",
                    statusFilter === status
                      ? "border-cyan-400/70 bg-cyan-400/10 text-cyan-100"
                      : "border-stroke bg-panelSoft text-slate-400 hover:border-cyan-400/45 hover:text-slate-100"
                  )}
                  onClick={() => setStatusFilter(status)}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>
          <div className="text-xs text-slate-500">
            Showing {visibleTasks.length} of {tasks.length} tasks
          </div>
        </section>

        {loading ? <p className="text-sm text-slate-500">Loading task history...</p> : null}
        {error ? <p className="rounded-md border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</p> : null}

        {!loading && !error && tasks.length === 0 ? (
          <div className="rounded-lg border border-stroke bg-panel p-5">
            <h2 className="font-semibold text-white">No tasks yet</h2>
            <p className="mt-2 text-sm text-slate-500">Create a browser task from New Chat, then it will appear here.</p>
          </div>
        ) : null}

        {!loading && !error && tasks.length > 0 && visibleTasks.length === 0 ? (
          <div className="rounded-lg border border-stroke bg-panel p-5">
            <h2 className="font-semibold text-white">No matching tasks</h2>
            <p className="mt-2 text-sm text-slate-500">Clear the search text or change the status filter.</p>
          </div>
        ) : null}

        <div className="grid gap-3">
          {visibleTasks.map((task) => (
            <article
              key={task.id}
              className="group rounded-lg border border-stroke bg-panel p-4 transition hover:border-cyan-400/50 hover:shadow-glow"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <StatusBadge status={task.status} />
                    <span className="text-xs text-slate-500">{task.id}</span>
                  </div>
                  <h2 className="line-clamp-2 text-base font-semibold text-white">{task.title}</h2>
                  <p className="mt-2 line-clamp-2 text-sm text-slate-400">{lastMessage(task)}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Link
                    href={`/runs/${task.id}`}
                    className="grid h-9 w-9 place-items-center rounded-md border border-stroke bg-panelSoft text-slate-400 transition hover:border-cyan-400/50 hover:text-cyan-300"
                    aria-label={`Open ${task.title}`}
                    title="Open task"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Link>
                  <button
                    className="grid h-9 w-9 place-items-center rounded-md border border-red-400/35 bg-red-500/10 text-red-300 transition hover:border-red-400/60 hover:bg-red-500/15 disabled:cursor-not-allowed disabled:opacity-50"
                    onClick={() => removeTask(task)}
                    disabled={deletingAll || deletingId === task.id}
                    aria-label={`Delete ${task.title}`}
                    title="Delete task"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-500">
                <span className="inline-flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5" />
                  {formatDate(task.startedAt)}
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <MessageSquare className="h-3.5 w-3.5" />
                  {task.messages.length} messages
                </span>
                <span>{task.timeline.length} steps</span>
                {task.extracted ? <span>Extracted output ready</span> : null}
              </div>
            </article>
          ))}
        </div>
      </main>
    </div>
  );
}
