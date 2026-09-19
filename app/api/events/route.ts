import { NextRequest, NextResponse } from "next/server";
import { dbStore } from "@/lib/data";
import { CORE_WEBOOK_SLUGS, hydrateEventData } from "@/lib/webookSync";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  // Ensure all live verified Webook events are populated
  for (const slug of CORE_WEBOOK_SLUGS) {
    if (!dbStore.events.some((e) => e.slug === slug)) {
      dbStore.events.push(hydrateEventData(slug));
    }
  }

  const { searchParams } = new URL(req.url);
  const search = searchParams.get("search")?.toLowerCase();
  const genre = searchParams.get("genre");
  const status = searchParams.get("status");

  let events = [...dbStore.events];

  if (search) {
    events = events.filter(
      (e) =>
        e.title_ar.toLowerCase().includes(search) ||
        e.title_en.toLowerCase().includes(search) ||
        e.slug.toLowerCase().includes(search) ||
        e.venue_name.toLowerCase().includes(search)
    );
  }

  if (genre && genre !== "all") {
    events = events.filter((e) => e.genre_slug === genre);
  }

  if (status && status !== "all") {
    events = events.filter((e) => e.hydration_status === status);
  }

  return NextResponse.json({
    events,
    total: events.length,
    stats: dbStore.getStats(),
  });
}
