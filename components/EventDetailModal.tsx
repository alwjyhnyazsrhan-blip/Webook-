"use client";

import React, { useState } from "react";
import Image from "next/image";
import { LiveEvent } from "@/lib/types";
import { formatDate, formatPrice } from "@/lib/utils";
import {
  X,
  MapPin,
  Calendar,
  Layers,
  Crosshair,
  ExternalLink,
  ShieldCheck,
  Check,
  Globe,
  Ticket,
} from "lucide-react";

interface EventDetailModalProps {
  event: LiveEvent | null;
  onClose: () => void;
  onLaunchSnipe: (params: {
    event_slug: string;
    event_title: string;
    category?: string;
    zone?: string;
    seat_count: number;
    sniper_mode: boolean;
  }) => void;
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

export const EventDetailModal: React.FC<EventDetailModalProps> = ({
  event,
  onClose,
  onLaunchSnipe,
  onOpenCheckout,
}) => {
  const [selectedSection, setSelectedSection] = useState<string>(
    event?.sections?.[0]?.category_name || "General Admission"
  );
  const [seatCount, setSeatCount] = useState<number>(2);
  const [sniperMode, setSniperMode] = useState<boolean>(true);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [imgError, setImgError] = useState<boolean>(false);

  if (!event) return null;

  const fallbackPlaceholder = "https://picsum.photos/seed/event-placeholder/800/600";

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onLaunchSnipe({
      event_slug: event.slug,
      event_title: event.title_ar,
      category: selectedSection,
      zone: selectedSection,
      seat_count: seatCount,
      sniper_mode: sniperMode,
    });
    setSubmitted(true);
    setTimeout(() => {
      setSubmitted(false);
      onClose();
    }, 1500);
  };

  const webookUrl = `https://webook.com/ar/events/${event.slug}`;
  const webookBookUrl = `https://webook.com/ar/events/${event.slug}/book`;
  const webookSearchUrl = `https://webook.com/ar?search=${encodeURIComponent(event.title_ar || event.slug || "")}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto">
      <div
        id="event-detail-modal"
        className="glass-card w-full max-w-4xl rounded-[2.5rem] overflow-hidden border border-slate-700/60 shadow-2xl relative my-8"
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 z-20 w-10 h-10 rounded-full bg-slate-900/80 border border-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header Banner */}
        <div className="relative h-64 md:h-72 w-full bg-slate-800">
          {event.image_url && !imgError ? (
            <Image
              src={event.image_url}
              alt={event.title_ar}
              fill
              onError={() => setImgError(true)}
              referrerPolicy="no-referrer"
              className="object-cover"
            />
          ) : (
            <Image
              src={fallbackPlaceholder}
              alt={event.title_ar}
              fill
              referrerPolicy="no-referrer"
              className="object-cover"
            />
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-[#0f172a] via-[#0f172a]/60 to-transparent"></div>
          
          <div className="absolute bottom-6 left-6 right-6 z-10">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="px-3 py-1 rounded-full text-[10px] font-black tracking-widest uppercase bg-emerald-500 text-white flex items-center gap-1.5 shadow">
                <span className="w-2 h-2 rounded-full bg-white animate-pulse"></span>
                Webook Live Verified
              </span>
              <a
                href={webookUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1 rounded-full text-[10px] font-bold bg-blue-600/30 hover:bg-blue-600/50 text-blue-300 border border-blue-500/40 flex items-center gap-1 transition-all"
              >
                <Globe className="w-3 h-3" />
                <span>webook.com/{event.slug}</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
            </div>
            <h2 className="text-2xl md:text-3xl font-extrabold text-white">
              {event.title_ar}
            </h2>
            <p className="text-sm text-slate-300 mt-1">{event.title_en}</p>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 md:p-8 space-y-8">
          {/* Quick Direct Links on Webook */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 p-4 rounded-2xl bg-blue-950/40 border border-blue-500/30">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center shrink-0">
                <Ticket className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-white">الارتباط المباشر مع Webook.com</h4>
                <p className="text-xs text-slate-400">يمكنك حجز التذاكر مباشرة على المنصة الرسمية أو إطلاق مهمة القنص التلقائي</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
              <a
                href={webookUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 sm:flex-none px-4 py-2 rounded-xl text-xs font-bold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-600 flex items-center justify-center gap-1.5 transition-all"
              >
                <span>صفحة الفعالية</span>
                <ExternalLink className="w-3 h-3" />
              </a>
              <a
                href={webookSearchUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 sm:flex-none px-4 py-2 rounded-xl text-xs font-bold text-emerald-300 bg-slate-900 hover:bg-slate-800 border border-emerald-500/30 flex items-center justify-center gap-1.5 transition-all"
                title="البحث المباشر على webook.com"
              >
                <span>🔍 بحث حي Webook</span>
              </a>
              <a
                href={webookBookUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 sm:flex-none px-4 py-2 rounded-xl text-xs font-bold text-white bg-pink-600 hover:bg-pink-500 shadow flex items-center justify-center gap-1.5 transition-all"
              >
                <span>حجز مباشر ↗</span>
              </a>
            </div>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="glass p-4 rounded-2xl">
              <div className="text-xs text-slate-400 flex items-center gap-2 mb-1">
                <MapPin className="w-4 h-4 text-blue-400" />
                <span>الموقع والمدينة</span>
              </div>
              <div className="text-sm font-bold text-white">
                {event.venue_name}
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                {event.venue_address || event.city || "المملكة العربية السعودية"}
              </div>
            </div>

            <div className="glass p-4 rounded-2xl">
              <div className="text-xs text-slate-400 flex items-center gap-2 mb-1">
                <Calendar className="w-4 h-4 text-emerald-400" />
                <span>الموعد والحالة</span>
              </div>
              <div className="text-sm font-bold text-white">
                {formatDate(event.starts_at)}
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                الحالة: <span className="text-emerald-400 font-semibold">{event.status}</span>
              </div>
            </div>

            <div className="glass p-4 rounded-2xl">
              <div className="text-xs text-slate-400 flex items-center gap-2 mb-1">
                <Layers className="w-4 h-4 text-purple-400" />
                <span>نطاق الأسعار</span>
              </div>
              <div className="text-sm font-bold text-white">
                {formatPrice(event.min_price)} - {formatPrice(event.max_price)}
              </div>
              <div className="text-xs text-slate-400 mt-0.5 font-mono">
                Slug: {event.slug}
              </div>
            </div>
          </div>

          {/* Description */}
          {event.description && (
            <div className="glass p-5 rounded-2xl">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                تفاصيل الفعالية
              </h4>
              <p className="text-sm text-slate-300 leading-relaxed">
                {event.description}
              </p>
            </div>
          )}

          {/* Seat Map / Categories Matrix */}
          <div>
            <h4 className="text-base font-bold text-white mb-4 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-blue-400" />
                فئات المقاعد والأسعار المعتمدة (SeatCloud / Webook)
              </span>
              <span className="text-xs font-normal text-slate-400 font-mono">
                Token: {event.chart_token || "auto-derived"}
              </span>
            </h4>

            {event.sections && event.sections.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {event.sections.map((sec) => (
                  <div
                    key={sec.id}
                    onClick={() => setSelectedSection(sec.category_name)}
                    className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                      selectedSection === sec.category_name
                        ? "bg-blue-500/15 border-blue-500 shadow-lg shadow-blue-500/10"
                        : "glass border-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs font-bold text-slate-300">
                        {sec.name}
                      </span>
                      <span className="text-sm font-extrabold text-blue-400">
                        {sec.price} ر.س
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 mb-3">
                      الفئة: {sec.category_name}
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-emerald-400 font-semibold">
                        {sec.available_seats} مقعد متاح
                      </span>
                      <span className="text-slate-500 font-mono text-[10px]">
                        من {sec.total_seats}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="glass p-6 rounded-2xl text-center text-slate-400 text-sm">
                تذاكر الدخول العام وفئات الأسعار متزامنة تلقائياً من Webook.
              </div>
            )}
          </div>

          {/* Quick Sniper Reservation Form */}
          <div className="bg-slate-900/90 border border-blue-500/30 rounded-3xl p-6 relative overflow-hidden">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-xl accent-gradient flex items-center justify-center">
                <Crosshair className="w-4 h-4 text-white" />
              </div>
              <div>
                <h4 className="text-base font-bold text-white">
                  إطلاق مهمة القنص والتثبيت التلقائي (Sniper Lock)
                </h4>
                <p className="text-xs text-slate-400">
                  توجيه طلب الحجز المتزامن عبر محرك المهام مع قفل تذاكر المقاعد تلقائياً.
                </p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">
                    الفئة المستهدفة
                  </label>
                  <select
                    value={selectedSection}
                    onChange={(e) => setSelectedSection(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl py-2.5 px-3 text-xs text-white focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    {event.sections?.map((s) => (
                      <option key={s.id} value={s.category_name}>
                        {s.name} ({s.price} ر.س)
                      </option>
                    )) || (
                      <option value="General Admission">
                        General Admission
                      </option>
                    )}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-300 mb-1.5">
                    عدد المقاعد
                  </label>
                  <div className="flex items-center border border-slate-700 rounded-xl bg-slate-950 px-3 py-1">
                    <button
                      type="button"
                      onClick={() => setSeatCount(Math.max(1, seatCount - 1))}
                      className="text-slate-400 hover:text-white px-2 py-1 text-sm font-bold cursor-pointer"
                    >
                      -
                    </button>
                    <input
                      type="number"
                      value={seatCount}
                      onChange={(e) =>
                        setSeatCount(Math.max(1, parseInt(e.target.value) || 1))
                      }
                      className="w-full bg-transparent text-center text-xs font-bold text-white outline-none"
                      min="1"
                      max="10"
                    />
                    <button
                      type="button"
                      onClick={() => setSeatCount(Math.min(10, seatCount + 1))}
                      className="text-slate-400 hover:text-white px-2 py-1 text-sm font-bold cursor-pointer"
                    >
                      +
                    </button>
                  </div>
                </div>

                <div className="flex flex-col justify-end">
                  <label className="flex items-center gap-2 cursor-pointer pb-2.5">
                    <input
                      type="checkbox"
                      checked={sniperMode}
                      onChange={(e) => setSniperMode(e.target.checked)}
                      className="rounded border-slate-700 text-blue-500 focus:ring-0 w-4 h-4 bg-slate-950"
                    />
                    <span className="text-xs font-bold text-purple-300">
                      تفعيل وضع القنص فائق السرعة
                    </span>
                  </label>
                </div>
              </div>

              <div className="flex justify-between items-center pt-2 border-t border-slate-800">
                <a
                  href={webookUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-slate-400 hover:text-blue-400 flex items-center gap-1 transition-colors"
                >
                  <span>عرض الفعالية على Webook.com</span>
                  <ExternalLink className="w-3 h-3" />
                </a>

                <button
                  type="button"
                  onClick={() => {
                    const sec = event.sections?.find((s) => s.category_name === selectedSection);
                    if (onOpenCheckout) {
                      onOpenCheckout({
                        eventTitle: event.title_ar,
                        eventSlug: event.slug,
                        venueName: event.venue_name,
                        city: event.city,
                        category: selectedSection,
                        seatCount: seatCount,
                        pricePerSeat: sec?.price || event.min_price || 150,
                      });
                    } else {
                      window.open(`https://webook.com/ar/events/${event.slug}/book`, "_blank");
                    }
                  }}
                  className="px-4 py-2.5 rounded-xl text-xs font-bold text-slate-900 bg-emerald-400 hover:bg-emerald-300 shadow-md transition-all flex items-center gap-1.5 cursor-pointer"
                >
                  <span>الدفع والتثبيت السريع Webook ↗</span>
                </button>

                <button
                  type="submit"
                  disabled={submitted}
                  className="accent-gradient hover:opacity-90 active:scale-95 px-6 py-2.5 rounded-xl text-xs font-bold text-white shadow-lg transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {submitted ? (
                    <>
                      <Check className="w-4 h-4 text-white" />
                      <span>تمت جدولة مهمة القنص بنجاح!</span>
                    </>
                  ) : (
                    <>
                      <Crosshair className="w-4 h-4" />
                      <span>بدء تنفيذ القنص اللحظي</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
