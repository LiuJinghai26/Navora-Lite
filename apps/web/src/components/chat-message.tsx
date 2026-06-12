import { Check, Circle, Loader2, X } from "lucide-react";
import type { ChatMessage as ChatMessageType } from "@/lib/types";

function formatTime(value: string) {
  return new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", second: "2-digit" }).format(new Date(value));
}

function ChecklistIcon({ status }: { status: string }) {
  if (status === "success") return <Check className="h-3.5 w-3.5 text-emerald-300" />;
  if (status === "failed") return <X className="h-3.5 w-3.5 text-red-300" />;
  if (status === "running") return <Loader2 className="h-3.5 w-3.5 animate-spin text-sky-300" />;
  return <Circle className="h-3.5 w-3.5 text-slate-500" />;
}

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const label = message.role === "user" ? "User" : message.role === "system" ? "System" : "Navora";
  return (
    <div className="grid gap-2 rounded-lg border border-stroke bg-[#0b1424] p-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-semibold uppercase tracking-wide text-cyan-200">{label}</span>
        <span className="text-xs text-slate-500">{formatTime(message.createdAt)}</span>
      </div>
      <p className="text-sm leading-6 text-slate-100">{message.content}</p>
      {message.checklist?.length ? (
        <div className="grid gap-1.5 border-t border-stroke pt-2">
          {message.checklist.map((item) => (
            <div key={item.text} className="flex items-center gap-2 text-sm text-slate-300">
              <ChecklistIcon status={item.status} />
              <span>{item.text}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

