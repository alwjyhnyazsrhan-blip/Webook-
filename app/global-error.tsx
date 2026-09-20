"use client";

import { useEffect } from "react";

export default function GlobalError({
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
    <html lang="ar" dir="rtl">
      <body className="bg-[#07090e] text-white flex flex-col items-center justify-center min-h-screen p-6 text-center">
        <h2 className="text-3xl font-bold mb-4">حدث خطأ في النظام</h2>
        <p className="text-slate-400 mb-6">{error?.message || "يرجى إعادة المحاولة"}</p>
        <button
          onClick={() => reset()}
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 rounded-xl font-bold text-white transition-all cursor-pointer shadow-lg shadow-blue-500/20"
        >
          إعادة المحاولة
        </button>
      </body>
    </html>
  );
}
