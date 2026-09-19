"use client";

import React from "react";
import { IngestionStats } from "@/lib/types";

interface FunnelHealthProps {
  stats: IngestionStats;
}

export const FunnelHealth: React.FC<FunnelHealthProps> = ({ stats }) => {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5 mb-8">
      <div
        id="funnel-categorized"
        className="glass p-4 rounded-2xl border-l-4 border-blue-500 hover:bg-slate-800/40 transition-colors"
      >
        <div className="text-[11px] text-slate-400 font-bold uppercase mb-1">
          Categorized
        </div>
        <div className="text-2xl font-bold text-white tracking-tight">
          {stats.categorized}
        </div>
        <div className="text-[10px] text-slate-500 mt-1">Genre assigned</div>
      </div>

      <div
        id="funnel-uncategorized"
        className="glass p-4 rounded-2xl border-l-4 border-yellow-500 hover:bg-slate-800/40 transition-colors"
      >
        <div className="text-[11px] text-slate-400 font-bold uppercase mb-1">
          Uncategorized
        </div>
        <div className="text-2xl font-bold text-white tracking-tight">
          {stats.uncategorized}
        </div>
        <div className="text-[10px] text-slate-500 mt-1">Needs derivation</div>
      </div>

      <div
        id="funnel-hydrated"
        className="glass p-4 rounded-2xl border-l-4 border-emerald-500 hover:bg-slate-800/40 transition-colors"
      >
        <div className="text-[11px] text-slate-400 font-bold uppercase mb-1">
          Hydrated
        </div>
        <div className="text-2xl font-bold text-white tracking-tight">
          {stats.hydrated}
        </div>
        <div className="text-[10px] text-slate-500 mt-1">Seats schema cached</div>
      </div>

      <div
        id="funnel-blocked"
        className="glass p-4 rounded-2xl border-l-4 border-red-500 hover:bg-slate-800/40 transition-colors"
      >
        <div className="text-[11px] text-slate-400 font-bold uppercase mb-1">
          403 Blocked
        </div>
        <div className="text-2xl font-bold text-white tracking-tight">
          {stats["403_failed"]}
        </div>
        <div className="text-[10px] text-slate-500 mt-1">Turnstile challenged</div>
      </div>

      <div
        id="funnel-skipped"
        className="glass p-4 rounded-2xl border-l-4 border-slate-500 hover:bg-slate-800/40 transition-colors"
      >
        <div className="text-[11px] text-slate-400 font-bold uppercase mb-1">
          Skipped Dupes
        </div>
        <div className="text-2xl font-bold text-white tracking-tight">
          {stats.duplicate_skipped}
        </div>
        <div className="text-[10px] text-slate-500 mt-1">Idempotency match</div>
      </div>
    </div>
  );
};
