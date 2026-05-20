from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.keyboards import date_keyboard, time_keyboard
from bot.states import BookingStates
from services.sheets_service import SheetsService
from core.logger import logger
from core.security import SecurityManager

router = Router()
sheets = SheetsService()

@router.callback_query(F.data.startswith("service_"))
async def callback_service(callback: CallbackQuery, state: FSMContext):
    if not SecurityManager.check_rate_limit(callback.from_user.id):
        await callback.answer("⏳ Sačekajte par sekundi između akcija.", show_alert=True)
        return

    service = callback.data.replace("service_", "").replace("_", " ")
    await state.update_data(usluga=service)
    await state.set_state(BookingStates.waiting_for_date)
    
    await callback.message.edit_text("🗓️ *Tražim slobodne termine...* ⏳")
    await callback.answer()

    try:
        free_dates = await sheets.get_free_dates()
        if not free_dates:
            await callback.message.edit_text("❌ Trenutno nema slobodnih termina.")
            return
        await callback.message.edit_text("🗓️ *Izaberite datum:*", reply_markup=date_keyboard(free_dates))
    except Exception as e:
        logger.error("Greška pri dohvatanju datuma", error=str(e))
        await callback.message.edit_text("❌ Greška pri učitavanju termina.")

@router.callback_query(F.data.startswith("date_"))
async def callback_date(callback: CallbackQuery, state: FSMContext):
    if not SecurityManager.check_rate_limit(callback.from_user.id):
        await callback.answer("⏳ Sačekajte par sekundi...", show_alert=True)
        return

    date = callback.data.replace("date_", "")
    await state.update_data(datum=date)
    await state.set_state(BookingStates.waiting_for_time)
    
    await callback.message.edit_text(f"⏰ *Tražim slobodna vremena za {date}...* ⏳")
    await callback.answer()

    try:
        free_times = await sheets.get_free_times(date)
        if not free_times:
            await callback.message.edit_text("❌ Nema slobodnih termina za ovaj datum.")
            return
        await callback.message.edit_text(f"⏰ *Izaberite vreme za {date}:*", reply_markup=time_keyboard(free_times))
    except Exception as e:
        logger.error("Greška pri dohvatanju vremena", error=str(e))

@router.callback_query(F.data.startswith("time_"))
async def callback_time(callback: CallbackQuery, state: FSMContext):
    if not SecurityManager.check_rate_limit(callback.from_user.id):
        await callback.answer("⏳ Sačekajte...", show_alert=True)
        return

    time_str = callback.data.replace("time_", "")
    await state.update_data(vreme=time_str)
    await state.set_state(BookingStates.waiting_for_name)
    
    await callback.message.edit_text("👤 *Unesite ime i prezime ljubimca/vlasnika:*")
    await callback.answer()