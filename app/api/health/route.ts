import { NextResponse } from "next/server";
import { dbStore } from "@/lib/data";

export async function GET() {
  return NextResponse.json({
    status: "healthy",
    engine: "high-concurrency",
    platform: "Webook Ingestion Platform v7.0",
    worker_active: dbStore.workerStatus.active,
    active_workers: dbStore.workerStatus.activeWorkers,
    last_sync: dbStore.workerStatus.lastSync,
    timestamp: new Date().toISOString()
  });
}
