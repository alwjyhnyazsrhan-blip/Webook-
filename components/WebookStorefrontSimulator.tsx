"use client";

import React, { useState } from "react";
import Image from "next/image";
import { 
  Search, 
  MapPin, 
  Calendar, 
  Tag, 
  ChevronRight, 
  ExternalLink, 
  Ticket, 
  User, 
  Globe, 
  Flame, 
  SlidersHorizontal,
  CheckCircle2,
  Clock,
  Sparkles,
  Heart,
  Share2,
  CreditCard,
  Lock,
  ArrowRight
} from "lucide-react";
import { LiveEvent } from "@/lib/types";
import { formatPrice, formatDate } from "@/lib/utils";

interface WebookStorefrontSimulatorProps {
  events: LiveEvent[];
  onOpenSeatSelection: (event: LiveEvent) => void;
  onDirectSnipe?: (event: LiveEvent) => void;
  onOpenCheckout?: (data: {
    eventTitle: string;
    eventSlug: string;
    venueName: string;
    city?: string;
    category: string;
    seatCount: number;
    pricePerSeat: number;
  }) => void;
}

export const WebookStorefrontSimulator: React.FC<WebookStorefrontSimulatorProps> = ({
  events,
  onOpenSeatSelection,
  onDirectSnipe,
  onOpenCheckout,
}) => {
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [selectedCity, setSelectedCity] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [userSimulationLoggedIn, setUserSimulationLoggedIn] = useState<boolean>(true);
  const [simulatedAccountEmail] = useState<string>("neyazyyy@gmail.com");
  const [selectedFeaturedIndex, setSelectedFeaturedIndex] = useState<number>(0);
  const [likedEvents, setLikedEvents] = useState<Record<string, boolean>>({});

  const categories = [
    { id: "all", label: "الكل", icon: "✨" },
    { id: "concerts", label: "حفلات وموسيقى", icon: "🎤" },
    { id: "sports", label: "رياضة و EWC", icon: "🏆" },
    { id: "theatre", label: "مسرحيات وعروض", icon: "🎭" },
    { id: "experiences", label: "تجارب وبوليفارد", icon: "🎡" },
    { id: "comedy", label: "ستاند أب كوميدي", icon: "🎙️" },
  ];

  const cities = ["all", "الرياض", "جدة", "العلا", "الدمام", "الخبر", "أبها"];

  const toggleLike = (slug: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setLikedEvents(prev => ({ ...prev, [slug]: !prev[slug] }));
  };

  const filteredEvents = events.filter((ev) => {
    const q = searchTerm.toLowerCase().trim();
    const matchSearch = !q || ev.title_ar.toLowerCase().includes(q) || ev.venue_name.toLowerCase().includes(q) || ev.slug.includes(q);
    const matchCity = selectedCity === "all" || ev.city === selectedCity;
    const matchCat = activeCategory === "all" || 
      (activeCategory === "concerts" && (ev.genre_slug?.includes("concert") || ev.genre_slug?.includes("music") || ev.title_ar.includes("حفل") || ev.title_ar.includes("أنغام") || ev.title_ar.includes("تامر"))) ||
      (activeCategory === "sports" && (ev.genre_slug?.includes("sport") || ev.title_ar.includes("كأس") || ev.title_ar.includes("دوري") || ev.title_ar.includes("سباق") || ev.title_ar.includes("فورمولا"))) ||
      (activeCategory === "theatre" && (ev.genre_slug?.includes("theatre") || ev.genre_slug?.includes("art") || ev.title_ar.includes("مسرحية"))) ||
      (activeCategory === "experiences" && (ev.genre_slug?.includes("experience") || ev.genre_slug?.includes("tour") || ev.title_ar.includes("بوليفارد") || ev.title_ar.includes("عالم"))) ||
      (activeCategory === "comedy" && (ev.genre_slug?.includes("comedy") || ev.title_ar.includes("كوميدي")));
    
    return matchSearch && matchCity && matchCat;
  });

  const heroEvents = events.slice(0, 4);
  const currentHero = heroEvents[selectedFeaturedIndex] || events[0];

  return (
    <div className="w-full bg-[#0b0e14] text-slate-100 rounded-3xl border border-slate-800 shadow-2xl overflow-hidden font-sans">
      {/* Webook Top Official-style Banner */}
      <div className="bg-gradient-to-r from-pink-600 via-purple-700 to-indigo-800 px-4 py-2 text-xs font-bold text-white flex flex-wrap items-center justify-between gap-2 shadow-inner">
        <div className="flex items-center gap-2">
          <span className="bg-black/30 backdrop-blur-md px-2.5 py-0.5 rounded-full text-[10px] tracking-wider uppercase font-black">
            WEBOOK.COM SIMULATOR
          </span>
          <span className="hidden sm:inline">محاكي منصة Webook التفاعلي المباشر — حجز المقاعد، التذاكر، واختيار العروض</span>
        </div>

        <div className="flex items-center gap-3">
          <a
            href="https://webook.com/ar"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 hover:underline text-[11px] bg-white/10 hover:bg-white/20 px-2.5 py-1 rounded-lg transition-all"
          >
            <span>زيارة Webook.com الحقيقي</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* Webook Brand Navigation Bar */}
      <div className="bg-[#10131a] border-b border-slate-800 px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 cursor-pointer">
            <div className="w-9 h-9 rounded-xl bg-pink-600 flex items-center justify-center font-black text-white text-lg shadow-lg shadow-pink-600/40">
              W
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-black tracking-tight text-white flex items-center gap-1">
                webook<span className="text-pink-500">.com</span>
              </span>
              <span className="text-[9px] text-pink-400 font-bold uppercase tracking-widest -mt-1">
                Saudi Super App
              </span>
            </div>
          </div>

          <div className="hidden lg:flex items-center gap-1 text-xs font-bold text-slate-300">
            {categories.map((c) => (
              <button
                key={c.id}
                onClick={() => setActiveCategory(c.id)}
                className={`px-3 py-1.5 rounded-xl transition-all flex items-center gap-1 cursor-pointer ${
                  activeCategory === c.id
                    ? "bg-pink-600/20 text-pink-400 border border-pink-500/30"
                    : "hover:bg-slate-800 hover:text-white"
                }`}
              >
                <span>{c.icon}</span>
                <span>{c.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* User Account State simulation */}
          {userSimulationLoggedIn ? (
            <div className="flex items-center gap-2 bg-slate-900 border border-emerald-500/40 px-3 py-1.5 rounded-xl">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
              <User className="w-3.5 h-3.5 text-emerald-400" />
              <div className="text-right">
                <div className="text-[11px] font-bold text-white">{simulatedAccountEmail}</div>
                <div className="text-[9px] text-emerald-400 font-mono">جلسة Webook موثقة</div>
              </div>
            </div>
          ) : (
            <button 
              onClick={() => setUserSimulationLoggedIn(true)}
              className="px-4 py-1.5 rounded-xl bg-pink-600 hover:bg-pink-500 text-white font-bold text-xs shadow-md shadow-pink-600/30"
            >
              تسجيل الدخول
            </button>
          )}

          <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 px-2.5 py-1.5 rounded-xl text-xs font-bold text-slate-300">
            <Globe className="w-3.5 h-3.5 text-pink-400" />
            <span>العربية (SAR)</span>
          </div>
        </div>
      </div>

      {/* Main Hero Showcase (Webook Banner Style) */}
      {currentHero && (
        <div className="relative w-full h-80 sm:h-96 md:h-[420px] bg-slate-950 overflow-hidden group">
          <Image
            src={currentHero.image_url || "https://picsum.photos/seed/webookbanner/1200/600"}
            alt={currentHero.title_ar || "Webook Event"}
            fill
            className="object-cover opacity-45 group-hover:scale-105 transition-transform duration-700"
            referrerPolicy="no-referrer"
            priority
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#0b0e14] via-[#0b0e14]/60 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#0b0e14] via-[#0b0e14]/40 to-transparent" />

          {/* Hero Content Overlay */}
          <div className="absolute bottom-6 right-6 left-6 flex flex-col md:flex-row md:items-end justify-between gap-6 z-10">
            <div className="max-w-2xl space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-black bg-pink-600 text-white flex items-center gap-1 shadow-lg shadow-pink-600/50">
                  <Flame className="w-3.5 h-3.5 fill-white" />
                  <span>فعالية مميزة ومطلوبة</span>
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-900/80 backdrop-blur-md border border-slate-700 text-slate-200">
                  📍 {currentHero.city || "المملكة العربية السعودية"}
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-900/80 backdrop-blur-md border border-slate-700 text-emerald-300">
                  تبدأ من {formatPrice(currentHero.min_price || 150)}
                </span>
              </div>

              <h2 className="text-2xl sm:text-3xl md:text-4xl font-black text-white tracking-tight leading-tight">
                {currentHero.title_ar}
              </h2>
              <p className="text-xs sm:text-sm text-slate-300 line-clamp-2 max-w-xl">
                {currentHero.description || "احجز تذاكرك الآن وعش تجربة ترفيهية استثنائية ضمن أضخم فعاليات المملكة على Webook."}
              </p>

              <div className="flex items-center gap-4 text-xs font-semibold text-slate-400 pt-1">
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-pink-400" />
                  <span>{formatDate(currentHero.starts_at || currentHero.ends_at)}</span>
                </span>
                <span className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-pink-400" />
                  <span>{currentHero.venue_name}</span>
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-3 shrink-0">
              <button
                onClick={() => onOpenSeatSelection(currentHero)}
                className="px-6 py-3 rounded-2xl bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-white font-black text-sm shadow-xl shadow-pink-600/40 flex items-center gap-2 transform active:scale-95 transition-all cursor-pointer"
              >
                <Ticket className="w-4 h-4" />
                <span>حجز المقاعد والتذاكر الآن</span>
              </button>

              <a
                href={`https://webook.com/ar/events/${currentHero.slug}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-3 rounded-2xl bg-slate-900/90 hover:bg-slate-800 border border-slate-700 text-slate-200 font-bold text-xs flex items-center gap-1.5 backdrop-blur-md transition-all"
              >
                <span>فتح الفعالية في Webook ↗</span>
              </a>
            </div>
          </div>

          {/* Hero Slider Dots */}
          <div className="absolute top-6 left-6 flex items-center gap-1.5 z-10 bg-slate-950/60 backdrop-blur-md p-1.5 rounded-full border border-slate-800">
            {heroEvents.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedFeaturedIndex(idx)}
                className={`h-2 rounded-full transition-all cursor-pointer ${
                  selectedFeaturedIndex === idx ? "w-6 bg-pink-500" : "w-2 bg-slate-600 hover:bg-slate-400"
                }`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Filter and Live Search Bar */}
      <div className="p-6 border-b border-slate-800 bg-[#0d1017]">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Search Box */}
          <div className="relative w-full md:w-96">
            <Search className="w-4 h-4 absolute right-3.5 top-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="ابحث عن فعالية، فنان، مسرحية، أو ملعب..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 focus:border-pink-500 rounded-2xl py-2.5 pr-10 pl-4 text-xs sm:text-sm text-white placeholder-slate-500 focus:outline-none transition-colors"
            />
          </div>

          {/* City Filter Pills */}
          <div className="flex items-center gap-2 overflow-x-auto max-w-full pb-1 md:pb-0">
            <span className="text-xs font-bold text-slate-400 whitespace-nowrap">المدينة:</span>
            {cities.map((city) => (
              <button
                key={city}
                onClick={() => setSelectedCity(city)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer ${
                  selectedCity === city
                    ? "bg-pink-600 text-white shadow-md shadow-pink-600/30"
                    : "bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                {city === "all" ? "جميع المدن" : city}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Events Grid */}
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-black text-white">الفعاليات المتاحة للحجز الفوري</h3>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-pink-500/20 text-pink-400 border border-pink-500/30">
              {filteredEvents.length} فعالية نشطة
            </span>
          </div>

          <div className="text-xs text-slate-400 hidden sm:block">
            اختر أي فعالية لفتح خريطة المقاعد وحجز تذكرتك فوراً
          </div>
        </div>

        {filteredEvents.length === 0 ? (
          <div className="text-center py-16 bg-slate-900/30 rounded-3xl border border-dashed border-slate-800">
            <Search className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <p className="text-sm font-bold text-slate-300">لا توجد فعاليات مطابقة لبحثك</p>
            <p className="text-xs text-slate-500 mt-1">جرب تغيير كلمات البحث أو تصفية المدن والتصنيفات</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {filteredEvents.map((ev) => {
              const isLiked = likedEvents[ev.slug] || false;
              const hasSeats = ev.sections && ev.sections.length > 0;
              const minPrice = ev.min_price || ev.sections?.[0]?.price || 120;

              return (
                <div
                  key={ev.slug}
                  onClick={() => onOpenSeatSelection(ev)}
                  className="group bg-[#121620] hover:bg-[#161b28] border border-slate-800 hover:border-pink-500/50 rounded-2xl overflow-hidden transition-all duration-300 hover:shadow-xl hover:shadow-pink-950/20 flex flex-col cursor-pointer"
                >
                  {/* Card Thumbnail */}
                  <div className="relative w-full h-48 bg-slate-900 overflow-hidden">
                    <Image
                      src={ev.image_url || "https://picsum.photos/seed/webookevent/600/400"}
                      alt={ev.title_ar || "Webook Event"}
                      fill
                      className="object-cover group-hover:scale-105 transition-transform duration-500"
                      referrerPolicy="no-referrer"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#121620] via-transparent to-black/30" />

                    {/* Like button */}
                    <button
                      onClick={(e) => toggleLike(ev.slug, e)}
                      className="absolute top-3 left-3 w-8 h-8 rounded-full bg-black/50 backdrop-blur-md flex items-center justify-center text-white hover:text-pink-500 transition-colors"
                    >
                      <Heart className={`w-4 h-4 ${isLiked ? "fill-pink-500 text-pink-500" : ""}`} />
                    </button>

                    {/* Status / Category tag */}
                    <div className="absolute top-3 right-3 flex flex-col items-end gap-1">
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-black bg-pink-600 text-white shadow">
                        {ev.city || "الرياض"}
                      </span>
                    </div>

                    {/* Price banner */}
                    <div className="absolute bottom-2.5 right-3">
                      <span className="px-2.5 py-1 rounded-lg text-xs font-black bg-slate-950/80 backdrop-blur-md text-emerald-300 border border-slate-700">
                        يبدأ من {formatPrice(minPrice)}
                      </span>
                    </div>
                  </div>

                  {/* Card Body */}
                  <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                    <div className="space-y-1.5">
                      <div className="flex items-center gap-1.5 text-[11px] text-pink-400 font-bold">
                        <Calendar className="w-3 h-3" />
                        <span>{formatDate(ev.starts_at || ev.ends_at)}</span>
                      </div>
                      
                      <h4 className="text-sm font-black text-white group-hover:text-pink-300 transition-colors line-clamp-2 leading-snug">
                        {ev.title_ar}
                      </h4>

                      <p className="text-[11px] text-slate-400 flex items-center gap-1 truncate">
                        <MapPin className="w-3 h-3 text-slate-500 shrink-0" />
                        <span className="truncate">{ev.venue_name}</span>
                      </p>
                    </div>

                    {/* Card Footer Actions */}
                    <div className="pt-2 border-t border-slate-800/80 flex items-center gap-1.5">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenSeatSelection(ev);
                        }}
                        className="flex-1 py-2 px-2.5 rounded-xl bg-pink-600 hover:bg-pink-500 text-white font-bold text-xs transition-all shadow-md shadow-pink-600/20 flex items-center justify-center gap-1 cursor-pointer"
                      >
                        <Ticket className="w-3.5 h-3.5" />
                        <span>حجز التذاكر</span>
                      </button>

                      {onOpenCheckout && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpenCheckout({
                              eventTitle: ev.title_ar,
                              eventSlug: ev.slug,
                              venueName: ev.venue_name,
                              city: ev.city,
                              category: ev.sections?.[0]?.category_name || "General Admission",
                              seatCount: 2,
                              pricePerSeat: minPrice,
                            });
                          }}
                          className="py-2 px-2.5 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 text-xs font-bold transition-all flex items-center justify-center gap-1 cursor-pointer"
                          title="توجيه سريع لبوابة الدفع Webook"
                        >
                          <CreditCard className="w-3.5 h-3.5" />
                          <span className="hidden sm:inline">دفع سريع</span>
                        </button>
                      )}

                      {onDirectSnipe && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDirectSnipe(ev);
                          }}
                          className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-emerald-400 border border-slate-700 text-xs transition-colors cursor-pointer"
                          title="حجز وقنص آلي سريع"
                        >
                          <Sparkles className="w-3.5 h-3.5" />
                        </button>
                      )}

                      <a
                        href={`https://webook.com/ar/events/${ev.slug}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 text-xs transition-colors"
                        title="فتح في webook.com"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Webook Footer Simulator */}
      <div className="bg-[#080a0f] border-t border-slate-800/80 px-6 py-6 text-xs text-slate-500 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 rounded-lg bg-pink-600/30 border border-pink-500/40 flex items-center justify-center text-pink-400 font-black text-xs">
            W
          </div>
          <span>© 2026 Webook.com Entertainment & Events Platform Simulation</span>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-slate-400">
          <span className="flex items-center gap-1">
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span>مدفوعات آمنة 100% (Mada, Visa, Mastercard, Apple Pay)</span>
          </span>
          <span className="flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-pink-400" />
            <span>تذاكر أصلية معتمدة</span>
          </span>
        </div>
      </div>
    </div>
  );
};
