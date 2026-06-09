import asyncio
import sys

from core.logger import logger

from bot.bot_instance import bot, dp, start_bot

from bot.handlers.commands import router as commands_router
from bot.handlers.callbacks import router as callbacks_router
from bot.handlers.booking import router as booking_router

from core.scheduler import ReminderScheduler

# ==================== SLOT GENERATOR ====================

from utils.generate_slots import generateSlots

# ==================== REGISTER ROUTERS ====================

dp.include_router(commands_router)
dp.include_router(callbacks_router)
dp.include_router(booking_router)

# ==================== MAIN ====================

async def main():

    try:

        # ==================== GENERATE SLOTS ====================
        # Phase 4: wrap generateSlots() in its own try/except so a failure
        # (empty sheet, bad credentials, API quota) does not prevent the bot
        # from starting. The scheduler will retry every 6 hours automatically.

        try:
            logger.info("📅 Generisanje termina...")
            await generateSlots()
            logger.info("✅ Termini generisani.")
        except Exception as slot_err:
            logger.error(
                "Termini nisu generisani pri startu - scheduler ce pokusati ponovo za 6h.",
                error=str(slot_err),
            )

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

        logger.info(
            "🛑 Bot zaustavljen ručno"
        )

    except Exception as e:

        logger.error(
            "❌ Kritična greška pri pokretanju",
            error=str(e)
        )

        sys.exit(1)