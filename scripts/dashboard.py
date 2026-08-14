import asyncio
from rich.console import Console
from rich.table import Table
from rich.live import Live
from core.database.postgres import AsyncSessionLocal
from database.repositories.reservation import ReservationRepository
from database.models.reservation import TaskStatus
from datetime import datetime, timezone

console = Console()

async def get_stats():
    async with AsyncSessionLocal() as db:
        repo = ReservationRepository(db)
        tasks = await repo.get_active_tasks()
        
        table = Table(title="\U0001f680 Webook Sniper: Live Operations", border_style="cyan")
        table.add_column("Task ID", justify="center", style="dim")
        table.add_column("Event Slug", style="bold white")
        table.add_column("Status", justify="center")
        table.add_column("Hold Expires", justify="center")
        table.add_column("Last Log", style="italic")

        for t in tasks:
            status_style = "green" if t.status == TaskStatus.SUCCESS else "yellow"
            expiry = t.hold_expires_at.strftime("%H:%M:%S") if t.hold_expires_at else "N/A"
            last_log = t.logs[-1]["msg"] if t.logs else "Initializing..."
            
            table.add_row(
                str(t.id),
                t.event_slug,
                f"[{status_style}]{t.status.value}[/]",
                expiry,
                last_log[:40] + "..." if len(last_log) > 40 else last_log
            )
            
        return table

async def run_dashboard():
    with Live(await get_stats(), refresh_per_second=1, console=console) as live:
        while True:
            live.update(await get_stats())
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(run_dashboard())
    except KeyboardInterrupt:
        console.print("\n[bold red]Dashboard Closed.[/]")
