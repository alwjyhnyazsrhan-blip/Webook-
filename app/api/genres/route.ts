import { NextRequest, NextResponse } from "next/server";
import { dbStore } from "@/lib/data";

export const dynamic = "force-dynamic";

export async function GET(_req: NextRequest) {
  return NextResponse.json({
    genres: dbStore.genres,
    total: dbStore.genres.length,
  });
}
