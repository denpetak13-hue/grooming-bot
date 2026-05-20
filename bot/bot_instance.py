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


# ==================== GRACEFUL SHUTDOWN (Windows friendly) ====================
import asyncio
import signal

async def shutdown():
    logger.info("⛔ Bot se gasi...")
    await bot.session.close()
    logger.info("✅ Bot uspešno zaustavljen")

# Za Windows
def setup_shutdown():
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
        except NotImplementedError:
            # Windows fallback
            pass

setup_shutdown()