"use client";

import React, { useState } from "react";
import Image from "next/image";
import { 
  Calendar, 
  Sparkles, 
  Trophy, 
  Activity, 
  Plane, 
  Building, 
  Music, 
  Film, 
  Utensils, 
  ShoppingBag, 
  Gavel, 
  ChevronRight, 
  ChevronLeft,
  ExternalLink,
  Flame,
  Zap,
  Ticket
} from "lucide-react";
import { LiveEvent } from "@/lib/types";

interface WebookHeroBarProps {
  onSelectCategory: (categorySlug: string) => void;
  selectedCategory: string;
  onQuickBotTarget: (eventSlug: string) => void;
}

export const WebookHeroBar: React.FC<WebookHeroBarProps> = ({
  onSelectCategory,
  selectedCategory,
  onQuickBotTarget
}) => {
  const [currentSlide, setCurrentSlide] = useState(0);

  const categories = [
    { id: "all", label: "الكل", icon: Sparkles, badge: null },
    { id: "today", label: "اليوم", icon: Calendar, badge: null },
    { id: "experiences", label: "التجارب", icon: Sparkles, badge: null },
    { id: "sports", label: "الرياضة", icon: Trophy, badge: null },
    { id: "football", label: "كرة القدم", icon: Activity, badge: null },
    { id: "this-week", label: "هذا الأسبوع", icon: Calendar, badge: null },
    { id: "flights", label: "طيران", icon: Plane, badge: "جديد" },
    { id: "hotels", label: "فنادق", icon: Building, badge: "جديد" },
    { id: "concerts", label: "الحفلات", icon: Music, badge: null },
    { id: "shows", label: "العروض", icon: Film, badge: null },
    { id: "restaurants", label: "المطاعم", icon: Utensils, badge: null },
    { id: "store", label: "المتجر", icon: ShoppingBag, badge: null },
    { id: "auctions", label: "مزادات", icon: Gavel, badge: "جديد" },
  ];

  const featuredSlides = [
    {
      title: "دوري أبطال آسيا للنخبة: النصر ضد الشمال",
      subtitle: "22 سبتمبر 2026 | استاد الأول بارك، الرياض - الساعة 8:00 مساءً",
      tag: "يبدأ من 50 ر.س",
      eventSlug: "afc-elite-26-27-al-nassr-vs-al-shamal-h6u2r7",
      image: "https://picsum.photos/seed/nassr-shamal-afc/1200/600",
      accent: "from-amber-950 via-slate-900 to-blue-950",
      pill: "دوري أبطال آسيا للنخبة - مباشر",
    },
    {
      title: "مدينة أكوارابيا المائية - القدية (Aquarabia)",
      subtitle: "مفتوح يومياً 10:00 ص إلى 10:00 م | أكبر مدينة مائية بالشرق الأوسط",
      tag: "يبدأ من 185 ر.س",
      eventSlug: "aquarabia-qiddiya-tickets",
      image: "https://picsum.photos/seed/aquarabia-qiddiya/1200/600",
      accent: "from-cyan-950 via-slate-900 to-blue-950",
      pill: "مدينة القدية الترفيهية",
    },
    {
      title: "حفل الفنان عايض - احتفالات اليوم الوطني السعودي",
      subtitle: "23 سبتمبر 2026 | مسرح محمد عبده أرينا - بوليفارد سيتي",
      tag: "يبدأ من 175 ر.س",
      eventSlug: "ayed-in-alriyadh-vocally-tickets-national-day",
      image: "https://picsum.photos/seed/ayed-riyadh-national/1200/600",
      accent: "from-emerald-950 via-slate-900 to-teal-950",
      pill: "احتفالات اليوم الوطني 94",
    },
    {
      title: "دوري روشن: النصر ضد القادسية",
      subtitle: "18 أكتوبر 2026 | استاد الأول بارك، الرياض",
      tag: "يبدأ من 35 ر.س",
      eventSlug: "rsl-26-27-nassr-vs-al-qadsiah-d5g4z7t2",
      image: "https://picsum.photos/seed/nassr-qadsiah/1200/600",
      accent: "from-blue-950 via-slate-900 to-rose-950",
      pill: "دوري روشن السعودي",
    },
    {
      title: "سيكس فلاجز مدينة القدية (Six Flags Qiddiya)",
      subtitle: "مفتوح يومياً 2:00 م إلى 11:30 م | عاصمة الترفيه والرياضة",
      tag: "يبدأ من 195 ر.س",
      eventSlug: "six-flags-new-2026",
      image: "https://picsum.photos/seed/sixflags-qiddiya/1200/600",
      accent: "from-purple-950 via-slate-900 to-pink-950",
      pill: "أضخم ملاهي ترفيهية",
    },
  ];

  const slide = featuredSlides[currentSlide];

  return (
    <div className="mb-8 space-y-6">
      
      {/* Top Webook Banner Notice */}
      <div className="bg-gradient-to-r from-pink-600 via-rose-500 to-pink-600 py-2 px-4 rounded-2xl flex items-center justify-between text-white text-xs font-bold shadow-lg shadow-pink-500/20">
        <div className="flex items-center gap-2 mx-auto">
          <Sparkles className="w-4 h-4 animate-spin text-yellow-200" />
          <span>وظائف للمبدعين فقط، قدم الآن! ✨ احجز أفضل الفعاليات والتجارب والمسرحيات في المملكة العربية السعودية</span>
        </div>
      </div>

      {/* Top Category Chips (matching Webook mobile & desktop app) */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 pt-1 scrollbar-none">
        {categories.map((cat) => {
          const Icon = cat.icon;
          const isSelected = selectedCategory === cat.id;
          return (
            <button
              key={cat.id}
              onClick={() => onSelectCategory(cat.id)}
              className={`flex flex-col items-center justify-center min-w-[76px] py-2.5 px-3 rounded-2xl border transition-all shrink-0 cursor-pointer ${
                isSelected
                  ? "bg-pink-600 border-pink-500 text-white shadow-lg shadow-pink-600/30 scale-105"
                  : "bg-slate-900/80 border-slate-800 text-slate-300 hover:text-white hover:border-slate-700"
              }`}
            >
              <div className="relative mb-1">
                <Icon className={`w-5 h-5 ${isSelected ? "text-white" : "text-pink-400"}`} />
                {cat.badge && (
                  <span className="absolute -top-2 -right-3 text-[9px] font-black bg-emerald-500 text-white px-1 rounded-full scale-90">
                    {cat.badge}
                  </span>
                )}
              </div>
              <span className="text-[11px] font-bold tracking-tight whitespace-nowrap">{cat.label}</span>
            </button>
          );
        })}
      </div>

      {/* Hero Banner Carousel (matching Webook screenshot) */}
      <div className="relative h-64 md:h-80 rounded-[2.5rem] overflow-hidden border border-slate-800 shadow-2xl group">
        <Image
          src={slide.image}
          alt={slide.title}
          fill
          priority
          referrerPolicy="no-referrer"
          className="object-cover group-hover:scale-105 transition-transform duration-700"
        />
        <div className={`absolute inset-0 bg-gradient-to-t ${slide.accent} opacity-90`}></div>
        <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/60 to-transparent"></div>

        {/* Content */}
        <div className="absolute inset-0 p-6 md:p-10 flex flex-col justify-between z-10">
          <div className="flex items-center justify-between">
            <span className="bg-pink-500/20 backdrop-blur-md text-pink-300 border border-pink-500/40 text-xs font-black px-3.5 py-1 rounded-full flex items-center gap-1.5 shadow">
              <Flame className="w-3.5 h-3.5 text-pink-400 fill-pink-400" />
              <span>{slide.pill}</span>
            </span>

            {/* Slider controls */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentSlide((prev) => (prev === 0 ? featuredSlides.length - 1 : prev - 1))}
                className="w-8 h-8 rounded-full bg-slate-900/80 backdrop-blur-md border border-slate-700 text-white flex items-center justify-center hover:bg-pink-600 transition-colors cursor-pointer"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => setCurrentSlide((prev) => (prev === featuredSlides.length - 1 ? 0 : prev + 1))}
                className="w-8 h-8 rounded-full bg-slate-900/80 backdrop-blur-md border border-slate-700 text-white flex items-center justify-center hover:bg-pink-600 transition-colors cursor-pointer"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div>
            <div className="text-xs font-mono font-bold text-pink-400 mb-1">
              {slide.subtitle}
            </div>
            <h2 className="text-2xl md:text-4xl font-black text-white leading-tight max-w-2xl mb-4">
              {slide.title}
            </h2>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => onQuickBotTarget(slide.eventSlug)}
                className="px-5 py-3 rounded-2xl bg-gradient-to-r from-pink-600 to-rose-500 hover:from-pink-500 hover:to-rose-400 text-white font-black text-xs shadow-xl shadow-pink-600/30 flex items-center gap-2 transition-all cursor-pointer active:scale-95"
              >
                <Zap className="w-4 h-4 fill-white" />
                <span>تشغيل البوت على هذه الفعالية ⚡</span>
              </button>

              <a
                href={`https://webook.com/ar/events/${slide.eventSlug}`}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-3 rounded-2xl bg-slate-900/80 hover:bg-slate-800 text-white font-bold text-xs border border-slate-700 transition-all flex items-center gap-1.5 backdrop-blur-md"
              >
                <span>فتح الفعالية على webook.com</span>
                <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
              </a>
            </div>
          </div>

          {/* Dots */}
          <div className="flex items-center gap-1.5">
            {featuredSlides.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentSlide(idx)}
                className={`h-1.5 rounded-full transition-all cursor-pointer ${
                  currentSlide === idx ? "w-6 bg-pink-500" : "w-2 bg-slate-600 hover:bg-slate-400"
                }`}
              />
            ))}
          </div>
        </div>
      </div>

    </div>
  );
};
