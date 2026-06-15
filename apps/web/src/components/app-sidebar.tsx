"use client";

import clsx from "clsx";
import { BarChart3, ListChecks, MessageSquare, Monitor, Settings } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { DEFAULT_PROFILE, PROFILE_UPDATED_EVENT, readStoredProfile, type UserProfile } from "@/lib/profile";
import { buildRunStats, failureLabels } from "@/lib/run-stats";
import { getCachedTasks, refreshTaskCache, subscribeTaskCache } from "@/lib/task-cache";
import type { FailureType, Run } from "@/lib/types";

const nav = [
  { label: "New Chat", href: "/new-chat", icon: MessageSquare },
  { label: "Tasks", href: "/tasks", icon: ListChecks },
  { label: "Sessions", href: "/sessions", icon: Monitor },
  { label: "Settings", href: "/settings", icon: Settings }
];

export function AppSidebar() {
  const pathname = usePathname();
  const [tasks, setTasks] = useState<Run[]>(() => getCachedTasks() || []);
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE);

  useEffect(() => {
    // Keep the last known stats visible while a background refresh fetches fresh history.
    const unsubscribe = subscribeTaskCache(setTasks);
    void refreshTaskCache().catch(() => undefined);
    return unsubscribe;
  }, []);

  useEffect(() => {
    setProfile(readStoredProfile());
    const updateProfile = () => setProfile(readStoredProfile());
    window.addEventListener(PROFILE_UPDATED_EVENT, updateProfile);
    window.addEventListener("storage", updateProfile);
    return () => {
      window.removeEventListener(PROFILE_UPDATED_EVENT, updateProfile);
      window.removeEventListener("storage", updateProfile);
    };
  }, []);

  const stats = useMemo(() => buildRunStats(tasks), [tasks]);

  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-stroke px-4 py-4 md:sticky md:top-0 md:h-screen md:w-[244px] md:overflow-y-auto md:border-b-0 md:border-r md:py-5" style={{ background: "var(--color-sidebar)" }}>
      <Link href="/new-chat" className="mb-4 flex items-center gap-3 md:mb-7">
        <span className="brand-logo relative grid h-10 w-10 place-items-center rounded-lg border">
          <span className="brand-logo-mark absolute h-5 w-5 rotate-45 border-l-2 border-t-2" />
          <span className="brand-logo-letter text-sm font-black">N</span>
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

      <Link
        href="/stats"
        className={clsx(
          "mt-4 hidden rounded-lg border p-3 transition md:block",
          pathname.startsWith("/stats")
            ? "border-cyan-400/40 bg-cyan-400/10"
            : "border-stroke bg-panelSoft hover:border-cyan-400/45 hover:bg-cyan-400/10"
        )}
        aria-label="Open detailed run statistics"
      >
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
      </Link>

      <Link
        href="/profile"
        className={clsx(
          "mt-auto hidden rounded-lg border p-3 transition md:block",
          pathname.startsWith("/profile")
            ? "border-cyan-400/40 bg-cyan-400/10"
            : "border-stroke bg-panelSoft hover:border-cyan-400/45 hover:bg-cyan-400/10"
        )}
        aria-label="Open profile"
      >
        <div className="flex items-center gap-3">
          <div className="profile-avatar grid h-9 w-9 place-items-center rounded-md text-sm font-bold">
            {profile.initials}
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-slate-100">{profile.name}</div>
            <div className="truncate text-xs text-slate-500">{profile.role}</div>
          </div>
        </div>
      </Link>
    </aside>
  );
}
