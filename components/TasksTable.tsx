"use client";

import React from "react";
import { ReservationTask } from "@/lib/types";
import { formatTime } from "@/lib/utils";
import {
  RefreshCw,
  ExternalLink,
  Terminal,
  Clock,
  CheckCircle2,
  AlertCircle,
  Play,
  Plus,
  Globe,
} from "lucide-react";

interface TasksTableProps {
  tasks: ReservationTask[];
  onOpenNewTask: () => void;
  onRetryTask: (taskId: number) => void;
  onViewLogs: (task: ReservationTask) => void;
}

export const TasksTable: React.FC<TasksTableProps> = ({
  tasks,
  onOpenNewTask,
  onRetryTask,
  onViewLogs,
}) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "SUCCESS":
      case "COMPLETED":
        return (
          <span className="px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5 w-fit">
            <CheckCircle2 className="w-3 h-3" />
            SUCCESS
          </span>
        );
      case "FAILED":
        return (
          <span className="px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase bg-red-500/20 text-red-400 border border-red-500/30 flex items-center gap-1.5 w-fit">
            <AlertCircle className="w-3 h-3" />
            FAILED
          </span>
        );
      case "HOLDING":
      case "RUNNING":
      case "SEARCHING":
      case "PROCESSING":
        return (
          <span className="px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase bg-blue-500/20 text-blue-400 border border-blue-500/30 flex items-center gap-1.5 w-fit animate-pulse">
            <Play className="w-3 h-3 fill-blue-400" />
            {status}
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 flex items-center gap-1.5 w-fit">
            <Clock className="w-3 h-3" />
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-xl font-bold text-white">
            مهام القنص والحجز الآلي المتزامنة مع Webook
          </h2>
          <p className="text-xs text-slate-400">
            متابعة فورية لتخصيص المقاعد، وتثبيت التوكنات، وحجز التذاكر عبر Webook Cloud.
          </p>
        </div>
        <button
          onClick={onOpenNewTask}
          className="accent-gradient hover:opacity-90 px-4 py-2 rounded-xl text-xs font-bold text-white shadow-lg flex items-center gap-2 cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>مهمة حجز جديدة</span>
        </button>
      </div>

      <div className="glass rounded-3xl overflow-hidden border border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-slate-900/80 text-xs font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-5">معرف المهمة</th>
                <th className="p-5">الفعالية والفئة</th>
                <th className="p-5">الحالة</th>
                <th className="p-5">توكن الحجز / Webook Hold</th>
                <th className="p-5 text-right">الإجراءات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-sm">
              {tasks.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-500 text-xs">
                    لا توجد مهام نشطة حالياً. أنشئ مهمة جديدة لبدء القنص والحجز.
                  </td>
                </tr>
              ) : (
                tasks.map((task) => (
                  <tr
                    key={task.id}
                    id={`task-row-${task.id}`}
                    className="hover:bg-slate-800/30 transition-colors group"
                  >
                    <td className="p-5">
                      <div className="font-mono font-bold text-blue-400">
                        #{task.id}
                      </div>
                      <div
                        className="text-[11px] text-slate-400 mt-1 flex items-center gap-1 font-mono"
                        suppressHydrationWarning
                      >
                        <Clock className="w-3 h-3 text-slate-500" />
                        {formatTime(task.created_at)}
                      </div>
                    </td>

                    <td className="p-5">
                      <div className="font-bold text-white max-w-sm truncate">
                        {task.event_title || task.event_slug}
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-2 mt-1">
                        <span className="bg-slate-900 px-2 py-0.5 rounded text-[11px] font-mono text-purple-300 border border-slate-800">
                          {task.category || "Best Available"}
                        </span>
                        <span>•</span>
                        <span>{task.seat_count} {task.seat_count === 1 ? 'مقعد' : 'مقاعد'}</span>
                        {task.sniper_mode && (
                          <span className="text-[10px] text-yellow-400 font-bold bg-yellow-400/10 px-1.5 py-0.5 rounded">
                            SNIPER
                          </span>
                        )}
                        <a
                          href={`https://webook.com/ar/events/${task.event_slug}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-400 hover:underline text-[10px] flex items-center gap-0.5 ml-1 font-mono"
                        >
                          <Globe className="w-2.5 h-2.5" />
                          <span>webook</span>
                        </a>
                      </div>
                    </td>

                    <td className="p-5">{getStatusBadge(task.status)}</td>

                    <td className="p-5">
                      {task.hold_token ? (
                        <div>
                          <div className="text-xs text-emerald-300 font-mono bg-emerald-950/40 border border-emerald-800/60 px-2.5 py-1 rounded-lg w-fit">
                            {task.hold_token}
                          </div>
                          {task.hold_expires_at && (
                            <div className="text-[10px] text-slate-400 mt-1 font-mono">
                              مؤقت التثبيت: متبقي ~15 دقيقة
                            </div>
                          )}
                        </div>
                      ) : task.error_message ? (
                        <div className="text-xs text-red-400 font-mono max-w-xs truncate" title={task.error_message}>
                          {task.error_message}
                        </div>
                      ) : (
                        <div className="text-xs text-slate-400 font-mono animate-pulse">
                          بانتظار تأكيد وتثبيت التوكن...
                        </div>
                      )}
                    </td>

                    <td className="p-5 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => onViewLogs(task)}
                          title="عرض سجلات التنفيذ"
                          className="p-2 rounded-xl glass hover:bg-slate-700/60 text-slate-300 hover:text-white transition-all cursor-pointer"
                        >
                          <Terminal className="w-3.5 h-3.5" />
                        </button>

                        {task.status === "FAILED" && (
                          <button
                            onClick={() => onRetryTask(task.id)}
                            className="px-3 py-1.5 rounded-xl bg-yellow-500/20 text-yellow-300 hover:bg-yellow-500 hover:text-black text-xs font-bold transition-all flex items-center gap-1 cursor-pointer"
                          >
                            <RefreshCw className="w-3 h-3" />
                            <span>إعادة المحاولة</span>
                          </button>
                        )}

                        <a
                          href={`https://webook.com/ar/events/${task.event_slug}/book`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="accent-gradient hover:opacity-90 px-3.5 py-1.5 rounded-xl text-xs font-bold text-white shadow-md flex items-center gap-1 cursor-pointer"
                        >
                          <span>فتح الحجز على Webook</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
