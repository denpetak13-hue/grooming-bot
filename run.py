import asyncio
from core.logger import logger
from bot.bot_instance import bot, dp, start_bot
from bot.handlers.commands import router as commands_router
from bot.handlers.callbacks import router as callbacks_router
from bot.handlers.booking import router as booking_router
from core.scheduler import ReminderScheduler

# Registracija handlera
dp.include_router(commands_router)
dp.include_router(callbacks_router)
dp.include_router(booking_router)

async def main():
    try:
        await start_bot()
        
        # Pokretanje remindera
        ReminderScheduler.start()
        
        logger.info("🚀 GroomingBot je ONLINE + Reminder Scheduler AKTIVAN")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("Kritična greška", error=str(e))
    finally:
        ReminderScheduler.stop()

import os
import sys

if __name__ == "__main__":
    # Za Render - bolji error handling
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot zaustavljen ručno")
    except Exception as e:
        logger.error("Kritična greška pri pokretanju", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())