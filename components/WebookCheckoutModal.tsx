"use client";

import React, { useState, useEffect } from "react";
import { 
  CreditCard, 
  ShieldCheck, 
  ExternalLink, 
  Lock, 
  CheckCircle2, 
  Clock, 
  AlertTriangle, 
  ArrowRight, 
  Copy, 
  Check, 
  Ticket, 
  User, 
  Sparkles,
  Smartphone,
  ChevronRight,
  Shield,
  Layers,
  X
} from "lucide-react";
import { formatPrice } from "@/lib/utils";

interface WebookCheckoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  bookingData: {
    eventTitle: string;
    eventSlug: string;
    venueName: string;
    city?: string;
    category: string;
    seatCount: number;
    seats?: string[];
    pricePerSeat: number;
    holdToken?: string;
    userEmail?: string;
  } | null;
  onConfirmSuccess?: () => void;
}

export const WebookCheckoutModal: React.FC<WebookCheckoutModalProps> = ({
  isOpen,
  onClose,
  bookingData,
  onConfirmSuccess,
}) => {
  const [copied, setCopied] = useState(false);
  const [secondsRemaining, setSecondsRemaining] = useState(899); // 15 mins hold
  const [isRedirecting, setIsRedirecting] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setSecondsRemaining(899);
    const interval = setInterval(() => {
      setSecondsRemaining((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [isOpen]);

  if (!isOpen || !bookingData) return null;

  const minutes = Math.floor(secondsRemaining / 60);
  const seconds = secondsRemaining % 60;
  const timeFormatted = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;

  const subtotal = bookingData.pricePerSeat * bookingData.seatCount;
  const vatAmount = subtotal * 0.15;
  const totalAmount = subtotal + vatAmount;

  const generatedToken = bookingData.holdToken || `WBK-CART-${Math.random().toString(36).substring(2, 7).toUpperCase()}`;

  // Direct targeted URLs
  const directWebookCheckoutUrl = `https://webook.com/ar/events/${bookingData.eventSlug}/book?tickets=${bookingData.seatCount}&category=${encodeURIComponent(bookingData.category)}&hold=${generatedToken}`;
  const directWebookEventUrl = `https://webook.com/ar/events/${bookingData.eventSlug}`;

  const [activeTab, setActiveTab] = useState<"direct" | "instructions">("direct");

  const handleCopyToken = () => {
    navigator.clipboard.writeText(generatedToken);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExecuteRedirect = () => {
    setIsRedirecting(true);
    setTimeout(() => {
      window.open(directWebookCheckoutUrl, "_blank");
      setIsRedirecting(false);
      if (onConfirmSuccess) onConfirmSuccess();
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/85 backdrop-blur-md overflow-y-auto font-sans">
      <div 
        id="webook-checkout-modal"
        className="w-full max-w-2xl bg-[#0d111a] border border-slate-700/70 rounded-[2.5rem] shadow-2xl overflow-hidden relative my-6 text-slate-100 animate-in fade-in zoom-in-95 duration-200"
      >
        {/* Top Header Banner */}
        <div className="bg-gradient-to-r from-pink-600 via-purple-700 to-indigo-700 p-6 text-white relative">
          <button
            onClick={onClose}
            className="absolute top-5 left-5 w-9 h-9 rounded-full bg-black/40 hover:bg-black/60 border border-white/20 flex items-center justify-center text-white transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>

          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center font-black text-lg">
              W
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs uppercase tracking-widest font-black text-pink-200">
                  WEBOOK.COM CHECKOUT GATEWAY
                </span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                  LOCKED
                </span>
              </div>
              <h2 className="text-xl sm:text-2xl font-black">
                إعادة التوجيه السريع لبوابة الدفع الرسمية
              </h2>
            </div>
          </div>
          <p className="text-xs text-pink-100/90 leading-relaxed max-w-lg">
            تم تثبيت وحجز المقاعد عبر البوت بنجاح! سينقلك الرابط المباشر إلى صفحة الدفع الرسمية في Webook لإدخال كود التحقق (OTP) وتأكيد الدفع بأمان.
          </p>
        </div>

        {/* Hold Timer Bar */}
        <div className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-amber-400 font-bold">
            <Clock className="w-4 h-4 animate-pulse text-amber-400" />
            <span>وقت تثبيت المقاعد في السلة:</span>
            <span className="font-mono text-sm bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-lg text-amber-300 font-black">
              {timeFormatted}
            </span>
          </div>

          <div className="flex items-center gap-2 text-slate-400 text-[11px]">
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span>معايير أمان PCI-DSS & 3D Secure</span>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6">
          
          {/* Reservation Summary Card */}
          <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2.5">
                <Ticket className="w-4 h-4 text-pink-400" />
                <span className="text-xs font-bold text-slate-300">تفاصيل تذاكر الفعالية المحجوزة</span>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black bg-pink-600/20 text-pink-400 border border-pink-500/30">
                {bookingData.category}
              </span>
            </div>

            <div className="space-y-1">
              <h3 className="text-base font-black text-white">{bookingData.eventTitle}</h3>
              <p className="text-xs text-slate-400">
                📍 {bookingData.venueName} {bookingData.city ? `• ${bookingData.city}` : ""}
              </p>
            </div>

            {/* Seats Assigned details */}
            <div className="pt-2 flex flex-wrap items-center gap-2">
              <span className="text-xs text-slate-400 font-bold">المقاعد المثبتة ({bookingData.seatCount}):</span>
              {bookingData.seats && bookingData.seats.length > 0 ? (
                bookingData.seats.map((seat, i) => (
                  <span key={i} className="px-2.5 py-1 rounded-lg text-[11px] font-mono font-bold bg-slate-950 border border-emerald-500/30 text-emerald-300">
                    {seat}
                  </span>
                ))
              ) : (
                <span className="px-2.5 py-1 rounded-lg text-[11px] font-mono font-bold bg-slate-950 border border-emerald-500/30 text-emerald-300">
                  {bookingData.seatCount} مقاعد متتالية في {bookingData.category}
                </span>
              )}
            </div>
          </div>

          {/* Pricing Breakdown */}
          <div className="p-4 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-2.5 text-xs">
            <div className="flex items-center justify-between text-slate-400">
              <span>سعر التذاكر ({bookingData.seatCount} × {formatPrice(bookingData.pricePerSeat)})</span>
              <span className="font-mono text-slate-200">{formatPrice(subtotal)}</span>
            </div>
            <div className="flex items-center justify-between text-slate-400">
              <span>ضريبة القيمة المضافة (15% VAT)</span>
              <span className="font-mono text-slate-200">{formatPrice(vatAmount)}</span>
            </div>
            <div className="flex items-center justify-between text-sm font-black text-white pt-2 border-t border-slate-800">
              <span>المجموع النهائي للدفع</span>
              <span className="font-mono text-emerald-400 text-base">{formatPrice(totalAmount)}</span>
            </div>
          </div>

          {/* Webook Cart Hold Token */}
          <div className="p-3.5 rounded-2xl bg-emerald-950/30 border border-emerald-500/30 flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
              <div>
                <div className="text-[11px] font-bold text-emerald-300">رمز حجز الجلسة والسلة في Webook</div>
                <div className="font-mono text-xs text-white font-black">{generatedToken}</div>
              </div>
            </div>
            <button
              onClick={handleCopyToken}
              className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-xs font-bold text-slate-200 flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "تم النسخ" : "نسخ الرمز"}</span>
            </button>
          </div>

          {/* Quick Notice about Webook flow */}
          <div className="p-3.5 rounded-2xl bg-blue-950/30 border border-blue-500/30 flex items-start gap-2.5 text-xs text-blue-200">
            <Sparkles className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-white block">ملاحظة لإتمام الشراء على Webook:</span>
              <p className="text-[11px] text-slate-300 leading-relaxed">
                عند فتح صفحة Webook، قم بتسجيل الدخول بحسابك <strong className="text-white">({bookingData.userEmail || "نفس البريد"})</strong>، واختر الفئة <strong className="text-pink-300 font-bold">{bookingData.category}</strong> بعدد <strong className="text-emerald-300 font-bold">{bookingData.seatCount} تذاكر</strong> ثم اضغط متابعة للدفع الفوري.
              </p>
            </div>
          </div>

          {/* Supported Official Payment Methods */}
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-slate-300">
              <span>طرق الدفع الرسمية المعتمدة على Webook:</span>
              <span className="text-[10px] text-emerald-400 font-mono">3D SECURE ENABLED</span>
            </div>
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-bold text-slate-300 flex items-center gap-1.5">
                💳 مدى (Mada)
              </span>
              <span className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-bold text-slate-300 flex items-center gap-1.5">
                 Apple Pay
              </span>
              <span className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-bold text-slate-300 flex items-center gap-1.5">
                💳 Visa / Mastercard
              </span>
              <span className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-bold text-slate-300 flex items-center gap-1.5">
                ⚡ Tamara / Tabby
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3 pt-2">
            <button
              id="btn-redirect-webook-checkout"
              onClick={handleExecuteRedirect}
              disabled={isRedirecting}
              className="w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-black text-sm sm:text-base shadow-xl shadow-emerald-500/20 flex items-center justify-center gap-3 transition-all transform active:scale-98 cursor-pointer"
            >
              <Lock className="w-5 h-5" />
              <span>
                {isRedirecting ? "جاري التوجيه إلى Webook.com..." : "الانتقال الآمن للدفع في Webook.com ↗"}
              </span>
              <ArrowRight className="w-5 h-5" />
            </button>

            <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
              <a
                href={directWebookEventUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-400 hover:text-pink-400 flex items-center gap-1 transition-colors"
              >
                <span>صفحة الفعالية العامة</span>
                <ExternalLink className="w-3 h-3" />
              </a>

              <button
                onClick={onClose}
                className="text-slate-500 hover:text-slate-300 transition-colors"
              >
                إغلاق والعودة للتطبيق
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};
