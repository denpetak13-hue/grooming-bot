from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from core.config import settings
from core.logger import logger

bot = Bot(
    token=settings.TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)

dp = Dispatcher()

# ==================== GLOBAL ERROR HANDLER ====================
@dp.errors()
async def error_handler(event):
    """Hvata sve greške u botu"""
    logger.error("Globalna greška u botu", error=str(event.exception))
    
    try:
        if event.update and event.update.message:
            await event.update.message.answer(
                "❌ Došlo je do neočekivane greške.\n\n"
                "Pokušajte ponovo za par sekundi ili pozovite salon na 069/188-3389."
            )
    except:
        pass


async def start_bot():
    logger.info("🤖 GroomingBot se pokreće...")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Bot uspešno pokrenut i spreman za rad!")


# ==================== GRACEFUL SHUTDOWN ====================
# RC-12: setup_shutdown() previously called asyncio.get_event_loop() at module
# import time (before any event loop exists), which is deprecated since
# Python 3.10 and raises DeprecationWarning on 3.12+.
#
# Cleanup is already handled by:
#   - run.py finally: ReminderScheduler.stop()
#   - aiogram dp.start_polling() which handles KeyboardInterrupt internally
#
# The shutdown() coroutine is kept as a utility in case it is needed later,
# but it is NOT called at import time.

import asyncio


async def shutdown():
    logger.info("Bot se gasi...")
    await bot.session.close()
    logger.info("Bot uspesno zaustavljen")