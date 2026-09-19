import { NextRequest, NextResponse } from "next/server";
import { dbStore } from "@/lib/data";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({
    tasks: dbStore.tasks,
    total: dbStore.tasks.length,
  });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const {
      event_slug,
      event_title,
      category,
      zone,
      seat_count,
      sniper_mode,
      user_id,
      account_id,
    } = body;

    if (!event_slug) {
      return NextResponse.json(
        { error: "event_slug is required" },
        { status: 400 }
      );
    }

    const newTask = dbStore.addTask({
      user_id: user_id || Math.floor(Math.random() * 900000000 + 100000000),
      account_id: account_id || "account_1",
      event_slug,
      event_title: event_title || event_slug,
      category: category || "Best Available",
      zone: zone || "Default Area",
      seat_count: seat_count || 1,
      sniper_mode: sniper_mode ?? true,
      worker_id: "wrk_eu_central_01",
    });

    return NextResponse.json({
      success: true,
      message: "Reservation task scheduled successfully",
      task: newTask,
    });
  } catch {
    return NextResponse.json(
      { error: "Invalid request payload" },
      { status: 400 }
    );
  }
}
