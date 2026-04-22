from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.api.v1.alerts import run_global_market_scan

scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(
        func=run_global_market_scan,
        args=["Market Open"],
        trigger=CronTrigger(day_of_week='mon-fri', hour=9, minute=30),
        id="scan_open",
        replace_existing=True
    )
    scheduler.add_job(
        func=run_global_market_scan,
        args=["Mid-Day"],
        trigger=CronTrigger(day_of_week='mon-fri', hour=12, minute=30),
        id='scan_midday',
        name='Mid-Day Scan',
        replace_existing=True
    )

    # 3. The Market Close Wrap-Up (15:45 PM, Mon-Fri)
    scheduler.add_job(
        func=run_global_market_scan,
        args=["Market Close"],
        trigger=CronTrigger(day_of_week='mon-fri', hour=15, minute=39),
        id='scan_close',
        name='Market Close Scan',
        replace_existing=True
    )

    scheduler.start()
    print("Background Market Scheduler Started. Jobs loaded.")