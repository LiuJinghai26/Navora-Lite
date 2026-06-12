"use client";

import { X } from "lucide-react";

export function FullscreenPreviewDialog({
  open,
  imageUrl,
  onClose
}: {
  open: boolean;
  imageUrl: string;
  onClose: () => void;
}) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/80 p-5" onClick={onClose}>
      <div className="relative w-full max-w-6xl rounded-lg border border-stroke bg-panel p-3" onClick={(event) => event.stopPropagation()}>
        <button
          className="absolute right-4 top-4 z-10 grid h-9 w-9 place-items-center rounded-md border border-stroke bg-[#050b14] text-slate-200"
          onClick={onClose}
          aria-label="Close fullscreen preview"
        >
          <X className="h-4 w-4" />
        </button>
        <img className="max-h-[82vh] w-full rounded-md object-contain" src={imageUrl} alt="Fullscreen browser preview" />
      </div>
    </div>
  );
}

