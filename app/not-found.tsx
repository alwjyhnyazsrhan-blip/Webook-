import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#07090e] text-white p-6 text-center">
      <h2 className="text-4xl font-extrabold text-blue-400 mb-3">404</h2>
      <p className="text-lg text-slate-300 mb-6">الصفحة المطلوبة غير متوفرة أو تم نقلها</p>
      <Link
        href="/"
        className="px-6 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-all shadow-lg shadow-blue-500/20"
      >
        العودة إلى المنصة الرئيسية
      </Link>
    </div>
  );
}
