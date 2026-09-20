"use client";

import React from "react";
import { IngestionStats } from "@/lib/types";
import { Database, CheckCircle, Clock, AlertTriangle } from "lucide-react";

interface MetricsGridProps {
  stats: IngestionStats;
}

export const MetricsGrid: React.FC<MetricsGridProps> = ({ stats }) => {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
      {/* Total Discovered */}
      <div
        id="metric-total-discovered"
        className="glass p-6 rounded-3xl relative overflow-hidden group hover:border-blue-500/40 transition-all"
      >
        <div className="flex items-center justify-between mb-3">
          <span className="text-slate-400 text-xs font-bold uppercase tracking-wider">
            Total Discovered
          </span>
          <div className="p-2 bg-blue-500/10 rounded-xl text-blue-400">
            <Database className="w-4 h-4" />
          </div>
        </div>
        <div className="text-4xl font-extrabold text-white tracking-tight" suppressHydrationWarning>
          {stats.total_events}
        </div>
        <div className="text-xs text-slate-500 mt-2 font-mono flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
          Ingested from Webook API v2
        </div>
      </div>

      {/* Ready / Hydrated */}
      <div
        id="metric-ready-hydrated"
        className="glass p-6 rounded-3xl relative overflow-hidden group hover:border-emerald-500/40 transition-all"
      >
        <div className="flex items-center justify-between mb-3">
          <span className="text-emerald-400 text-xs font-bold uppercase tracking-wider">
            Ready / Hydrated
          </span>
          <div className="p-2 bg-emerald-500/10 rounded-xl text-emerald-400">
            <CheckCircle className="w-4 h-4" />
          </div>
        </div>
        <div className="text-4xl font-extrabold text-white tracking-tight" suppressHydrationWarning>
          {stats.ready_events}
        </div>
        <div className="text-xs text-emerald-400 mt-2 font-semibold flex items-center gap-1">
          <span>↑ High Fidelity Ready</span>
        </div>
      </div>

      {/* Pending Hydration */}
      <div
        id="metric-pending-hydration"
        className="glass p-6 rounded-3xl relative overflow-hidden group hover:border-yellow-500/40 transition-all"
      >
        <div className="flex items-center justify-between mb-3">
          <span className="text-yellow-400 text-xs font-bold uppercase tracking-wider">
            Pending Hydration
          </span>
          <div className="p-2 bg-yellow-500/10 rounded-xl text-yellow-400">
            <Clock className="w-4 h-4" />
          </div>
        </div>
        <div className="text-4xl font-extrabold text-white tracking-tight" suppressHydrationWarning>
          {stats.discovered_events}
        </div>
        <div className="text-xs text-yellow-500/90 mt-2 font-mono">
          Status: DISCOVERED
        </div>
      </div>

      {/* 403 / Failed */}
      <div
        id="metric-failed-events"
        className="glass p-6 rounded-3xl relative overflow-hidden group hover:border-red-500/40 transition-all"
      >
        <div className="flex items-center justify-between mb-3">
          <span className="text-red-400 text-xs font-bold uppercase tracking-wider">
            403 / Failed
          </span>
          <div className="p-2 bg-red-500/10 rounded-xl text-red-400">
            <AlertTriangle className="w-4 h-4" />
          </div>
        </div>
        <div className="text-4xl font-extrabold text-white tracking-tight" suppressHydrationWarning>
          {stats.failed_events}
        </div>
        <div className="text-xs text-red-400/90 mt-2">
          Requires Session Refresh
        </div>
      </div>
    </div>
  );
};
