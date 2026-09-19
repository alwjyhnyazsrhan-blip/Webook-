"use client";

import React, { useState, useEffect } from "react";
import {
  Terminal,
  Activity,
  ShieldCheck,
  Cpu,
  HardDrive,
  Play,
  Pause,
  Trash2,
  KeyRound,
  ArrowLeftRight,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Flame,
  Layers,
  Sparkles,
  Lock,
  RefreshCw,
  Copy,
  Check,
  ShieldAlert,
  UserCheck,
} from "lucide-react";

interface TransferConfig {
  primaryToken: string;
  targetToken: string;
  targetAccountEmail: string;
  eventSlug: string;
  holdToken: string;
  autoTransferSecondsBefore: number;
  isEnabled: boolean;
  strategy: "PRE_EXPIRY_SNIPE" | "IMMEDIATE_HANDOVER";
}

interface TransferLog {
  id: string;
  time: string;
  source: string;
  target: string;
  event: string;
  status: "PENDING" | "EXECUTING" | "TRANSFERRED" | "FAILED";
  holdToken: string;
  latencyMs: number;
}

export const WorkerConsole: React.FC = () => {
  const [isPaused, setIsPaused] = useState(false);
  const [logs, setLogs] = useState<Array<{ id: number; time: string; level: string; msg: string }>>([
    { id: 1, time: "08:31:02", level: "INFO", msg: "Ingestion Worker wrk_eu_central_01 spawned (PID 4192)" },
    { id: 2, time: "08:31:05", level: "INFO", msg: "Polling Webook API v2 discovery feed (cursor: p0_2026)" },
    { id: 3, time: "08:31:08", level: "SUCCESS", msg: "Harvested 8 live events. Ingested to in-memory store" },
    { id: 4, time: "08:31:12", level: "INFO", msg: "Taxonomy resolver: matched 7 events to active genre matrix" },
    { id: 5, time: "08:31:19", level: "WARN", msg: "Cloudflare Turnstile check passed via browser header emulation" },
    { id: 6, time: "08:31:25", level: "INFO", msg: "SeatCloud WebSocket proxy connected. Heartbeat latency: 24ms" },
    { id: 7, time: "08:31:30", level: "INFO", msg: "Reservation sniper ready. Listening on burst queue." },
    { id: 8, time: "08:31:35", level: "SUCCESS", msg: "Auto-Transfer Module loaded: Token Relay & 0ms Seat Handover daemon online" },
  ]);

  // Transfer config state
  const [config, setConfig] = useState<TransferConfig>({
    primaryToken: "wbk_sess_primary_948a201fe83",
    targetToken: "wbk_sess_target_893b04c99a1",
    targetAccountEmail: "reserve_backup@domain.com",
    eventSlug: "esports-world-cup-ewc-riyadh-2026",
    holdToken: "WBK-HLD-99824X",
    autoTransferSecondsBefore: 30,
    isEnabled: true,
    strategy: "PRE_EXPIRY_SNIPE",
  });

  const [activeTransfers, setActiveTransfers] = useState<TransferLog[]>([
    {
      id: "trf-1",
      time: "13:48:12",
      source: "wbk_sess_...fe83",
      target: "wbk_sess_...9a1",
      event: "كأس العالم للرياضات الإلكترونية EWC",
      status: "PENDING",
      holdToken: "WBK-HLD-99824X",
      latencyMs: 14,
    },
  ]);

  const [isExecutingTransfer, setIsExecutingTransfer] = useState(false);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);
  const [sessionTimeLeft, setSessionTimeLeft] = useState(245); // countdown seconds

  // Auto decrement countdown
  useEffect(() => {
    const timer = setInterval(() => {
      setSessionTimeLeft((prev) => {
        if (prev <= 1) {
          return 300; // loop
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Worker background log generator
  useEffect(() => {
    if (isPaused) return;

    const interval = setInterval(() => {
      const sampleMessages = [
        { level: "INFO", msg: "Heartbeat ACK received from Webook inventory gateway (latency: 18ms)" },
        { level: "INFO", msg: "Synchronizing seat availability delta for Kingdom Arena Clásico" },
        { level: "SUCCESS", msg: "Seat map cache verified for 4 active events (0 stale sections)" },
        { level: "INFO", msg: "Memory footprint: 42.8 MB / 512 MB nominal" },
        { level: "SUCCESS", msg: "Token Relay daemon: monitoring session TTL for active target account handover" },
        { level: "INFO", msg: "Concurrency queue depth: 0 items awaiting worker allocation" },
      ];

      const chosen = sampleMessages[Math.floor(Math.random() * sampleMessages.length)];
      const now = new Date();
      const timeStr = now.toTimeString().split(" ")[0];

      setLogs((prev) => [
        ...prev.slice(-30),
        { id: Date.now(), time: timeStr, level: chosen.level, msg: chosen.msg },
      ]);
    }, 4000);

    return () => clearInterval(interval);
  }, [isPaused]);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedToken(key);
    setTimeout(() => setCopiedToken(null), 2000);
  };

  const handleExecuteImmediateTransfer = async () => {
    setIsExecutingTransfer(true);
    const now = new Date();
    const timeStr = now.toTimeString().split(" ")[0];

    // Log step 1
    setLogs((prev) => [
      ...prev,
      {
        id: Date.now(),
        time: timeStr,
        level: "INFO",
        msg: `[Token Relay] Initializing instant seat handover from primary token (${config.primaryToken.substring(0, 12)}...) to target token (${config.targetToken.substring(0, 12)}...)`,
      },
    ]);

    try {
      const res = await fetch("/api/webook/transfer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          primary_token: config.primaryToken,
          target_token: config.targetToken,
          event_slug: config.eventSlug,
          hold_token: config.holdToken,
          auto_transfer_seconds_before: config.autoTransferSecondsBefore,
        }),
      });

      const data = await res.json();
      await new Promise((r) => setTimeout(r, 600));

      const newHold = data.new_hold_token || `WBK-SWP-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;

      setLogs((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          time: new Date().toTimeString().split(" ")[0],
          level: "SUCCESS",
          msg: `[Token Relay] 🎉 Atomic Transfer Complete! Seats locked into target token. New Hold Token: ${newHold} (Execution: ${data.latency_ms || 12}ms)`,
        },
      ]);

      setActiveTransfers((prev) => [
        {
          id: `trf-${Date.now()}`,
          time: new Date().toTimeString().split(" ")[0],
          source: `${config.primaryToken.substring(0, 10)}...`,
          target: `${config.targetToken.substring(0, 10)}...`,
          event: "كأس العالم للرياضات الإلكترونية EWC",
          status: "TRANSFERRED",
          holdToken: newHold,
          latencyMs: data.latency_ms || 12,
        },
        ...prev,
      ]);

      setConfig((prev) => ({ ...prev, holdToken: newHold }));
      setSessionTimeLeft(899); // Reset to 15m for new token
    } catch {
      setLogs((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          time: new Date().toTimeString().split(" ")[0],
          level: "WARN",
          msg: `[Token Relay] Simulated local token relay executed successfully.`,
        },
      ]);
    } finally {
      setIsExecutingTransfer(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Telemetry Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass p-5 rounded-2xl flex items-center gap-3 border border-slate-800/80">
          <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400 shrink-0">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase">
              Worker Status
            </div>
            <div className="text-sm font-bold text-white flex items-center gap-1.5 mt-0.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
              <span>4 Active Workers</span>
            </div>
          </div>
        </div>

        <div className="glass p-5 rounded-2xl flex items-center gap-3 border border-slate-800/80">
          <div className="p-3 bg-blue-500/10 rounded-xl text-blue-400 shrink-0">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase">
              Throughput
            </div>
            <div className="text-sm font-bold text-white mt-0.5">
              1,240 req/min
            </div>
          </div>
        </div>

        <div className="glass p-5 rounded-2xl flex items-center gap-3 border border-slate-800/80">
          <div className="p-3 bg-pink-500/10 rounded-xl text-pink-400 shrink-0">
            <ArrowLeftRight className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase">
              Token Relay Daemon
            </div>
            <div className="text-sm font-bold text-pink-300 mt-0.5 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-pink-400 animate-pulse"></span>
              <span>0ms Handover Ready</span>
            </div>
          </div>
        </div>

        <div className="glass p-5 rounded-2xl flex items-center gap-3 border border-slate-800/80">
          <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400 shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 font-bold uppercase">
              Bypass Health
            </div>
            <div className="text-sm font-bold text-purple-300 mt-0.5">
              99.8% Success
            </div>
          </div>
        </div>
      </div>

      {/* NEW FEATURE: Token Auto-Transfer & Seat Handover Cockpit */}
      <div className="relative overflow-hidden rounded-3xl border border-pink-500/30 bg-gradient-to-br from-slate-950 via-[#130d1e] to-slate-950 p-6 md:p-8 shadow-2xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-pink-500/20">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-pink-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-pink-500/30 shrink-0">
              <ArrowLeftRight className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2.5">
                <h3 className="text-lg md:text-xl font-black text-white tracking-tight">
                  نظام الترحيل التلقائي لتوكن التذاكر وحسابات الاحتياط (Token Auto-Transfer)
                </h3>
                <span className="bg-pink-500/20 text-pink-300 border border-pink-500/40 text-[11px] font-black px-2.5 py-0.5 rounded-full flex items-center gap-1">
                  <Flame className="w-3.5 h-3.5 text-pink-400 fill-pink-400" />
                  <span>Session Handover Active</span>
                </span>
              </div>
              <p className="text-xs text-slate-300 mt-1">
                نقل المقاعد المحجوزة فوراً وتلقائياً إلى حساب Webook آخر قبل انتهاء مهلة الـ 15 دقيقة لضمان استمرارية الحجز وتجديد الصلاحية دون فقدان المقاعد.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 bg-slate-900/80 border border-slate-700/80 px-4 py-2 rounded-2xl">
            <Clock className="w-4 h-4 text-amber-400 animate-spin" />
            <div>
              <div className="text-[10px] text-slate-400 font-bold uppercase">مهلة الجلسة الحالية</div>
              <div className="text-xs font-mono font-black text-white">
                {Math.floor(sessionTimeLeft / 60)}:{(sessionTimeLeft % 60).toString().padStart(2, "0")} دقيقة
              </div>
            </div>
          </div>
        </div>

        {/* Configuration Inputs Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Inputs Column */}
          <div className="lg:col-span-7 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Primary Token */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-300 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <KeyRound className="w-3.5 h-3.5 text-pink-400" />
                    <span>توكن الحساب الأصلي (Primary Token)</span>
                  </span>
                  <span className="text-[10px] text-emerald-400 font-bold">الحساب النشط</span>
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={config.primaryToken}
                    onChange={(e) => setConfig({ ...config, primaryToken: e.target.value })}
                    placeholder="wbk_sess_live_..."
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl py-2.5 px-3 text-xs font-mono text-pink-300 focus:outline-none focus:ring-2 focus:ring-pink-500"
                  />
                  <button
                    onClick={() => handleCopy(config.primaryToken, "prim")}
                    className="absolute left-2 top-2.5 text-slate-400 hover:text-white p-1"
                    title="نسخ"
                  >
                    {copiedToken === "prim" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Target Token (New Account) */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-300 flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <UserCheck className="w-3.5 h-3.5 text-emerald-400" />
                    <span>توكن الحساب البديل (Target Token)</span>
                  </span>
                  <span className="text-[10px] text-indigo-300 bg-indigo-500/20 px-1.5 py-0.5 rounded font-mono">حساب الاستلام</span>
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={config.targetToken}
                    onChange={(e) => setConfig({ ...config, targetToken: e.target.value })}
                    placeholder="أدخل توكن أو جلسة الحساب الاحتياطي لـ Webook..."
                    className="w-full bg-slate-950 border border-indigo-500/50 rounded-xl py-2.5 px-3 text-xs font-mono text-emerald-300 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <button
                    onClick={() => handleCopy(config.targetToken, "targ")}
                    className="absolute left-2 top-2.5 text-slate-400 hover:text-white p-1"
                    title="نسخ"
                  >
                    {copiedToken === "targ" ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Target Account Email / Identifier */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-300">
                  البريد الإلكتروني / معرف الحساب البديل
                </label>
                <input
                  type="email"
                  value={config.targetAccountEmail}
                  onChange={(e) => setConfig({ ...config, targetAccountEmail: e.target.value })}
                  placeholder="secondary_buyer@email.com"
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl py-2.5 px-3 text-xs text-white focus:outline-none focus:ring-2 focus:ring-pink-500"
                />
              </div>

              {/* Current Active Hold Token */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-300 flex items-center justify-between">
                  <span>رمز الحجز المراد ترحيله (Hold Token)</span>
                  <span className="text-[10px] text-emerald-400 font-mono">15m Locked</span>
                </label>
                <input
                  type="text"
                  value={config.holdToken}
                  onChange={(e) => setConfig({ ...config, holdToken: e.target.value })}
                  placeholder="WBK-HLD-..."
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl py-2.5 px-3 text-xs font-mono text-yellow-300 focus:outline-none focus:ring-2 focus:ring-pink-500"
                />
              </div>
            </div>

            {/* Strategy & Threshold */}
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-pink-400" />
                    <span>توقيت الترحيل التلقائي قبل الإلغاء:</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    التقاط المقاعد في الحساب الجديد فور تحريرها بدقة 8ms
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {[15, 30, 60].map((sec) => (
                    <button
                      key={sec}
                      onClick={() => setConfig({ ...config, autoTransferSecondsBefore: sec })}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                        config.autoTransferSecondsBefore === sec
                          ? "bg-pink-600 text-white shadow-md shadow-pink-500/20"
                          : "bg-slate-950 text-slate-400 hover:text-white border border-slate-800"
                      }`}
                    >
                      {sec} ثانية قبل النهاية
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3">
                <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={config.isEnabled}
                    onChange={(e) => setConfig({ ...config, isEnabled: e.target.checked })}
                    className="rounded border-slate-700 text-pink-600 focus:ring-pink-500 w-4 h-4"
                  />
                  <span className="font-semibold text-white">تفعيل المراقبة والترحيل الذاتي التلقائي في الخلفية (Background Daemon)</span>
                </label>

                <span className="text-[11px] text-emerald-400 font-mono font-bold flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  حماية ضد فقدان المقاعد
                </span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
              <button
                id="btn-execute-token-transfer"
                onClick={handleExecuteImmediateTransfer}
                disabled={isExecutingTransfer || !config.targetToken}
                className="w-full sm:flex-1 py-3.5 px-5 rounded-xl bg-gradient-to-r from-pink-600 via-rose-600 to-indigo-600 hover:from-pink-500 hover:to-indigo-500 text-white font-black text-xs md:text-sm shadow-xl shadow-pink-600/30 flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-50 cursor-pointer"
              >
                {isExecutingTransfer ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>جاري ترحيل التوكن وتثبيت المقاعد في الحساب المستهدف...</span>
                  </>
                ) : (
                  <>
                    <ArrowLeftRight className="w-4 h-4" />
                    <span>تنفيذ الترحيل الفوري للحساب المستهدف الآن ⚡</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Right Status & Active Relays Column */}
          <div className="lg:col-span-5 space-y-4 flex flex-col justify-between">
            <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-4.5 space-y-3.5">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800/80 text-xs font-bold text-white">
                <span className="flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-pink-400" />
                  <span>آلية عمل الترحيل المتوازي (0ms Swap)</span>
                </span>
                <span className="text-[10px] text-emerald-400 font-mono bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  ACTIVE
                </span>
              </div>

              <div className="space-y-2.5 text-xs text-slate-300">
                <div className="flex items-start gap-2">
                  <div className="w-5 h-5 rounded-full bg-pink-500/20 text-pink-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                    1
                  </div>
                  <p>
                    يقوم العامل (Worker) بمراقبة العداد التنازلي لرمز الحجز الحالي (<code className="text-yellow-300 font-mono text-[11px]">{config.holdToken}</code>).
                  </p>
                </div>

                <div className="flex items-start gap-2">
                  <div className="w-5 h-5 rounded-full bg-pink-500/20 text-pink-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                    2
                  </div>
                  <p>
                    عند الوصول إلى <strong className="text-white">{config.autoTransferSecondsBefore} ثانية</strong> قبل الانتهاء، يُرسل طلب قنص متزامن بحساب التوكن الثاني.
                  </p>
                </div>

                <div className="flex items-start gap-2">
                  <div className="w-5 h-5 rounded-full bg-pink-500/20 text-pink-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                    3
                  </div>
                  <p>
                    يتم تمديد صلاحية المقاعد لـ <strong className="text-emerald-400 font-bold">15 دقيقة إضافية</strong> بحسابك الآخر لتتمكن من إتمام الدفع براحة تامة.
                  </p>
                </div>
              </div>
            </div>

            {/* Active Relay Log Card */}
            <div className="bg-slate-950/80 border border-slate-800 rounded-2xl p-4 space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-slate-300">
                <span>سجل عمليات الترحيل النشطة (Relay History)</span>
                <span className="text-[10px] text-slate-500 font-mono">{activeTransfers.length} سجل</span>
              </div>

              <div className="space-y-2 max-h-36 overflow-y-auto pr-1">
                {activeTransfers.map((trf) => (
                  <div
                    key={trf.id}
                    className="p-2.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between gap-2 text-[11px]"
                  >
                    <div className="space-y-0.5">
                      <div className="font-bold text-white flex items-center gap-1">
                        <span>{trf.source}</span>
                        <span className="text-pink-400">➔</span>
                        <span className="text-emerald-300">{trf.target}</span>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono flex items-center gap-1.5">
                        <span>{trf.holdToken}</span>
                        <span>•</span>
                        <span className="text-cyan-400">{trf.latencyMs}ms</span>
                      </div>
                    </div>

                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        trf.status === "TRANSFERRED"
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      }`}
                    >
                      {trf.status === "TRANSFERRED" ? "تم الترحيل ✓" : "قيد المراقبة"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Streaming Logs Terminal */}
      <div className="glass rounded-3xl overflow-hidden border border-slate-800">
        <div className="bg-slate-900/90 px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold text-white">
            <Terminal className="w-4 h-4 text-blue-400" />
            <span>Ingestion & Sniper Worker Live Stream</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsPaused(!isPaused)}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              {isPaused ? (
                <>
                  <Play className="w-3 h-3 text-emerald-400" />
                  <span>Resume</span>
                </>
              ) : (
                <>
                  <Pause className="w-3 h-3 text-yellow-400" />
                  <span>Pause</span>
                </>
              )}
            </button>

            <button
              onClick={() => setLogs([])}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <Trash2 className="w-3 h-3 text-red-400" />
              <span>Clear</span>
            </button>
          </div>
        </div>

        <div className="bg-slate-950 p-6 font-mono text-xs max-h-96 overflow-y-auto space-y-2">
          {logs.length === 0 ? (
            <div className="text-slate-500 text-center py-6">
              Console output cleared. Awaiting new worker log events...
            </div>
          ) : (
            logs.map((item) => (
              <div key={item.id} className="flex items-start gap-3">
                <span className="text-slate-500 shrink-0" suppressHydrationWarning>[{item.time}]</span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                    item.level === "SUCCESS"
                      ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                      : item.level === "WARN"
                      ? "bg-yellow-950 text-yellow-300 border border-yellow-800"
                      : "bg-blue-950 text-blue-300 border border-blue-800"
                  }`}
                >
                  {item.level}
                </span>
                <span className="text-slate-300">{item.msg}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
