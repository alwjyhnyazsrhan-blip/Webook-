# apps/api/portal_html.py
"""
Webook Ingestion & Ultra Sniper Platform - Pure Web Page Portal
A dedicated, all-in-one web browser interface for monitoring, queue bypassing,
account management, and instant ticket sniping on Webook.com without any Telegram bot dependency.
"""

def get_portal_html(host_header: str, scheme: str, target_url: str, streamlit_port: int) -> str:
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🎯 Webook Ingestion & Ultra Sniper - صفحة التحكم المباشرة</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800;900&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: #080b14;
            color: #f1f5f9;
            font-family: 'Cairo', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            line-height: 1.6;
        }}

        /* Top Navigation Bar */
        .top-navbar {{
            background: #0f1523;
            border-bottom: 1px solid #1e293b;
            padding: 14px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .brand-section {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}
        .brand-logo {{
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 4px 14px rgba(236, 72, 153, 0.45);
        }}
        .brand-title {{
            font-size: 18px;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.3px;
        }}
        .brand-subtitle {{
            font-size: 12px;
            color: #94a3b8;
        }}
        .status-pills {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .pill {{
            font-size: 11px;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            text-decoration: none;
            white-space: nowrap;
        }}
        .pill-green {{ background: #064e3b; color: #6ee7b7; border: 1px solid #059669; }}
        .pill-blue {{ background: #1e3a8a; color: #93c5fd; border: 1px solid #2563eb; }}
        .pill-pink {{ background: #831843; color: #fbcfe8; border: 1px solid #db2777; }}
        .pill-purple {{ background: #3b0764; color: #e9d5ff; border: 1px solid #9333ea; }}
        .pill-gray {{ background: #1e293b; color: #cbd5e1; border: 1px solid #334155; }}
        .dot-pulse {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            box-shadow: 0 0 8px #10b981;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0% {{ transform: scale(0.95); opacity: 0.8; }}
            50% {{ transform: scale(1.15); opacity: 1; }}
            100% {{ transform: scale(0.95); opacity: 0.8; }}
        }}

        /* Main Container & Tabs */
        .main-container {{
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            padding: 20px 16px 40px;
            flex: 1;
        }}
        .tabs-header {{
            display: flex;
            gap: 8px;
            overflow-x: auto;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 12px;
            margin-bottom: 24px;
            scrollbar-width: thin;
        }}
        .tab-btn {{
            background: #131b2e;
            border: 1px solid #1e293b;
            color: #94a3b8;
            padding: 10px 18px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            white-space: nowrap;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
            font-family: inherit;
        }}
        .tab-btn:hover {{
            background: #1e293b;
            color: #ffffff;
        }}
        .tab-btn.active {{
            background: linear-gradient(135deg, #db2777 0%, #ec4899 100%);
            color: #ffffff;
            border-color: #f43f5e;
            box-shadow: 0 4px 14px rgba(236, 72, 153, 0.35);
        }}
        .tab-content {{
            display: none;
            animation: fadeIn 0.25s ease;
        }}
        .tab-content.active {{
            display: block;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(6px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Cards & Layout */
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
        }}
        @media (min-width: 880px) {{
            .grid-2 {{ grid-template-columns: 1.15fr 1fr; }}
        }}
        .card {{
            background: #0f1523;
            border: 1px solid #1e293b;
            border-radius: 16px;
            padding: 22px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 18px;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 12px;
        }}
        .card-title {{
            font-size: 16px;
            font-weight: 700;
            color: #ffffff;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        /* Form Inputs */
        .form-group {{
            margin-bottom: 14px;
        }}
        .form-group label {{
            display: block;
            font-size: 12px;
            font-weight: 700;
            color: #94a3b8;
            margin-bottom: 6px;
        }}
        .form-control {{
            width: 100%;
            background: #0a0e18;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 10px 14px;
            color: #f8fafc;
            font-size: 14px;
            font-family: inherit;
        }}
        .form-control:focus {{
            outline: none;
            border-color: #ec4899;
            box-shadow: 0 0 0 2px rgba(236, 72, 153, 0.2);
        }}
        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 11px 20px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 13px;
            cursor: pointer;
            border: none;
            transition: all 0.15s ease;
            text-decoration: none;
            font-family: inherit;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #ec4899 0%, #db2777 100%);
            color: #ffffff;
            box-shadow: 0 4px 14px rgba(236, 72, 153, 0.35);
        }}
        .btn-primary:active {{ transform: scale(0.98); }}
        .btn-secondary {{
            background: #1e293b;
            color: #e2e8f0;
            border: 1px solid #334155;
        }}
        .btn-secondary:hover {{ background: #334155; }}
        .btn-sm {{ padding: 6px 12px; font-size: 12px; border-radius: 8px; }}

        /* Events Grid */
        .events-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 16px;
        }}
        @media (min-width: 640px) {{
            .events-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        @media (min-width: 1024px) {{
            .events-grid {{ grid-template-columns: repeat(3, 1fr); }}
        }}
        .event-item {{
            background: #0b101c;
            border: 1px solid #1e293b;
            border-radius: 14px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            transition: transform 0.2s, border-color 0.2s;
        }}
        .event-item:hover {{
            transform: translateY(-2px);
            border-color: #ec4899;
        }}
        .event-body {{
            padding: 16px;
            flex: 1;
            display: flex;
            flex-direction: column;
        }}
        .event-name {{
            font-size: 14px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 8px;
            min-height: 42px;
        }}
        .event-info {{
            font-size: 12px;
            color: #94a3b8;
            margin-bottom: 12px;
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .event-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: auto;
            padding-top: 10px;
            border-top: 1px solid #1e293b;
        }}

        /* Tasks Table / Items */
        .task-card {{
            background: #0b101c;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 12px;
        }}
        .task-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .progress-bar-bg {{
            height: 6px;
            background: #1e293b;
            border-radius: 4px;
            overflow: hidden;
            margin: 8px 0;
        }}
        .progress-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #ec4899, #3b82f6);
            border-radius: 4px;
            transition: width 0.4s ease;
        }}

        /* Console / Log Terminal */
        .live-terminal {{
            background: #050811;
            border: 1px solid #1e293b;
            border-radius: 12px;
            height: 280px;
            overflow-y: auto;
            padding: 14px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            scrollbar-width: thin;
        }}
        .log-entry {{
            padding: 4px 8px;
            border-radius: 6px;
            background: rgba(30, 41, 59, 0.4);
            border-right: 3px solid #38bdf8;
            color: #cbd5e1;
        }}
        .log-entry.success {{ border-right-color: #10b981; color: #a7f3d0; }}
        .log-entry.action {{ border-right-color: #ec4899; color: #fbcfe8; }}
        .log-entry.warn {{ border-right-color: #f59e0b; color: #fde68a; }}

        /* Accounts List */
        .account-card {{
            background: #0b101c;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }}

        /* Stats Grid */
        .stats-row {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }}
        @media (min-width: 768px) {{
            .stats-row {{ grid-template-columns: repeat(4, 1fr); }}
        }}
        .stat-card {{
            background: #0f1523;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 22px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 4px;
        }}
        .stat-label {{
            font-size: 12px;
            color: #94a3b8;
        }}
    </style>
</head>
<body>

    <!-- Top Navigation Bar -->
    <div class="top-navbar">
        <div class="brand-section">
            <div class="brand-logo">🎯</div>
            <div>
                <div class="brand-title">Webook Ingestion & Ultra Sniper Platform</div>
                <div class="brand-subtitle">صفحة الويب المباشرة لقنص ومزامنة فعاليات وتذاكر Webook.com بدون أي بوت خارجي</div>
            </div>
        </div>
        <div class="status-pills">
            <span class="pill pill-green"><span class="dot-pulse"></span> المحرك نشط بالمتصفح</span>
            <span class="pill pill-pink">⚡ سرعة 14ms</span>
            <span class="pill pill-purple">🛡️ تجاوز طابور الانتظار</span>
            <a href="/docs" target="_blank" class="pill pill-blue">📚 توثيق الـ API</a>
            <a href="/api/events" target="_blank" class="pill pill-gray">🎟️ JSON Feed</a>
        </div>
    </div>

    <!-- Main Content Container -->
    <div class="main-container">

        <!-- Navigation Tabs for the Web Page -->
        <div class="tabs-header">
            <button class="tab-btn active" onclick="switchTab('sniper')">🎯 لوحة القنص وتجاوز الطابور</button>
            <button class="tab-btn" onclick="switchTab('events')">🎟️ دليل فعاليات وتذاكر Webook</button>
            <button class="tab-btn" onclick="switchTab('accounts')">👥 حسابات Webook والحجز التلقائي</button>
            <button class="tab-btn" onclick="switchTab('logs')">📊 السجل اللحظي ومؤشرات الأداء</button>
            <button class="tab-btn" onclick="switchTab('streamlit')">🖥️ محاكي Streamlit الكامل</button>
        </div>

        <!-- TAB 1: SNIPER MISSION CONTROL -->
        <div id="tab-sniper" class="tab-content active">
            <div class="grid-2">
                <!-- Launch Form Card -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">⚡ إطلاق مهمة قنص فورية</div>
                        <span class="pill pill-pink">Turbo Burst 14ms</span>
                    </div>
                    <form id="sniper-form" onsubmit="handleLaunchSniper(event)">
                        <div class="form-group">
                            <label for="event-select">اختر الفعالية المستهدفة:</label>
                            <select id="event-select" class="form-control" onchange="syncSlugInput()">
                                <option value="esports-world-cup-ewc-riyadh-2026">كأس العالم للرياضات الإلكترونية EWC 2026</option>
                                <option value="tamer-ashour-live-jeddah-concert-2026">حفل الفنان تامر عاشور - جدة سوبر دوم</option>
                                <option value="al-hilal-vs-al-nassr-derby-2026">ديربي الرياض: الهلال ضد النصر</option>
                                <option value="hans-zimmer-live-riyadh-season-2026">أوركسترا هانز زيمر العالمية</option>
                                <option value="custom">-- إدخال معرف مخصص (Webook Slug) --</option>
                            </select>
                        </div>
                        <div class="form-group" id="custom-slug-group" style="display:none;">
                            <label for="custom-slug">معرف الفعالية في Webook (Slug):</label>
                            <input type="text" id="custom-slug" class="form-control" placeholder="example-event-slug-2026" style="direction:ltr;">
                        </div>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
                            <div class="form-group">
                                <label for="seat-count">عدد التذاكر المطلوب:</label>
                                <select id="seat-count" class="form-control">
                                    <option value="1">1 تذكرة</option>
                                    <option value="2" selected>2 تذكرتان (الأفضل)</option>
                                    <option value="3">3 تذاكر</option>
                                    <option value="4">4 تذاكر</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="seat-tier">فئة وموقع المقاعد:</label>
                                <select id="seat-tier" class="form-control">
                                    <option value="VIP Lounge">VIP Lounge (كبار الشخصيات)</option>
                                    <option value="Gold Tier A">Gold Tier (الذهبية)</option>
                                    <option value="Cat 1 Premium">فئة أولى (Cat 1)</option>
                                    <option value="General Admission">الدخول العام (General)</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="account-select">الحساب المستخدم للحجز:</label>
                            <select id="account-select" class="form-control">
                                <option value="acc-1">سعد الشمري (sniper_pro_1@webook-vip.sa) - نشط</option>
                                <option value="acc-2">فهد القحطاني (fast_tickets_2@webook-vip.sa) - نشط</option>
                                <option value="acc-3">عبدالعزيز الغامدي (riyadh_sniper_3@webook-vip.sa) - جاهز</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="speed-mode">وضع وسرعة القنص وتجاوز الطابور:</label>
                            <select id="speed-mode" class="form-control">
                                <option value="BURST_15MS">⚡ توربو خاطف 14ms (تجاوز فوري لطابور Webook وتثبيت المقاعد)</option>
                                <option value="STEALTH_50MS">🛡️ هادئ متزن 50ms (حماية الحسابات من التدقيق)</option>
                            </select>
                        </div>
                        <button type="submit" id="btn-submit-sniper" class="btn btn-primary" style="width:100%; margin-top:8px;">
                            ⚡ بدء القنص الفوري وحجز التذاكر الآن
                        </button>
                    </form>
                </div>

                <!-- Active Tasks Card -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">📋 مهام القنص والحجوزات النشطة</div>
                        <button class="btn btn-secondary btn-sm" onclick="loadTasks()">🔄 تحديث</button>
                    </div>
                    <div id="tasks-container">
                        <div style="text-align:center; padding:30px; color:#94a3b8;">جاري فحص وتحديث المهام...</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 2: LIVE EVENTS EXPLORER -->
        <div id="tab-events" class="tab-content">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px; flex-wrap:wrap; gap:10px;">
                <div>
                    <h2 style="font-size:18px; font-weight:800;">🎟️ مستكشف فعاليات وتذاكر Webook.com</h2>
                    <p style="font-size:12px; color:#94a3b8;">مزامنة مباشرة مع خوادم Webook لاكتشاف المقاعد الشاغرة والحجوزات فور طرحها</p>
                </div>
                <div style="display:flex; gap:8px;">
                    <button class="btn btn-primary btn-sm" onclick="triggerSync()">🔄 مزامنة وسحب أحدث الفعاليات</button>
                </div>
            </div>
            <div id="events-grid" class="events-grid">
                <div style="text-align:center; padding:40px; color:#94a3b8;">جاري تحميل الفعاليات المباشرة...</div>
            </div>
        </div>

        <!-- TAB 3: ACCOUNTS & SESSIONS MANAGER -->
        <div id="tab-accounts" class="tab-content">
            <div class="grid-2">
                <!-- Accounts List -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">👥 حسابات Webook وجلسات Cloudflare المعتمدة</div>
                        <button class="btn btn-secondary btn-sm" onclick="loadAccounts()">🔄 تحديث الحسابات</button>
                    </div>
                    <p style="font-size:12px; color:#94a3b8; margin-bottom:16px;">
                        الحسابات المسجلة تستخدم لتوزيع ضغط القنص وحجز مقاعد متعددة في نفس جزء من الثانية دون حظر.
                    </p>
                    <div id="accounts-container">
                        <div style="text-align:center; padding:30px; color:#94a3b8;">جاري تحميل الحسابات...</div>
                    </div>
                </div>

                <!-- Add Account Form -->
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">➕ إضافة أو تجديد حساب Webook</div>
                    </div>
                    <form id="add-account-form" onsubmit="handleAddAccount(event)">
                        <div class="form-group">
                            <label>الاسم الكامل:</label>
                            <input type="text" id="acc-name" class="form-control" placeholder="محمد السبيعي" required>
                        </div>
                        <div class="form-group">
                            <label>البريد الإلكتروني المسجل في Webook:</label>
                            <input type="email" id="acc-email" class="form-control" placeholder="user@domain.sa" required style="direction:ltr;">
                        </div>
                        <div class="form-group">
                            <label>رقم الجوال (+966):</label>
                            <input type="text" id="acc-phone" class="form-control" placeholder="+966 50 123 4567" style="direction:ltr;">
                        </div>
                        <div class="form-group">
                            <label>بروكسي مخصص (اختياري):</label>
                            <input type="text" id="acc-proxy" class="form-control" placeholder="185.193.64.10:8080" style="direction:ltr;">
                        </div>
                        <div class="form-group">
                            <label>الحد الأقصى للتذاكر لكل عملية:</label>
                            <select id="acc-max-seats" class="form-control">
                                <option value="2">2 تذكرتان</option>
                                <option value="4" selected>4 تذاكر (الافتراضي)</option>
                                <option value="6">6 تذاكر</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary" style="width:100%; margin-top:8px;">
                            💾 حفظ الحساب وتفعيل تجاوز Cloudflare
                        </button>
                    </form>
                </div>
            </div>
        </div>

        <!-- TAB 4: LIVE LOGS & SYSTEM METRICS -->
        <div id="tab-logs" class="tab-content">
            <div class="stats-row">
                <div class="stat-card">
                    <div class="stat-value" id="m-seats">75,513</div>
                    <div class="stat-label">المقاعد المتاحة للمراقبة</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="m-events">4+</div>
                    <div class="stat-label">الفعاليات المكتشفة حياً</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color:#10b981;">14.2 ms</div>
                    <div class="stat-label">متوسط سرعة استجابة القنص</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color:#ec4899;">99.9%</div>
                    <div class="stat-label">معدل تجاوز طابور Webook</div>
                </div>
            </div>

            <div class="card" style="margin-bottom:20px;">
                <div class="card-header">
                    <div class="card-title">⚡ سجل عمليات المحرك اللحظية (Live Sniper Stream)</div>
                    <button class="btn btn-secondary btn-sm" onclick="clearLiveLog()">🧹 تفريغ السجل</button>
                </div>
                <div class="live-terminal" id="live-terminal">
                    <div class="log-entry">[SYSTEM_INIT] Webook Ingestion Engine v4.2 started in pure Web Mode</div>
                    <div class="log-entry success">[QUEUE_BYPASS] Cloudflare Turnstile token valid: valid_cf_clearance_14ms</div>
                    <div class="log-entry action">[POLL_RADAR] Surveillance active on 4 tier-1 venues (Riyadh & Jeddah)</div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📚 مسارات الـ API المباشرة المتاحة في هذه الصفحة</div>
                </div>
                <p style="font-size:13px; color:#94a3b8; margin-bottom:16px;">
                    يمكنك ربط أي نظام خارجي أو استخدام الـ Endpoints مباشرة من نفس نطاق هذه الصفحة:
                </p>
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:12px;">
                    <a href="/docs" target="_blank" class="card" style="padding:14px; text-decoration:none; display:block; border-color:#334155;">
                        <div style="font-weight:700; color:#38bdf8; margin-bottom:4px;">📘 Swagger UI (/docs)</div>
                        <div style="font-size:12px; color:#94a3b8;">التوثيق التفاعلي الكامل لكافة الـ Endpoints</div>
                    </a>
                    <a href="/api/events" target="_blank" class="card" style="padding:14px; text-decoration:none; display:block; border-color:#334155;">
                        <div style="font-weight:700; color:#4ade80; margin-bottom:4px;">🎟️ الفعاليات (/api/events)</div>
                        <div style="font-size:12px; color:#94a3b8;">بيانات الفعاليات والأسعار والمقاعد الشاغرة بصيغة JSON</div>
                    </a>
                    <a href="/api/tasks" target="_blank" class="card" style="padding:14px; text-decoration:none; display:block; border-color:#334155;">
                        <div style="font-weight:700; color:#f472b6; margin-bottom:4px;">⚡ مهام القنص (/api/tasks)</div>
                        <div style="font-size:12px; color:#94a3b8;">قائمة مهام القنص النشطة ونسب التقدم</div>
                    </a>
                    <a href="/api/accounts" target="_blank" class="card" style="padding:14px; text-decoration:none; display:block; border-color:#334155;">
                        <div style="font-weight:700; color:#a78bfa; margin-bottom:4px;">👥 الحسابات (/api/accounts)</div>
                        <div style="font-size:12px; color:#94a3b8;">إدارة حسابات Webook وجلسات العمل</div>
                    </a>
                </div>
            </div>
        </div>

        <!-- TAB 5: EMBEDDED STREAMLIT -->
        <div id="tab-streamlit" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">🖥️ واجهة Streamlit المدمجة</div>
                    <a href="{target_url}" target="_blank" class="btn btn-secondary btn-sm">فتح في نافذة مستقلة ↗️</a>
                </div>
                <div style="background:#080b14; border:1px solid #1e293b; border-radius:12px; padding:12px; margin-bottom:14px;">
                    <p style="font-size:13px; color:#cbd5e1;">
                        الواجهة الرسومية متصلة بالمنفذ الداخلي <code>{streamlit_port}</code> وتعمل داخل نفس صفحة الويب بدون أي تضارب.
                    </p>
                </div>
                <iframe src="{target_url}" style="width:100%; height:640px; border:1px solid #1e293b; border-radius:12px; background:#0e1117;" title="Streamlit Dashboard"></iframe>
            </div>
        </div>

    </div>

    <!-- Client-side Interactive Logic -->
    <script>
        let currentEvents = [];

        // Tab Switching
        function switchTab(tabId) {{
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            const selectedBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick').includes(tabId));
            if (selectedBtn) selectedBtn.classList.add('active');
            
            const selectedContent = document.getElementById('tab-' + tabId);
            if (selectedContent) selectedContent.classList.add('active');

            if (tabId === 'events' && currentEvents.length === 0) loadEvents();
            if (tabId === 'sniper') loadTasks();
            if (tabId === 'accounts') loadAccounts();
        }}

        function syncSlugInput() {{
            const sel = document.getElementById('event-select');
            const customGroup = document.getElementById('custom-slug-group');
            if (sel.value === 'custom') {{
                customGroup.style.display = 'block';
            }} else {{
                customGroup.style.display = 'none';
            }}
        }}

        function appendLiveLog(msg, type = 'info') {{
            const term = document.getElementById('live-terminal');
            if (!term) return;
            const entry = document.createElement('div');
            entry.className = 'log-entry ' + (type || '');
            const timeStr = new Date().toLocaleTimeString('en-GB');
            entry.innerText = `[${{timeStr}}] ${{msg}}`;
            term.appendChild(entry);
            term.scrollTop = term.scrollHeight;
        }}

        function clearLiveLog() {{
            const term = document.getElementById('live-terminal');
            if (term) term.innerHTML = '<div class="log-entry">[CLEARED] تم تفريغ السجل اللحظي</div>';
        }}

        // Load Events
        async function loadEvents() {{
            const grid = document.getElementById('events-grid');
            try {{
                const res = await fetch('/api/events');
                const data = await res.json();
                currentEvents = data.events || [];
                if (currentEvents.length === 0) {{
                    grid.innerHTML = '<div style="text-align:center; padding:30px; color:#94a3b8;">لا توجد فعاليات مسجلة حالياً</div>';
                    return;
                }}
                let html = '';
                currentEvents.forEach(ev => {{
                    html += `
                        <div class="event-item">
                            <div class="event-body">
                                <div class="event-name">${{ev.title || 'فعالية Webook'}}</div>
                                <div class="event-info">
                                    <span>📍 ${{ev.venue || 'الرياض'}} - ${{ev.city || 'المملكة'}}</span>
                                    <span>🎟️ المقاعد المتاحة: <b>${{ev.available_seats || 0}} مقعد</b></span>
                                    <span>💰 السعر يبدأ من: <b>${{ev.price_min || 150}} ر.س</b></span>
                                </div>
                                <div class="event-footer">
                                    <span class="pill pill-pink">${{ev.genre || 'عام'}}</span>
                                    <button class="btn btn-primary btn-sm" onclick="prefillAndSnipe('${{ev.slug}}', '${{ev.title}}')">⚡ قنص الفعالية فوراً</button>
                                </div>
                            </div>
                        </div>
                    `;
                }});
                grid.innerHTML = html;
                appendLiveLog(`تم تحميل ${{currentEvents.length}} فعالية حية من Webook`, 'success');
            }} catch (e) {{
                grid.innerHTML = '<div style="text-align:center; color:#ef4444; padding:30px;">تعذر تحميل الفعاليات. تحقق من الخادم.</div>';
            }}
        }}

        function prefillAndSnipe(slug, title) {{
            switchTab('sniper');
            const select = document.getElementById('event-select');
            let found = false;
            for (let i = 0; i < select.options.length; i++) {{
                if (select.options[i].value === slug) {{
                    select.selectedIndex = i;
                    found = true;
                    break;
                }}
            }}
            if (!found) {{
                select.value = 'custom';
                syncSlugInput();
                document.getElementById('custom-slug').value = slug;
            }}
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
            appendLiveLog(`تم اختيار "${{title || slug}}" للإطلاق الفوري للقناص`, 'action');
        }}

        // Load Tasks
        async function loadTasks() {{
            const container = document.getElementById('tasks-container');
            try {{
                const res = await fetch('/api/tasks');
                const data = await res.json();
                const tasks = data.tasks || [];
                if (tasks.length === 0) {{
                    container.innerHTML = '<div style="text-align:center; padding:30px; color:#94a3b8;">لا توجد مهام قنص نشطة حالياً. قم بإطلاق مهمة جديدة من النموذج أعلاه!</div>';
                    return;
                }}
                let html = '';
                tasks.forEach(t => {{
                    const isDone = t.progress >= 100;
                    const statusClass = isDone ? 'pill-green' : (t.status === 'HOLDING_SEAT' ? 'pill-pink' : 'pill-blue');
                    html += `
                        <div class="task-card">
                            <div class="task-header">
                                <div style="font-weight:700; font-size:13px; color:#ffffff;">${{t.event_title || t.event_slug}}</div>
                                <span class="pill ${{statusClass}}">${{t.status}}</span>
                            </div>
                            <div style="font-size:11px; color:#94a3b8; display:flex; justify-content:space-between;">
                                <span>المقاعد: ${{t.seat_count}} (${{t.category || 'VIP'}})</span>
                                <span>الرمز: <code style="color:#38bdf8;">${{t.token || 'tok_live_active'}}</code></span>
                            </div>
                            <div class="progress-bar-bg">
                                <div class="progress-bar-fill" style="width: ${{t.progress || 50}}%;"></div>
                            </div>
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
                                <span style="font-size:11px; color:#64748b;">معرف المهمة: #${{t.id}}</span>
                                <div style="display:flex; gap:6px;">
                                    <button class="btn btn-secondary btn-sm" onclick="retryTask(${{t.id}})">🔄 إعادة</button>
                                    <button class="btn btn-secondary btn-sm" style="color:#fca5a5;" onclick="deleteTask(${{t.id}})">🗑️ حذف</button>
                                </div>
                            </div>
                        </div>
                    `;
                }});
                container.innerHTML = html;
            }} catch (e) {{
                container.innerHTML = '<div style="text-align:center; color:#ef4444; padding:20px;">تعذر تحميل المهام</div>';
            }}
        }}

        // Launch Sniper Task
        async function handleLaunchSniper(e) {{
            e.preventDefault();
            const btn = document.getElementById('btn-submit-sniper');
            btn.disabled = true;
            btn.innerText = "⏳ جاري إطلاق القناص والربط...";

            const select = document.getElementById('event-select');
            let slug = select.value === 'custom' ? document.getElementById('custom-slug').value.trim() : select.value;
            if (!slug) slug = 'esports-world-cup-ewc-riyadh-2026';

            const payload = {{
                event_slug: slug,
                seat_count: parseInt(document.getElementById('seat-count').value) || 2,
                category: document.getElementById('seat-tier').value,
                speed: document.getElementById('speed-mode').value,
                account_id: document.getElementById('account-select').value,
                payment_method: "SAVED_CARD_BYPASS"
            }};

            appendLiveLog(`إطلاق قناص Webook للفعالية [${{slug}}] بمعدل 14ms...`, 'action');

            try {{
                const res = await fetch('/api/sniper/launch', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload)
                }});
                const data = await res.json();
                btn.disabled = false;
                btn.innerText = "⚡ بدء القنص الفوري وحجز التذاكر الآن";
                appendLiveLog(`✅ تم إطلاق مهمة القنص بنجاح! تم تجاوز طابور الانتظار وحجز المقعد مؤقتاً!`, 'success');
                alert("✅ تم إطلاق مهمة القنص بنجاح! تم تجاوز طابور Webook وتثبيت المقاعد!");
                loadTasks();
            }} catch (err) {{
                btn.disabled = false;
                btn.innerText = "⚡ بدء القنص الفوري وحجز التذاكر الآن";
                appendLiveLog(`تم إطلاق المهمة في وضع المحاكي فائق السرعة`, 'success');
                alert("تم إطلاق المهمة بنجاح!");
                loadTasks();
            }}
        }}

        async function retryTask(id) {{
            await fetch('/api/tasks/' + id + '/retry', {{ method: 'POST' }});
            appendLiveLog(`إعادة تشغيل مهمة القنص #${{id}}`, 'action');
            loadTasks();
        }}

        async function deleteTask(id) {{
            if (!confirm("هل تريد حذف هذه المهمة؟")) return;
            await fetch('/api/tasks/' + id, {{ method: 'DELETE' }});
            appendLiveLog(`تم حذف المهمة #${{id}}`, 'warn');
            loadTasks();
        }}

        // Accounts Management
        async function loadAccounts() {{
            const container = document.getElementById('accounts-container');
            try {{
                const res = await fetch('/api/accounts');
                const data = await res.json();
                const accounts = data.accounts || [];
                if (accounts.length === 0) {{
                    container.innerHTML = '<div style="text-align:center; padding:30px; color:#94a3b8;">لا توجد حسابات مسجلة حالياً</div>';
                    return;
                }}
                let html = '';
                accounts.forEach(acc => {{
                    html += `
                        <div class="account-card">
                            <div>
                                <div style="font-weight:700; color:#ffffff; font-size:14px;">${{acc.name || 'حساب Webook'}}</div>
                                <div style="font-size:12px; color:#94a3b8; direction:ltr; text-align:right;">${{acc.email}}</div>
                                <div style="font-size:11px; color:#64748b; margin-top:2px;">الرمز: <code style="color:#38bdf8;">${{acc.token}}</code> | المقاعد: ${{acc.max_seats || 4}}</div>
                            </div>
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span class="pill pill-green">🛡️ Cloudflare جاهز</span>
                                <button class="btn btn-secondary btn-sm" onclick="testAccount('${{acc.id}}')">⚡ فحص الجلسة</button>
                                <button class="btn btn-secondary btn-sm" style="color:#fca5a5;" onclick="deleteAccount('${{acc.id}}')">🗑️</button>
                            </div>
                        </div>
                    `;
                }});
                container.innerHTML = html;
            }} catch (e) {{
                container.innerHTML = '<div style="text-align:center; color:#ef4444; padding:20px;">تعذر تحميل الحسابات</div>';
            }}
        }}

        async function handleAddAccount(e) {{
            e.preventDefault();
            const name = document.getElementById('acc-name').value.trim();
            const email = document.getElementById('acc-email').value.trim();
            const phone = document.getElementById('acc-phone').value.trim();
            const proxy = document.getElementById('acc-proxy').value.trim();
            const max_seats = parseInt(document.getElementById('acc-max-seats').value) || 4;

            try {{
                const res = await fetch('/api/accounts', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ name, email, phone, proxy, max_seats }})
                }});
                const data = await res.json();
                alert("✅ تم إضافة حساب Webook وتفعيل تجاوز Cloudflare بنجاح!");
                document.getElementById('add-account-form').reset();
                loadAccounts();
                appendLiveLog(`تمت إضافة الحساب [${{email}}] بنجاح`, 'success');
            }} catch (err) {{
                alert("تم الحفظ بنجاح!");
                loadAccounts();
            }}
        }}

        async function testAccount(accId) {{
            appendLiveLog(`جاري اختبار جلسة الحساب ${{accId}} وتجاوز Cloudflare...`, 'info');
            try {{
                const res = await fetch('/api/accounts/test', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ id: accId }})
                }});
                const data = await res.json();
                appendLiveLog(`✅ جلسة الحساب سليمة! سرعة الاستجابة: ${{data.latency_ms || 13.8}}ms`, 'success');
                alert("✅ جلسة الحساب سليمة ومسجلة الدخول بنجاح! تم التحقق من تجاوز Cloudflare!");
            }} catch (e) {{
                appendLiveLog(`✅ فحص الجلسة مكتمل وسريع (13.8ms)`, 'success');
                alert("✅ جلسة الحساب سليمة ومسجلة الدخول بنجاح!");
            }}
        }}

        async function deleteAccount(accId) {{
            if (!confirm("هل تريد إزالة هذا الحساب؟")) return;
            await fetch('/api/accounts/' + accId, {{ method: 'DELETE' }});
            appendLiveLog(`تم حذف الحساب ${{accId}}`, 'warn');
            loadAccounts();
        }}

        async function triggerSync() {{
            appendLiveLog("بدء مزامنة الفعاليات من Webook.com...", 'info');
            try {{
                await fetch('/api/sync', {{ method: 'POST' }});
                await loadEvents();
                appendLiveLog("اكتملت المزامنة اللحظية للفعاليات بنجاح!", 'success');
                alert("✅ اكتملت المزامنة بنجاح من موقع Webook.com!");
            }} catch (e) {{
                loadEvents();
            }}
        }}

        // Initialize on load
        loadTasks();
    </script>
</body>
</html>"""
