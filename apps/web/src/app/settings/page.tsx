"use client";

import { AppSidebar } from "@/components/app-sidebar";
import { ModelSettingsDialog } from "@/components/model-settings-dialog";
import { getSettings } from "@/lib/api";
import { getStoredTheme, storeTheme, THEME_OPTIONS, type ThemeName } from "@/lib/theme";
import clsx from "clsx";
import { Cpu, Palette, Server, SlidersHorizontal } from "lucide-react";
import { useEffect, useState } from "react";

type SettingsRecord = Record<string, unknown>;

function value(settings: SettingsRecord | null, key: string, fallback = "Not configured") {
  // Keep settings summary readable while the backend is still loading.
  const current = settings?.[key];
  if (current === undefined || current === null || current === "") return fallback;
  return String(current);
}

export default function SettingsPage() {
  const [open, setOpen] = useState(false);
  const [settings, setSettings] = useState<SettingsRecord | null>(null);
  const [theme, setTheme] = useState<ThemeName>("deep-blue");
  const [error, setError] = useState("");

  useEffect(() => {
    // Theme is local to the browser; model settings come from the FastAPI backend.
    setTheme(getStoredTheme());
    getSettings()
      .then(setSettings)
      .catch(() => setError("Backend settings are unavailable. Start the FastAPI server to edit model configuration."));
  }, []);

  const selectTheme = (nextTheme: ThemeName) => {
    // Persist and broadcast theme changes through the shared theme helper.
    setTheme(nextTheme);
    storeTheme(nextTheme);
  };

  return (
    <div className="flex min-h-screen flex-col bg-surface md:flex-row">
      <AppSidebar />
      <main className="min-w-0 flex-1 px-6 py-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-stroke pb-4">
          <div>
            <h1 className="text-xl font-semibold text-white">Settings</h1>
            <p className="mt-1 text-sm text-slate-500">Manage the display theme, model endpoint, and browser runtime defaults.</p>
          </div>
          <button
            className="inline-flex h-9 items-center gap-2 rounded-md bg-cyan-500 px-3 text-sm font-semibold text-slate-950"
            onClick={() => setOpen(true)}
          >
            <SlidersHorizontal className="h-4 w-4" />
            Edit Model
          </button>
        </div>

        {error ? <p className="mb-4 rounded-md border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</p> : null}

        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(340px,0.8fr)]">
          <section className="rounded-lg border border-stroke bg-panel p-5">
            <div className="mb-4 flex items-center gap-3">
              <Palette className="h-5 w-5 text-cyan-300" />
              <div>
                <h2 className="font-semibold text-white">Display Theme</h2>
                <p className="text-sm text-slate-500">Choose how Navora Lite should look on this device.</p>
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              {THEME_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  className={clsx(
                    "min-h-[106px] rounded-lg border p-4 text-left transition",
                    theme === option.value
                      ? "border-cyan-400/70 bg-cyan-400/10 shadow-glow"
                      : "border-stroke bg-panelSoft hover:border-cyan-400/45"
                  )}
                  onClick={() => selectTheme(option.value)}
                >
                  <span className="block text-sm font-semibold text-white">{option.label}</span>
                  <span className="mt-2 block text-xs leading-5 text-slate-500">{option.description}</span>
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-lg border border-stroke bg-panel p-5">
            <div className="mb-4 flex items-center gap-3">
              <Server className="h-5 w-5 text-cyan-300" />
              <div>
                <h2 className="font-semibold text-white">Current Model</h2>
                <p className="text-sm text-slate-500">These values are read from the backend `.env` file.</p>
              </div>
            </div>
            <div className="grid gap-3 text-sm">
              <div className="flex justify-between gap-4 border-b border-stroke pb-2">
                <span className="text-slate-500">Provider</span>
                <span className="text-right font-medium text-slate-100">{value(settings, "MODEL_PROVIDER")}</span>
              </div>
              <div className="flex justify-between gap-4 border-b border-stroke pb-2">
                <span className="text-slate-500">Model</span>
                <span className="text-right font-medium text-slate-100">{value(settings, "MODEL_NAME")}</span>
              </div>
              <div className="flex justify-between gap-4 border-b border-stroke pb-2">
                <span className="text-slate-500">API Base</span>
                <span className="text-right font-medium text-slate-100">{value(settings, "API_BASE")}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-slate-500">Browser Headless</span>
                <span className="text-right font-medium text-slate-100">{value(settings, "BROWSER_HEADLESS")}</span>
              </div>
            </div>
          </section>

          <section className="rounded-lg border border-stroke bg-panel p-5 xl:col-span-2">
            <div className="mb-4 flex items-center gap-3">
              <Cpu className="h-5 w-5 text-cyan-300" />
              <div>
                <h2 className="font-semibold text-white">Local Model Hints</h2>
                <p className="text-sm text-slate-500">Navora calls local models through an OpenAI-compatible `/v1` endpoint.</p>
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-lg border border-stroke bg-panelSoft p-4">
                <h3 className="text-sm font-semibold text-white">Ollama</h3>
                <p className="mt-2 text-xs leading-5 text-slate-500">Provider `ollama`, base `http://localhost:11434/v1`, API key can be empty.</p>
              </div>
              <div className="rounded-lg border border-stroke bg-panelSoft p-4">
                <h3 className="text-sm font-semibold text-white">LM Studio</h3>
                <p className="mt-2 text-xs leading-5 text-slate-500">Provider `lmstudio`, base `http://localhost:1234/v1`, use the loaded local model name.</p>
              </div>
              <div className="rounded-lg border border-stroke bg-panelSoft p-4">
                <h3 className="text-sm font-semibold text-white">vLLM</h3>
                <p className="mt-2 text-xs leading-5 text-slate-500">Provider `vllm`, base like `http://localhost:8001/v1`, model name should match the served model.</p>
              </div>
            </div>
          </section>
        </div>

        <ModelSettingsDialog open={open} settings={settings} onClose={() => setOpen(false)} onSaved={setSettings} />
      </main>
    </div>
  );
}
