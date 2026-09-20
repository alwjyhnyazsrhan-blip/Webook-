"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
      <h2 className="text-2xl font-bold text-white mb-2">حدث خطأ أثناء تحميل البيانات</h2>
      <p className="text-slate-400 mb-6">{error?.message || "يرجى إعادة المحاولة"}</p>
      <button
        onClick={() => reset()}
        className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-all shadow-lg shadow-blue-500/20 cursor-pointer"
      >
        إعادة المحاولة
      </button>
    </div>
  );
}
