from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from services.sheets_service import SheetsService
from services.twilio_service import TwilioService
from core.logger import logger

class ReminderScheduler:
    scheduler = None
    sheets = SheetsService()
    twilio = TwilioService()

    @classmethod
    def start(cls):
        if cls.scheduler is not None:
            return

        cls.scheduler = AsyncIOScheduler(timezone="Europe/Belgrade")
        
        cls.scheduler.add_job(
            cls.check_and_send_reminders,
            trigger=IntervalTrigger(minutes=5),   # svakih 5 minuta za test
            id='whatsapp_reminders',
            replace_existing=True
        )
        
        cls.scheduler.start()
        logger.info("✅ Reminder Scheduler pokrenut (provera svakih 5 minuta)")

    @classmethod
    async def check_and_send_reminders(cls):
        try:
            logger.info("🔍 Provera sutrašnjih termina...")
            appointments = await cls.sheets.get_tomorrows_appointments()
            
            if not appointments:
                # logger.info("Nema termina za podsetnik danas")
                return

            logger.info(f"Nađeno {len(appointments)} termina za slanje podsetnika")

            for app in appointments:
                success = await cls.twilio.send_whatsapp_reminder(
                    phone=app['telefon'],
                    name=app['ime'],
                    date=app['datum'],
                    time=app['vreme']
                )

                if success:
                    await cls.sheets.mark_reminder_sent(app['row_num'])
                    logger.info(f"✅ Podsetnik POSLAT → {app['ime']} ({app['vreme']})")
                else:
                    logger.error(f"❌ Neuspešno slanje za {app['ime']}")

        except Exception as e:
            logger.error("Greška u reminder scheduleru", error=str(e))

    @classmethod
    def stop(cls):
        if cls.scheduler:
            cls.scheduler.shutdown()
            logger.info("⛔ Scheduler zaustavljen")