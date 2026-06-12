"use client";

import { AppSidebar } from "@/components/app-sidebar";
import { ModelSettingsDialog } from "@/components/model-settings-dialog";
import { SlidersHorizontal } from "lucide-react";
import { useState } from "react";

export default function SettingsPage() {
  const [open, setOpen] = useState(false);
  return (
    <div className="flex min-h-screen flex-col bg-surface md:flex-row">
      <AppSidebar />
      <main className="flex-1 px-6 py-6">
        <div className="mb-5 flex items-center justify-between border-b border-stroke pb-4">
          <h1 className="text-xl font-semibold text-white">Settings</h1>
          <button
            className="inline-flex h-9 items-center gap-2 rounded-md bg-cyan-500 px-3 text-sm font-semibold text-slate-950"
            onClick={() => setOpen(true)}
          >
            <SlidersHorizontal className="h-4 w-4" />
            Model
          </button>
        </div>
        <div className="grid max-w-3xl gap-3 rounded-lg border border-stroke bg-panel p-5">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="text-slate-500">MODEL_PROVIDER</div>
            <div className="text-slate-100">openai-compatible</div>
            <div className="text-slate-500">MODEL_NAME</div>
            <div className="text-slate-100">qwen3-32b</div>
            <div className="text-slate-500">API_BASE</div>
            <div className="text-slate-100">http://localhost:8001/v1</div>
            <div className="text-slate-500">BROWSER_HEADLESS</div>
            <div className="text-slate-100">true</div>
          </div>
        </div>
        <ModelSettingsDialog open={open} onClose={() => setOpen(false)} />
      </main>
    </div>
  );
}
