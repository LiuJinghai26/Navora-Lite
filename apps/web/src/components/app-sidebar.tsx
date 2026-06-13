"use client";

import clsx from "clsx";
import { Home, ListChecks, Monitor, Play, Settings } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const nav = [
  { label: "Home", href: "/runs/demo", icon: Home },
  { label: "Tasks", href: "/tasks", icon: ListChecks },
  { label: "Runs", href: "/runs/demo", icon: Play },
  { label: "Sessions", href: "/sessions", icon: Monitor },
  { label: "Settings", href: "/settings", icon: Settings }
];

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-full shrink-0 flex-col border-b border-stroke px-4 py-4 md:sticky md:top-0 md:h-screen md:w-[244px] md:overflow-y-auto md:border-b-0 md:border-r md:py-5" style={{ background: "var(--color-sidebar)" }}>
      <Link href="/runs/demo" className="mb-4 flex items-center gap-3 md:mb-7">
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
            (item.label === "Runs" && pathname.startsWith("/runs")) ||
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
