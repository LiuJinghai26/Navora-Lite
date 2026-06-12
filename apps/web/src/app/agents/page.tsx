import { AppSidebar } from "@/components/app-sidebar";
import { Bot, ShieldCheck } from "lucide-react";

export default function AgentsPage() {
  return (
    <div className="flex min-h-screen flex-col bg-surface md:flex-row">
      <AppSidebar />
      <main className="flex-1 px-6 py-6">
        <h1 className="mb-5 border-b border-stroke pb-4 text-xl font-semibold text-white">Agents</h1>
        <div className="grid max-w-4xl gap-3 md:grid-cols-2">
          <article className="rounded-lg border border-stroke bg-panel p-5">
            <Bot className="mb-3 h-5 w-5 text-cyan-300" />
            <h2 className="font-semibold text-white">Navora Browser Agent</h2>
            <p className="mt-2 text-sm text-slate-400">Mock planner, OpenAI-compatible planner, Playwright execution.</p>
          </article>
          <article className="rounded-lg border border-stroke bg-panel p-5">
            <ShieldCheck className="mb-3 h-5 w-5 text-emerald-300" />
            <h2 className="font-semibold text-white">Safety Guard</h2>
            <p className="mt-2 text-sm text-slate-400">Payment, password, account deletion, captcha, and sensitive upload checks.</p>
          </article>
        </div>
      </main>
    </div>
  );
}
