"use client";

import { AppSidebar } from "@/components/app-sidebar";
import { DEFAULT_PROFILE, readStoredProfile, storeProfile, type UserProfile } from "@/lib/profile";
import { RotateCcw, Save, UserRound } from "lucide-react";
import { useEffect, useState } from "react";

const fields: Array<{ key: keyof UserProfile; label: string; type?: string; placeholder: string }> = [
  { key: "name", label: "Name", placeholder: "Your name" },
  { key: "email", label: "Email", type: "email", placeholder: "you@example.com" },
  { key: "role", label: "Role", placeholder: "Personal account" },
  { key: "initials", label: "Initials", placeholder: "JL" }
];

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile>(DEFAULT_PROFILE);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setProfile(readStoredProfile());
  }, []);

  const updateField = (key: keyof UserProfile, value: string) => {
    setSaved(false);
    setProfile((current) => ({ ...current, [key]: value }));
  };

  const saveProfile = () => {
    setProfile(storeProfile(profile));
    setSaved(true);
  };

  const resetProfile = () => {
    setProfile(DEFAULT_PROFILE);
    setSaved(false);
  };

  return (
    <div className="flex min-h-screen flex-col bg-surface md:flex-row">
      <AppSidebar />
      <main className="min-w-0 flex-1 px-6 py-6">
        <header className="mb-6 flex flex-wrap items-center justify-between gap-3 border-b border-stroke pb-4">
          <div>
            <h1 className="text-xl font-semibold text-white">Profile</h1>
            <p className="mt-1 text-sm text-slate-500">Manage the account details shown in the workspace sidebar.</p>
          </div>
        </header>

        <div className="grid gap-5 xl:grid-cols-[360px_minmax(0,1fr)]">
          <section className="rounded-lg border border-stroke bg-panel p-5">
            <div className="flex items-center gap-4">
              <div className="profile-avatar grid h-16 w-16 shrink-0 place-items-center rounded-lg text-lg font-bold">
                {profile.initials || DEFAULT_PROFILE.initials}
              </div>
              <div className="min-w-0">
                <h2 className="break-words text-lg font-semibold text-white">{profile.name || DEFAULT_PROFILE.name}</h2>
                <p className="mt-1 break-words text-sm text-slate-500">{profile.role || DEFAULT_PROFILE.role}</p>
                <p className="mt-1 break-words text-sm text-slate-400">{profile.email || DEFAULT_PROFILE.email}</p>
              </div>
            </div>
          </section>

          <section className="rounded-lg border border-stroke bg-panel p-5">
            <div className="mb-5 flex items-center gap-3">
              <UserRound className="h-5 w-5 text-cyan-300" />
              <h2 className="font-semibold text-white">Personal Details</h2>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {fields.map((field) => (
                <label key={field.key} className="grid gap-2 text-sm">
                  <span className="font-medium text-slate-300">{field.label}</span>
                  <input
                    className="h-10 rounded-md border border-stroke bg-panelSoft px-3 text-slate-100 outline-none placeholder:text-slate-600 focus:border-cyan-400/60"
                    type={field.type || "text"}
                    value={profile[field.key]}
                    onChange={(event) => updateField(field.key, event.target.value)}
                    placeholder={field.placeholder}
                  />
                </label>
              ))}
            </div>

            <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-stroke pt-4">
              <span className="text-sm text-emerald-200">{saved ? "Profile saved." : ""}</span>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  className="inline-flex h-9 items-center gap-2 rounded-md border border-stroke bg-panelSoft px-3 text-sm font-semibold text-slate-200 hover:border-cyan-400/50"
                  onClick={resetProfile}
                >
                  <RotateCcw className="h-4 w-4" />
                  Reset
                </button>
                <button
                  className="inline-flex h-9 items-center gap-2 rounded-md bg-cyan-500 px-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400"
                  onClick={saveProfile}
                >
                  <Save className="h-4 w-4" />
                  Save
                </button>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
