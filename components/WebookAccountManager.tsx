"use client";

import React, { useState, useEffect } from "react";
import {
  Users,
  UserPlus,
  Edit3,
  Trash2,
  CheckCircle2,
  XCircle,
  Clock,
  Shield,
  Key,
  Smartphone,
  Server,
  RefreshCw,
  Copy,
  Check,
  Eye,
  EyeOff,
  Upload,
  Download,
  Search,
  Lock,
  Unlock,
  AlertTriangle,
  Flame,
  ArrowRight,
} from "lucide-react";
import { WebookAccount, AccountStatus } from "@/lib/types";

interface WebookAccountManagerProps {
  onAccountSelectForBot?: (account: WebookAccount) => void;
  onAccountsUpdated?: () => void;
  compact?: boolean;
}

export const WebookAccountManager: React.FC<WebookAccountManagerProps> = ({
  onAccountSelectForBot,
  onAccountsUpdated,
  compact = false,
}) => {
  const [accounts, setAccounts] = useState<WebookAccount[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("ALL");

  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [isBulkImportOpen, setIsBulkImportOpen] = useState<boolean>(false);
  const [editingAccount, setEditingAccount] = useState<WebookAccount | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // Form states for Add / Edit
  const [formEmail, setFormEmail] = useState<string>("");
  const [formName, setFormName] = useState<string>("");
  const [formPhone, setFormPhone] = useState<string>("");
  const [formPassword, setFormPassword] = useState<string>("");
  const [formToken, setFormToken] = useState<string>("");
  const [formProxy, setFormProxy] = useState<string>("");
  const [formStatus, setFormStatus] = useState<AccountStatus>("ACTIVE");
  const [formMaxSeats, setFormMaxSeats] = useState<number>(4);
  const [formNotes, setFormNotes] = useState<string>("");

  // Bulk import state
  const [bulkInput, setBulkInput] = useState<string>("");

  // UI helpers
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [showTokens, setShowTokens] = useState<{ [key: string]: boolean }>({});
  const [testingId, setTestingId] = useState<string | null>(null);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const showFeedback = (text: string, type: "success" | "error" = "success") => {
    setFeedbackMsg({ type, text });
    setTimeout(() => setFeedbackMsg(null), 3500);
  };

  // Fetch accounts from API
  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/accounts");
      const data = await res.json();
      if (data.accounts) {
        setAccounts(data.accounts);
      }
    } catch (err) {
      console.error("Error fetching accounts:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const handleCopy = (text: string, fieldKey: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(fieldKey);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const toggleShowToken = (id: string) => {
    setShowTokens((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Open Edit Modal
  const handleOpenEdit = (acc: WebookAccount) => {
    setEditingAccount(acc);
    setFormEmail(acc.email);
    setFormName(acc.name || "");
    setFormPhone(acc.phone || "");
    setFormPassword(acc.password || "");
    setFormToken(acc.token);
    setFormProxy(acc.proxy || "");
    setFormStatus(acc.status);
    setFormMaxSeats(acc.max_seats || 4);
    setFormNotes(acc.notes || "");
  };

  // Submit Edit
  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingAccount) return;

    try {
      const res = await fetch("/api/accounts", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: editingAccount.id,
          email: formEmail.trim(),
          name: formName.trim(),
          phone: formPhone.trim(),
          password: formPassword,
          token: formToken.trim(),
          proxy: formProxy.trim(),
          status: formStatus,
          max_seats: Number(formMaxSeats),
          notes: formNotes.trim(),
        }),
      });
      const data = await res.json();
      if (data.success) {
        setAccounts(data.accounts);
        setEditingAccount(null);
        showFeedback(`✓ تم تحديث بيانات الحساب (${formEmail}) بنجاح!`);
        onAccountsUpdated?.();
      } else {
        showFeedback(data.error || "فشل التحديث", "error");
      }
    } catch {
      showFeedback("حدث خطأ أثناء حفظ التعديلات", "error");
    }
  };

  // Submit Add Account
  const handleSaveAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formEmail.trim()) {
      showFeedback("البريد الإلكتروني مطلوب", "error");
      return;
    }

    try {
      const res = await fetch("/api/accounts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: formEmail.trim(),
          name: formName.trim() || formEmail.split("@")[0],
          phone: formPhone.trim() || "+966 50 000 0000",
          password: formPassword || "••••••••••••",
          token: formToken.trim() || `wbk_live_${Math.random().toString(36).substring(2, 16)}`,
          proxy: formProxy.trim() || "185.193.64.10:8080",
          status: formStatus,
          max_seats: Number(formMaxSeats),
          notes: formNotes.trim(),
        }),
      });
      const data = await res.json();
      if (data.success) {
        setAccounts(data.accounts);
        setIsAddModalOpen(false);
        // Reset form
        setFormEmail("");
        setFormName("");
        setFormPhone("");
        setFormPassword("");
        setFormToken("");
        setFormProxy("");
        setFormNotes("");
        showFeedback("✓ تم إضافة حساب Webook الجديد بنجاح!");
        onAccountsUpdated?.();
      } else {
        showFeedback(data.error || "فشل إضافة الحساب", "error");
      }
    } catch {
      showFeedback("حدث خطأ أثناء الاتصال بالخادم", "error");
    }
  };

  // Submit Bulk Import
  const handleBulkImport = async (e: React.FormEvent) => {
    e.preventDefault();
    const lines = bulkInput.split("\n").map((l) => l.trim()).filter(Boolean);
    if (lines.length === 0) {
      showFeedback("يرجى إدخال الحسابات أولاً", "error");
      return;
    }

    const parsedAccounts = lines.map((line, idx) => {
      // Supports formats:
      // email:pass
      // email:pass:token
      // email:pass:token:proxy
      // email:pass:proxy
      const parts = line.split(":");
      const email = parts[0] || `user_${Date.now()}_${idx}@webook.com`;
      const password = parts[1] || "••••••••••••";
      let token = `wbk_live_${Math.random().toString(36).substring(2, 16)}`;
      let proxy = "185.193.64.10:8080";

      if (parts.length >= 4) {
        token = parts[2];
        proxy = `${parts[3]}:${parts[4] || "8080"}`;
      } else if (parts.length === 3) {
        if (parts[2].includes(".")) {
          proxy = parts[2];
        } else {
          token = parts[2];
        }
      }

      return {
        email,
        password,
        token,
        proxy,
        name: email.split("@")[0],
        status: "ACTIVE" as AccountStatus,
        max_seats: 4,
      };
    });

    try {
      const res = await fetch("/api/accounts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accounts: parsedAccounts }),
      });
      const data = await res.json();
      if (data.success) {
        setAccounts(data.accounts);
        setIsBulkImportOpen(false);
        setBulkInput("");
        showFeedback(`✓ تم استيراد ${parsedAccounts.length} حساب Webook بنجاح!`);
        onAccountsUpdated?.();
      } else {
        showFeedback(data.error || "فشل الاستيراد", "error");
      }
    } catch {
      showFeedback("خطأ أثناء معالجة الاستيراد الجماعي", "error");
    }
  };

  // Delete Account
  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`/api/accounts?id=${id}`, { method: "DELETE" });
      const data = await res.json();
      if (data.success) {
        setAccounts(data.accounts);
        setDeleteConfirmId(null);
        showFeedback("✓ تم حذف الحساب بنجاح");
        onAccountsUpdated?.();
      } else {
        showFeedback(data.error || "فشل الحذف", "error");
      }
    } catch {
      showFeedback("خطأ أثناء حذف الحساب", "error");
    }
  };

  // Test Account Login / Ping Webook Session
  const handleTestAccount = async (acc: WebookAccount) => {
    setTestingId(acc.id);
    try {
      const res = await fetch("/api/accounts/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: acc.id }),
      });
      const data = await res.json();
      if (data.success) {
        showFeedback(`✓ الجلسة نشطة وموثقة لـ (${acc.email}) - زمن الاستجابة ${data.latency_ms}ms`);
        fetchAccounts();
      } else {
        showFeedback(`⚠️ ${data.message}`, "error");
      }
    } catch {
      showFeedback("فشل فحص الاتصال بالخادم", "error");
    } finally {
      setTestingId(null);
    }
  };

  // Toggle quick status (e.g. ACTIVE <-> DISABLED)
  const handleToggleStatus = async (acc: WebookAccount) => {
    const newStatus: AccountStatus = acc.status === "DISABLED" ? "ACTIVE" : "DISABLED";
    try {
      const res = await fetch("/api/accounts", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: acc.id, status: newStatus }),
      });
      const data = await res.json();
      if (data.success) {
        setAccounts(data.accounts);
        showFeedback(`✓ تم تغيير حالة الحساب إلى (${newStatus})`);
        onAccountsUpdated?.();
      }
    } catch {
      showFeedback("فشل تغيير الحالة", "error");
    }
  };

  // Export Accounts
  const handleExportAccounts = () => {
    const dataStr = JSON.stringify(accounts, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `webook_accounts_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showFeedback("✓ تم تصدير بيانات الحسابات بصيغة JSON");
  };

  // Filter accounts
  const filteredAccounts = accounts.filter((acc) => {
    const matchesSearch =
      !searchQuery ||
      acc.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      acc.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      acc.phone?.includes(searchQuery) ||
      acc.proxy?.includes(searchQuery);

    const matchesStatus =
      statusFilter === "ALL" || acc.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const totalSeatsHolding = accounts.reduce(
    (sum, a) => sum + (a.allocated_seats?.length || 0),
    0
  );

  return (
    <div className="space-y-6">
      {/* Toast Feedback */}
      {feedbackMsg && (
        <div
          className={`fixed top-6 left-6 z-50 px-5 py-3.5 rounded-2xl shadow-2xl flex items-center gap-3 animate-in fade-in slide-in-from-top-4 duration-300 font-bold text-xs ${
            feedbackMsg.type === "success"
              ? "bg-emerald-950 border border-emerald-500/70 text-emerald-200"
              : "bg-rose-950 border border-rose-500/70 text-rose-200"
          }`}
        >
          {feedbackMsg.type === "success" ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          )}
          <span>{feedbackMsg.text}</span>
        </div>
      )}

      {/* Top Banner & Stats */}
      <div className="bg-[#0b0f19] border border-slate-800 rounded-3xl p-5 md:p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-pink-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-pink-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-pink-500/20">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl md:text-2xl font-black text-white tracking-tight">
                  إدارة وتعديل حسابات Webook.com
                </h2>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-pink-500/20 text-pink-300 border border-pink-500/30">
                  Account Manager
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                تعديل، إضافة، ومزامنة حسابات الحجز والقنص التلقائي لتجاوز الطوابير وتثبيت المقاعد بدون أي فارق عن موقع webook.com الرسمي
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2.5">
            <button
              onClick={() => setIsAddModalOpen(true)}
              className="px-4 py-2 rounded-xl bg-pink-600 hover:bg-pink-500 text-white text-xs font-bold transition-all shadow-md shadow-pink-600/30 flex items-center gap-2 cursor-pointer"
            >
              <UserPlus className="w-4 h-4" />
              <span>إضافة حساب جديد</span>
            </button>

            <button
              onClick={() => setIsBulkImportOpen(true)}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 transition-all flex items-center gap-2 cursor-pointer"
            >
              <Upload className="w-4 h-4 text-pink-400" />
              <span>استيراد جماعي</span>
            </button>

            <button
              onClick={handleExportAccounts}
              className="px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-medium border border-slate-800 transition-all flex items-center gap-1.5 cursor-pointer"
              title="تصدير الحسابات"
            >
              <Download className="w-4 h-4" />
              <span>تصدير JSON</span>
            </button>

            <button
              onClick={fetchAccounts}
              disabled={loading}
              className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-800 transition-all cursor-pointer"
              title="تحديث القائمة"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-pink-400" : ""}`} />
            </button>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-3">
            <div className="text-[11px] text-slate-400 font-bold mb-1">إجمالي الحسابات</div>
            <div className="text-2xl font-mono font-black text-white">{accounts.length}</div>
          </div>

          <div className="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-3">
            <div className="text-[11px] text-emerald-400 font-bold mb-1 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>نشطة ومتصلة</span>
            </div>
            <div className="text-2xl font-mono font-black text-emerald-400">
              {accounts.filter((a) => a.status === "ACTIVE" || a.status === "LOGGED_IN").length}
            </div>
          </div>

          <div className="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-3">
            <div className="text-[11px] text-pink-400 font-bold mb-1 flex items-center gap-1">
              <Lock className="w-3 h-3 text-pink-400" />
              <span>حسابات محجوز لها مقاعد</span>
            </div>
            <div className="text-2xl font-mono font-black text-pink-400">
              {accounts.filter((a) => a.status === "LOCKED" || (a.allocated_seats && a.allocated_seats.length > 0)).length}
            </div>
          </div>

          <div className="bg-slate-950/60 border border-slate-800/80 rounded-2xl p-3">
            <div className="text-[11px] text-amber-400 font-bold mb-1 flex items-center gap-1">
              <Flame className="w-3 h-3 text-amber-400" />
              <span>إجمالي المقاعد المحجوزة</span>
            </div>
            <div className="text-2xl font-mono font-black text-amber-400">
              {totalSeatsHolding} مقعد
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-[#0b0f19] p-3 rounded-2xl border border-slate-800">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="ابحث بالبريد، الاسم، الهاتف، أو البروكسي..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 pl-9 pr-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-pink-500 transition-all font-sans"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          <span className="text-[11px] text-slate-400 font-bold ml-1 shrink-0">الحالة:</span>
          {(["ALL", "ACTIVE", "LOGGED_IN", "LOCKED", "DISABLED"] as const).map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-3 py-1 rounded-xl text-xs font-bold transition-colors cursor-pointer whitespace-nowrap ${
                statusFilter === st
                  ? "bg-pink-600 text-white"
                  : "bg-slate-950/80 text-slate-400 hover:text-white border border-slate-800"
              }`}
            >
              {st === "ALL" && "الكل"}
              {st === "ACTIVE" && "نشط"}
              {st === "LOGGED_IN" && "متصل"}
              {st === "LOCKED" && "محجوز له"}
              {st === "DISABLED" && "معطل"}
            </button>
          ))}
        </div>
      </div>

      {/* Accounts List */}
      {loading ? (
        <div className="bg-[#0b0f19] border border-slate-800 rounded-3xl p-12 text-center text-slate-400">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-pink-500 mb-3" />
          <div className="text-sm font-bold">جاري تحميل حسابات Webook...</div>
        </div>
      ) : filteredAccounts.length === 0 ? (
        <div className="bg-[#0b0f19] border border-slate-800 rounded-3xl p-12 text-center text-slate-400">
          <Users className="w-10 h-10 mx-auto text-slate-600 mb-3" />
          <div className="text-base font-bold text-white mb-1">لا توجد حسابات مطابقة</div>
          <p className="text-xs text-slate-500 mb-4">
            قم بإضافة حساب جديد أو جرب تغيير معايير البحث والفلترة.
          </p>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-pink-600 hover:bg-pink-500 text-white text-xs font-bold transition-all cursor-pointer"
          >
            + إضافة حساب Webook
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredAccounts.map((acc) => {
            const isHolding = acc.allocated_seats && acc.allocated_seats.length > 0;
            const isTokenVisible = showTokens[acc.id];

            return (
              <div
                key={acc.id}
                className="bg-[#0b0f19] border border-slate-800/90 hover:border-pink-500/50 rounded-2xl p-4 transition-all shadow-md flex flex-col justify-between gap-3 group relative overflow-hidden"
              >
                {/* Top header: Email + Status badge */}
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2.5">
                      <div className="w-9 h-9 rounded-xl bg-slate-900 border border-slate-700/80 flex items-center justify-center font-bold text-sm text-pink-400 shrink-0">
                        {acc.name ? acc.name.charAt(0) : acc.email.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-black text-white truncate max-w-[190px] sm:max-w-[240px]">
                            {acc.name || acc.email}
                          </h4>
                          {acc.status === "ACTIVE" && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                              نشط
                            </span>
                          )}
                          {acc.status === "LOGGED_IN" && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/15 text-blue-400 border border-blue-500/30">
                              متصل Live
                            </span>
                          )}
                          {acc.status === "LOCKED" && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-pink-500/20 text-pink-300 border border-pink-500/40">
                              محجوز له ✅
                            </span>
                          )}
                          {acc.status === "DISABLED" && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-400 border border-slate-700">
                              معطل
                            </span>
                          )}
                        </div>
                        <div className="text-xs font-mono text-slate-400 truncate max-w-[240px]">
                          {acc.email}
                        </div>
                      </div>
                    </div>

                    {/* Quick status switch */}
                    <button
                      onClick={() => handleToggleStatus(acc)}
                      className={`p-1.5 rounded-lg border transition-colors cursor-pointer ${
                        acc.status === "DISABLED"
                          ? "bg-slate-800 border-slate-700 text-slate-400 hover:text-white"
                          : "bg-emerald-950/60 border-emerald-500/30 text-emerald-400 hover:bg-emerald-900/60"
                      }`}
                      title={acc.status === "DISABLED" ? "تفعيل الحساب" : "تعطيل الحساب"}
                    >
                      {acc.status === "DISABLED" ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                    </button>
                  </div>

                  {/* Account Details & Badges */}
                  <div className="grid grid-cols-2 gap-2 text-[11px] mb-3">
                    <div className="bg-slate-950/80 p-2 rounded-xl border border-slate-800/80 flex items-center gap-1.5 text-slate-300">
                      <Smartphone className="w-3 h-3 text-slate-500 shrink-0" />
                      <span className="truncate font-mono">{acc.phone || "+966 50 *** ****"}</span>
                    </div>

                    <div className="bg-slate-950/80 p-2 rounded-xl border border-slate-800/80 flex items-center gap-1.5 text-slate-300">
                      <Server className="w-3 h-3 text-slate-500 shrink-0" />
                      <span className="truncate font-mono">{acc.proxy || "Direct IP"}</span>
                    </div>
                  </div>

                  {/* Token & Secret Bar */}
                  <div className="bg-slate-950/90 rounded-xl p-2 border border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-300 mb-2">
                    <div className="flex items-center gap-1.5 truncate max-w-[240px]">
                      <Key className="w-3 h-3 text-pink-400 shrink-0" />
                      <span className="text-slate-500 font-bold">Token:</span>
                      <span className="truncate">
                        {isTokenVisible ? acc.token : "••••••••••••••••••••••••"}
                      </span>
                    </div>

                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        onClick={() => toggleShowToken(acc.id)}
                        className="p-1 text-slate-400 hover:text-white cursor-pointer"
                        title={isTokenVisible ? "إخفاء" : "إظهار"}
                      >
                        {isTokenVisible ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                      </button>
                      <button
                        onClick={() => handleCopy(acc.token, `token-${acc.id}`)}
                        className="p-1 text-slate-400 hover:text-pink-400 cursor-pointer"
                        title="نسخ التوكن"
                      >
                        {copiedField === `token-${acc.id}` ? (
                          <Check className="w-3 h-3 text-emerald-400" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* If Holding Seats (Hold Token & Allocated Seats) */}
                  {isHolding && (
                    <div className="bg-pink-950/20 border border-pink-500/30 rounded-xl p-2.5 mb-2 space-y-1.5">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-pink-300 flex items-center gap-1">
                          <Lock className="w-3 h-3 text-pink-400" />
                          <span>المقاعد المحجوزة ({acc.allocated_seats?.length}):</span>
                        </span>
                        <span className="font-mono text-[10px] text-emerald-400 font-bold bg-emerald-950/80 px-2 py-0.5 rounded-md border border-emerald-500/30">
                          Hold: 15:00 min
                        </span>
                      </div>
                      <div className="font-mono text-xs font-bold text-emerald-300 bg-slate-950/80 p-1.5 rounded-lg border border-slate-800 truncate">
                        {acc.allocated_seats?.join(", ")}
                      </div>
                      {acc.hold_token && (
                        <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                          <span className="truncate max-w-[200px]">HoldToken: {acc.hold_token}</span>
                          <button
                            onClick={() => handleCopy(acc.hold_token || "", `hold-${acc.id}`)}
                            className="text-pink-400 hover:text-white flex items-center gap-1 cursor-pointer"
                          >
                            <Copy className="w-2.5 h-2.5" />
                            <span>نسخ الرمز</span>
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {acc.notes && (
                    <div className="text-[11px] text-slate-400 bg-slate-900/50 p-2 rounded-xl border border-slate-800/60 mb-2">
                      💡 {acc.notes}
                    </div>
                  )}
                </div>

                {/* Footer Controls: Edit, Test, Delete */}
                <div className="pt-2.5 border-t border-slate-800/80 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    {/* Test button */}
                    <button
                      onClick={() => handleTestAccount(acc)}
                      disabled={testingId === acc.id}
                      className="px-2.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white text-[11px] font-bold border border-slate-800 transition-colors flex items-center gap-1 cursor-pointer"
                      title="فحص الاتصال وتأكيد الجلسة في Webook"
                    >
                      <RefreshCw className={`w-3 h-3 ${testingId === acc.id ? "animate-spin text-pink-400" : "text-emerald-400"}`} />
                      <span>{testingId === acc.id ? "فحص..." : "فحص الجلسة"}</span>
                    </button>

                    {/* Edit button */}
                    <button
                      onClick={() => handleOpenEdit(acc)}
                      className="px-3 py-1.5 rounded-lg bg-pink-600/15 hover:bg-pink-600 text-pink-300 hover:text-white text-[11px] font-bold border border-pink-500/30 hover:border-pink-600 transition-all flex items-center gap-1.5 cursor-pointer"
                    >
                      <Edit3 className="w-3 h-3" />
                      <span>تعديل الحساب</span>
                    </button>
                  </div>

                  <div className="flex items-center gap-1">
                    {deleteConfirmId === acc.id ? (
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleDelete(acc.id)}
                          className="px-2 py-1 rounded bg-rose-600 hover:bg-rose-500 text-white text-[10px] font-bold cursor-pointer"
                        >
                          تأكيد الحذف
                        </button>
                        <button
                          onClick={() => setDeleteConfirmId(null)}
                          className="px-1.5 py-1 rounded bg-slate-800 text-slate-300 text-[10px] cursor-pointer"
                        >
                          إلغاء
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setDeleteConfirmId(acc.id)}
                        className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-950/30 transition-colors cursor-pointer"
                        title="حذف الحساب"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* EDIT ACCOUNT MODAL */}
      {editingAccount && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-[#0d121f] border border-slate-700 rounded-3xl p-6 max-w-lg w-full shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Edit3 className="w-5 h-5 text-pink-400" />
                <h3 className="text-base font-bold text-white">تعديل بيانات حساب Webook</h3>
              </div>
              <button
                onClick={() => setEditingAccount(null)}
                className="text-slate-400 hover:text-white p-1"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 font-bold mb-1">البريد الإلكتروني المسجل في Webook *</label>
                <input
                  type="email"
                  required
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-bold mb-1">اسم صاحب الحساب</label>
                  <input
                    type="text"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-bold mb-1">رقم الجوال السعودي</label>
                  <input
                    type="text"
                    value={formPhone}
                    onChange={(e) => setFormPhone(e.target.value)}
                    placeholder="+966 5x xxx xxxx"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-bold mb-1">كلمة المرور (اختياري)</label>
                <input
                  type="text"
                  value={formPassword}
                  onChange={(e) => setFormPassword(e.target.value)}
                  placeholder="اتركها فارغة إن لم ترغب بتغييرها"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-bold mb-1">رمز الجلسة / Bearer Token أو Cookie</label>
                <textarea
                  rows={2}
                  value={formToken}
                  onChange={(e) => setFormToken(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500 font-mono text-[11px]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-bold mb-1">بروكسي مخصص (IP:Port:User:Pass)</label>
                  <input
                    type="text"
                    value={formProxy}
                    onChange={(e) => setFormProxy(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-bold mb-1">أقصى عدد مقاعد للحساب</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={formMaxSeats}
                    onChange={(e) => setFormMaxSeats(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-bold mb-1">حالة الحساب</label>
                <select
                  value={formStatus}
                  onChange={(e) => setFormStatus(e.target.value as AccountStatus)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500"
                >
                  <option value="ACTIVE">نشط (ACTIVE) - جاهز للقنص</option>
                  <option value="LOGGED_IN">متصل (LOGGED_IN) - جلسة حية</option>
                  <option value="LOCKED">محجوز (LOCKED) - لديه حجز معلق</option>
                  <option value="EXPIRED">منتهي الجلسة (EXPIRED)</option>
                  <option value="DISABLED">معطل (DISABLED) - مستثنى من البوت</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-bold mb-1">ملاحظات إضافية</label>
                <input
                  type="text"
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  placeholder="مثال: حساب مخصص لحفلات اليوم الوطني"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500"
                />
              </div>

              <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setEditingAccount(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold cursor-pointer"
                >
                  إلغاء
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-pink-600 hover:bg-pink-500 text-white font-bold cursor-pointer shadow-md shadow-pink-600/30"
                >
                  حفظ التعديلات
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ADD ACCOUNT MODAL */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-[#0d121f] border border-slate-700 rounded-3xl p-6 max-w-lg w-full shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-pink-400" />
                <h3 className="text-base font-bold text-white">إضافة حساب Webook جديد</h3>
              </div>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="text-slate-400 hover:text-white p-1"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveAdd} className="space-y-3.5 text-xs">
              <div>
                <label className="block text-slate-300 font-bold mb-1">البريد الإلكتروني المسجل في Webook *</label>
                <input
                  type="email"
                  required
                  placeholder="username@domain.com"
                  value={formEmail}
                  onChange={(e) => setFormEmail(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-bold mb-1">الاسم</label>
                  <input
                    type="text"
                    placeholder="محمد السعد"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-bold mb-1">رقم الجوال السعودي</label>
                  <input
                    type="text"
                    placeholder="+966 50 123 4567"
                    value={formPhone}
                    onChange={(e) => setFormPhone(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-bold mb-1">كلمة المرور</label>
                <input
                  type="password"
                  placeholder="كلمة مرور حساب Webook"
                  value={formPassword}
                  onChange={(e) => setFormPassword(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-bold mb-1">رمز التوكن / الجلسة (اختياري - يتم توليده آلياً إن ترك فارغاً)</label>
                <input
                  type="text"
                  placeholder="wbk_live_..."
                  value={formToken}
                  onChange={(e) => setFormToken(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500 font-mono text-[11px]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-bold mb-1">بروكسي سعودي (اختياري)</label>
                  <input
                    type="text"
                    placeholder="185.193.64.10:8080"
                    value={formProxy}
                    onChange={(e) => setFormProxy(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500 font-mono"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-bold mb-1">أقصى عدد مقاعد</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={formMaxSeats}
                    onChange={(e) => setFormMaxSeats(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-bold mb-1">ملاحظات الحساب</label>
                <input
                  type="text"
                  placeholder="حساب احتياطي لقنص مباريات النصر"
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl py-2 px-3 text-white focus:outline-none focus:border-pink-500"
                />
              </div>

              <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold cursor-pointer"
                >
                  إلغاء
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-pink-600 hover:bg-pink-500 text-white font-bold cursor-pointer shadow-md shadow-pink-600/30"
                >
                  إضافة الحساب الآن
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* BULK IMPORT MODAL */}
      {isBulkImportOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-[#0d121f] border border-slate-700 rounded-3xl p-6 max-w-lg w-full shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Upload className="w-5 h-5 text-pink-400" />
                <h3 className="text-base font-bold text-white">استيراد جماعي لحسابات Webook</h3>
              </div>
              <button
                onClick={() => setIsBulkImportOpen(false)}
                className="text-slate-400 hover:text-white p-1"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleBulkImport} className="space-y-3 text-xs">
              <p className="text-slate-400 text-xs leading-relaxed">
                أدخل سطراً لكل حساب بالصيغ التالية:
                <br />
                <span className="font-mono text-pink-400 text-[11px]">email:password</span> أو{" "}
                <span className="font-mono text-pink-400 text-[11px]">email:password:token</span> أو{" "}
                <span className="font-mono text-pink-400 text-[11px]">email:password:token:proxy_ip:port</span>
              </p>

              <textarea
                rows={7}
                required
                value={bulkInput}
                onChange={(e) => setBulkInput(e.target.value)}
                placeholder={`sniper1@hotmail.com:Pass12345:wbk_token1:185.193.64.10:8080\nsniper2@gmail.com:Pass998877\nsniper3@yahoo.com:Saudi2026`}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white focus:outline-none focus:border-pink-500 font-mono text-[11px] leading-5"
              />

              <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setIsBulkImportOpen(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold cursor-pointer"
                >
                  إلغاء
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-pink-600 hover:bg-pink-500 text-white font-bold cursor-pointer shadow-md shadow-pink-600/30"
                >
                  بدء الاستيراد
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
