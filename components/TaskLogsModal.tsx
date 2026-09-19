"use client";

import React from "react";
import { ReservationTask } from "@/lib/types";
import { formatTime } from "@/lib/utils";
import { X, Terminal, Clock } from "lucide-react";

interface TaskLogsModalProps {
  task: ReservationTask | null;
  onClose: () => void;
}

export const TaskLogsModal: React.FC<TaskLogsModalProps> = ({ task, onClose }) => {
  if (!task) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div
        id="task-logs-modal"
        className="glass-card w-full max-w-2xl rounded-3xl overflow-hidden border border-slate-700 shadow-2xl p-6 relative"
      >
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
            <Terminal className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">
              Execution Logs • Task #{task.id}
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              Target: {task.event_slug} • Status: {task.status}
            </p>
          </div>
        </div>

        <div className="bg-slate-950 rounded-2xl p-4 border border-slate-800 font-mono text-xs max-h-80 overflow-y-auto space-y-2.5">
          {task.logs && task.logs.length > 0 ? (
            task.logs.map((log, idx) => (
              <div key={idx} className="flex items-start gap-2.5 text-slate-300">
                <span
                  className="text-slate-500 shrink-0"
                  suppressHydrationWarning
                >
                  [{formatTime(log.timestamp)}]
                </span>
                <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-blue-900/60 text-blue-300 shrink-0">
                  {log.state}
                </span>
                <span className="text-slate-300">{log.message}</span>
              </div>
            ))
          ) : (
            <div className="text-slate-500 text-center py-4">
              No logs recorded for this task execution.
            </div>
          )}
        </div>

        {task.hold_token && (
          <div className="mt-4 p-3.5 bg-emerald-950/40 border border-emerald-800/60 rounded-xl flex items-center justify-between">
            <div>
              <div className="text-[10px] text-emerald-400 font-bold uppercase">
                Acquired Hold Token
              </div>
              <div className="text-xs font-mono font-bold text-emerald-200">
                {task.hold_token}
              </div>
            </div>
            <a
              href={`https://webook.com/en/checkout/${task.hold_token}`}
              target="_blank"
              rel="noopener noreferrer"
              className="accent-gradient px-3 py-1.5 rounded-lg text-xs font-bold text-white"
            >
              Go to Checkout
            </a>
          </div>
        )}

        <div className="flex justify-end mt-4">
          <button
            onClick={onClose}
            className="glass hover:bg-slate-800 px-4 py-2 rounded-xl text-xs font-bold text-slate-300 hover:text-white cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
