"use client";

import React, { useState } from "react";
import { Zap, RefreshCw, Download, Activity, CheckCircle2, Globe, ExternalLink, ShieldCheck, Key, ShoppingCart, Flame } from "lucide-react";
import { formatTime } from "@/lib/utils";

interface HeaderProps {
  onSync: () => Promise<void>;
  onExport: () => void;
  isSyncing: boolean;
  lastSyncTime: string;
  cartCount?: number;
  onOpenCart?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onSync,
  onExport,
  isSyncing,
  lastSyncTime,
  cartCount = 0,
  onOpenCart,
}) => {
  const [copiedNotification, setCopiedNotification] = useState(false);
  const [isBridgeModalOpen, setIsBridgeModalOpen] = useState(false);
  const [authToken, setAuthToken] = useState("wbk_live_sess_894f29a008c2");
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleExport = () => {
    onExport();
    setCopiedNotification(true);
    setTimeout(() => setCopiedNotification(false), 2500);
  };

  const handleSaveToken = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveSuccess(true);
    setTimeout(() => {
      setSaveSuccess(false);
      setIsBridgeModalOpen(false);
    }, 1500);
  };

  return (
    <>
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-6 border-b border-slate-800/80 pb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-11 h-11 accent-gradient rounded-2xl flex items-center justify-center glow shadow-lg">
              <Zap className="w-6 h-6 text-white fill-white/20" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-3xl font-black tracking-tight text-white">
                  Webook Ingestion & Sniper Platform
                </h1>
                <span className="text-xs font-mono font-bold bg-blue-500/10 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-md">
                  v7.2
                </span>
                <a
                  href="https://webook.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 px-2.5 py-0.5 rounded-full flex items-center gap-1 hover:bg-emerald-500/25 transition-colors"
                >
                  <Globe className="w-3 h-3" />
                  <span>webook.com Live</span>
                  <ExternalLink className="w-2.5 h-2.5" />
                </a>
              </div>
            </div>
          </div>
          <p className="text-slate-400 text-sm max-w-xl">
            منظومة استيراد ومزامنة وقنص التذاكر اللحظية المتكاملة مع شبكة وفعاليات Webook.com
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Bridge connection button */}
          <button
            onClick={() => setIsBridgeModalOpen(true)}
            className="glass hover:border-emerald-500/50 px-4 py-2.5 rounded-2xl flex items-center gap-3 transition-all cursor-pointer group"
          >
            <div className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </div>
            <div className="text-left">
              <div className="text-xs font-semibold text-white group-hover:text-emerald-300 transition-colors flex items-center gap-1">
                <span>Webook Live Hub</span>
                <Key className="w-3 h-3 text-slate-400" />
              </div>
              <div
                className="text-[10px] text-slate-400 font-mono"
                suppressHydrationWarning
              >
                آخر مزامنة: {formatTime(lastSyncTime)}
              </div>
            </div>
          </button>

          {/* Sniper Cart Button */}
          {onOpenCart && (
            <button
              onClick={onOpenCart}
              className="px-4 py-2.5 rounded-xl bg-pink-500/15 hover:bg-pink-500/25 border border-pink-500/40 text-pink-300 font-bold text-xs flex items-center gap-2 transition-all cursor-pointer relative"
              title="فتح سلة القنص المتوازي"
            >
              <ShoppingCart className="w-4 h-4 text-pink-400" />
              <span>سلة القنص</span>
              {cartCount > 0 && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-pink-600 text-white font-black animate-pulse">
                  {cartCount}
                </span>
              )}
            </button>
          )}

          <button
            id="export-json-btn"
            onClick={handleExport}
            className="glass hover:bg-slate-800/80 px-4 py-2.5 rounded-xl text-xs font-bold text-slate-200 transition-all flex items-center gap-2 cursor-pointer"
          >
            {copiedNotification ? (
              <>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>تم التصدير!</span>
              </>
            ) : (
              <>
                <Download className="w-4 h-4 text-slate-400" />
                <span>تصدير JSON</span>
              </>
            )}
          </button>

          <button
            id="manual-sync-btn"
            onClick={onSync}
            disabled={isSyncing}
            className="accent-gradient hover:opacity-90 active:scale-95 px-5 py-2.5 rounded-xl text-xs font-bold text-white shadow-lg transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw
              className={`w-4 h-4 ${isSyncing ? "animate-spin" : ""}`}
            />
            <span>{isSyncing ? "جاري المزامنة..." : "مزامنة Webook"}</span>
          </button>
        </div>
      </header>

      {/* Webook Bridge Settings Modal */}
      {isBridgeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="glass-card w-full max-w-lg rounded-3xl p-6 border border-slate-700 shadow-2xl relative">
            <div className="flex items-center justify-between mb-5 border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
                  <ShieldCheck className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">إعدادات الارتباط المباشر مع Webook</h3>
                  <p className="text-xs text-slate-400">Webook Production Integration & Token Session</p>
                </div>
              </div>
              <button
                onClick={() => setIsBridgeModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs space-y-2">
                <div className="flex justify-between items-center text-slate-300">
                  <span>خادم الموقع الرسمي:</span>
                  <a href="https://webook.com" target="_blank" rel="noreferrer" className="text-blue-400 font-mono hover:underline">
                    https://webook.com
                  </a>
                </div>
                <div className="flex justify-between items-center text-slate-300">
                  <span>حالة بروتوكول خرائط الفعاليات:</span>
                  <span className="text-emerald-400 font-bold">نشط ومتزامن (56+ فعالية)</span>
                </div>
                <div className="flex justify-between items-center text-slate-300">
                  <span>مزود المخططات والتذاكر:</span>
                  <span className="text-blue-400 font-mono">SeatCloud / HalaYalla V2</span>
                </div>
                <div className="flex justify-between items-center text-slate-300">
                  <span>زمن الاستجابة (Latency):</span>
                  <span className="text-emerald-400 font-mono font-bold">28ms</span>
                </div>
              </div>

              <form onSubmit={handleSaveToken} className="space-y-3">
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1">
                    جلسة حساب Webook (Webook Bearer / Session Token)
                  </label>
                  <input
                    type="text"
                    value={authToken}
                    onChange={(e) => setAuthToken(e.target.value)}
                    placeholder="wbk_live_sess_..."
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-white focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                  <p className="text-[11px] text-slate-500 mt-1">
                    يستخدم هذا التوكن لتثبيت حجوزات القنص المباشرة لحسابك على Webook.com
                  </p>
                </div>

                <div className="flex justify-end gap-2 pt-3">
                  <button
                    type="button"
                    onClick={() => setIsBridgeModalOpen(false)}
                    className="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white transition-colors cursor-pointer"
                  >
                    إغلاق
                  </button>
                  <button
                    type="submit"
                    className="accent-gradient px-5 py-2 rounded-xl text-xs font-bold text-white shadow-lg cursor-pointer flex items-center gap-1"
                  >
                    {saveSuccess ? (
                      <>
                        <CheckCircle2 className="w-4 h-4 text-white" />
                        <span>تم الحفظ والربط!</span>
                      </>
                    ) : (
                      <span>حفظ الجلسة</span>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
