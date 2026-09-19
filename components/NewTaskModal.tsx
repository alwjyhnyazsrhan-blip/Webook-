"use client";

import React, { useState } from "react";
import { LiveEvent } from "@/lib/types";
import { X, Crosshair } from "lucide-react";

interface NewTaskModalProps {
  events: LiveEvent[];
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (params: {
    event_slug: string;
    event_title: string;
    category: string;
    seat_count: number;
    sniper_mode: boolean;
  }) => void;
}

export const NewTaskModal: React.FC<NewTaskModalProps> = ({
  events,
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [selectedSlug, setSelectedSlug] = useState<string>(
    events[0]?.slug || ""
  );
  const [category, setCategory] = useState<string>("Best Available");
  const [seatCount, setSeatCount] = useState<number>(2);
  const [sniperMode, setSniperMode] = useState<boolean>(true);

  if (!isOpen) return null;

  const currentEvent = events.find((e) => e.slug === selectedSlug) || events[0];

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSlug) return;
    onSubmit({
      event_slug: selectedSlug,
      event_title: currentEvent?.title_ar || selectedSlug,
      category,
      seat_count: seatCount,
      sniper_mode: sniperMode,
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
      <div
        id="new-task-modal"
        className="glass-card w-full max-w-lg rounded-3xl overflow-hidden border border-slate-700 shadow-2xl p-6 relative"
      >
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-2xl accent-gradient flex items-center justify-center glow">
            <Crosshair className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">
              Launch Reservation Task
            </h3>
            <p className="text-xs text-slate-400">
              Queue atomic seat sniper with Webook API v2 concurrency lock.
            </p>
          </div>
        </div>

        <form onSubmit={handleFormSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">
              Select Target Event
            </label>
            <select
              value={selectedSlug}
              onChange={(e) => setSelectedSlug(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl py-2.5 px-3 text-xs text-white focus:ring-2 focus:ring-blue-500 outline-none"
            >
              {events.map((ev) => (
                <option key={ev.slug} value={ev.slug}>
                  {ev.title_ar} ({ev.slug})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">
              Target Ticket Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl py-2.5 px-3 text-xs text-white focus:ring-2 focus:ring-blue-500 outline-none"
            >
              <option value="Best Available">⚡ Best Available (Auto-Pick)</option>
              {currentEvent?.sections?.map((s) => (
                <option key={s.id} value={s.category_name}>
                  {s.name} - SAR {s.price}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5">
              Seats Quantity (1-10)
            </label>
            <input
              type="number"
              min="1"
              max="10"
              value={seatCount}
              onChange={(e) => setSeatCount(parseInt(e.target.value) || 1)}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl py-2.5 px-3 text-xs text-white focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800">
            <label className="flex items-center gap-2.5 cursor-pointer">
              <input
                type="checkbox"
                checked={sniperMode}
                onChange={(e) => setSniperMode(e.target.checked)}
                className="rounded border-slate-700 text-blue-500 w-4 h-4 bg-slate-950"
              />
              <div>
                <div className="text-xs font-bold text-purple-300">
                  Burst Sniper Mode
                </div>
                <div className="text-[10px] text-slate-400">
                  Bypasses human simulation pacing for millisecond slot lock.
                </div>
              </div>
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="accent-gradient hover:opacity-90 px-5 py-2.5 rounded-xl text-xs font-bold text-white shadow-lg cursor-pointer"
            >
              Dispatch Task
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
