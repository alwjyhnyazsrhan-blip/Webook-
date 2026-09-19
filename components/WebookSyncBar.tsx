"use client";

import React, { useState } from "react";
import { Globe, RefreshCw, CheckCircle, ArrowRight, ShieldCheck, Zap, ExternalLink, Sparkles } from "lucide-react";

interface WebookSyncBarProps {
  onSync: (slug?: string) => Promise<void>;
  isSyncing: boolean;
  totalEvents: number;
}

export const WebookSyncBar: React.FC<WebookSyncBarProps> = ({
  onSync,
  isSyncing,
  totalEvents,
}) => {
  const [inputUrl, setInputUrl] = useState("");
  const [autoSync, setAutoSync] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  // Auto-sync effect
  React.useEffect(() => {
    if (!autoSync) return;
    const interval = setInterval(() => {
      onSync();
    }, 15000);
    return () => clearInterval(interval);
  }, [autoSync, onSync]);

  const handleDirectImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputUrl.trim()) return;
    setStatusMsg("جاري الاتصال بـ Webook.com وسحب الفعالية مباشرة...");
    await onSync(inputUrl.trim());
    setInputUrl("");
    setStatusMsg("تمت مزامنة الفعالية بنجاح من منصة Webook.com!");
    setTimeout(() => setStatusMsg(null), 4000);
  };

  const quickSlugs = [
    { label: "ديربي الرياض", slug: "al-hilal-vs-al-nassr-riyadh-derby-spl-2026" },
    { label: "الملوك الستة", slug: "six-kings-slam-tennis-riyadh-season-2026" },
    { label: "بوليفارد وورلد", slug: "boulevard-world-riyadh-season-zones-2026" },
    { label: "محمد عبده", slug: "mohammed-abdo-riyadh-gala-concert-2026" },
    { label: "WWE كراون جول", slug: "wwe-crown-jewel-superdome-riyadh-2026" },
  ];

  return (
    <div className="glass bg-gradient-to-r from-blue-950/50 via-slate-900/70 to-purple-950/50 border border-blue-500/30 rounded-3xl p-5 md:p-6 mb-8 relative overflow-hidden shadow-2xl">
      <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20"></div>

      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 relative z-10">
        {/* Left info badge */}
        <div className="flex items-start gap-3.5">
          <div className="w-12 h-12 rounded-2xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center shrink-0 shadow-lg shadow-blue-500/10">
            <Globe className="w-6 h-6 text-blue-400 animate-pulse" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-base font-bold text-white tracking-wide">
                بوابة الربط الحي مع Webook.com (Live Integration Hub)
              </h2>
              <span className="flex items-center gap-1 text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/40 px-2.5 py-0.5 rounded-full shadow">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                متصل ومزامن (56+ فعالية رسمية)
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-xl">
              تكامل لحظي مع خرائط الموقع وبيانات الفعاليات والتذاكر على{" "}
              <a
                href="https://webook.com"
                target="_blank"
                rel="noreferrer"
                className="text-blue-400 hover:underline font-mono inline-flex items-center gap-1 font-semibold"
              >
                <span>webook.com</span>
                <ExternalLink className="w-3 h-3" />
              </a>
              {" "}مع دعم الاستيراد المباشر لأي رابط أو فعالية.
            </p>
          </div>
        </div>

        {/* Right action tools */}
        <div className="w-full lg:w-auto flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {/* Direct slug/url import form */}
          <form onSubmit={handleDirectImport} className="relative flex-1 sm:w-80">
            <input
              type="text"
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
              placeholder="ضع رابط Webook (webook.com/events/...)"
              className="w-full bg-slate-950/90 border border-slate-700/80 rounded-xl py-2.5 pl-3 pr-20 text-xs text-white placeholder-slate-500 focus:ring-2 focus:ring-blue-500 outline-none font-mono"
              dir="auto"
            />
            <button
              type="submit"
              disabled={isSyncing || !inputUrl.trim()}
              className="absolute right-1.5 top-1.5 bottom-1.5 px-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white rounded-lg text-[11px] font-bold transition-all flex items-center gap-1 cursor-pointer"
            >
              <span>استيراد</span>
              <ArrowRight className="w-3 h-3" />
            </button>
          </form>

          {/* Quick sync button */}
          <button
            onClick={() => onSync()}
            disabled={isSyncing}
            className="accent-gradient hover:opacity-90 disabled:opacity-50 px-4 py-2.5 rounded-xl text-xs font-bold text-white flex items-center justify-center gap-2 transition-all shadow-md cursor-pointer shrink-0"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? "animate-spin" : ""}`} />
            <span>{isSyncing ? "جاري المزامنة..." : "مزامنة كاملة"}</span>
          </button>

          {/* Auto sync switch */}
          <button
            onClick={() => setAutoSync(!autoSync)}
            className={`px-3 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 border cursor-pointer shrink-0 ${
              autoSync
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                : "bg-slate-800/60 text-slate-400 border-slate-700 hover:text-white"
            }`}
            title="مزامنة دورية تلقائية كل 15 ثانية"
          >
            <Zap className={`w-3.5 h-3.5 ${autoSync ? "text-emerald-400 fill-emerald-400" : ""}`} />
            <span>{autoSync ? "تلقائي: 15s" : "مزامنة دورية"}</span>
          </button>
        </div>
      </div>

      {/* Quick shortcuts */}
      <div className="mt-4 pt-3.5 border-t border-slate-800/80 flex flex-wrap items-center gap-2 text-xs">
        <span className="text-slate-400 text-[11px] flex items-center gap-1">
          <Sparkles className="w-3.5 h-3.5 text-yellow-400" />
          <span>سحب فعاليات سريعة:</span>
        </span>
        {quickSlugs.map((qs) => (
          <button
            key={qs.slug}
            onClick={() => onSync(qs.slug)}
            disabled={isSyncing}
            className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-slate-800/80 hover:bg-blue-600/30 text-slate-300 hover:text-blue-300 border border-slate-700/60 hover:border-blue-500/40 transition-all cursor-pointer"
          >
            {qs.label}
          </button>
        ))}
      </div>

      {statusMsg && (
        <div className="mt-3 pt-3 border-t border-blue-500/20 flex items-center gap-2 text-xs text-emerald-300 animate-in fade-in">
          <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{statusMsg}</span>
        </div>
      )}
    </div>
  );
};
