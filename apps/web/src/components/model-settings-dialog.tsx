"use client";

import { getSettings, saveSettings } from "@/lib/api";
import { Check, Cpu, X } from "lucide-react";
import { useEffect, useState } from "react";

type SettingsRecord = Record<string, unknown>;

interface FormState {
  MODEL_PROVIDER: string;
  MODEL_NAME: string;
  API_BASE: string;
  API_KEY: string;
  MAX_TOKENS: string;
  TEMPERATURE: string;
  BROWSER_HEADLESS: string;
}

const defaults: FormState = {
  MODEL_PROVIDER: "openai-compatible",
  MODEL_NAME: "qwen3-32b",
  API_BASE: "",
  API_KEY: "",
  MAX_TOKENS: "4096",
  TEMPERATURE: "0.2",
  BROWSER_HEADLESS: "true"
};

const providers = [
  { value: "openai-compatible", label: "OpenAI-compatible" },
  { value: "ollama", label: "Ollama local" },
  { value: "lmstudio", label: "LM Studio local" },
  { value: "vllm", label: "vLLM local" },
  { value: "custom", label: "Custom local" }
];

const presets = [
  {
    label: "Ollama",
    values: { MODEL_PROVIDER: "ollama", MODEL_NAME: "qwen3:latest", API_BASE: "http://localhost:11434/v1", API_KEY: "" }
  },
  {
    label: "LM Studio",
    values: { MODEL_PROVIDER: "lmstudio", MODEL_NAME: "qwen3-4bit", API_BASE: "http://localhost:1234/v1", API_KEY: "" }
  },
  {
    label: "vLLM",
    values: { MODEL_PROVIDER: "vllm", MODEL_NAME: "Qwen/Qwen3-32B", API_BASE: "http://localhost:8001/v1", API_KEY: "" }
  }
];

function toForm(settings?: SettingsRecord | null): FormState {
  if (!settings) return defaults;
  return {
    MODEL_PROVIDER: String(settings.MODEL_PROVIDER ?? defaults.MODEL_PROVIDER),
    MODEL_NAME: String(settings.MODEL_NAME ?? defaults.MODEL_NAME),
    API_BASE: String(settings.API_BASE ?? defaults.API_BASE),
    API_KEY: String(settings.API_KEY ?? defaults.API_KEY),
    MAX_TOKENS: String(settings.MAX_TOKENS ?? defaults.MAX_TOKENS),
    TEMPERATURE: String(settings.TEMPERATURE ?? defaults.TEMPERATURE),
    BROWSER_HEADLESS: String(settings.BROWSER_HEADLESS ?? defaults.BROWSER_HEADLESS)
  };
}

function toPayload(form: FormState) {
  return {
    MODEL_PROVIDER: form.MODEL_PROVIDER,
    MODEL_NAME: form.MODEL_NAME,
    API_BASE: form.API_BASE,
    API_KEY: form.API_KEY,
    MAX_TOKENS: Number.parseInt(form.MAX_TOKENS, 10) || 4096,
    TEMPERATURE: Number.parseFloat(form.TEMPERATURE) || 0.2,
    BROWSER_HEADLESS: form.BROWSER_HEADLESS === "true"
  };
}

export function ModelSettingsDialog({
  open,
  settings,
  onClose,
  onSaved
}: {
  open: boolean;
  settings?: SettingsRecord | null;
  onClose: () => void;
  onSaved: (settings: SettingsRecord) => void;
}) {
  const [form, setForm] = useState<FormState>(toForm(settings));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setError("");
    if (settings) {
      setForm(toForm(settings));
      return;
    }
    getSettings()
      .then((loaded) => {
        setForm(toForm(loaded));
        onSaved(loaded);
      })
      .catch(() => setError("Could not load current backend settings."));
  }, [open, settings, onSaved]);

  if (!open) return null;

  const setValue = (key: keyof FormState, value: string) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const save = async () => {
    setSaving(true);
    setError("");
    try {
      const updated = await saveSettings(toPayload(form));
      onSaved(updated);
      onClose();
    } catch {
      setError("Could not save settings. Check that the backend is running.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/80 p-5 backdrop-blur-sm" onClick={onClose}>
      <div
        className="w-full max-w-2xl rounded-lg border-2 border-cyan-400/45 bg-panel p-5 shadow-glow"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mb-5 flex items-start justify-between gap-4 border-b border-stroke pb-4">
          <div>
            <h2 className="text-lg font-semibold text-white">Model Connection</h2>
            <p className="mt-1 text-sm text-slate-500">
              Configure an OpenAI-compatible endpoint. Local providers can leave the API key empty.
            </p>
          </div>
          <button
            className="grid h-9 w-9 place-items-center rounded-md border border-stroke bg-panelSoft text-slate-200 hover:border-cyan-400/50"
            onClick={onClose}
            aria-label="Close settings"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mb-4 flex flex-wrap gap-2">
          {presets.map((preset) => (
            <button
              key={preset.label}
              className="inline-flex h-9 items-center gap-2 rounded-md border border-stroke bg-panelSoft px-3 text-sm font-semibold text-slate-200 hover:border-cyan-400/50"
              onClick={() => setForm((current) => ({ ...current, ...preset.values }))}
            >
              <Cpu className="h-4 w-4" />
              {preset.label}
            </button>
          ))}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="grid gap-1.5 text-xs font-semibold text-slate-400">
            MODEL_PROVIDER
            <select
              className="h-10 rounded-md border border-stroke px-3 text-sm outline-none focus:border-cyan-400/60 theme-input"
              value={form.MODEL_PROVIDER}
              onChange={(event) => setValue("MODEL_PROVIDER", event.target.value)}
            >
              {providers.map((provider) => (
                <option key={provider.value} value={provider.value}>
                  {provider.label}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1.5 text-xs font-semibold text-slate-400">
            MODEL_NAME
            <input
              className="h-10 rounded-md border border-stroke px-3 text-sm outline-none focus:border-cyan-400/60 theme-input"
              value={form.MODEL_NAME}
              onChange={(event) => setValue("MODEL_NAME", event.target.value)}
            />
          </label>
          <label className="grid gap-1.5 text-xs font-semibold text-slate-400 md:col-span-2">
            API_BASE
            <input
              className="h-10 rounded-md border border-stroke px-3 text-sm outline-none focus:border-cyan-400/60 theme-input"
              value={form.API_BASE}
              placeholder="http://localhost:11434/v1"
              onChange={(event) => setValue("API_BASE", event.target.value)}
            />
            <span className="text-xs font-normal text-slate-500">Use the `/v1` base URL. The backend appends `/chat/completions`.</span>
          </label>
          <label className="grid gap-1.5 text-xs font-semibold text-slate-400">
            API_KEY
            <input
              className="h-10 rounded-md border border-stroke px-3 text-sm outline-none focus:border-cyan-400/60 theme-input"
              type="password"
              value={form.API_KEY}
              placeholder="Optional for local providers"
              onFocus={() => {
                if (form.API_KEY === "********") setValue("API_KEY", "");
              }}
              onChange={(event) => setValue("API_KEY", event.target.value)}
            />
          </label>
          <label className="grid gap-1.5 text-xs font-semibold text-slate-400">
            BROWSER_HEADLESS
            <select
              className="h-10 rounded-md border border-stroke px-3 text-sm outline-none focus:border-cyan-400/60 theme-input"
              value={form.BROWSER_HEADLESS}
              onChange={(event) => setValue("BROWSER_HEADLESS", event.target.value)}
            >
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </label>
          <label className="grid gap-1.5 text-xs font-semibold text-slate-400">
            MAX_TOKENS
            <input
              className="h-10 rounded-md border border-stroke px-3 text-sm outline-none focus:border-cyan-400/60 theme-input"
              value={form.MAX_TOKENS}
              onChange={(event) => setValue("MAX_TOKENS", event.target.value)}
            />
          </label>
          <label className="grid gap-1.5 text-xs font-semibold text-slate-400">
            TEMPERATURE
            <input
              className="h-10 rounded-md border border-stroke px-3 text-sm outline-none focus:border-cyan-400/60 theme-input"
              value={form.TEMPERATURE}
              onChange={(event) => setValue("TEMPERATURE", event.target.value)}
            />
          </label>
        </div>

        {error ? <p className="mt-4 rounded-md border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</p> : null}

        <div className="mt-5 flex flex-wrap justify-end gap-2">
          <button className="h-9 rounded-md border border-stroke px-3 text-sm text-slate-300" onClick={onClose}>
            Cancel
          </button>
          <button
            className="inline-flex h-9 items-center gap-2 rounded-md bg-cyan-500 px-3 text-sm font-semibold text-slate-950 disabled:opacity-50"
            onClick={save}
            disabled={saving}
          >
            <Check className="h-4 w-4" />
            {saving ? "Saving" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
