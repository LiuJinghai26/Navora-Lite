"use client";

import { X } from "lucide-react";
import { useEffect, useState } from "react";

const defaults = {
  MODEL_PROVIDER: "openai-compatible",
  MODEL_NAME: "qwen3-32b",
  API_BASE: "http://localhost:8001/v1",
  API_KEY: "",
  MAX_TOKENS: "4096",
  TEMPERATURE: "0.2",
  BROWSER_HEADLESS: "true"
};

export function ModelSettingsDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [form, setForm] = useState(defaults);

  useEffect(() => {
    const raw = localStorage.getItem("navora-model-settings");
    if (raw) setForm({ ...defaults, ...JSON.parse(raw) });
  }, []);

  if (!open) return null;

  const save = () => {
    localStorage.setItem("navora-model-settings", JSON.stringify(form));
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-5" onClick={onClose}>
      <div className="w-full max-w-xl rounded-lg border border-stroke bg-panel p-5" onClick={(event) => event.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Model Settings</h2>
          <button className="grid h-8 w-8 place-items-center rounded-md border border-stroke" onClick={onClose} aria-label="Close settings">
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="grid gap-3">
          {Object.entries(form).map(([key, value]) => (
            <label key={key} className="grid gap-1 text-xs font-semibold text-slate-400">
              {key}
              <input
                className="h-10 rounded-md border border-stroke bg-[#050b14] px-3 text-sm text-slate-100 outline-none focus:border-cyan-400/60"
                value={value}
                onChange={(event) => setForm((current) => ({ ...current, [key]: event.target.value }))}
              />
            </label>
          ))}
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button className="h-9 rounded-md border border-stroke px-3 text-sm text-slate-300" onClick={onClose}>
            Cancel
          </button>
          <button className="h-9 rounded-md bg-cyan-500 px-3 text-sm font-semibold text-slate-950" onClick={save}>
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

