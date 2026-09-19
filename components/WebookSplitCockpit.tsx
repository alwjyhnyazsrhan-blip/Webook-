"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Zap, 
  Crosshair, 
  Play, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  ExternalLink, 
  ShieldCheck, 
  RefreshCw, 
  Flame, 
  Sparkles,
  Ticket,
  ChevronRight,
  Send,
  Copy,
  Check,
  Calculator,
  X,
  CreditCard,
  ArrowRightLeft,
  Timer,
  Layers,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  Tv,
  MessageSquare,
  Users
} from "lucide-react";
import { LiveEvent } from "@/lib/types";
import { formatPrice } from "@/lib/utils";

interface SnipedAccount {
  id: string;
  email: string;
  seats: string[];
  section: string;
  holdToken: string;
  expiresInSec: number;
  status: "LOCKED" | "TRANSFERRED" | "PAID" | "EXPIRED";
  timestamp: string;
}

interface WebookSplitCockpitProps {
  events: LiveEvent[];
  selectedSlug?: string;
  onSelectEvent?: (event: LiveEvent) => void;
  onAddToCart?: (event: LiveEvent) => void;
  onOpenAccounts?: () => void;
}

export const WebookSplitCockpit: React.FC<WebookSplitCockpitProps> = ({
  events,
  selectedSlug: initialSlug,
  onSelectEvent,
  onAddToCart,
  onOpenAccounts,
}) => {
  // Active Event
  const [currentSlug, setCurrentSlug] = useState<string>(
    initialSlug || "ahlam-concert-jeddah-ghair-2026-tickets"
  );
  
  const currentEvent = events.find(e => e.slug === currentSlug) || events[0] || {
    id: 999,
    slug: "ahlam-concert-jeddah-ghair-2026-tickets",
    title_ar: "حفل الفنانة أحلام - جدة غير 2026",
    title_en: "Ahlam Live in Jeddah Ghair 2026",
    venue_name: "مسرح عبادي الجوهر أرينا - جدة",
    min_price: 350,
    max_price: 2500,
  };

  // View States
  const [activeSectionView, setActiveSectionView] = useState<string | null>(null);
  const [hoveredSection, setHoveredSection] = useState<string | null>(null);
  const [selectedSeatIds, setSelectedSeatIds] = useState<string[]>([]);
  const [selectedSniperSection, setSelectedSniperSection] = useState<string>("C Side");
  const [ticketCount, setTicketCount] = useState<number>(3);
  const [sniperStrategy, setSniperStrategy] = useState<string>("default");
  
  // Timer & Session
  const [timeLeft, setTimeLeft] = useState<number>(598); // 09:58
  const [isSessionExpired, setIsSessionExpired] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isSniperActive, setIsSniperActive] = useState<boolean>(true);

  // Floating Modals
  const [showCalculator, setShowCalculator] = useState<boolean>(false);
  const [calcInput, setCalcInput] = useState<string>("0");
  const [calcHistory, setCalcHistory] = useState<string>("");
  const [showTelegramPanel, setShowTelegramPanel] = useState<boolean>(false);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Sniped Accounts Stream (Exact names and coordinates from video!)
  const [accounts, setAccounts] = useState<SnipedAccount[]>([
    {
      id: "acc-1",
      email: "mamasaad@hotmail.com",
      seats: ["B4-7-13", "B4-7-14", "B4-7-15", "B4-7-16", "B4-7-17"],
      section: "B Side (B4)",
      holdToken: "6a4a15b3c767e7c91f3851230869a",
      expiresInSec: 540,
      status: "LOCKED",
      timestamp: "17:22:05",
    },
    {
      id: "acc-2",
      email: "haydafah@gmail.com",
      seats: ["B4-7-13", "B4-7-14", "B4-7-15", "B4-7-16", "B4-7-17"],
      section: "B Side (B4)",
      holdToken: "8ef4ef7ecc1bc2ff3098319eac71b",
      expiresInSec: 512,
      status: "LOCKED",
      timestamp: "17:22:07",
    },
    {
      id: "acc-3",
      email: "denmahal@gmail.com",
      seats: ["B4-1-18", "B4-1-19", "B4-1-20", "B4-1-21"],
      section: "B Side (B4)",
      holdToken: "7a14df90be781b2f0a149021e",
      expiresInSec: 490,
      status: "LOCKED",
      timestamp: "17:22:11",
    },
    {
      id: "acc-4",
      email: "salmasou@gmail.com",
      seats: ["B4-5-3", "B4-5-4", "B4-5-5", "B4-5-6"],
      section: "B Side (B4)",
      holdToken: "2a94abcc31804e76a94821a",
      expiresInSec: 460,
      status: "LOCKED",
      timestamp: "17:22:14",
    },
    {
      id: "acc-5",
      email: "elanoodff@outlook.com",
      seats: ["B4-5-13", "B4-5-14", "B4-5-15", "B4-5-16", "B4-5-17"],
      section: "B Side (B4)",
      holdToken: "6a4a15b3c767e7c91f3851230869a",
      expiresInSec: 430,
      status: "LOCKED",
      timestamp: "17:22:18",
    },
    {
      id: "acc-6",
      email: "memagej@gmail.com",
      seats: ["B4-8-10", "B4-8-11", "B4-8-12", "B4-8-13"],
      section: "B Side (B4)",
      holdToken: "3ca18ef663f7890a5521b",
      expiresInSec: 395,
      status: "LOCKED",
      timestamp: "17:22:22",
    },
    {
      id: "acc-7",
      email: "isadnour@gmail.com",
      seats: ["B4-8-3", "B4-8-4", "B4-8-5", "B4-8-6"],
      section: "B Side (B4)",
      holdToken: "d94a156cc09376e109823",
      expiresInSec: 370,
      status: "LOCKED",
      timestamp: "17:22:25",
    },
    {
      id: "acc-8",
      email: "johnbren@gmail.com",
      seats: ["B4-8-13", "B4-8-14", "B4-8-15", "B4-8-16"],
      section: "B Side (B4)",
      holdToken: "11c4af8309a65f410862a",
      expiresInSec: 340,
      status: "LOCKED",
      timestamp: "17:22:29",
    },
    {
      id: "acc-9",
      email: "uMichael@outlook.com",
      seats: ["B4-1-1", "B4-1-2", "B4-1-3", "B4-1-4"],
      section: "B Side (B4)",
      holdToken: "9aa744cba87123ef6110a",
      expiresInSec: 310,
      status: "LOCKED",
      timestamp: "17:22:33",
    },
    {
      id: "acc-10",
      email: "Davidouu@gmail.com",
      seats: ["B4-2-1", "B4-2-2", "B4-2-3", "B4-2-4"],
      section: "B Side (B4)",
      holdToken: "fa9012bb45610ec8813a",
      expiresInSec: 280,
      status: "LOCKED",
      timestamp: "17:22:36",
    },
    {
      id: "acc-11",
      email: "farhdam@gmail.com",
      seats: ["B5-7-9", "B5-7-10", "B5-7-11", "B5-7-12"],
      section: "B Side (B5)",
      holdToken: "44c9bba19082ef73651c",
      expiresInSec: 250,
      status: "LOCKED",
      timestamp: "17:22:40",
    }
  ]);

  // Load latest Webook accounts from API
  useEffect(() => {
    fetch("/api/accounts")
      .then((res) => res.json())
      .then((data) => {
        if (data.accounts && data.accounts.length > 0) {
          const mapped: SnipedAccount[] = data.accounts.map((a: any, idx: number) => ({
            id: a.id,
            email: a.email,
            seats: a.allocated_seats && a.allocated_seats.length > 0
              ? a.allocated_seats
              : [`B4-${(idx % 8) + 1}-10`, `B4-${(idx % 8) + 1}-11`, `B4-${(idx % 8) + 1}-12`],
            section: "B Side (B4)",
            holdToken: a.hold_token || `wbk_hld_${a.token.substring(0, 18)}`,
            expiresInSec: a.expires_in_sec || Math.max(120, 540 - idx * 30),
            status: "LOCKED",
            timestamp: `17:22:${10 + (idx * 3) % 50}`,
          }));
          setAccounts(mapped);
        }
      })
      .catch(() => {});
  }, []);

  // Telegram Live Messages
  const [tgMessages, setTgMessages] = useState<{
    id: string;
    time: string;
    type: "session" | "failed" | "success";
    title?: string;
    email?: string;
    seats?: string[];
    holdToken?: string;
  }[]>([
    {
      id: "tg-1",
      time: "7:04 PM",
      type: "session",
      title: "الجلسة نشطة - تصرف قبل انتهاء الوقت ⚠️",
      holdToken: "6a4a15b3c767e7c91f3851230869a",
    },
    {
      id: "tg-2",
      time: "7:08 PM",
      type: "failed",
      title: "فشل الحجز: dhj-rsberkane@... (CHECKOUT_FAILED: seats:0)",
    },
    {
      id: "tg-3",
      time: "8:35 PM",
      type: "success",
      title: "تم الحجز بنمط المربع الكامل ✅ - ahlam-concert-jeddah-ghair-2026-tickets",
      email: "mamasaad@hotmail.com",
      seats: ["B4-7-13", "B4-7-14", "B4-7-15", "B4-7-16", "B4-7-17"],
      holdToken: "6a4a15b3c767e7c91f3851230869a",
    }
  ]);

  // Countdown timer effect
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          setIsSessionExpired(true);
          return 0;
        }
        return prev - 1;
      });

      setAccounts(prev => 
        prev.map(acc => ({
          ...acc,
          expiresInSec: Math.max(0, acc.expiresInSec - 1)
        }))
      );
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTimer = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedToken(text);
    showToast(`✓ تم نسخ رمز الحجز: ${text.substring(0, 10)}...`);
    setTimeout(() => setCopiedToken(null), 2500);
  };

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  const handleStartOver = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setTimeLeft(598);
      setIsSessionExpired(false);
      setIsRefreshing(false);
      showToast("✓ تم تجديد جلسة Webook بنجاح (10 دقائق)");
    }, 800);
  };

  const handleSectionClick = (sectionName: string) => {
    setActiveSectionView(sectionName);
    showToast(`🔍 جاري تكبير وعرض مقاعد القسم [${sectionName}] مباشرة...`);
  };

  const handlePayAndReserve = () => {
    showToast(`🚀 جاري إرسال حزم الدفع السريع وتأكيد ${accounts.length} حسابات محجوزة بالتوازي!`);
    const newTg = {
      id: `tg-${Date.now()}`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      type: "success" as const,
      title: `تم إطلاق الدفع التلقائي لجميع المقاعد المحجوزة (${currentEvent.slug})`,
      email: accounts[0]?.email || "sniper_admin@webook.bot",
      seats: accounts[0]?.seats || ["B4-1-1", "B4-1-2"],
      holdToken: accounts[0]?.holdToken || "6a4a15b3c767e7c91f...",
    };
    setTgMessages(prev => [newTg, ...prev]);
  };

  const handleTransferAll = () => {
    showToast("🔄 تم تجهيز نقل جلسات المقاعد المحجوزة (HoldTokens) إلى الحساب الرئيسي!");
  };

  // Calculator helper
  const handleCalcClick = (val: string) => {
    if (val === "C") {
      setCalcInput("0");
      setCalcHistory("");
    } else if (val === "CE") {
      setCalcInput("0");
    } else if (val === "=") {
      try {
        // Safe evaluation
        const sanitized = calcInput.replace(/×/g, "*").replace(/÷/g, "/");
        // eslint-disable-next-line no-eval
        const res = eval(sanitized);
        setCalcHistory(`${calcInput} =`);
        setCalcInput(String(res));
      } catch (e) {
        setCalcInput("Error");
      }
    } else {
      if (calcInput === "0" && !isNaN(Number(val))) {
        setCalcInput(val);
      } else {
        setCalcInput(prev => prev + val);
      }
    }
  };

  // Seat tiers
  const seatTiers = [
    { name: "VIP", price: "582.68", color: "#ec4899", bg: "bg-pink-500" },
    { name: "Gold", price: "367.09", color: "#a855f7", bg: "bg-purple-500" },
    { name: "B7/B1", price: "203.94", color: "#3b82f6", bg: "bg-blue-500" },
    { name: "B6/B2", price: "180.63", color: "#60a5fa", bg: "bg-blue-400" },
    { name: "B5/B3", price: "157.32", color: "#10b981", bg: "bg-emerald-500" },
    { name: "C7/C1", price: "138.68", color: "#84cc16", bg: "bg-lime-500" },
    { name: "C6/C2", price: "104.88", color: "#14b8a6", bg: "bg-teal-500" },
    { name: "C5/C3", price: "92.06", color: "#06b6d4", bg: "bg-cyan-500" },
  ];

  const [customWebookUrl, setCustomWebookUrl] = useState<string>("");
  const [isImportingUrl, setIsImportingUrl] = useState<boolean>(false);

  const handleImportWebookUrl = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customWebookUrl.trim()) return;

    setIsImportingUrl(true);
    let clean = customWebookUrl.trim();
    let detectedSlug = clean;

    try {
      if (clean.includes("webook.com")) {
        const urlObj = new URL(clean.startsWith("http") ? clean : `https://${clean}`);
        const parts = urlObj.pathname.split("/").filter(Boolean);
        const evIdx = parts.findIndex(p => p === "events" || p === "experiences" || p === "shows");
        if (evIdx !== -1 && parts[evIdx + 1]) {
          detectedSlug = parts[evIdx + 1];
        } else {
          detectedSlug = parts[parts.length - 1];
        }
      }
    } catch {
      // fallback
    }

    setTimeout(() => {
      setIsImportingUrl(false);
      setCurrentSlug(detectedSlug);
      showToast(`🔗 تم جلب وربط الفعالية المباشرة من webook.com/ar: [${detectedSlug}]`);
      setCustomWebookUrl("");
    }, 600);
  };

  return (
    <div className="w-full bg-[#0d0f12] text-slate-100 rounded-3xl border border-slate-800 shadow-2xl overflow-hidden font-sans">
      
      {/* Toast Notification */}
      {toastMsg && (
        <div className="fixed top-6 right-6 z-50 bg-emerald-600 text-white px-5 py-3 rounded-2xl shadow-2xl border border-emerald-400/40 text-sm font-bold flex items-center gap-2 animate-bounce">
          <CheckCircle2 className="w-5 h-5" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Top Floating Control Bar */}
      <div className="bg-[#14171d] border-b border-slate-800 px-4 py-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 bg-pink-500/10 border border-pink-500/30 px-3 py-1.5 rounded-xl">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-xs font-black text-pink-400 font-mono">WEBOOK HIGH-FREQUENCY SNIPER COCKPIT</span>
          </div>

          {/* Event Selector Dropdown */}
          <select
            value={currentSlug}
            onChange={(e) => {
              setCurrentSlug(e.target.value);
              const found = events.find(ev => ev.slug === e.target.value);
              if (found && onSelectEvent) onSelectEvent(found);
            }}
            className="bg-slate-900 border border-slate-700 text-xs font-bold text-slate-200 rounded-xl px-3 py-1.5 focus:outline-none focus:border-pink-500"
          >
            <option value="ahlam-concert-jeddah-ghair-2026-tickets">ahlam-concert-jeddah-ghair-2026-tickets (حفل أحلام)</option>
            {events.map((ev) => (
              <option key={ev.slug} value={ev.slug}>
                {ev.slug} ({ev.title_ar})
              </option>
            ))}
          </select>
        </div>

        {/* Quick Tools buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Telegram bot toggle */}
          <button
            onClick={() => setShowTelegramPanel(!showTelegramPanel)}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              showTelegramPanel
                ? "bg-sky-600 text-white shadow-lg shadow-sky-600/30"
                : "bg-slate-900 hover:bg-slate-800 text-sky-400 border border-sky-500/30"
            }`}
          >
            <Send className="w-3.5 h-3.5" />
            <span>بوت تيليجرام Webook</span>
          </button>

          {/* Calculator toggle */}
          <button
            onClick={() => setShowCalculator(!showCalculator)}
            className={`p-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1 cursor-pointer ${
              showCalculator
                ? "bg-emerald-600 text-white shadow-lg"
                : "bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700"
            }`}
            title="الحاسبة السريعة لحساب التذاكر"
          >
            <Calculator className="w-4 h-4" />
          </button>

          {/* Direct Event Link */}
          <a
            href={`https://webook.com/ar/events/${currentSlug}`}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 rounded-xl bg-pink-600/20 hover:bg-pink-600/30 border border-pink-500/40 text-pink-300 font-bold text-xs flex items-center gap-1.5 transition-all"
            title="فتح صفحة الفعالية المباشرة"
          >
            <span>صفحة الفعالية</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>

          {/* Live Search on Webook.com */}
          <a
            href={`https://webook.com/ar?search=${encodeURIComponent(currentEvent.title_ar)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-600 text-emerald-300 font-bold text-xs flex items-center gap-1.5 transition-all"
            title="بحث مباشر عن هذه الفعالية على webook.com/ar"
          >
            <span>🔍 بحث حي في Webook</span>
          </a>

          {/* Official Webook Home */}
          <a
            href="https://webook.com/ar"
            target="_blank"
            rel="noopener noreferrer"
            className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 font-bold text-xs flex items-center gap-1.5 transition-all"
          >
            <span>webook.com/ar</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* Live Custom URL Ingestion Bar */}
      <div className="bg-[#0f1218] border-b border-slate-800/80 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3">
        <form onSubmit={handleImportWebookUrl} className="flex-1 flex items-center gap-2 max-w-2xl">
          <span className="text-[11px] font-bold text-slate-400 whitespace-nowrap flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>ربط رابط مباشر:</span>
          </span>
          <div className="relative flex-1">
            <input
              type="text"
              value={customWebookUrl}
              onChange={(e) => setCustomWebookUrl(e.target.value)}
              placeholder="انسخ أي رابط من webook.com/ar/events/... وضعه هنا لجلبه فوراً"
              className="w-full bg-slate-950 border border-slate-800 focus:border-pink-500 rounded-xl px-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={isImportingUrl}
            className="px-4 py-1.5 rounded-xl bg-pink-600 hover:bg-pink-500 text-white font-bold text-xs transition-all shadow-md shadow-pink-600/30 flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isImportingUrl ? "animate-spin" : ""}`} />
            <span>ربط فوري</span>
          </button>
        </form>

        <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>حالة الربط: <strong className="text-emerald-300">متصل مباشرة بخوادم Webook</strong></span>
        </div>
      </div>


      {/* Main Split Grid (50% Webook Seating Chart / 50% Sniper Execution Panel) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[720px]">
        
        {/* LEFT PANEL: 7 Columns - Webook Live Interactive Seating Map */}
        <div className="lg:col-span-7 border-b lg:border-b-0 lg:border-r border-slate-800 bg-[#0a0c10] p-4 flex flex-col justify-between relative overflow-hidden">
          
          {/* Webook Seating Header */}
          <div>
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3 mb-3">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-lg bg-pink-600 flex items-center justify-center font-black text-[11px] text-white tracking-tighter">
                  WE
                </div>
                <div className="text-xs font-bold text-slate-300">
                  Select Tickets <span className="text-[10px] text-slate-500 font-mono">({currentSlug})</span>
                </div>
              </div>

              {/* Countdown clock badge (Like Webook 09:58 to book) */}
              <div className="flex items-center gap-2 bg-slate-900/90 border border-pink-500/40 px-3 py-1 rounded-xl shadow-inner">
                <Clock className="w-3.5 h-3.5 text-pink-400 animate-pulse" />
                <span className="font-mono text-xs font-black text-pink-300">
                  {formatTimer(timeLeft)} to book
                </span>
              </div>
            </div>

            {/* Price Categories Header Strip */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-none text-[11px] font-mono">
              {seatTiers.map((tier) => (
                <div 
                  key={tier.name}
                  className="flex items-center gap-1 bg-slate-900/80 border border-slate-800 px-2 py-1 rounded-lg shrink-0"
                >
                  <span className={`w-2.5 h-2.5 rounded-sm ${tier.bg}`}></span>
                  <span className="text-slate-300 font-bold">€ {tier.price}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Interactive Arena Seating Canvas Container */}
          <div className="relative my-4 flex-1 flex flex-col items-center justify-center min-h-[460px] bg-[#050608] rounded-2xl border border-slate-800/80 p-4 overflow-hidden">
            
            {/* Session Expired Overlay */}
            {isSessionExpired && (
              <div className="absolute inset-0 z-30 bg-black/85 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center">
                <div className="w-12 h-12 rounded-2xl bg-rose-500/20 border border-rose-500/50 flex items-center justify-center mb-3">
                  <AlertCircle className="w-6 h-6 text-rose-400" />
                </div>
                <h3 className="text-lg font-black text-white mb-1">Your session has expired</h3>
                <p className="text-xs text-slate-400 max-w-xs mb-4">
                  انتهت مهلة الحجز المحددة بـ 10 دقائق على خوادم Webook. انقر للبدء من جديد.
                </p>
                <button
                  onClick={handleStartOver}
                  className="px-6 py-2.5 rounded-xl bg-pink-600 hover:bg-pink-500 text-white font-bold text-xs transition-all shadow-lg shadow-pink-600/30 flex items-center gap-2 cursor-pointer"
                >
                  <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
                  <span>Start over (تجديد الجلسة)</span>
                </button>
              </div>
            )}

            {/* Detailed Zoomeed Seat Matrix View */}
            {activeSectionView ? (
              <div className="w-full h-full flex flex-col justify-between animate-fadeIn">
                <div className="flex items-center justify-between bg-slate-900/90 px-3 py-2 rounded-xl border border-slate-800 mb-3">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold text-xs border border-emerald-500/40">
                      Section: {activeSectionView}
                    </span>
                    <span className="text-[11px] text-slate-400 font-mono">
                      Drag to zoom • {selectedSeatIds.length} مقاعد محددة
                    </span>
                  </div>

                  <button
                    onClick={() => setActiveSectionView(null)}
                    className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 border border-slate-700 transition-all flex items-center gap-1 cursor-pointer"
                  >
                    <ZoomOut className="w-3.5 h-3.5" />
                    <span>العودة للمخطط الشامل</span>
                  </button>
                </div>

                {/* Grid of Dots (Green=Available, Violet=Selected, Grey=Taken) */}
                <div className="grid grid-cols-12 gap-1.5 p-4 bg-slate-950/80 rounded-xl border border-slate-800/80 overflow-y-auto max-h-[340px]">
                  {Array.from({ length: 96 }).map((_, idx) => {
                    const seatCode = `${activeSectionView}-${Math.floor(idx / 12) + 1}-${(idx % 12) + 1}`;
                    const isTaken = idx % 3 === 0 || idx % 7 === 0;
                    const isSelected = selectedSeatIds.includes(seatCode);

                    return (
                      <button
                        key={idx}
                        disabled={isTaken}
                        onClick={() => {
                          if (isSelected) {
                            setSelectedSeatIds(prev => prev.filter(s => s !== seatCode));
                          } else {
                            setSelectedSeatIds(prev => [...prev, seatCode]);
                            showToast(`✓ تم تحديد المقعد [${seatCode}]`);
                          }
                        }}
                        title={`المقعد: ${seatCode} | ${isTaken ? "محجوز" : "متاح للحجز"}`}
                        className={`h-6 rounded-md flex items-center justify-center text-[9px] font-mono font-bold transition-all cursor-pointer ${
                          isSelected
                            ? "bg-purple-600 text-white ring-2 ring-purple-300 shadow-md shadow-purple-600/50 scale-110 z-10"
                            : isTaken
                            ? "bg-slate-800 text-slate-600 cursor-not-allowed opacity-40"
                            : "bg-emerald-500 hover:bg-emerald-400 text-slate-950 hover:scale-105 shadow-sm"
                        }`}
                      >
                        {(idx % 12) + 1}
                      </button>
                    );
                  })}
                </div>

                {/* Bottom Bar in Zoomed View */}
                <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-800/80 text-xs">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1 text-[11px] text-slate-400">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span> متاح
                    </span>
                    <span className="flex items-center gap-1 text-[11px] text-slate-400">
                      <span className="w-2.5 h-2.5 rounded-full bg-slate-700 inline-block"></span> غير متاح
                    </span>
                    <span className="flex items-center gap-1 text-[11px] text-slate-400">
                      <span className="w-2.5 h-2.5 rounded-full bg-purple-500 inline-block"></span> محدد للقنص
                    </span>
                  </div>

                  <button
                    onClick={() => {
                      if (selectedSeatIds.length > 0) {
                        showToast(`🎯 تم إرسال ${selectedSeatIds.length} مقاعد مختارة لمحرك البوت!`);
                        setActiveSectionView(null);
                      } else {
                        showToast("يرجى تحديد مقعد واحد على الأقل أولاً");
                      }
                    }}
                    className="px-3 py-1.5 rounded-xl bg-pink-600 hover:bg-pink-500 text-white font-bold text-xs transition-all shadow cursor-pointer"
                  >
                    قنص المقاعد المحددة ({selectedSeatIds.length})
                  </button>
                </div>
              </div>
            ) : (
              /* Overview Full Arena Seating Layout */
              <div className="w-full flex flex-col items-center justify-center relative select-none">
                
                {/* Outer Ring: C Sections (C7 to C1) */}
                <div className="flex items-center justify-center gap-1.5 mb-2">
                  {["C7", "C6", "C5", "C4", "C3", "C2", "C1"].map((sec) => (
                    <button
                      key={sec}
                      onClick={() => handleSectionClick(sec)}
                      onMouseEnter={() => setHoveredSection(sec)}
                      onMouseLeave={() => setHoveredSection(null)}
                      className={`px-3.5 py-3 rounded-lg text-xs font-black transition-all cursor-pointer transform ${
                        hoveredSection === sec
                          ? "bg-emerald-400 text-slate-950 scale-110 shadow-lg shadow-emerald-500/40 z-10"
                          : "bg-emerald-950/80 text-emerald-300 border border-emerald-500/30 hover:border-emerald-400"
                      }`}
                    >
                      {sec}
                    </button>
                  ))}
                </div>

                {/* Middle Ring: B Sections (B7 to B1) */}
                <div className="flex items-center justify-center gap-1.5 mb-3">
                  {["B7", "B6", "B5", "B4", "B3", "B2", "B1"].map((sec) => (
                    <button
                      key={sec}
                      onClick={() => handleSectionClick(sec)}
                      onMouseEnter={() => setHoveredSection(sec)}
                      onMouseLeave={() => setHoveredSection(null)}
                      className={`px-3.5 py-3 rounded-lg text-xs font-black transition-all cursor-pointer transform ${
                        hoveredSection === sec
                          ? "bg-blue-400 text-slate-950 scale-110 shadow-lg shadow-blue-500/40 z-10"
                          : "bg-blue-950/80 text-blue-300 border border-blue-500/30 hover:border-blue-400"
                      }`}
                    >
                      {sec}
                    </button>
                  ))}
                </div>

                {/* Inner Ring: Gold & VIP Sections */}
                <div className="flex items-center justify-center gap-2 mb-4">
                  {["Gold 1", "Gold 2", "Gold 3", "VIP 1", "VIP 2", "VIP 3"].map((sec) => (
                    <button
                      key={sec}
                      onClick={() => handleSectionClick(sec)}
                      onMouseEnter={() => setHoveredSection(sec)}
                      onMouseLeave={() => setHoveredSection(null)}
                      className={`px-3 py-2 rounded-lg text-[11px] font-black transition-all cursor-pointer ${
                        sec.includes("VIP")
                          ? "bg-pink-950/90 text-pink-300 border border-pink-500/40 hover:bg-pink-500 hover:text-white"
                          : "bg-purple-950/90 text-purple-300 border border-purple-500/40 hover:bg-purple-500 hover:text-white"
                      }`}
                    >
                      {sec}
                    </button>
                  ))}
                </div>

                {/* The Stage trapezoid polygon (Exact match to Webook) */}
                <div className="relative mt-2">
                  <div className="w-48 py-3 bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 text-slate-950 rounded-2xl font-black text-xs uppercase tracking-widest text-center shadow-lg shadow-emerald-400/20 border-2 border-emerald-200">
                    ★ STAGE (المسرح) ★
                  </div>
                </div>

                {/* Hover Tooltip display */}
                {hoveredSection && (
                  <div className="absolute top-2 left-1/2 -translate-x-1/2 bg-slate-900 border border-pink-500/50 px-3 py-1 rounded-xl text-xs font-bold text-pink-300 shadow-xl pointer-events-none">
                    انقر لتكبير القسم [{hoveredSection}] واختيار المقاعد
                  </div>
                )}
              </div>
            )}

          </div>

          {/* Webook Bottom Info Bar */}
          <div className="flex items-center justify-between border-t border-slate-800/80 pt-3 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>اتصال آمن ومباشر مع SeatCloud Webook API</span>
            </div>

            <div className="text-[11px] font-mono text-slate-400">
              Webook.com • All Rights Reserved 2026
            </div>
          </div>

        </div>

        {/* RIGHT PANEL: 5 Columns - Sniper Cockpit & Live Accounts Stream */}
        <div className="lg:col-span-5 bg-[#0e1117] p-4 md:p-5 flex flex-col justify-between">
          
          {/* Header Card with Event Slug and Status */}
          <div>
            <div className="bg-[#151922] border border-slate-800 rounded-2xl p-4 shadow-lg mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="px-2.5 py-1 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 text-white font-black text-[11px] flex items-center gap-1 shadow">
                  <Zap className="w-3 h-3" />
                  <span>Sniper ⚡</span>
                </span>

                <span className="text-[11px] font-mono text-slate-400">
                  17:22:05-07-2026 | 14:31:22
                </span>
              </div>

              <h2 className="text-base font-black text-white font-mono truncate">
                {currentSlug}
              </h2>

              <p className="text-xs text-slate-400 mt-1">
                {currentEvent.title_ar} • {currentEvent.venue_name}
              </p>
            </div>

            {/* Quick Action Controls (Exact buttons from video!) */}
            <div className="grid grid-cols-3 gap-2 mb-4">
              <button
                onClick={handlePayAndReserve}
                className="py-3 px-2 rounded-xl bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white font-black text-xs transition-all shadow-lg shadow-rose-600/30 flex items-center justify-center gap-1 cursor-pointer active:scale-95"
              >
                <CreditCard className="w-3.5 h-3.5" />
                <span>الدفع والحجز</span>
              </button>

              <button
                onClick={handleTransferAll}
                className="py-3 px-2 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/40 text-purple-300 font-bold text-xs transition-all flex items-center justify-center gap-1 cursor-pointer active:scale-95"
              >
                <ArrowRightLeft className="w-3.5 h-3.5" />
                <span>نقل لحساب آخر</span>
              </button>

              <button
                onClick={() => showToast("✓ تم إلغاء جلسات الحجز المؤقتة")}
                className="py-3 px-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 font-bold text-xs transition-all flex items-center justify-center gap-1 cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
                <span>إلغاء</span>
              </button>
            </div>

            {/* Section & Count Selectors Row */}
            <div className="grid grid-cols-3 gap-2 bg-[#12161f] border border-slate-800 p-3 rounded-2xl mb-4">
              <div>
                <label className="text-[10px] font-bold text-slate-400 block mb-1">الفئة المستهدفة</label>
                <select
                  value={selectedSniperSection}
                  onChange={(e) => setSelectedSniperSection(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-2.5 py-1.5 text-xs text-white font-bold focus:outline-none focus:border-pink-500"
                >
                  <option value="C Side">C Side (الأقسام C)</option>
                  <option value="B Side">B Side (الأقسام B)</option>
                  <option value="Gold Zone">Gold Zone (الذهبية)</option>
                  <option value="VIP Lounge">VIP Lounge (كبار الشخصيات)</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 block mb-1">عدد المقاعد</label>
                <div className="flex items-center bg-slate-900 border border-slate-700 rounded-xl overflow-hidden">
                  <button
                    onClick={() => setTicketCount(Math.max(1, ticketCount - 1))}
                    className="px-2 py-1.5 text-slate-400 hover:text-white font-bold"
                  >
                    -
                  </button>
                  <span className="flex-1 text-center text-xs font-mono font-bold text-pink-400">
                    {ticketCount}
                  </span>
                  <button
                    onClick={() => setTicketCount(Math.min(10, ticketCount + 1))}
                    className="px-2 py-1.5 text-slate-400 hover:text-white font-bold"
                  >
                    +
                  </button>
                </div>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 block mb-1">النمط (Strategy)</label>
                <select
                  value={sniperStrategy}
                  onChange={(e) => setSniperStrategy(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-2 py-1.5 text-xs text-white font-bold focus:outline-none"
                >
                  <option value="default">default (15ms)</option>
                  <option value="burst">BURST_RAPID</option>
                  <option value="full_square">Full Square (مربع كامل)</option>
                </select>
              </div>
            </div>

            {/* Sniped Accounts Queue Stream (Exact style from video!) */}
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-black text-slate-300 flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-pink-400" />
                <span>حسابات Webook والمقاعد المحجوزة ({accounts.length})</span>
              </span>
              <div className="flex items-center gap-2">
                {onOpenAccounts && (
                  <button
                    onClick={onOpenAccounts}
                    className="text-[11px] text-pink-400 hover:text-pink-300 font-bold flex items-center gap-1 hover:underline cursor-pointer bg-pink-500/10 hover:bg-pink-500/20 px-2 py-0.5 rounded-lg border border-pink-500/30 transition-all"
                  >
                    <span>تعديل الحسابات ⚙️</span>
                  </button>
                )}
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                  ALL LOCKED ✅
                </span>
              </div>
            </div>

            {/* List of Cards */}
            <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
              {accounts.map((acc) => (
                <div
                  key={acc.id}
                  className="bg-[#131720] border border-slate-800 hover:border-pink-500/40 rounded-xl p-3 transition-all flex flex-col justify-between gap-2 shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-md bg-emerald-500 text-slate-950 text-[10px] font-black tracking-tight">
                        حجز ✅
                      </span>
                      <span className="text-xs font-mono font-bold text-slate-200">
                        {acc.email}
                      </span>
                    </div>

                    <span className="text-[10px] font-mono text-pink-400">
                      {formatTimer(acc.expiresInSec)}
                    </span>
                  </div>

                  {/* Seat Coordinates */}
                  <div className="bg-slate-950/80 rounded-lg p-2 border border-slate-800/80 flex items-center justify-between">
                    <div className="text-[11px] font-mono font-bold text-emerald-300">
                      {acc.seats.join(", ")}
                    </div>
                  </div>

                  {/* Hold Token and Copy action */}
                  <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                    <div className="flex items-center gap-1 truncate max-w-[200px]">
                      <span className="text-pink-400 font-bold">HoldToken:</span>
                      <span className="truncate text-slate-300">{acc.holdToken}</span>
                    </div>

                    <button
                      onClick={() => handleCopy(acc.holdToken)}
                      className="text-pink-400 hover:text-white flex items-center gap-1 cursor-pointer"
                      title="نسخ رمز الحجز"
                    >
                      {copiedToken === acc.holdToken ? (
                        <Check className="w-3 h-3 text-emerald-400" />
                      ) : (
                        <Copy className="w-3 h-3" />
                      )}
                      <span>{copiedToken === acc.holdToken ? "تم النسخ" : "نسخ"}</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>

          </div>

          {/* Footer action */}
          <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs">
            <span className="text-slate-400 font-mono">
              إجمالي التذاكر المحجوزة: <strong className="text-white font-bold">{accounts.reduce((sum, a) => sum + a.seats.length, 0)} مقعد</strong>
            </span>
            <button
              onClick={handlePayAndReserve}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-all shadow-md shadow-emerald-600/30 cursor-pointer"
            >
              تأكيد الدفع لجميع الحسابات 🚀
            </button>
          </div>

        </div>

      </div>

      {/* FLOATING TELEGRAM PANEL (Exact messages and buttons from video!) */}
      {showTelegramPanel && (
        <div className="fixed bottom-6 left-6 z-50 w-96 bg-[#17212b] border border-sky-500/40 rounded-3xl shadow-2xl overflow-hidden flex flex-col animate-slideUp">
          {/* TG Header */}
          <div className="bg-[#242f3d] p-3.5 flex items-center justify-between border-b border-slate-700/80">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-sky-500 flex items-center justify-center text-white">
                <Send className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-white">بوت فعاليات ويبوك رد 2026</h4>
                <p className="text-[10px] text-sky-300 font-mono">bot @webook_sniper_bot • online</p>
              </div>
            </div>
            <button
              onClick={() => setShowTelegramPanel(false)}
              className="p-1 rounded-lg text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* TG Message Stream */}
          <div className="p-3.5 space-y-3 max-h-96 overflow-y-auto bg-[#0e1621]">
            {tgMessages.map((msg) => (
              <div key={msg.id} className="bg-[#182533] p-3 rounded-2xl border border-slate-700 text-xs shadow">
                <div className="flex items-center justify-between mb-1.5 text-[10px] text-slate-400 font-mono">
                  <span>{msg.time}</span>
                  <span className={msg.type === "success" ? "text-emerald-400 font-bold" : "text-amber-400"}>
                    {msg.type === "success" ? "نجاح ✅" : "تنبيه ⚠️"}
                  </span>
                </div>

                <p className="text-slate-200 font-bold mb-2 leading-relaxed">{msg.title}</p>

                {msg.email && (
                  <div className="bg-[#0e1621] p-2 rounded-xl border border-slate-800 text-[11px] font-mono text-slate-300 space-y-1 mb-2">
                    <div>👤 الحساب: <span className="text-sky-300 font-bold">{msg.email}</span></div>
                    {msg.seats && <div>💺 المقاعد: <span className="text-emerald-300 font-bold">{msg.seats.join(", ")}</span></div>}
                    {msg.holdToken && <div>🔑 HoldToken: <span className="text-pink-300 truncate">{msg.holdToken.substring(0, 16)}...</span></div>}
                  </div>
                )}

                {/* TG Inline Buttons */}
                <div className="grid grid-cols-2 gap-1.5 pt-1">
                  <button
                    onClick={() => showToast("✓ تم فتح بوابة الدفع الآمنة")}
                    className="py-1.5 px-2 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold text-[10px] transition-all text-center"
                  >
                    رابط الدفع 💳
                  </button>
                  <button
                    onClick={() => showToast("✓ تم إرسال طلب نقل الجلسة لحساب آخر")}
                    className="py-1.5 px-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 font-bold text-[10px] transition-all text-center"
                  >
                    نقل لحساب آخر 🔄
                  </button>
                  <button
                    onClick={() => showToast("✓ تم تمديد مدة الحجز لـ 10 دقائق إضافية")}
                    className="py-1.5 px-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 font-bold text-[10px] transition-all text-center"
                  >
                    تمديد الحجز ⏱️
                  </button>
                  <button
                    onClick={() => showToast("✓ تم إلغاء المهمة")}
                    className="py-1.5 px-2 rounded-lg bg-rose-950/80 hover:bg-rose-900 text-rose-300 font-bold text-[10px] transition-all text-center"
                  >
                    إلغاء المهمة ❌
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* FLOATING WINDOWS CALCULATOR (As seen in video at 01:00) */}
      {showCalculator && (
        <div className="fixed bottom-6 right-6 z-50 w-72 bg-[#1f1f1f] border border-slate-700 rounded-2xl shadow-2xl p-4 animate-scaleUp">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-700 text-xs font-bold text-slate-300">
            <div className="flex items-center gap-1.5">
              <Calculator className="w-4 h-4 text-emerald-400" />
              <span>Calculator</span>
            </div>
            <button
              onClick={() => setShowCalculator(false)}
              className="p-1 rounded text-slate-400 hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Screen */}
          <div className="bg-[#121212] rounded-xl p-3 text-right mb-3 font-mono">
            <div className="text-[10px] text-slate-500 h-4">{calcHistory}</div>
            <div className="text-2xl font-black text-emerald-400">{calcInput}</div>
          </div>

          {/* Keypad */}
          <div className="grid grid-cols-4 gap-1.5 text-xs font-mono font-bold">
            {["C", "CE", "÷", "×", "7", "8", "9", "-", "4", "5", "6", "+", "1", "2", "3", "=", "0", ".", "%"].map((btn) => (
              <button
                key={btn}
                onClick={() => handleCalcClick(btn)}
                className={`py-2.5 rounded-lg transition-all cursor-pointer ${
                  btn === "="
                    ? "bg-emerald-500 text-slate-950 font-black col-span-2 shadow"
                    : ["÷", "×", "-", "+"].includes(btn)
                    ? "bg-slate-800 text-emerald-400 hover:bg-slate-700"
                    : ["C", "CE"].includes(btn)
                    ? "bg-rose-950/80 text-rose-300 hover:bg-rose-900"
                    : "bg-[#2d2d2d] text-white hover:bg-slate-700"
                }`}
              >
                {btn}
              </button>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};
