// Client-side auth state. The API key and user id are kept in localStorage;
// the http helpers read these on every request. Falls back to the values
// baked at build time (NEXT_PUBLIC_API_KEY) if localStorage is empty.

const API_KEY_STORAGE = "corpusai.api_key";
const USER_ID_STORAGE = "corpusai.user_id";

const FALLBACK_API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

export function getApiKey(): string {
  if (!isBrowser()) return FALLBACK_API_KEY;
  return window.localStorage.getItem(API_KEY_STORAGE) ?? FALLBACK_API_KEY;
}

export function setApiKey(key: string): void {
  if (!isBrowser()) return;
  if (key) window.localStorage.setItem(API_KEY_STORAGE, key);
  else window.localStorage.removeItem(API_KEY_STORAGE);
}

export function getUserId(): string {
  if (!isBrowser()) return "";
  return window.localStorage.getItem(USER_ID_STORAGE) ?? "";
}

export function setUserId(value: string): void {
  if (!isBrowser()) return;
  const cleaned = value.trim();
  if (cleaned) window.localStorage.setItem(USER_ID_STORAGE, cleaned);
  else window.localStorage.removeItem(USER_ID_STORAGE);
}
