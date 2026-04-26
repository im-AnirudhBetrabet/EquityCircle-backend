from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.api.v1.alerts import run_global_market_scan
from app.services.logger import sys_logger

scheduler = BackgroundScheduler()

def job_wrapper(time_of_day: str):
    sys_logger.info(f"[SCHEDULER] running job: {time_of_day}")
    try:
        run_global_market_scan(time_of_day)
    except Exception as e:
        sys_logger.error(f"[SCHEDULER ERROR]: {e} ")

def start_scheduler():
    # 1. Market open job ( 9:30 AM IST Monday - Friday )
    sys_logger.info("Setting up market open job..")
    scheduler.add_job(
        func=job_wrapper,
        args=["Market Open"],
        trigger=CronTrigger(day_of_week='mon-fri', hour=4, minute=0),
        id="scan_open",
        replace_existing=True
    )
    sys_logger.info("Market - open job set up successfully.")

    # 2. Mid day job ( 12:30 PM IST Monday - Friday )
    sys_logger.info("Setting up Mid day job..")
    scheduler.add_job(
        func=job_wrapper,
        args=["Mid-Day"],
        trigger=CronTrigger(day_of_week='mon-fri', hour=7, minute=0),
        id='scan_midday',
        name='Mid-Day Scan',
        replace_existing=True
    )
    sys_logger.info("Mid day job set up successfully.")

    # 3. The Market Close Wrap-Up (15:45 PM, Mon-Fri)
    sys_logger.info("Setting up market close job..")
    scheduler.add_job(
        func=job_wrapper,
        args=["Market Close"],
        trigger=CronTrigger(day_of_week='mon-fri', hour=10, minute=15),
        id='scan_close',
        name='Market Close Scan',
        replace_existing=True
    )
    sys_logger.info("Market close job set up successfully.")

    sys_logger.info("Scanning for existing schedules..")

    if not scheduler.running:
        sys_logger.info("Scan completed no schedules found. Setting up new schedule..")
        scheduler.start()
    else:
        sys_logger.info(f"Scan completed. Schedule exists already.")