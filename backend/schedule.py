from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from scraper import scrape_marketplace
from config_parser import read_config
from loguru import logger

def scheduled_task():
    config = read_config('config/monitoring.yaml')
    logger.info("Запуск запланированного сбора данных")
    scrape_marketplace(config)

def start_scheduler(app):
    scheduler = BackgroundScheduler(daemon=True)
    interval = int(app.config.get('SCHEDULE_INTERVAL_DEFAULT', 43200))
    scheduler.add_job(scheduled_task, 'interval', seconds=interval)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
