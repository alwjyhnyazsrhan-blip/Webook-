"use client";

import React, { useState } from "react";
import Image from "next/image";
import { 
  Globe, 
  ExternalLink, 
  RefreshCw, 
  ArrowLeft, 
  ArrowRight, 
  ShieldCheck, 
  Zap, 
  Crosshair, 
  ShoppingCart, 
  Search, 
  Sparkles, 
  Sliders, 
  Eye, 
  Flame, 
  Layers, 
  Check, 
  Copy,
  Maximize2,
  Minimize2,
  Tv,
  CheckCircle2,
  Ticket
} from "lucide-react";
import { LiveEvent } from "@/lib/types";
import { formatPrice, formatDate } from "@/lib/utils";

interface WebookLivePortalProps {
  events: LiveEvent[];
  onSelectEventForBot: (event: LiveEvent) => void;
  onAddToCart?: (event: LiveEvent) => void;
  cartSlugs?: string[];
}

export const WebookLivePortal: React.FC<WebookLivePortalProps> = ({
  events,
  onSelectEventForBot,
  onAddToCart,
  cartSlugs = [],
}) => {
  const [currentUrl, setCurrentUrl] = useState("https://webook.com/ar");
  const [activeCategory, setActiveCategory] = useState("all");
  const [searchFilter, setSearchFilter] = useState("");
  const [viewMode, setViewMode] = useState<"interactive_mirror" | "live_iframe">("interactive_mirror");
  const [isCopied, setIsCopied] = useState(false);
  const [isLoadingFrame, setIsLoadingFrame] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false);

  const categories = [
    { id: "all", name: "الكل (Home)", path: "https://webook.com/ar" },
    { id: "concerts", name: "🎤 حفلات وموسيقى", path: "https://webook.com/ar/category/concerts" },
    { id: "sports", name: "🏆 رياضة وكأس العالم EWC", path: "https://webook.com/ar/category/sports" },
    { id: "theatre", name: "🎭 مسرحيات وفنون", path: "https://webook.com/ar/category/theatre" },
    { id: "experiences", name: "✨ تجارب ومطاعم فيا رياض", path: "https://webook.com/ar/category/experiences" },
  ];

  const handleNavigate = (path: string, catId?: string) => {
    setCurrentUrl(path);
    if (catId) setActiveCategory(catId);
    setIsLoadingFrame(true);
    setTimeout(() => setIsLoadingFrame(false), 500);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(currentUrl);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
  };

  const filteredEvents = events.filter((ev) => {
    const q = searchFilter.toLowerCase().trim();
    const matchSearch = !q || ev.title_ar.toLowerCase().includes(q) || ev.venue_name.toLowerCase().includes(q) || ev.slug.includes(q);
    const matchCat = activeCategory === "all" || 
      (activeCategory === "concerts" && (ev.genre_slug?.includes("concert") || ev.genre_slug?.includes("music") || ev.title_ar.includes("حفل") || ev.title_ar.includes("أنغام") || ev.title_ar.includes("تامر"))) ||
      (activeCategory === "sports" && (ev.genre_slug?.includes("sport") || ev.title_ar.includes("كأس") || ev.title_ar.includes("دوري") || ev.title_ar.includes("سباق") || ev.title_ar.includes("فورمولا"))) ||
      (activeCategory === "theatre" && (ev.genre_slug?.includes("theatre") || ev.genre_slug?.includes("art") || ev.title_ar.includes("مسرحية"))) ||
      (activeCategory === "experiences" && (ev.genre_slug?.includes("experience") || ev.genre_slug?.includes("food") || ev.venue_name.includes("فيا رياض") || ev.venue_name.includes("Via")));
    return matchSearch && matchCat;
  });

  return (
    <div className={`rounded-3xl border border-pink-500/30 bg-slate-950/90 shadow-2xl overflow-hidden transition-all duration-300 ${isFullScreen ? "fixed inset-4 z-50 overflow-y-auto" : "mt-6"}`}>
      
      {/* Browser Top Navigation Bar */}
      <div className="bg-slate-900/90 border-b border-slate-800 p-3 md:p-4 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        
        {/* Navigation buttons & indicator */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 pl-2 border-l border-slate-700/80">
            <span className="w-3 h-3 rounded-full bg-rose-500/80 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block"></span>
          </div>

          <div className="flex items-center gap-1 text-slate-400">
            <button 
              onClick={() => handleNavigate("https://webook.com/ar", "all")}
              title="الصفحة الرئيسية Webook"
              className="p-1.5 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            >
              <Globe className="w-4 h-4 text-pink-400" />
            </button>
            <button 
              onClick={() => {
                setIsLoadingFrame(true);
                setTimeout(() => setIsLoadingFrame(false), 400);
              }}
              title="تحديث الموقع"
              className="p-1.5 hover:text-white hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${isLoadingFrame ? "animate-spin text-pink-400" : ""}`} />
            </button>
          </div>
        </div>

        {/* Address Bar */}
        <div className="flex-1 flex items-center bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-1.5 gap-2 shadow-inner">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span className="text-[11px] font-mono text-emerald-400 font-bold shrink-0">https://</span>
          <input
            type="text"
            value={currentUrl.replace("https://", "")}
            onChange={(e) => setCurrentUrl(`https://${e.target.value}`)}
            className="flex-1 bg-transparent text-xs font-mono text-slate-200 focus:outline-none truncate"
          />
          
          <button
            onClick={handleCopy}
            className="text-slate-400 hover:text-white p-1"
            title="نسخ الرابط"
          >
            {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          <a
            href={currentUrl}
            target="_blank"
            rel="noopener noreferrer"
            title="فتح في تبويب مستقل"
            className="text-pink-400 hover:text-pink-300 p-1 flex items-center gap-1 text-[10px] font-bold"
          >
            <span>فتح خارجي</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>

        {/* View Mode Controls */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-xl p-1">
            <button
              onClick={() => setViewMode("interactive_mirror")}
              className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                viewMode === "interactive_mirror"
                  ? "bg-pink-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Zap className="w-3 h-3" />
              <span>كتالوج Webook المباشر</span>
            </button>
            <button
              onClick={() => setViewMode("live_iframe")}
              className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                viewMode === "live_iframe"
                  ? "bg-pink-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Tv className="w-3 h-3" />
              <span>إطار المتصفح (Webook Iframe)</span>
            </button>
          </div>

          <button
            onClick={() => setIsFullScreen(!isFullScreen)}
            className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors cursor-pointer"
            title={isFullScreen ? "تصغير" : "ملء الشاشة"}
          >
            {isFullScreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>

      </div>

      {/* Webook Category Pills Strip */}
      <div className="bg-slate-900/50 border-b border-slate-800/80 px-4 py-2.5 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          {categories.map((c) => (
            <button
              key={c.id}
              onClick={() => handleNavigate(c.path, c.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                activeCategory === c.id
                  ? "bg-pink-500/20 text-pink-300 border border-pink-500/40 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <span>{c.name}</span>
            </button>
          ))}
        </div>

        {/* Live Search inside embedded portal */}
        <div className="relative w-full md:w-60">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="بحث فوري في فعاليات Webook..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl py-1.5 pl-8 pr-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-pink-500"
          />
        </div>
      </div>

      {/* Portal Main Body */}
      {viewMode === "live_iframe" ? (
        <div className="relative w-full h-[600px] bg-slate-950">
          {isLoadingFrame && (
            <div className="absolute inset-0 bg-slate-950/90 z-20 flex flex-col items-center justify-center gap-3">
              <RefreshCw className="w-8 h-8 text-pink-500 animate-spin" />
              <p className="text-xs font-bold text-slate-300 font-mono">
                جاري الاتصال وتحميل صفحة webook.com/ar...
              </p>
            </div>
          )}
          <iframe
            src={currentUrl}
            title="Webook Live Portal"
            className="w-full h-full border-0"
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
            loading="lazy"
          />
          {/* Helper overlay bar at bottom */}
          <div className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-slate-900/95 border border-pink-500/40 text-slate-200 px-4 py-2 rounded-2xl shadow-xl backdrop-blur-md flex items-center gap-3 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>بث حي من Webook.com — يمكنك أيضاً استخدام "كتالوج Webook المباشر" للقنص السريع</span>
            <button
              onClick={() => setViewMode("interactive_mirror")}
              className="px-2.5 py-1 rounded-lg bg-pink-600 hover:bg-pink-500 text-white font-bold text-[11px] transition-all cursor-pointer"
            >
              التحويل للكتالوج المباشر
            </button>
          </div>
        </div>
      ) : (
        <div className="p-4 md:p-6 bg-gradient-to-b from-slate-950 via-slate-900/60 to-slate-950 min-h-[500px]">
          
          {/* Header highlight */}
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800/80">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full bg-pink-500/20 text-pink-300 border border-pink-500/40 text-[10px] font-mono font-bold">
                  LIVE INGESTION MATRIX
                </span>
                <span className="text-slate-400 text-xs font-mono">
                  متصل بـ <strong className="text-white">api.webook.com/v2</strong>
                </span>
              </div>
              <h3 className="text-lg font-black text-white mt-1">
                دليل فعاليات Webook الحي والمباشر ({filteredEvents.length} فعالية متاحة للحجز)
              </h3>
              <p className="text-xs text-slate-400">
                انقر على أي فعالية لتعيينها كهدف مباشر للبوت، أو أضفها إلى سلة القنص المتوازي
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-mono bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-800">
                زمن الاستجابة: <strong className="text-emerald-400">14ms</strong>
              </span>
            </div>
          </div>

          {/* Events Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredEvents.map((event) => {
              const isInCart = cartSlugs.includes(event.slug);

              return (
                <div
                  key={event.id}
                  className="rounded-2xl border border-slate-800 bg-slate-900/80 hover:border-pink-500/50 transition-all p-4 flex flex-col justify-between group shadow-lg"
                >
                  <div>
                    {/* Image & Badges */}
                    <div className="relative h-40 w-full rounded-xl overflow-hidden bg-slate-950 mb-3 border border-slate-800">
                      {event.image_url ? (
                        <Image
                          src={event.image_url}
                          alt={event.title_ar}
                          fill
                          referrerPolicy="no-referrer"
                          className="object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-slate-600">
                          <Ticket className="w-8 h-8" />
                        </div>
                      )}

                      <div className="absolute top-2.5 right-2.5 bg-black/75 backdrop-blur-md px-2.5 py-1 rounded-lg text-[10px] font-bold text-pink-300 border border-pink-500/30">
                        {event.genre_slug || "Webook Event"}
                      </div>

                      <div className="absolute bottom-2.5 left-2.5 bg-emerald-950/90 border border-emerald-500/40 text-emerald-300 font-mono text-[10px] font-bold px-2 py-0.5 rounded-md flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                        <span>متاح للحجز</span>
                      </div>
                    </div>

                    {/* Title and details */}
                    <h4 className="text-sm font-black text-white line-clamp-1 group-hover:text-pink-300 transition-colors">
                      {event.title_ar}
                    </h4>
                    <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
                      {event.venue_name} {event.city ? `• ${event.city}` : ""}
                    </p>

                    {/* Price and Sections */}
                    <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-800 text-xs">
                      <span className="text-slate-400 font-mono text-[11px]">ابتداءً من:</span>
                      <span className="font-mono font-black text-pink-400">
                        {formatPrice(event.min_price)}
                      </span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="grid grid-cols-2 gap-2 mt-3 pt-2">
                    {/* Instant Bot Snipe Target */}
                    <button
                      onClick={() => onSelectEventForBot(event)}
                      className="py-2 px-2.5 rounded-xl bg-pink-600 hover:bg-pink-500 text-white font-bold text-[11px] transition-all flex items-center justify-center gap-1 shadow-md shadow-pink-600/20 active:scale-95 cursor-pointer"
                    >
                      <Crosshair className="w-3.5 h-3.5" />
                      <span>قنص بالبوت</span>
                    </button>

                    {/* Add to Sniper Cart */}
                    {onAddToCart && (
                      <button
                        onClick={() => onAddToCart(event)}
                        className={`py-2 px-2.5 rounded-xl text-[11px] font-bold transition-all flex items-center justify-center gap-1 cursor-pointer ${
                          isInCart
                            ? "bg-emerald-600 text-white"
                            : "bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
                        }`}
                      >
                        {isInCart ? (
                          <>
                            <Check className="w-3.5 h-3.5" />
                            <span>في السلة</span>
                          </>
                        ) : (
                          <>
                            <ShoppingCart className="w-3.5 h-3.5 text-pink-400" />
                            <span>+ سلة القنص</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

        </div>
      )}

    </div>
  );
};
