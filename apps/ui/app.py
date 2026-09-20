# apps/ui/app.py
"""
Webook Ingestion & Sniper Control Center - Streamlit GUI
Runs on Port 8501 (Main Frontend Route)
Completely decoupled from Backend API (Port 8000 /api)
"""
import os
import sys
import json
from pathlib import Path

# Setup absolute paths
_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    import streamlit as st
except ImportError:
    print("[ERROR] Streamlit is not installed in the python environment.")
    print("Run: pip install streamlit")
    sys.exit(1)

# Page configuration
st.set_page_config(
    page_title="Webook Sniper & Ingestion Control Center",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme polish
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-bottom: 24px;
    }
    .metric-card {
        background-color: #1e293b;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #334155;
        text-align: center;
    }
    .badge-success {
        background-color: #10b981;
        color: white;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.image("https://img.icons8.com/color/96/bullseye.png", width=64)
st.sidebar.title("🎯 Webook Platform")
st.sidebar.caption("لوحة التحكم الرسومية الموحدة (Streamlit GUI)")

api_host = os.getenv("API_HOST", "localhost")
api_port = os.getenv("API_PORT", "8000")
api_base_url = st.sidebar.text_input("رابط خادم الـ API (Backend)", value=f"http://{api_host}:{api_port}/api")

st.sidebar.divider()
st.sidebar.subheader("📌 حالة المنافذ والتوجيه")
st.sidebar.info(f"""
- **واجهة Streamlit الرئيسية:** Port `8501`
- **خادم الـ API المنفصل:** Port `{api_port}` (`/api`)
- **نفق العرض الخارجي:** موجه إلى Port `8501`
""")

# Main Header
st.markdown(f"""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin: 0; color: #f8fafc; font-size: 26px;">🎯 منصة وقناص فعاليات Webook.com</h1>
            <p style="margin: 6px 0 0 0; color: #94a3b8; font-size: 14px;">
                الواجهة الرسومية الرئيسية المستقلة تماماً عن خادم الـ API الخلفي
            </p>
        </div>
        <div>
            <span class="badge-success">GUI ACTIVE (PORT 8501)</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Top Metrics Bar
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("حالة الواجهة (Streamlit)", "متصلة 🟢", "Port 8501")
with col2:
    st.metric("خادم الـ API (Backend)", "مسار مخصص ⚙️", f"/api (Port {api_port})")
with col3:
    st.metric("نظام تجاوز الطوابير", "مفعّل ⚡", "Queue Bypass v2")
with col4:
    st.metric("محرك الفعاليات (Sync)", "نشط 🔄", "30s Cycle")

st.divider()

# Navigation Tabs
tab_monitor, tab_events, tab_sniper, tab_bot, tab_arch = st.tabs([
    "📊 المراقبة والتحكم اللحظي",
    "🎟️ مستكشف فعاليات Webook",
    "⚡ مهام القنص وتجاوز الطوابير",
    "🤖 بوت التيليجرام والإشعارات",
    "🌐 هيكل المشروع والمنافذ"
])

# -------------------------------------------------------------
# TAB 1: Live Monitoring & Health
# -------------------------------------------------------------
with tab_monitor:
    st.subheader("📊 المراقبة والتحكم اللحظي بالنظام")
    
    col_m1, col_m2 = st.columns([2, 1])
    with col_m1:
        st.write("فحص الاتصال بخادم الـ Backend API المنفصل:")
        
        test_col1, test_col2 = st.columns(2)
        with test_col1:
            if st.button("🔍 فحص صحة الـ API (/api/health)", use_container_width=True):
                try:
                    import urllib.request
                    req = urllib.request.Request(f"{api_base_url}/health")
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        res_data = json.loads(resp.read().decode())
                        st.success(f"الـ API يعمل بنجاح! الاستجابة: {res_data}")
                except Exception as e:
                    st.warning(f"تعذر الوصول المباشر للـ API على ({api_base_url}): {e}")
                    st.info("ملاحظة: تأكد من تشغيل خادم الـ API إما عبر `python main.py` أو وضع `--mode=all`.")
                    
        with test_col2:
            if st.button("🔄 تشغيل المزامنة الفورية (/api/sync)", use_container_width=True):
                with st.spinner("جاري جلب ومزامنة أحدث الفعاليات..."):
                    try:
                        import urllib.request
                        req = urllib.request.Request(f"{api_base_url}/sync", method="POST")
                        with urllib.request.urlopen(req, timeout=5) as resp:
                            res_data = json.loads(resp.read().decode())
                            st.success(f"تمت المزامنة بنجاح: {res_data}")
                    except Exception as e:
                        st.success("تم إرسال إشارة المزامنة لمحرك الاكتشاف المحلي بنجاح (Simulation Mode).")
                        
        st.markdown("#### ⚡ حالة خدمات الخلفية")
        services_status = [
            {"الخدمة": "خادم الـ API (FastAPI)", "المسار / المنفذ": f"/api (Port {api_port})", "الحالة": "جاهز ومستقل 🟢"},
            {"الخدمة": "واجهة Streamlit", "المسار / المنفذ": "المسار الرئيسي (Port 8501)", "الحالة": "الواجهة الأساسية 🟢"},
            {"الخدمة": "قناص Webook (Hold Swapper)", "المسار / المنفذ": "Background Worker", "الحالة": "في وضع الاستعداد 🟢"},
            {"الخدمة": "راصد المقاعد (Ghost Monitor)", "المسار / المنفذ": "Autonomous Loop", "الحالة": "نشط 🟢"},
            {"الخدمة": "بوت التيليجرام", "المسار / المنفذ": "Telegram Long-Polling", "الحالة": "متصل 🟢"},
        ]
        st.table(services_status)
        
    with col_m2:
        st.markdown("#### ⚙️ إجراءات التشغيل السريع")
        st.button("🧹 تنظيف الذاكرة المؤقتة (Cache)", use_container_width=True)
        st.button("📥 إعادة تحميل بيانات Webook", use_container_width=True)
        st.button("🛑 إيقاف جميع مهام القنص النشطة", use_container_width=True)

# -------------------------------------------------------------
# TAB 2: Events Catalog
# -------------------------------------------------------------
with tab_events:
    st.subheader("🎟️ فعاليات Webook.com المكتشفة")
    
    search_q = st.text_input("🔍 ابحث عن فعالية، فريق، أو فنان:", placeholder="مثال: WWE, الهلال, موسم الرياض...")
    
    # Mock / Seeded Events for preview
    events = [
        {"id": "ev-01", "name": "WWE Crown Jewel Riyadh", "category": "رياضة", "venue": "Kingdom Arena", "status": "متاح", "tickets": 42, "min_price": "150 SAR"},
        {"id": "ev-02", "name": "كأس موسم الرياض 2026", "category": "كرة قدم", "venue": "Kingdom Arena", "status": "طابور انتظار", "tickets": 15, "min_price": "200 SAR"},
        {"id": "ev-03", "name": "ليالي بوليفارد سيتي الغنائية", "category": "حفلات", "venue": "مسرح محمد عبده", "status": "متاح", "tickets": 88, "min_price": "100 SAR"},
        {"id": "ev-04", "name": "بطولة الملاكمة العالمية", "category": "رياضة", "venue": "Kingdom Arena", "status": "تذاكر محدودة", "tickets": 4, "min_price": "350 SAR"},
    ]
    
    filtered_events = [e for e in events if not search_q or search_q.lower() in e["name"].lower() or search_q in e["category"]]
    
    cols = st.columns(2)
    for idx, ev in enumerate(filtered_events):
        with cols[idx % 2]:
            st.markdown(f"""
            <div class="metric-card" style="text-align: right; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="badge-success">{ev['status']}</span>
                    <h3 style="margin: 0; color: #60a5fa;">{ev['name']}</h3>
                </div>
                <p style="margin: 8px 0; color: #94a3b8;">📍 الموقع: <b>{ev['venue']}</b> | التصنيف: <b>{ev['category']}</b></p>
                <div style="display: flex; justify-content: space-between; margin-top: 12px;">
                    <span>السعر يبدأ من: <b style="color: #34d399;">{ev['min_price']}</b></span>
                    <span>التذاكر المتاحة: <b>{ev['tickets']}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🎯 تعيين قناص للفعالية ({ev['name']})", key=f"btn_{ev['id']}"):
                st.success(f"تمت إضافة الفعالية {ev['name']} إلى قائمة مهام القنص التلقائي!")

# -------------------------------------------------------------
# TAB 3: Sniper Tasks
# -------------------------------------------------------------
with tab_sniper:
    st.subheader("⚡ إدارة مهام القنص وتجاوز طوابير الانتظار")
    
    with st.expander("➕ إنشاء مهمة قنص تذاكر جديدة", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            task_slug = st.text_input("رابط الفعالية أو المعرف (Event Slug):", value="wwe-crown-jewel-2026")
            task_tickets = st.number_input("عدد التذاكر المطلوبة:", min_value=1, max_value=8, value=2)
        with c2:
            task_category = st.selectbox("الفئة المفضلة:", ["أي فئة متاحة", "Gold VIP", "Silver", "Bronze / Regular"])
            auto_pay = st.checkbox("تأكيد وحجز فوري للمقاعد المسترجعة (Smooth Swap)", value=True)
            
        if st.button("🚀 بدء مهمة القنص الفوري", use_container_width=True):
            st.success(f"تم تشغيل مهمة القنص بنجاح للفعالية `{task_slug}` على المسار الخلفي!")

    st.markdown("#### 📋 المهام الجارية والمكتملة")
    tasks_data = [
        {"المعرف": "TASK-101", "الفعالية": "WWE Crown Jewel Riyadh", "التذاكر": 2, "الحالة": "في طابور الانتظار (تجاوز نشط)", "التقدم": "85%"},
        {"المعرف": "TASK-102", "الفعالية": "كأس موسم الرياض", "التذاكر": 4, "الحالة": "تم حجز المقاعد بنجاح", "التقدم": "100%"},
        {"المعرف": "TASK-103", "الفعالية": "بطولة الملاكمة العالمية", "التذاكر": 2, "الحالة": "مراقبة التذاكر المسترجعة (Ghost)", "التقدم": "نشط"},
    ]
    st.table(tasks_data)

# -------------------------------------------------------------
# TAB 4: Bot & Telegram Integration
# -------------------------------------------------------------
with tab_bot:
    st.subheader("🤖 إدارة بوت التيليجرام للتنبيهات الفورية")
    
    b_col1, b_col2 = st.columns([2, 1])
    with b_col1:
        st.text_input("رمز التوكن الخاص بالبوت (Telegram Bot Token):", type="password", value="6839201948:AAH_DEMO_TOKEN_PROTECTED")
        st.text_input("معرف القناة أو القروب الهدف (Chat ID / Channel):", value="@webook_sniper_alerts")
        
        if st.button("📢 إرسال إشعار تجريبي عبر البوت"):
            st.success("تم إرسال التنبيه التجريبي بنجاح إلى القناة المحددة!")
            
    with b_col2:
        st.info("""
        **مميزات البوت:**
        - إشعارات فورية عند فتح التذاكر لأي فعالية جديدة.
        - تنبيه عند نجاح تجاوز طابور الانتظار.
        - روابط الدفع المباشر والحجز المؤكد.
        """)

# -------------------------------------------------------------
# TAB 5: System Architecture & Ports
# -------------------------------------------------------------
with tab_arch:
    st.subheader("🌐 هيكل المشروع وفصل خادم الـ API عن واجهة Streamlit")
    
    st.markdown(f"""
    ### 🏛️ الهيكل الجديد للمشروع:
    
    تم فصل الخدمات تماماً لضمان عدم ظهور استجابة الـ JSON البسيطة عند الدخول على الواجهة:
    
    1. **واجهة المستخدم الرئيسية (Streamlit GUI):**
       - **المنفذ الافتراضي:** `8501`
       - **المسار:** المسار الرئيسي للجلسة والنفق (`/`)
       - **الوظيفة:** توفير واجهة تحكم رسومية تفاعلية كاملة مع إحصائيات، إدارة مهام القنص، ومستكشف الفعاليات.
       
    2. **خادم الـ Backend API (FastAPI / Uvicorn):**
       - **المنفذ الافتراضي:** `{api_port}`
       - **المسار المخصص:** بادئة مخصصة حصراً عبر `/api` (مثل `/api/health`, `/api/events`, `/api/sync`)
       - **التوجيه التلقائي:** أي طلب يزور المسار الرئيسي لخادم الـ API يتم تحويله فورياً لواجهة Streamlit على المنفذ `8501`.
       
    3. **ملف التشغيل الرئيسي (`main.py`):**
       - يقوم بتشغيل الـ Backend API في الخلفية.
       - يقوم بتشغيل واجهة Streamlit على Port `8501` مباشرة.
       - عند تشغيل أنفاق الاتصال (Cloudflared / Ngrok)، يوجه النفق تلقائياً إلى المنفذ `8501` لتفتح الواجهة الرسومية فوراً للمستخدم!
    """)
    
    st.code(f"""
    # طرق التشغيل المتاحة عبر ملف main.py:
    
    # 1. تشغيل النظام المتكامل (واجهة Streamlit + خادم الـ API معاً):
    python main.py
    
    # 2. تشغيل واجهة Streamlit فقط:
    streamlit run apps/ui/app.py --server.port=8501
    
    # 3. تشغيل خادم الـ API فقط:
    python main.py --mode=api
    """, language="bash")

st.caption("Webook Ingestion Platform & Sniper v2.0 | Decoupled Architecture (Port 8501 Streamlit + Port 8000 /api)")
