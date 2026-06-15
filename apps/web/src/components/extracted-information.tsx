"use client";

import { Check, Copy } from "lucide-react";
import { useMemo, useState } from "react";

export function ExtractedInformation({ data }: { data: unknown }) {
  const [copied, setCopied] = useState(false);
  // Memoize formatted JSON so copying and rendering use the exact same text.
  const text = useMemo(() => JSON.stringify(data ?? {}, null, 2), [data]);
  const lines = text.split("\n");

  const copy = async () => {
    // Reset the copied state shortly after the clipboard write for lightweight feedback.
    await navigator.clipboard.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  };

  return (
    <section className="min-w-0 rounded-lg border border-stroke bg-panel">
      <div className="flex items-center justify-between border-b border-stroke px-4 py-3">
        <h2 className="text-sm font-semibold text-white">Extracted Information</h2>
        <button
          className="inline-flex h-8 items-center gap-2 rounded-md border border-stroke bg-panelSoft px-2.5 text-xs text-slate-200 hover:border-cyan-400/50"
          onClick={copy}
        >
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? "Copied" : "Copy JSON"}
        </button>
      </div>
      <div className="min-w-0 overflow-auto p-4">
        {data ? (
          <pre className="grid min-w-0 gap-0.5 text-sm leading-6 text-cyan-100">
            {lines.map((line, index) => (
              <code key={`${line}-${index}`} className="grid min-w-0 grid-cols-[40px_minmax(0,1fr)] gap-3">
                <span className="select-none text-right text-slate-600">{index + 1}</span>
                <span className="min-w-0">{line}</span>
              </code>
            ))}
          </pre>
        ) : (
          <div className="rounded-md border border-dashed border-stroke p-6 text-sm text-slate-500">No extracted data</div>
        )}
      </div>
    </section>
  );
}
