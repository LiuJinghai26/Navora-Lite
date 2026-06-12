import { AppSidebar } from "@/components/app-sidebar";
import { Monitor, Radio } from "lucide-react";

export default function SessionsPage() {
  return (
    <div className="flex min-h-screen flex-col bg-surface md:flex-row">
      <AppSidebar />
      <main className="flex-1 px-6 py-6">
        <h1 className="mb-5 border-b border-stroke pb-4 text-xl font-semibold text-white">Sessions</h1>
        <div className="grid max-w-4xl gap-3">
          <article className="flex items-center justify-between rounded-lg border border-stroke bg-panel p-5">
            <div className="flex items-center gap-3">
              <Monitor className="h-5 w-5 text-cyan-300" />
              <div>
                <h2 className="font-semibold text-white">Chromium</h2>
                <p className="text-sm text-slate-500">1280 x 800</p>
              </div>
            </div>
            <span className="inline-flex items-center gap-2 rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-200">
              <Radio className="h-3.5 w-3.5" />
              Ready
            </span>
          </article>
        </div>
      </main>
    </div>
  );
}
