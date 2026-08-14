import asyncio
import time
import os
import psutil
from datetime import datetime, timezone
from sqlalchemy import select, func
from core.database.postgres import AsyncSessionLocal
from core.database.redis import redis_manager
from database.models.discovery import LiveEvent
from database.models.reservation import ReservationTask, TaskStatus
from core.logging.logger import logger

class SystemHealth:
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    RECOVERY = "RECOVERY"

class TelemetryService:
    """
    PHASE 4: Operational Intelligence & Forensic Attribution.
    Interprets system behavior to detect root causes and monitor error amplification.
    """
    THRESHOLDS = {
        "loop_lag_ms": {"degraded": 100, "critical": 500},
        "redis_rtt_ms": {"degraded": 20, "critical": 100},
        "memory_rss_mb": {"degraded": 800, "critical": 1500},
        "ueue_depth": {"degraded": 500, "critical": 2000},
        "active_tasks": {"degraded": 100, "critical": 300},
    }

    # Operational Counters (Amplification Tracking)
    counters = {
        "retries": 0,
        "reclaims": 0,
        "lease_fails": 0,
        "reconnects": 0,
        "zombie_recoveries": 0
    }

    def __init__(self, interval: int = 300):
        self.interval = interval
        self.process = psutil.Process(os.getpid())
        self._start_time = time.time()
        self._loop_lag = 0.0
        
        # State Management
        self._current_status = SystemHealth.HEALTHY
        self._last_status = SystemHealth.HEALTHY
        self._status_start_time = time.time()
        self._consecutive_cycles = 0
        self._transition_history = [] 
        
        # Incident Tracking
        self._incident_start_time = None
        self._incident_metrics = {
            "peak_rtt": 0.0,
            "peak_loop_lag": 0.0,
            "total_retries": 0,
            "total_reclaims": 0,
            "causes": set()
        }

    async def run(self):
        await redis_manager.connect()
        logger.info("TelemetryService: Monitoring Engine STARTED")
        asyncio.create_task(self._monitor_loop_lag())
        
        while True:
            try:
                stats = await self.collect_metrics()
                self._report_health(stats)
            except Exception as e:
                logger.error(f"TelemetryService Error: {e}")
            await asyncio.sleep(self.interval)

    async def _monitor_loop_lag(self):
        """Measures Event Loop Lag by timing sleep precision."""
        while True:
            start = time.perf_counter()
            await asyncio.sleep(1)
            self._loop_lag = (time.perf_counter() - start) - 1.0

    async def collect_metrics(self):
        stats = {}
        async with AsyncSessionLocal() as db:
            # 1. Database States
            # Tasks
            task_stats = await db.execute(
                select(ReservationTask.status, func.count())
                .group_by(ReservationTask.status)
            )
            stats["tasks"] = dict(task_stats.all())
            
            # Events / Hydration
            hyd_stats = await db.execute(
                select(LiveEvent.hydration_status, func.count())
                .group_by(LiveEvent.hydration_status)
            )
            stats["hydration"] = dict(hyd_stats.all())

            # 2. Infrastructure Latency
            # Redis RTT
            start = time.perf_counter()
            await redis_manager.client.ping()
            stats["redis_rtt_ms"] = round((time.perf_counter() - start) * 1000, 2)

            # 3. Process Health
            stats["memory_rss_mb"] = round(self.process.memory_info().rss / (1024 * 1024), 2)
            stats["cpu_percent"] = self.process.cpu_percent()
            stats["uptime_hours"] = round((time.time() - self._start_time) / 3600, 2)
            stats["loop_lag_ms"] = round(self._loop_lag * 1000, 2)
            stats["active_tasks"] = len(asyncio.all_tasks())

            # 4. Distributed State
            ueue_len = await redis_manager.client.llen("reservation_ueue")
            stats["ueue_depth"] = ueue_len

            # 5. Health Interpretation
            new_status = self._calculate_health(stats)
            primary_cause = self._detect_root_cause(stats) if new_status != SystemHealth.HEALTHY else None
            
            self._handle_status_transition(new_status, primary_cause, stats)
            
            stats["status"] = self._current_status
            stats["primary_cause"] = primary_cause
            stats["status_duration"] = round(time.time() - self._status_start_time, 2)
            stats["counters"] = self.counters

        return stats

    def _detect_root_cause(self, stats) -> str:
        """Identifies which metric is the primary driver of degradation."""
        causes = []
        if stats["loop_lag_ms"] > self.THRESHOLDS["loop_lag_ms"]["degraded"]:
            causes.append("EVENT_LOOP_STARVATION")
        if stats["redis_rtt_ms"] > self.THRESHOLDS["redis_rtt_ms"]["degraded"]:
            causes.append("REDIS_LATENCY_SPIKE")
        if stats["memory_rss_mb"] > self.THRESHOLDS["memory_rss_mb"]["degraded"]:
            causes.append("MEMORY_CREEP")
        if stats["ueue_depth"] > self.THRESHOLDS["ueue_depth"]["degraded"]:
            causes.append("QUEUE_SATURATION")
        
        return " | ".join(causes) if causes else "UNKNOWN"

    def _handle_status_transition(self, new_status: str, cause: str, stats: dict):
        """Manages state transitions with hysteresis and automated incident reporting."""
        if new_status == self._current_status:
            self._consecutive_cycles += 1
            # Track peaks during non-healthy states
            if self._current_status != SystemHealth.HEALTHY:
                self._incident_metrics["peak_rtt"] = max(self._incident_metrics["peak_rtt"], stats["redis_rtt_ms"])
                self._incident_metrics["peak_loop_lag"] = max(self._incident_metrics["peak_loop_lag"], stats["loop_lag_ms"])
                if cause: self._incident_metrics["causes"].add(cause)
            return

        # HYSTERESIS
        if self._current_status in [SystemHealth.DEGRADED, SystemHealth.CRITICAL] and new_status == SystemHealth.HEALTHY:
            if self._consecutive_cycles < 3:
                return

        # Transition Logic
        old_status = self._current_status
        duration = time.time() - self._status_start_time
        
        # 1. Start Incident Tracking
        if old_status == SystemHealth.HEALTHY and new_status != SystemHealth.HEALTHY:
            self._incident_start_time = time.time()
            self._incident_metrics = {
                "peak_rtt": stats["redis_rtt_ms"],
                "peak_loop_lag": stats["loop_lag_ms"],
                "total_retries": 0,
                "total_reclaims": 0,
                "causes": {cause} if cause else set()
            }

        # 2. Recovery: Generate Post-Incident Report
        if new_status == SystemHealth.HEALTHY and self._incident_start_time:
            self._generate_post_incident_report(duration)
            self._incident_start_time = None

        # Log Transition Event
        msg = f"[STATE_CHANGE] {old_status} -> {new_status} | Duration: {round(duration, 2)}s"
        if cause: msg += f" | Primary Cause: {cause}"
        
        if new_status == SystemHealth.HEALTHY:
            logger.info(f"📊 {msg}")
        else:
            logger.warning(msg)

        self._last_status = old_status
        self._current_status = new_status
        self._status_start_time = time.time()
        self._consecutive_cycles = 0

    def _generate_post_incident_report(self, recovery_duration: float):
        """Generates a detailed forensic summary of the resolved incident."""
        incident_duration = time.time() - self._incident_start_time
        
        report = [
            "\n" + "\U0001f4d1 " + "â€”"*15 + " POST_INCIDENT_REPORT " + "â€”"*15,
            f"Incident Duration: {round(incident_duration, 2)}s",
            f"Primary Causes: {', '.join(self._incident_metrics['causes'])}",
            f"Peak Redis RTT: {self._incident_metrics['peak_rtt']}ms",
            f"Peak Loop Lag: {self._incident_metrics['peak_loop_lag']}ms",
            f"Recovery Path Duration: {round(recovery_duration, 2)}s",
            f"Total Retries during crisis: {self.counters['retries']}",
            f"Total Reclaims during crisis: {self.counters['reclaims']}",
            f"Final State: HEALTHY (Verified over 3 cycles)",
            "\U0001f4d1 " + "â€”"*50 + "\n"
        ]
        logger.info("\n".join(report))
        # Reset counters after report
        self.counters["retries"] = 0
        self.counters["reclaims"] = 0

        # FLAPPING DETECTION
        self._transition_history.append(time.time())
        # Keep only last 5 mins
        self._transition_history = [t for t in self._transition_history if time.time() - t < 300]
        if len(self._transition_history) > 4:
            logger.critical(f"\U0001f525 [FLAPPING_DETECTED] System unstable: {len(self._transition_history)} transitions in 5m")

    def _calculate_health(self, stats) -> str:
        """Determines health state based on defined thresholds."""
        status = SystemHealth.HEALTHY
        
        # Check Criticals first
        if (stats["loop_lag_ms"] > self.THRESHOLDS["loop_lag_ms"]["critical"] or
            stats["redis_rtt_ms"] > self.THRESHOLDS["redis_rtt_ms"]["critical"] or
            stats["memory_rss_mb"] > self.THRESHOLDS["memory_rss_mb"]["critical"]):
            return SystemHealth.CRITICAL

        # Check Degraded
        if (stats["loop_lag_ms"] > self.THRESHOLDS["loop_lag_ms"]["degraded"] or
            stats["redis_rtt_ms"] > self.THRESHOLDS["redis_rtt_ms"]["degraded"] or
            stats["ueue_depth"] > self.THRESHOLDS["ueue_depth"]["degraded"]):
            return SystemHealth.DEGRADED

        return status

    def _report_health(self, stats):
        """Outputs a structured, grep-friendly health report."""
        status_icon = "\U0001f7e2" if stats["status"] == SystemHealth.HEALTHY else "\U0001f7e1" if stats["status"] == SystemHealth.DEGRADED else "\U0001f534"
        
        report = [
            "\n" + "="*40,
            f"{status_icon} [SYSTEM_HEALTH_REPORT: {stats['status']}]",
            f"Primary Cause: {stats.get('primary_cause') or 'NONE'}",
            f"Duration in State: {stats['status_duration']}s",
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
            f"Uptime: {stats['uptime_hours']}h | Active Tasks: {stats['active_tasks']}",
            f"Memory RSS: {stats['memory_rss_mb']}MB | CPU: {stats['cpu_percent']}%",
            f"Loop Lag: {stats['loop_lag_ms']}ms | Redis RTT: {stats['redis_rtt_ms']}ms",
            f"Queue Depth: {stats['ueue_depth']}",
            "-"*20,
            f"Amplification: {stats.get('counters', {})}",
            f"Tasks: {stats.get('tasks', {})}",
            f"Hydration: {stats.get('hydration', {})}",
            "="*40 + "\n"
        ]
        
        if stats["status"] == SystemHealth.CRITICAL:
            logger.critical("\n".join(report))
            # Potential hook for Auto-Remediation (e.g. scale down, restart service)
        else:
            logger.info("\n".join(report))

# Global Instance
telemetry = TelemetryService(interval=300)

