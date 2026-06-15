"use client";

import clsx from "clsx";
import { BarChart3, ListChecks, MessageSquare, Monitor, Settings } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { getTasks } from "@/lib/api";
import type { FailureType, Run } from "@/lib/types";

const nav = [
  { label: "New Chat", href: "/new-chat", icon: MessageSquare },
  { label: "Tasks", href: "/tasks", icon: ListChecks },
  { label: "Sessions", href: "/sessions", icon: Monitor },
  { label: "Settings", href: "/settings", icon: Settings }
];

const failureLabels: Record<FailureType, string> = {
  recognition_failed: "识别",
  planning_failed: "规划",
  execution_failed: "执行"
};

function failureTypeFor(run: Run): FailureType {
  if (run.failureType) return run.failureType;
  const failedStep = run.timeline.find((step) => step.status === "failed");
  if (failedStep?.action === "recognition") return "recognition_failed";
  if (failedStep?.action === "planning") return "planning_failed";
  return "execution_failed";
}

export function AppSidebar() {
  const pathname = usePathname();
  const [tasks, setTasks] = useState<Run[]>([]);

  useEffect(() => {
    let mounted = true;
    getTasks()
      .then((items) => {
        if (mounted) setTasks(items);
      })
      .catch(() => {
        if (mounted) setTasks([]);
      });
    return () => {
      mounted = false;
    };
  }, [pathname]);

  const stats = useMemo(() => {
    const terminal = tasks.filter((task) => ["completed", "failed", "stopped"].includes(task.status));
    const completed = terminal.filter((task) => task.status === "completed").length;
    const failed = terminal.filter((task) => task.status === "failed");
    const failures: Record<FailureType, number> = {
      recognition_failed: 0,
      planning_failed: 0,
      execution_failed: 0
    };
    for (const run of failed) {
      failures[failureTypeFor(run)] += 1;
    }
    return {
      total: terminal.length,
      completed,
      failed: failed.length,
      successRate: terminal.length ? Math.round((completed / terminal.length) * 100) : 0,
      failures
    };
  }, [tasks]);

  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-stroke px-4 py-4 md:sticky md:top-0 md:h-screen md:w-[244px] md:overflow-y-auto md:border-b-0 md:border-r md:py-5" style={{ background: "var(--color-sidebar)" }}>
      <Link href="/new-chat" className="mb-4 flex items-center gap-3 md:mb-7">
        <span className="relative grid h-10 w-10 place-items-center rounded-lg border border-cyan-400/40 bg-cyan-400/10 shadow-glow">
          <span className="absolute h-5 w-5 rotate-45 border-l-2 border-t-2 border-cyan-200" />
          <span className="text-sm font-black text-cyan-100">N</span>
        </span>
        <span>
          <span className="block text-sm font-bold text-white">Navora Lite</span>
          <span className="block text-xs text-slate-500">Browser Agent</span>
        </span>
      </Link>

      <nav className="grid grid-cols-2 gap-2 sm:grid-cols-5 md:block md:space-y-1">
        {nav.map((item) => {
          const active =
            pathname === item.href ||
            (item.label === "New Chat" && pathname.startsWith("/runs")) ||
            (item.label === "Tasks" && (pathname.startsWith("/tasks") || pathname.startsWith("/agents")));
          const Icon = item.icon;
          return (
            <Link
              key={item.label}
              href={item.href}
              className={clsx(
                "flex h-10 items-center gap-2 rounded-md px-3 text-sm font-medium transition md:gap-3",
                active
                  ? "border border-cyan-400/30 bg-cyan-400/10 text-cyan-100"
                  : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-100"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-4 hidden rounded-lg border border-stroke bg-panelSoft p-3 md:block">
        <div className="mb-3 flex items-center justify-between gap-2">
          <span className="inline-flex items-center gap-2 text-xs font-semibold uppercase text-slate-500">
            <BarChart3 className="h-3.5 w-3.5" />
            Stats
          </span>
          <span className="text-xs text-slate-500">{stats.total} runs</span>
        </div>
        <div className="mb-3 flex items-end justify-between">
          <div>
            <div className="text-2xl font-semibold text-white">{stats.successRate}%</div>
            <div className="text-xs text-slate-500">Success rate</div>
          </div>
          <div className="text-right text-xs text-slate-500">
            <div>{stats.completed} completed</div>
            <div>{stats.failed} failed</div>
          </div>
        </div>
        <div className="grid gap-1.5">
          {(Object.keys(failureLabels) as FailureType[]).map((type) => (
            <div key={type} className="flex items-center justify-between text-xs">
              <span className="text-slate-400">{failureLabels[type]}失败</span>
              <span className="font-semibold text-slate-200">{stats.failures[type]}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-auto hidden rounded-lg border border-stroke bg-panelSoft p-3 md:block">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-md bg-emerald-400/15 text-sm font-bold text-emerald-100">
            JL
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-100">Jinghai Liu</div>
            <div className="text-xs text-slate-500">Personal account</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
