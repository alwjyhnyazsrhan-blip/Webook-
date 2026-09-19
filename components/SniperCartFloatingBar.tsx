"use client";

import React from "react";
import { ShoppingCart, Zap, ArrowLeft, Flame, Sparkles } from "lucide-react";
import { SniperCartItem } from "@/lib/types";
import { formatPrice } from "@/lib/utils";

interface SniperCartFloatingBarProps {
  cartItems: SniperCartItem[];
  onOpenCart: () => void;
  onClearCart: () => void;
}

export const SniperCartFloatingBar: React.FC<SniperCartFloatingBarProps> = ({
  cartItems,
  onOpenCart,
}) => {
  if (cartItems.length === 0) return null;

  const totalSeats = cartItems.reduce((acc, item) => acc + item.seat_count, 0);
  const totalCost = cartItems.reduce(
    (acc, item) => acc + item.price_per_seat * item.seat_count,
    0
  );

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 w-full max-w-2xl px-4 animate-in slide-in-from-bottom-6 duration-300">
      <div className="bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 border border-pink-500/40 rounded-3xl p-3 md:p-4 shadow-2xl shadow-pink-500/20 backdrop-blur-xl flex items-center justify-between gap-4">
        
        {/* Left Info */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-pink-600 to-rose-500 flex items-center justify-center text-white shadow-lg shadow-pink-500/30 shrink-0">
            <ShoppingCart className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-black text-white">سلة القنص المتوازي</span>
              <span className="text-[10px] font-mono font-bold bg-pink-500/20 text-pink-300 border border-pink-500/40 px-2 py-0.2 rounded-full">
                {cartItems.length} فعاليات جاهزة
              </span>
            </div>
            <div className="text-[11px] text-slate-400 font-mono mt-0.5">
              {totalSeats} مقاعد • التقديري: <span className="text-pink-400 font-bold">{formatPrice(totalCost)}</span>
            </div>
          </div>
        </div>

        {/* Right Button */}
        <div className="flex items-center gap-2">
          <button
            onClick={onOpenCart}
            className="py-2.5 px-4 rounded-xl bg-gradient-to-r from-pink-600 to-rose-500 hover:from-pink-500 hover:to-rose-400 text-white font-black text-xs shadow-lg shadow-pink-600/30 flex items-center gap-1.5 transition-all active:scale-95 cursor-pointer whitespace-nowrap"
          >
            <Zap className="w-3.5 h-3.5 fill-white" />
            <span>تنفيذ القنص المتوازي ⚡</span>
          </button>
        </div>

      </div>
    </div>
  );
};
