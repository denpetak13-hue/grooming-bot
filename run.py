import asyncio
import sys

from core.logger import logger
from bot.bot_instance import bot, dp, start_bot

from bot.handlers.commands import router as commands_router
from bot.handlers.callbacks import router as callbacks_router
from bot.handlers.booking import router as booking_router

from core.scheduler import ReminderScheduler

# ==================== REGISTER ROUTERS ====================

dp.include_router(commands_router)
dp.include_router(callbacks_router)
dp.include_router(booking_router)

# ==================== MAIN ====================

async def main():

    try:

        # ==================== START BOT ====================

        await start_bot()

        # ==================== START REMINDER SCHEDULER ====================

        ReminderScheduler.start()

        logger.info(
            "🚀 GroomingBot ONLINE + Reminder Scheduler AKTIVAN"
        )

        # ==================== START POLLING ====================

        await dp.start_polling(bot)

    except Exception as e:

        logger.error(
            "❌ Kritična greška",
            error=str(e)
        )

    finally:

        ReminderScheduler.stop()

# ==================== RUN APP ====================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        logger.info("🛑 Bot zaustavljen ručno")

    except Exception as e:

        logger.error(
            "❌ Kritična greška pri pokretanju",
            error=str(e)
        )

        sys.exit(1)