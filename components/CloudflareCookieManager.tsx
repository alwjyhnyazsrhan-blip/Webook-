"use client";

import React, { useState, useEffect } from "react";
import {
  Shield,
  Key,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ExternalLink,
  Copy,
  Check,
  RefreshCw,
  X,
  Lock,
} from "lucide-react";

export interface CookieConfig {
  cfClearance?: string;
  cfBm?: string;
  webookSession?: string;
  userAgent?: string;
  rawCookie?: string;
  rawCookieString?: string;
}

interface CloudflareCookieManagerProps {
  isOpen?: boolean;
  onClose?: () => void;
  onSave?: (config: CookieConfig) => void;
  embedded?: boolean;
}

const STORAGE_KEY = "webook_cloudflare_cookies_v2";

export const CloudflareCookieManager: React.FC<CloudflareCookieManagerProps> = ({
  isOpen = true,
  onClose,
  onSave,
  embedded = false,
}) => {
  const [cfClearance, setCfClearance] = useState<string>("");
  const [cfBm, setCfBm] = useState<string>("");
  const [webookSession, setWebookSession] = useState<string>("");
  const [userAgent, setUserAgent] = useState<string>("");
  const [rawCookie, setRawCookie] = useState<string>("");
  const [isSaved, setIsSaved] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [showHelper, setShowHelper] = useState<boolean>(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.cfClearance) setCfClearance(parsed.cfClearance);
        if (parsed.cfBm) setCfBm(parsed.cfBm);
        if (parsed.webookSession) setWebookSession(parsed.webookSession);
        if (parsed.userAgent) setUserAgent(parsed.userAgent);
        if (parsed.rawCookie) setRawCookie(parsed.rawCookie);
      } else if (typeof navigator !== "undefined") {
        setUserAgent(navigator.userAgent);
      }
    } catch {
      // Ignore storage errors
    }
  }, []);

  const handleParseRawCookie = (raw: string) => {
    setRawCookie(raw);
    if (!raw.trim()) return;

    // Extract cf_clearance
    const clearanceMatch = raw.match(/cf_clearance=([^;]+)/);
    if (clearanceMatch) setCfClearance(clearanceMatch[1].trim());

    // Extract __cf_bm
    const bmMatch = raw.match(/__cf_bm=([^;]+)/);
    if (bmMatch) setCfBm(bmMatch[1].trim());

    // Extract _webook_session or token
    const sessionMatch = raw.match(/(?:_webook_session|session|wbk_token)=([^;]+)/);
    if (sessionMatch) setWebookSession(sessionMatch[1].trim());
  };

  const handleSave = () => {
    const config: CookieConfig = {
      cfClearance: cfClearance.trim(),
      cfBm: cfBm.trim(),
      webookSession: webookSession.trim(),
      userAgent: userAgent.trim(),
      rawCookie: rawCookie.trim(),
      rawCookieString: rawCookie.trim(),
    };

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    } catch {
      // Ignore storage errors
    }

    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);

    if (onSave) {
      onSave(config);
    }
    if (!embedded && onClose) {
      setTimeout(() => onClose(), 600);
    }
  };

  const handleClear = () => {
    setCfClearance("");
    setCfBm("");
    setWebookSession("");
    setRawCookie("");
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Ignore
    }
    if (onSave) {
      onSave({});
    }
  };

  const hasAnyCookie = Boolean(cfClearance || cfBm || webookSession || rawCookie);

  const content = (
    <div className="space-y-6 text-right" dir="rtl">
      {/* Header Info */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                hasAnyCookie ? "bg-emerald-400 animate-pulse" : "bg-amber-400"
              }`}
            />
            <span className="text-xs font-semibold text-slate-200">
              {hasAnyCookie ? "الكوكيز مفعلة وجاهزة لتخطي Cloudflare" : "وضع التخطي الافتراضي نشط"}
            </span>
          </div>
          <button
            type="button"
            onClick={() => setShowHelper(!showHelper)}
            className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>كيف استخرج الكوكيز؟</span>
          </button>
        </div>

        {showHelper && (
          <div className="mt-3 pt-3 border-t border-slate-700/60 text-xs text-slate-300 space-y-2 leading-relaxed">
            <p className="font-semibold text-white">طريقة النسخ السريع من المتصفح:</p>
            <ol className="list-decimal list-inside space-y-1 text-slate-300 pr-1">
              <li>افتح موقع <span className="text-emerald-400 font-mono">webook.com</span> في نافذة جديدة وسجل دخولك.</li>
              <li>اضغط <kbd className="px-1.5 py-0.5 bg-slate-900 border border-slate-700 rounded text-slate-200">F12</kbd> لفتح أدوات المطور، ثم اختر تبويب <span className="text-blue-400 font-semibold">Network</span>.</li>
              <li>قم بتحديث الصفحة، واضغط على أول طلب (webook.com).</li>
              <li>من قسم <span className="text-blue-400 font-semibold">Request Headers</span>، انسخ قيمة <span className="text-amber-400 font-mono">Cookie</span> والصقها في خانة &quot;اللصق المباشر&quot; أدناه.</li>
            </ol>
          </div>
        )}
      </div>

      {/* Direct Raw Cookie Paste */}
      <div>
        <label className="block text-xs font-medium text-slate-300 mb-1.5">
          لصق مباشر لسلسلة الكوكيز كاملة (Fast Auto-Detect)
        </label>
        <textarea
          rows={2}
          value={rawCookie}
          onChange={(e) => handleParseRawCookie(e.target.value)}
          placeholder="cf_clearance=...; __cf_bm=...; _webook_session=..."
          className="w-full text-xs font-mono bg-slate-900/90 border border-slate-700 rounded-lg p-3 text-slate-200 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors placeholder:text-slate-500"
        />
        <p className="text-[11px] text-slate-400 mt-1">
          يتم استخراج <span className="text-emerald-400">cf_clearance</span> و <span className="text-emerald-400">__cf_bm</span> وجلسة الحجز تلقائياً بمجرد اللصق.
        </p>
      </div>

      {/* Individual Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Cloudflare Clearance (cf_clearance)
          </label>
          <div className="relative">
            <Shield className="w-4 h-4 absolute left-3 top-2.5 text-slate-500 pointer-events-none" />
            <input
              type="text"
              value={cfClearance}
              onChange={(e) => setCfClearance(e.target.value)}
              placeholder="مثال: qbE4d8s... (اختياري)"
              className="w-full text-xs font-mono bg-slate-900/90 border border-slate-700 rounded-lg py-2 pr-3 pl-9 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            Cloudflare Bot Management (__cf_bm)
          </label>
          <div className="relative">
            <Lock className="w-4 h-4 absolute left-3 top-2.5 text-slate-500 pointer-events-none" />
            <input
              type="text"
              value={cfBm}
              onChange={(e) => setCfBm(e.target.value)}
              placeholder="مثال: abc123def... (اختياري)"
              className="w-full text-xs font-mono bg-slate-900/90 border border-slate-700 rounded-lg py-2 pr-3 pl-9 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            رمز جلسة Webook (User Session / Bearer Token)
          </label>
          <div className="relative">
            <Key className="w-4 h-4 absolute left-3 top-2.5 text-slate-500 pointer-events-none" />
            <input
              type="text"
              value={webookSession}
              onChange={(e) => setWebookSession(e.target.value)}
              placeholder="مثال: wbk_sess_9941..."
              className="w-full text-xs font-mono bg-slate-900/90 border border-slate-700 rounded-lg py-2 pr-3 pl-9 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">
            متصفح المستخدم (User-Agent Matching)
          </label>
          <input
            type="text"
            value={userAgent}
            onChange={(e) => setUserAgent(e.target.value)}
            placeholder="Mozilla/5.0..."
            className="w-full text-xs font-mono bg-slate-900/90 border border-slate-700 rounded-lg py-2 px-3 text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
          />
        </div>
      </div>

      {/* Actions */}
      <div className="pt-2 flex items-center justify-between border-t border-slate-700/60">
        <button
          type="button"
          onClick={handleClear}
          className="text-xs text-rose-400 hover:text-rose-300 px-3 py-1.5 rounded transition-colors"
        >
          مسح الكوكيز المخزنة
        </button>

        <div className="flex items-center gap-2">
          {onClose && !embedded && (
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            >
              إلغاء
            </button>
          )}

          <button
            type="button"
            onClick={handleSave}
            className="px-5 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 active:scale-[0.98] rounded-lg shadow-lg shadow-blue-500/20 flex items-center gap-1.5 transition-all"
          >
            {isSaved ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-300" />
                <span>تم الحفظ والتطبيق!</span>
              </>
            ) : (
              <>
                <Shield className="w-3.5 h-3.5" />
                <span>حفظ وتطبيق الكوكيز</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );

  if (embedded) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-400" />
              <span>إدارة كوكيز Cloudflare وجلسة Webook</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              تجاوز حماية Cloudflare WAF والربط المباشر مع حسابك لحجز المقاعد فور طرحها
            </p>
          </div>
          <span className="px-2.5 py-1 text-[11px] font-medium rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
            WAF Bypass Engine
          </span>
        </div>
        {content}
      </div>
    );
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl max-w-2xl w-full">
        <div className="flex items-center justify-between mb-5 pb-3 border-b border-slate-800">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-400" />
              <span>إدخال كوكيز Cloudflare وجلسة Webook</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              تجاوز طابور الانتظار وتأكيد التذاكر في نفس اللحظة
            </p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
        {content}
      </div>
    </div>
  );
};
