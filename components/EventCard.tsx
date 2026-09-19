"use client";

import React, { useState } from "react";
import Image from "next/image";
import { LiveEvent } from "@/lib/types";
import { formatDate, formatPrice } from "@/lib/utils";
import { MapPin, Calendar, ArrowRight, Copy, Check, Crosshair, ExternalLink, ShoppingCart, Sparkles } from "lucide-react";

interface EventCardProps {
  event: LiveEvent;
  onSelect: (event: LiveEvent) => void;
  onQuickReserve: (event: LiveEvent) => void;
  onAddToCart?: (event: LiveEvent) => void;
  isInCart?: boolean;
}

export const EventCard: React.FC<EventCardProps> = ({
  event,
  onSelect,
  onQuickReserve,
  onAddToCart,
  isInCart = false,
}) => {
  const [copied, setCopied] = useState(false);
  const [imgError, setImgError] = useState(false);

  const copySlug = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(event.slug);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStatusBadge = () => {
    switch (event.hydration_status) {
      case "READY":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-widest uppercase bg-emerald-500 text-white shadow-md flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-white animate-ping"></span>
            LIVE
          </span>
        );
      case "FAILED":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-widest uppercase bg-red-500 text-white shadow-md">
            FAILED
          </span>
        );
      case "HYDRATING":
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-widest uppercase bg-yellow-500 text-black shadow-md animate-pulse">
            SYNCING
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black tracking-widest uppercase bg-blue-600 text-white shadow-md">
            SYNCED
          </span>
        );
    }
  };

  const fallbackPlaceholder = "https://picsum.photos/seed/event-placeholder/800/600";

  return (
    <div
      id={`event-card-${event.id}`}
      className="glass rounded-[2rem] overflow-hidden group hover:border-blue-500/50 hover:shadow-2xl hover:shadow-blue-500/10 transition-all duration-300 flex flex-col justify-between"
    >
      <div>
        {/* Poster Header */}
        <div className="h-48 relative overflow-hidden bg-slate-800/80">
          {event.image_url && !imgError ? (
            <Image
              src={event.image_url}
              alt={event.title_ar}
              fill
              onError={() => setImgError(true)}
              referrerPolicy="no-referrer"
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
          ) : (
            <Image
              src={fallbackPlaceholder}
              alt={event.title_ar}
              fill
              referrerPolicy="no-referrer"
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/30 to-transparent"></div>
          <div className="absolute top-4 right-4 z-10">{getStatusBadge()}</div>
          <div className="absolute top-4 left-4 z-10 flex items-center gap-1.5">
            <span className="px-2 py-0.5 rounded-md text-[10px] font-extrabold tracking-tight bg-slate-900/90 backdrop-blur-md text-emerald-400 border border-emerald-500/30 shadow">
              webook.com
            </span>
            {event.genre_slug && (
              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase bg-slate-900/80 backdrop-blur-md text-blue-400 border border-slate-700/50">
                {event.genre_slug}
              </span>
            )}
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6">
          <div className="mb-3">
            <h3 className="font-bold text-lg leading-snug text-white group-hover:text-blue-400 transition-colors line-clamp-2">
              {event.title_ar}
            </h3>
            <p className="text-xs text-slate-400 font-medium line-clamp-1 mt-1">
              {event.title_en}
            </p>
          </div>

          <div className="space-y-2.5 mb-5">
            <div className="flex items-center justify-between text-xs text-slate-400 font-mono bg-slate-900/70 px-3 py-2 rounded-xl border border-slate-800/80">
              <span className="text-blue-400 font-bold truncate mr-2">
                {event.slug}
              </span>
              <button
                onClick={copySlug}
                title="نسخ معرف الفعالية"
                className="text-slate-400 hover:text-white transition-colors cursor-pointer"
              >
                {copied ? (
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
            </div>

            <div className="flex flex-col gap-1.5 text-xs text-slate-300">
              <div className="flex items-center gap-2">
                <MapPin className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                <span className="truncate">{event.venue_name}</span>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                <span>{formatDate(event.starts_at)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer / Actions */}
      <div className="px-6 pb-6 pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
        <div>
          <div className="text-[10px] text-slate-500 font-semibold uppercase">
            يبدأ من
          </div>
          <div className="text-base font-extrabold text-white">
            {formatPrice(event.min_price)}
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Add to Sniper Cart Button */}
          {onAddToCart && (
            <button
              onClick={() => onAddToCart(event)}
              title={isInCart ? "موجودة في سلة القنص المتوازي" : "إضافة إلى سلة القنص المتوازي"}
              className={`p-2 rounded-xl transition-all flex items-center gap-1 text-xs font-bold cursor-pointer ${
                isInCart
                  ? "bg-pink-600 text-white shadow-md shadow-pink-600/30"
                  : "bg-pink-500/10 text-pink-400 hover:bg-pink-600 hover:text-white border border-pink-500/20"
              }`}
            >
              {isInCart ? (
                <>
                  <Check className="w-3.5 h-3.5" />
                  <span className="text-[11px] font-bold">بالسلة</span>
                </>
              ) : (
                <>
                  <ShoppingCart className="w-3.5 h-3.5" />
                  <span className="text-[11px] font-bold hidden sm:inline">+ السلة</span>
                </>
              )}
            </button>
          )}

          {/* Direct link to Webook.com */}
          <a
            href={`https://webook.com/ar/events/${event.slug}`}
            target="_blank"
            rel="noopener noreferrer"
            title="فتح الفعالية مباشرة على Webook.com"
            onClick={(e) => e.stopPropagation()}
            className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-all flex items-center justify-center cursor-pointer"
          >
            <ExternalLink className="w-4 h-4 text-blue-400" />
          </a>

          <button
            onClick={() => onQuickReserve(event)}
            title="بدء مهمة القنص الفوري (Sniper)"
            className="p-2 rounded-xl bg-blue-500/10 text-blue-400 hover:bg-blue-500 hover:text-white transition-all cursor-pointer"
          >
            <Crosshair className="w-4 h-4" />
          </button>
          
          <button
            onClick={() => onSelect(event)}
            className="px-2.5 py-2 rounded-xl text-xs font-bold text-slate-300 hover:text-white hover:bg-slate-800 border border-slate-700/80 transition-all flex items-center gap-1 cursor-pointer"
          >
            <span>التفاصيل</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </div>
    </div>
  );
};
