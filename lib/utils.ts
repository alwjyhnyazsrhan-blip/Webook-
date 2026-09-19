import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

export function formatDate(dateString?: string): string {
  if (!dateString) return "TBD";
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    const day = d.getUTCDate();
    const month = MONTHS[d.getUTCMonth()];
    const year = d.getUTCFullYear();
    const h = String(d.getUTCHours()).padStart(2, "0");
    const m = String(d.getUTCMinutes()).padStart(2, "0");
    return `${day} ${month} ${year}, ${h}:${m} UTC`;
  } catch {
    return dateString;
  }
}

export function formatTime(dateString?: string): string {
  if (!dateString) return "--:--:--";
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return "--:--:--";
    const h = String(d.getUTCHours()).padStart(2, "0");
    const m = String(d.getUTCMinutes()).padStart(2, "0");
    const s = String(d.getUTCSeconds()).padStart(2, "0");
    return `${h}:${m}:${s} UTC`;
  } catch {
    return "--:--:--";
  }
}

export function formatPrice(price?: number): string {
  if (price === undefined || price === null || price === 0) return "Free";
  return `SAR ${price.toLocaleString("en-US")}`;
}

export function getWebookEventUrl(slug: string): string {
  if (!slug) return "https://webook.com/ar";
  if (slug.startsWith("http://") || slug.startsWith("https://")) return slug;
  return `https://webook.com/ar/events/${slug}`;
}

export function getWebookSearchUrl(query: string): string {
  if (!query) return "https://webook.com/ar";
  return `https://webook.com/ar?search=${encodeURIComponent(query)}`;
}

export function extractWebookSlug(input: string): string {
  if (!input) return "";
  let clean = input.trim();
  try {
    if (clean.includes("webook.com")) {
      const url = new URL(clean.startsWith("http") ? clean : `https://${clean}`);
      const parts = url.pathname.split("/").filter(Boolean);
      const eventsIdx = parts.findIndex(p => p === "events" || p === "experiences" || p === "shows");
      if (eventsIdx !== -1 && parts[eventsIdx + 1]) {
        return parts[eventsIdx + 1];
      }
      return parts[parts.length - 1] || clean;
    }
  } catch {
    // fallback
  }
  return clean.replace(/^[/#]+|[/#]+$/g, "");
}
