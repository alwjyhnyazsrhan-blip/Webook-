"use client";

import React, { useState, useEffect, useMemo } from "react";
import { LiveEvent, Genre, ReservationTask, IngestionStats, SniperCartItem } from "@/lib/types";
import { initialEvents, initialGenres, initialTasks, dbStore } from "@/lib/data";
import { Header } from "@/components/Header";
import { MetricsGrid } from "@/components/MetricsGrid";
import { FunnelHealth } from "@/components/FunnelHealth";
import { EventCard } from "@/components/EventCard";
import { EventDetailModal } from "@/components/EventDetailModal";
import { TasksTable } from "@/components/TasksTable";
import { NewTaskModal } from "@/components/NewTaskModal";
import { TaskLogsModal } from "@/components/TaskLogsModal";
import { TaxonomyView } from "@/components/TaxonomyView";
import { WorkerConsole } from "@/components/WorkerConsole";
import { WebookSyncBar } from "@/components/WebookSyncBar";
import { WebookBotRunner } from "@/components/WebookBotRunner";
import { WebookHeroBar } from "@/components/WebookHeroBar";
import { SniperCartDrawer } from "@/components/SniperCartDrawer";
import { SniperCartFloatingBar } from "@/components/SniperCartFloatingBar";
import { WebookStorefrontSimulator } from "@/components/WebookStorefrontSimulator";
import { WebookCheckoutModal } from "@/components/WebookCheckoutModal";
import { CloudflareCookieManager } from "@/components/CloudflareCookieManager";
import { Search, Filter, Layers, ListOrdered, Cpu, CheckCircle, Crosshair, Sparkles, MonitorPlay, Cookie } from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"bot" | "simulator" | "discovery" | "tasks" | "taxonomy" | "worker" | "cookies">("simulator");
  const [events, setEvents] = useState<LiveEvent[]>(initialEvents);
  const [genres, setGenres] = useState<Genre[]>(initialGenres);
  const [tasks, setTasks] = useState<ReservationTask[]>(initialTasks);
  const [stats, setStats] = useState<IngestionStats>(dbStore.getStats());

  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedGenre, setSelectedGenre] = useState<string>("all");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");
  const [selectedCity, setSelectedCity] = useState<string>("all");

  const [selectedEvent, setSelectedEvent] = useState<LiveEvent | null>(null);
  const [isNewTaskOpen, setIsNewTaskOpen] = useState<boolean>(false);
  const [inspectingTask, setInspectingTask] = useState<ReservationTask | null>(null);
  const [activeCheckout, setActiveCheckout] = useState<{
    eventTitle: string;
    eventSlug: string;
    venueName: string;
    city?: string;
    category: string;
    seatCount: number;
    seats?: string[];
    pricePerSeat: number;
    holdToken?: string;
  } | null>(null);

  // Sniper Cart state
  const [cartItems, setCartItems] = useState<SniperCartItem[]>([
    {
      id: "cart-1",
      event_slug: "esports-world-cup-ewc-riyadh-2026",
      event_title_ar: "كأس العالم للرياضات الإلكترونية EWC 2026",
      event_title_en: "Esports World Cup (EWC) Riyadh 2026",
      genre_slug: "sports-esports",
      city: "الرياض",
      venue_name: "SEF Arena, بوليفارد سيتي",
      image_url: "https://picsum.photos/seed/ewc2026/800/600",
      selected_section: "VIP Lounge - منصة كبار الشخصيات",
      seat_count: 2,
      price_per_seat: 450,
      sniper_speed: "BURST_15MS",
      status: "READY",
    },
    {
      id: "cart-2",
      event_slug: "tamer-ashour-jeddah-superdome",
      event_title_ar: "حفل الفنان تامر عاشور - جدة سوبر دوم",
      event_title_en: "Tamer Ashour Live in Jeddah",
      genre_slug: "concerts-arabic",
      city: "جدة",
      venue_name: "جدة سوبر دوم (Jeddah Superdome)",
      image_url: "https://picsum.photos/seed/tamerjeddah/800/600",
      selected_section: "Gold Zone A",
      seat_count: 2,
      price_per_seat: 350,
      sniper_speed: "BURST_15MS",
      status: "READY",
    }
  ]);
  const [isCartOpen, setIsCartOpen] = useState<boolean>(false);

  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [lastSyncTime, setLastSyncTime] = useState<string>(new Date().toISOString());
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleAddToCart = (event: LiveEvent) => {
    if (cartItems.some((item) => item.event_slug === event.slug)) {
      showToast(`⚠️ الفعالية "${event.title_ar}" موجودة مسبقاً في سلة القنص!`);
      setIsCartOpen(true);
      return;
    }

    const firstSection = event.sections?.[0];
    const newItem: SniperCartItem = {
      id: `cart-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
      event_slug: event.slug,
      event_title_ar: event.title_ar,
      event_title_en: event.title_en,
      genre_slug: event.genre_slug,
      city: event.city || "الرياض",
      venue_name: event.venue_name,
      image_url: event.image_url,
      selected_section: firstSection ? `${firstSection.name} - ${firstSection.category_name}` : "Best Available",
      seat_count: 2,
      price_per_seat: firstSection?.price || event.min_price || 150,
      sniper_speed: "BURST_15MS",
      status: "READY",
    };

    setCartItems((prev) => [...prev, newItem]);
    showToast(`✓ تم إضافة "${event.title_ar}" إلى سلة القنص المتوازي!`);
  };

  const handleRemoveFromCart = (id: string) => {
    setCartItems((prev) => prev.filter((item) => item.id !== id));
    showToast("✓ تم إزالة الفعالية من سلة القنص");
  };

  const handleUpdateSeatCount = (id: string, count: number) => {
    setCartItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, seat_count: count } : item))
    );
  };

  const handleUpdateSection = (id: string, section: string) => {
    setCartItems((prev) =>
      prev.map((item) => {
        if (item.id === id) {
          const ev = events.find((e) => e.slug === item.event_slug);
          const secObj = ev?.sections?.find((s) => `${s.name} - ${s.category_name}` === section || s.name === section);
          const price = secObj?.price || item.price_per_seat;
          return { ...item, selected_section: section, price_per_seat: price };
        }
        return item;
      })
    );
  };

  const handleClearCart = () => {
    setCartItems([]);
    showToast("✓ تم تفريغ سلة القنص");
  };

  const handleAddPresetBundle = (bundleType: "weekend" | "sports" | "entertainment") => {
    let targets: LiveEvent[] = [];
    if (bundleType === "sports") {
      targets = events.filter((e) => e.genre_slug?.includes("sport") || e.title_ar.includes("كأس") || e.title_ar.includes("دوري") || e.title_ar.includes("سباق")).slice(0, 4);
    } else if (bundleType === "entertainment") {
      targets = events.filter((e) => e.genre_slug?.includes("concert") || e.genre_slug?.includes("theatre") || e.title_ar.includes("حفل") || e.title_ar.includes("مسرحية")).slice(0, 3);
    } else {
      targets = events.slice(0, 3);
    }

    const newItems: SniperCartItem[] = targets.map((ev, i) => {
      const sec = ev.sections?.[0];
      return {
        id: `bundle-${Date.now()}-${i}`,
        event_slug: ev.slug,
        event_title_ar: ev.title_ar,
        event_title_en: ev.title_en,
        genre_slug: ev.genre_slug,
        city: ev.city || "الرياض",
        venue_name: ev.venue_name,
        image_url: ev.image_url,
        selected_section: sec ? `${sec.name} - ${sec.category_name}` : "Best Available",
        seat_count: 2,
        price_per_seat: sec?.price || ev.min_price || 150,
        sniper_speed: "BURST_15MS",
        status: "READY",
      };
    });

    setCartItems(newItems);
    showToast(`✓ تم تحميل حزمة فعاليات (${newItems.length} فعاليات) بنجاح!`);
  };

  // Fetch real data on initial mount and periodic poll
  const refreshFromAPI = async () => {
    try {
      const [eventsRes, tasksRes] = await Promise.all([
        fetch("/api/events"),
        fetch("/api/tasks"),
      ]);
      if (eventsRes.ok) {
        const eventsData = await eventsRes.json();
        if (eventsData.events) {
          setEvents(eventsData.events);
          setStats(eventsData.stats || dbStore.getStats());
        }
      }
      if (tasksRes.ok) {
        const tasksData = await tasksRes.json();
        if (tasksData.tasks) {
          setTasks(tasksData.tasks);
        }
      }
    } catch {
      setEvents([...dbStore.events]);
      setTasks([...dbStore.tasks]);
      setStats(dbStore.getStats());
    }
  };

  useEffect(() => {
    refreshFromAPI();
    const interval = setInterval(() => {
      refreshFromAPI();
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleManualSync = async (targetSlug?: string) => {
    setIsSyncing(true);
    try {
      const res = await fetch("/api/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(targetSlug ? { slug: targetSlug } : {}),
      });
      const data = await res.json();
      if (data.success) {
        if (data.events) {
          setEvents(data.events);
        } else {
          setEvents([...dbStore.events]);
        }
        setStats(data.stats || dbStore.getStats());
        setLastSyncTime(data.synced_at || new Date().toISOString());
        showToast(
          targetSlug
            ? `✓ تم استيراد ومزامنة الفعالية "${targetSlug}" بنجاح!`
            : `✓ تم مزامنة ${data.events_count || dbStore.events.length} فعالية مع Webook.com بنجاح!`
        );
      }
    } catch {
      // Fallback in-memory
      dbStore.syncInventory();
      setEvents([...dbStore.events]);
      setStats(dbStore.getStats());
      setLastSyncTime(new Date().toISOString());
      showToast("✓ اكتملت المزامنة بنجاح!");
    } finally {
      setIsSyncing(false);
    }
  };

  const handleExportJSON = () => {
    const exportData = {
      exported_at: new Date().toISOString(),
      stats,
      events,
      tasks,
      genres,
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `webook_inventory_export_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("✓ Inventory snapshot exported as JSON");
  };

  const handleCreateTask = async (params: {
    event_slug: string;
    event_title: string;
    category?: string;
    zone?: string;
    seat_count: number;
    sniper_mode: boolean;
  }) => {
    try {
      const res = await fetch("/api/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      const data = await res.json();
      if (data.task) {
        setTasks([...dbStore.tasks]);
        setStats(dbStore.getStats());
        showToast(`✓ تم إطلاق مهمة القنص للبوت #${data.task.id} بنجاح!`);
      }
    } catch {
      const newTask = dbStore.addTask(params);
      setTasks([...dbStore.tasks]);
      setStats(dbStore.getStats());
      showToast(`✓ تم إطلاق مهمة القنص للبوت #${newTask.id} بنجاح!`);
    }
  };

  const handleRetryTask = async (taskId: number) => {
    try {
      const res = await fetch(`/api/tasks/${taskId}/retry`, { method: "POST" });
      const data = await res.json();
      if (data.task) {
        setTasks([...dbStore.tasks]);
        showToast(`✓ Task #${taskId} retry queued`);
      }
    } catch {
      dbStore.retryTask(taskId);
      setTasks([...dbStore.tasks]);
      showToast(`✓ Task #${taskId} retry queued`);
    }
  };

  // Filtered Events
  const filteredEvents = useMemo(() => {
    return events.filter((ev) => {
      const q = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !q ||
        ev.title_ar.toLowerCase().includes(q) ||
        ev.title_en.toLowerCase().includes(q) ||
        ev.slug.toLowerCase().includes(q) ||
        ev.venue_name.toLowerCase().includes(q) ||
        (ev.city ? ev.city.toLowerCase().includes(q) : false) ||
        (ev.description ? ev.description.toLowerCase().includes(q) : false);

      const matchesGenre =
        selectedGenre === "all" || ev.genre_slug === selectedGenre;
      
      const matchesCategory =
        selectedCategory === "all" ||
        ev.genre_slug === selectedCategory ||
        (selectedCategory === "today" && ev.starts_at && new Date(ev.starts_at).getDate() === 14) ||
        (selectedCategory === "this-week");

      const matchesStatus =
        selectedStatus === "all" || ev.hydration_status === selectedStatus;
      const matchesCity =
        selectedCity === "all" || ev.city === selectedCity;

      return matchesSearch && matchesGenre && matchesCategory && matchesStatus && matchesCity;
    });
  }, [events, searchQuery, selectedGenre, selectedCategory, selectedStatus, selectedCity]);

  const handleCategorySelect = (catSlug: string) => {
    setSelectedCategory(catSlug);
    if (activeTab !== "discovery" && activeTab !== "bot") {
      setActiveTab("discovery");
    }
  };

  const handleQuickBotTarget = (slug: string) => {
    const target = events.find((e) => e.slug === slug);
    if (target) {
      setActiveTab("bot");
      const element = document.getElementById("webook-bot-runner");
      element?.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <main className="min-h-screen bg-[#07090e] text-slate-100 p-4 md:p-8 selection:bg-pink-500 selection:text-white">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-6 right-6 z-50 glass-card bg-emerald-950/95 border border-emerald-500/60 text-emerald-200 px-5 py-3.5 rounded-2xl shadow-2xl flex items-center gap-3 animate-in fade-in slide-in-from-top-4 duration-300">
          <CheckCircle className="w-5 h-5 text-emerald-400" />
          <span className="text-sm font-semibold">{toastMessage}</span>
        </div>
      )}

      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <Header
          onSync={() => handleManualSync()}
          onExport={handleExportJSON}
          isSyncing={isSyncing}
          lastSyncTime={lastSyncTime}
          cartCount={cartItems.length}
          onOpenCart={() => setIsCartOpen(true)}
        />

        {/* Webook Official Hero Carousel & Categories Bar */}
        <WebookHeroBar
          selectedCategory={selectedCategory}
          onSelectCategory={handleCategorySelect}
          onQuickBotTarget={handleQuickBotTarget}
        />

        {/* Real-time Webook.com Sync & Direct Import Bar */}
        <WebookSyncBar
          onSync={handleManualSync}
          isSyncing={isSyncing}
          totalEvents={events.length}
        />

        {/* Main Webook Sniper Bot Runner */}
        <WebookBotRunner
          events={events}
          onCreateTask={handleCreateTask}
          onSelectEvent={(ev) => setSelectedEvent(ev)}
          onAddToCart={handleAddToCart}
          cartSlugs={cartItems.map((c) => c.event_slug)}
          onOpenCheckout={(data) => setActiveCheckout(data)}
        />

        {/* Key Metrics */}
        <MetricsGrid stats={stats} />

        {/* Funnel Health Diagnostic */}
        <FunnelHealth stats={stats} />

        {/* Tab Navigation */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8">
          <div className="glass p-1.5 rounded-2xl flex items-center gap-1 overflow-x-auto max-w-full">
            <button
              id="tab-simulator"
              onClick={() => setActiveTab("simulator")}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer shrink-0 ${
                activeTab === "simulator"
                  ? "bg-gradient-to-r from-pink-600 via-purple-600 to-indigo-600 text-white shadow-lg shadow-pink-500/30 font-black"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/50"
              }`}
            >
              <MonitorPlay className="w-4 h-4 text-pink-400" />
              <span>محاكي Webook.com الكامل</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] bg-pink-500/20 text-pink-300 font-mono font-bold">
                Live Storefront
              </span>
            </button>

            <button
              id="tab-bot"
              onClick={() => setActiveTab("bot")}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer shrink-0 ${
                activeTab === "bot"
                  ? "bg-gradient-to-r from-pink-600 to-rose-600 text-white shadow-lg shadow-pink-500/20"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/50"
              }`}
            >
              <Crosshair className="w-4 h-4" />
              <span>قناص Webook الآلي</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            </button>

            <button
              id="tab-discovery"
              onClick={() => setActiveTab("discovery")}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer shrink-0 ${
                activeTab === "discovery"
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/50"
              }`}
            >
              <Layers className="w-4 h-4" />
              <span>دليل فعاليات Webook</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-900/60 font-mono">
                {events.length}
              </span>
            </button>

            <button
              id="tab-tasks"
              onClick={() => setActiveTab("tasks")}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer shrink-0 ${
                activeTab === "tasks"
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/50"
              }`}
            >
              <ListOrdered className="w-4 h-4" />
              <span>المهام والحجوزات</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-900/60 font-mono">
                {tasks.length}
              </span>
            </button>

            <button
              id="tab-taxonomy"
              onClick={() => setActiveTab("taxonomy")}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer shrink-0 ${
                activeTab === "taxonomy"
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/50"
              }`}
            >
              <Filter className="w-4 h-4" />
              <span>فئات ومصفوفة Webook</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] bg-slate-900/60 font-mono">
                {genres.length}
              </span>
            </button>

            <button
              id="tab-worker"
              onClick={() => setActiveTab("worker")}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer shrink-0 ${
                activeTab === "worker"
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/50"
              }`}
            >
              <Cpu className="w-4 h-4" />
              <span>سجلات Worker</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            </button>

            <button
              id="tab-cookies"
              onClick={() => setActiveTab("cookies")}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer shrink-0 ${
                activeTab === "cookies"
                  ? "bg-gradient-to-r from-amber-600 via-orange-600 to-pink-600 text-white shadow-lg shadow-orange-500/20 font-black"
                  : "text-amber-300/80 hover:text-amber-200 hover:bg-slate-800/50 border border-amber-500/30"
              }`}
            >
              <Cookie className="w-4 h-4 text-amber-400" />
              <span>كوكيز الحماية والجلسة</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] bg-amber-500/20 text-amber-300 font-mono">
                CF + Session
              </span>
            </button>
          </div>

          {(activeTab === "discovery" || activeTab === "bot") && (
            <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
              {/* Search Bar */}
              <div className="relative flex-1 md:w-72">
                <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
                <input
                  type="text"
                  placeholder="ابحث بالاسم، المدينة، أو الـ Slug..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl py-2 pl-9 pr-4 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-pink-500 transition-all font-sans"
                />
              </div>

              {/* Genre Filter */}
              <select
                value={selectedGenre}
                onChange={(e) => setSelectedGenre(e.target.value)}
                className="bg-slate-900/80 border border-slate-700/80 rounded-xl py-2 px-3 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-pink-500 cursor-pointer"
              >
                <option value="all">كل التصنيفات (All Genres)</option>
                {genres.map((g) => (
                  <option key={g.id} value={g.slug}>
                    {g.name_ar} ({g.name_en})
                  </option>
                ))}
              </select>

              {/* Status Filter */}
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="bg-slate-900/80 border border-slate-700/80 rounded-xl py-2 px-3 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-pink-500 cursor-pointer"
              >
                <option value="all">كل الحالات (All Statuses)</option>
                <option value="READY">READY (جاهز ومتاح)</option>
                <option value="DISCOVERED">DISCOVERED (مكتشف)</option>
                <option value="FAILED">FAILED (فشل)</option>
              </select>
            </div>
          )}
        </div>

        {/* Tab Contents: Simulator, Discovery or Bot List */}
        {activeTab === "simulator" && (
          <div className="space-y-6 animate-in fade-in duration-300">
            <WebookStorefrontSimulator
              events={events}
              onOpenSeatSelection={(ev) => setSelectedEvent(ev)}
              onOpenCheckout={(data) => setActiveCheckout(data)}
              onDirectSnipe={(ev) => {
                handleCreateTask({
                  event_slug: ev.slug,
                  event_title: ev.title_ar,
                  category: ev.sections?.[0]?.category_name || "Best Available",
                  zone: ev.sections?.[0]?.name || "Auto Selected",
                  seat_count: 2,
                  sniper_mode: true,
                });
              }}
            />
          </div>
        )}

        {(activeTab === "discovery" || activeTab === "bot") && (
          <div className="space-y-6">
            
            {/* Quick Category Pills Bar */}
            <div className="flex flex-wrap items-center gap-2 pb-2 overflow-x-auto">
              <button
                onClick={() => setSelectedGenre("all")}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
                  selectedGenre === "all"
                    ? "bg-pink-600 text-white shadow-md shadow-pink-500/20"
                    : "bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-800"
                }`}
              >
                <span>🌟 جميع الفعاليات</span>
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-black/30 font-mono">
                  {events.length}
                </span>
              </button>

              {genres.map((g) => {
                const count = events.filter((e) => e.genre_slug === g.slug).length;
                const isSelected = selectedGenre === g.slug;
                return (
                  <button
                    key={g.id}
                    onClick={() => setSelectedGenre(g.slug)}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
                      isSelected
                        ? "bg-pink-600 text-white shadow-md shadow-pink-500/20"
                        : "bg-slate-900/80 hover:bg-slate-800 text-slate-300 border border-slate-800"
                    }`}
                  >
                    <span>{g.name_ar}</span>
                    <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-black/30 font-mono">
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* City & Results Filter Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/50 p-3 rounded-2xl border border-slate-800/80 text-xs">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-slate-400 font-bold text-[11px] ml-1">المدينة:</span>
                {["all", "الرياض", "جدة", "الدمام", "بريدة", "نجران", "مدريد، إسبانيا", "ميلانو، إيطاليا", "بورتيماو، البرتغال"].map((c) => (
                  <button
                    key={c}
                    onClick={() => setSelectedCity(c)}
                    className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                      selectedCity === c
                        ? "bg-pink-500/20 text-pink-300 border border-pink-500/40 font-bold"
                        : "text-slate-400 hover:text-slate-200 bg-slate-950/60"
                    }`}
                  >
                    {c === "all" ? "الكل" : c}
                  </button>
                ))}
              </div>

              <div className="text-slate-400 font-mono text-[11px]">
                عرض <strong className="text-white">{filteredEvents.length}</strong> من أصل <strong className="text-pink-400">{events.length}</strong> فعالية في Webook
              </div>
            </div>

            {filteredEvents.length === 0 ? (
              <div className="glass rounded-3xl p-12 text-center my-8">
                <div className="text-slate-400 text-base font-semibold mb-2">
                  لم يتم العثور على أي فعاليات مطابقة للبحث
                </div>
                <p className="text-xs text-slate-500 mb-6">
                  جرّب تغيير كلمات البحث أو اختر تصنيفاً آخر، أو استخدم شريط المزامنة في الأعلى لإدخال رابط من Webook.
                </p>
                <button
                  onClick={() => {
                    setSearchQuery("");
                    setSelectedGenre("all");
                    setSelectedCategory("all");
                    setSelectedStatus("all");
                    setSelectedCity("all");
                  }}
                  className="px-5 py-2.5 rounded-xl bg-pink-600 hover:bg-pink-500 text-white text-xs font-bold transition-all cursor-pointer"
                >
                  إعادة تعيين الفلاتر
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredEvents.map((event) => (
                  <EventCard
                    key={event.id}
                    event={event}
                    onSelect={(ev) => setSelectedEvent(ev)}
                    onQuickReserve={(ev) => {
                      handleCreateTask({
                        event_slug: ev.slug,
                        event_title: ev.title_ar,
                        category: ev.sections?.[0]?.category_name || "Best Available",
                        zone: ev.sections?.[0]?.name || "Auto Selected",
                        seat_count: 2,
                        sniper_mode: true,
                      });
                    }}
                    onAddToCart={handleAddToCart}
                    isInCart={cartItems.some((c) => c.event_slug === event.slug)}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "tasks" && (
          <TasksTable
            tasks={tasks}
            onOpenNewTask={() => setIsNewTaskOpen(true)}
            onViewLogs={(task) => setInspectingTask(task)}
            onRetryTask={handleRetryTask}
          />
        )}

        {activeTab === "taxonomy" && (
          <TaxonomyView genres={genres} />
        )}

        {activeTab === "worker" && <WorkerConsole />}

        {activeTab === "cookies" && (
          <CloudflareCookieManager
            embedded={true}
            onSave={() => {
              showToast("✓ تم حفظ وتحديث كوكيز Cloudflare وجلسة Webook بنجاح!");
            }}
          />
        )}
      </div>

      {/* Event Detail & Seat Reservation Modal */}
      {selectedEvent && (
        <EventDetailModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
          onLaunchSnipe={handleCreateTask}
          onOpenCheckout={(data) => setActiveCheckout(data)}
        />
      )}

      {/* Create New Task Modal */}
      <NewTaskModal
        events={events}
        isOpen={isNewTaskOpen}
        onClose={() => setIsNewTaskOpen(false)}
        onSubmit={handleCreateTask}
      />

      {/* Task Logs Modal */}
      {inspectingTask && (
        <TaskLogsModal
          task={inspectingTask}
          onClose={() => setInspectingTask(null)}
        />
      )}

      {/* Floating Sniper Cart Quick Bar */}
      <SniperCartFloatingBar
        cartItems={cartItems}
        onOpenCart={() => setIsCartOpen(true)}
        onClearCart={handleClearCart}
      />

      {/* Sniper Cart Drawer / Parallel Execution Cockpit */}
      <SniperCartDrawer
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
        cartItems={cartItems}
        onRemoveItem={handleRemoveFromCart}
        onUpdateSeatCount={handleUpdateSeatCount}
        onUpdateSection={handleUpdateSection}
        onClearCart={handleClearCart}
        onAddPresetBundle={handleAddPresetBundle}
        allEvents={events}
        onOpenCheckout={(data) => setActiveCheckout(data)}
        onBatchComplete={() => {
          refreshFromAPI();
          showToast("✓ اكتمل تنفيذ قنص سلة الفعاليات بنجاح!");
        }}
      />

      {/* Webook Checkout Official Gateway Modal */}
      <WebookCheckoutModal
        isOpen={!!activeCheckout}
        bookingData={activeCheckout}
        onClose={() => setActiveCheckout(null)}
        onConfirmSuccess={() => {
          showToast("✓ تم فتح بوابة الدفع الرسمية لـ Webook بنجاح");
        }}
      />
    </main>
  );
}

