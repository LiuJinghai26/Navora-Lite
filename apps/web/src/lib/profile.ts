export interface UserProfile {
  name: string;
  email: string;
  role: string;
  initials: string;
}

export const PROFILE_STORAGE_KEY = "navora-user-profile";
export const PROFILE_UPDATED_EVENT = "navora-profile-updated";

export const DEFAULT_PROFILE: UserProfile = {
  name: "Jinghai Liu",
  email: "jinghai@example.com",
  role: "Personal account",
  initials: "JL"
};

function normalizeInitials(value: string, name: string) {
  const trimmed = value.trim().slice(0, 3);
  if (trimmed) return trimmed.toUpperCase();
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase() || DEFAULT_PROFILE.initials;
}

export function normalizeProfile(profile: UserProfile): UserProfile {
  const name = profile.name.trim() || DEFAULT_PROFILE.name;
  return {
    name,
    email: profile.email.trim(),
    role: profile.role.trim() || DEFAULT_PROFILE.role,
    initials: normalizeInitials(profile.initials, name)
  };
}

export function readStoredProfile(): UserProfile {
  if (typeof window === "undefined") return DEFAULT_PROFILE;
  try {
    const raw = window.localStorage.getItem(PROFILE_STORAGE_KEY);
    if (!raw) return DEFAULT_PROFILE;
    const parsed = JSON.parse(raw) as Partial<UserProfile>;
    return normalizeProfile({
      name: parsed.name || DEFAULT_PROFILE.name,
      email: parsed.email || DEFAULT_PROFILE.email,
      role: parsed.role || DEFAULT_PROFILE.role,
      initials: parsed.initials || DEFAULT_PROFILE.initials
    });
  } catch {
    return DEFAULT_PROFILE;
  }
}

export function storeProfile(profile: UserProfile) {
  const normalized = normalizeProfile(profile);
  window.localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(normalized));
  window.dispatchEvent(new CustomEvent(PROFILE_UPDATED_EVENT, { detail: normalized }));
  return normalized;
}
