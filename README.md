# 🦅 Webook Sniper Elite v1.0

The ultimate production-grade sniping platform for Webook. Designed for speed, anti-ban resilience, and 24/7 automated ticket holding.

## 🚀 Quick Start (Production)

1. **Configure Environment:**
   Update `.env` with your `BOT_TOKEN` and `ADMIN_IDS`.

2. **Launch Infrastructure:**
   ```bash
   docker-compose up --build -d
   ```

3. **Monitor Live Dashboard:**
   Open a separate terminal and run:
   ```bash
   python scripts/dashboard.py
   ```

## 🎮 How to Operate

### 1. Connect Accounts
- Open your Telegram Bot and send `/start`.
- Click `👤 Accounts` -> `➕ Add New Account`.
- Follow the **Interactive OTP Wizard** to verify your Webook sessions.

### 2. Set Up a Sniper
- Click `🚀 Start New Sniper`.
- Enter the **Event Slug** (e.g., `al-hilal-match`).
- Select your **Category** (VIP, Gold, Standard).
- Enter seat count.

### 3. The "Smooth Swap"
The system automatically monitors your holds. If a hold is within 60 seconds of expiring, the `HoldSwapper` service will atomically move the ticket to a fresh account to keep it held for another 10 minutes.

## 📊 Monitoring & Observability
- **Terminal:** `scripts/dashboard.py` for live task status.
- **Metrics:** Access Prometheus at `http://localhost:9090`.
- **Grafana:** Access dashboards at `http://localhost:3000` (User: `admin` / Pass: `admin`).

## 🛡️ Anti-Ban Architecture
- **Distributed Locking:** Redis ensures no two workers touch the same account simultaneously.
- **Fingerprinting:** Every request uses a unique, realistic User-Agent.
- **Residential Proxies:** Integrated at the client level to mimic human traffic.

---
**Developer Note:** This system is built for extreme performance. Ensure your server has low latency to Webook's region for optimal results.
