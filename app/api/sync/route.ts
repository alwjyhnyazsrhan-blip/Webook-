import { NextRequest, NextResponse } from "next/server";
import { dbStore } from "@/lib/data";
import { executeWebookSync } from "@/lib/webookSync";

export async function POST(req: NextRequest) {
  let targetSlug: string | undefined = undefined;

  try {
    const body = await req.json().catch(() => ({}));
    if (body && typeof body.slug === "string" && body.slug.trim()) {
      targetSlug = body.slug.trim();
    }
  } catch {
    // Ignore JSON parse errors if empty body
  }

  const result = await executeWebookSync(targetSlug);

  return NextResponse.json({
    success: true,
    message: targetSlug
      ? `Webook.com event "${targetSlug}" synchronized successfully`
      : "Live Webook.com synchronization completed successfully",
    synced_at: result.lastSync,
    discovered: result.discovered,
    hydrated: result.hydrated,
    events_count: result.events.length,
    events: result.events,
    stats: dbStore.getStats(),
  });
}

export async function GET() {
  return NextResponse.json({
    platform: "Webook.com Live Ingestion Engine",
    connected: true,
    last_sync: dbStore.workerStatus.lastSync,
    total_events: dbStore.events.length,
  });
}
