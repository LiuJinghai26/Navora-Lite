"use client";

import { AppSidebar } from "@/components/app-sidebar";
import { getTasks } from "@/lib/api";
import { buildRunStats, failureLabels } from "@/lib/run-stats";
import type { FailureType, Run } from "@/lib/types";
import clsx from "clsx";
import { AlertTriangle, BarChart3, CheckCircle2, Clock3, ExternalLink, ListChecks, XCircle } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type FailureFilter = "all" | FailureType;

const failureFilters: FailureFilter[] = ["all", "recognition_failed", "planning_failed", "execution_failed"];

function formatDate(value?: string) {
  if (!value) return "Unknown";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit"
  }).format(new Date(value));
}

function formatDuration(value?: number) {
  if (!value) return "n/a";
  if (value < 1000) return `${value} ms`;
  return `${(value / 1000).toFixed(1)} s`;
}

function statCards(stats: ReturnType<typeof buildRunStats>) {
  return [
    { label: "Success rate", value: `${stats.successRate}%`, detail: `${stats.completed} completed`, icon: CheckCircle2 },
    { label: "Terminal runs", value: stats.total, detail: `${stats.failed} failed`, icon: BarChart3 },
    { label: "Running", value: stats.running, detail: `${stats.idle} idle`, icon: Clock3 },
    { label: "Stopped", value: stats.stopped, detail: "User stopped", icon: XCircle }
  ];
}

export default function StatsPage() {
  const [tasks, setTasks] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [failureFilter, setFailureFilter] = useState<FailureFilter>("all");

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    setError("");
    getTasks()
      .then((items) => {
        if (mounted) setTasks(items);
      })
      .catch(() => {
        if (mounted) setError("Could not load run statistics. Start the FastAPI backend and try again.");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const stats = useMemo(() => buildRunStats(tasks), [tasks]);
  const visibleFailures = useMemo(
    () =>
      stats.failureRecords.filter((record) => failureFilter === "all" || record.failureType === failureFilter),
    [failureFilter, stats.failureRecords]
  );

  return (
    <div className="flex min-h-screen flex-col bg-surface md:flex-row">
      <AppSidebar />
      <main className="min-w-0 flex-1 px-6 py-6">
        <header className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-stroke pb-4">
          <div>
            <h1 className="text-xl font-semibold text-white">Stats</h1>
            <p className="mt-1 text-sm text-slate-500">Run reliability, failure categories, and detailed error records.</p>
          </div>
          <Link
            href="/tasks"
            className="inline-flex h-9 items-center gap-2 rounded-md border border-stroke bg-panelSoft px-3 text-sm font-semibold text-slate-200 hover:border-cyan-400/50"
          >
            <ListChecks className="h-4 w-4" />
            Tasks
          </Link>
        </header>

        {loading ? <p className="text-sm text-slate-500">Loading statistics...</p> : null}
        {error ? <p className="rounded-md border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</p> : null}

        {!loading && !error ? (
          <div className="grid gap-5">
            <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {statCards(stats).map((card) => {
                const Icon = card.icon;
                return (
                  <div key={card.label} className="rounded-lg border border-stroke bg-panel p-4">
                    <div className="mb-3 flex items-center justify-between gap-2">
                      <span className="text-xs font-semibold uppercase text-slate-500">{card.label}</span>
                      <Icon className="h-4 w-4 text-cyan-300" />
                    </div>
                    <div className="text-2xl font-semibold text-white">{card.value}</div>
                    <div className="mt-1 text-xs text-slate-500">{card.detail}</div>
                  </div>
                );
              })}
            </section>

            <section className="grid gap-5 xl:grid-cols-[320px_minmax(0,1fr)]">
              <div className="rounded-lg border border-stroke bg-panel p-4">
                <div className="mb-4 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-amber-300" />
                  <h2 className="text-sm font-semibold text-white">Failure breakdown</h2>
                </div>
                <div className="grid gap-2">
                  {(Object.keys(failureLabels) as FailureType[]).map((type) => (
                    <button
                      key={type}
                      className={clsx(
                        "flex h-10 items-center justify-between rounded-md border px-3 text-sm transition",
                        failureFilter === type
                          ? "border-cyan-400/60 bg-cyan-400/10 text-cyan-100"
                          : "border-stroke bg-panelSoft text-slate-300 hover:border-cyan-400/45"
                      )}
                      onClick={() => setFailureFilter(type)}
                    >
                      <span>{failureLabels[type]}失败</span>
                      <span className="font-semibold">{stats.failures[type]}</span>
                    </button>
                  ))}
                  <button
                    className={clsx(
                      "flex h-10 items-center justify-between rounded-md border px-3 text-sm transition",
                      failureFilter === "all"
                        ? "border-cyan-400/60 bg-cyan-400/10 text-cyan-100"
                        : "border-stroke bg-panelSoft text-slate-300 hover:border-cyan-400/45"
                    )}
                    onClick={() => setFailureFilter("all")}
                  >
                    <span>All failures</span>
                    <span className="font-semibold">{stats.failed}</span>
                  </button>
                </div>
              </div>

              <div className="rounded-lg border border-stroke bg-panel">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-stroke px-4 py-3">
                  <h2 className="text-sm font-semibold text-white">Failure records</h2>
                  <span className="text-xs text-slate-500">{visibleFailures.length} records</span>
                </div>

                {visibleFailures.length === 0 ? (
                  <div className="p-4 text-sm text-slate-500">No failure records for this filter.</div>
                ) : (
                  <div className="divide-y divide-stroke">
                    {visibleFailures.map((record) => (
                      <article key={record.run.id} className="grid gap-3 p-4">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div className="min-w-0">
                            <div className="mb-2 flex flex-wrap items-center gap-2">
                              <span className="rounded-md border border-red-400/35 bg-red-500/10 px-2 py-1 text-xs font-semibold text-red-200">
                                {failureLabels[record.failureType]}失败
                              </span>
                              <span className="text-xs text-slate-500">{formatDate(record.occurredAt)}</span>
                              <span className="text-xs text-slate-500">{formatDuration(record.run.durationMs)}</span>
                            </div>
                            <h3 className="break-words text-sm font-semibold text-white">{record.run.title}</h3>
                            <p className="mt-1 break-words text-xs leading-5 text-slate-500">{record.run.id}</p>
                          </div>
                          <Link
                            href={`/runs/${record.run.id}`}
                            className="inline-flex h-8 shrink-0 items-center gap-1.5 rounded-md border border-stroke bg-panelSoft px-2.5 text-xs font-semibold text-slate-200 hover:border-cyan-400/50"
                          >
                            <ExternalLink className="h-3.5 w-3.5" />
                            Open
                          </Link>
                        </div>

                        <div className="grid gap-2 text-sm">
                          <div>
                            <div className="mb-1 text-xs font-semibold uppercase text-slate-500">Error</div>
                            <p className="break-words rounded-md border border-stroke bg-panelSoft px-3 py-2 text-slate-200">
                              {record.error || "No error text captured."}
                            </p>
                          </div>
                          <div className="grid gap-2 lg:grid-cols-2">
                            <div>
                              <div className="mb-1 text-xs font-semibold uppercase text-slate-500">Failed step</div>
                              <p className="break-words rounded-md border border-stroke bg-panelSoft px-3 py-2 text-slate-300">
                                {record.failedStep
                                  ? `${record.failedStep.index}. ${record.failedStep.action} - ${record.failedStep.description}`
                                  : "No failed step recorded."}
                              </p>
                            </div>
                            <div>
                              <div className="mb-1 text-xs font-semibold uppercase text-slate-500">Latest message</div>
                              <p className="break-words rounded-md border border-stroke bg-panelSoft px-3 py-2 text-slate-300">
                                {record.message}
                              </p>
                            </div>
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
              </div>
            </section>
          </div>
        ) : null}
      </main>
    </div>
  );
}
