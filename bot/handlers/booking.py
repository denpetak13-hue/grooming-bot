from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.keyboards import consent_keyboard
from bot.states import BookingStates
from services.sheets_service import SheetsService
from core.logger import logger

router = Router()
sheets = SheetsService()


@router.message(BookingStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(ime=message.text.strip())
    await state.set_state(BookingStates.waiting_for_phone)
    await message.answer("📱 *Unesite broj telefona:*")


@router.message(BookingStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(telefon=message.text.strip())
    await state.set_state(BookingStates.waiting_for_consent)
    await message.answer(
        "🔔 *Želite li WhatsApp podsetnik dan pre termina?*",
        reply_markup=consent_keyboard()
    )


@router.callback_query(F.data == "consent_yes")
async def consent_yes(callback: CallbackQuery, state: FSMContext):
    await state.update_data(consent="Da")
    await callback.message.edit_text("✅ Hvala! Poslaćemo vam podsetnik.")
    await callback.answer()
    await ask_for_email(callback, state)


@router.callback_query(F.data == "consent_no")
async def consent_no(callback: CallbackQuery, state: FSMContext):
    await state.update_data(consent="Ne")
    await callback.message.edit_text("U redu.")
    await callback.answer()
    await ask_for_email(callback, state)


async def ask_for_email(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingStates.waiting_for_email)
    await callback.message.answer("📧 Unesite email (ili napišite / ako nemate):")


@router.message(BookingStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    data = await state.get_data()
    email = message.text.strip()

    success = await sheets.reserve_slot(
        data.get('datum'), data.get('vreme'), 
        {**data, "email": email, "chat_id": message.chat.id}
    )

    if success:
        await message.answer(
            f"🎉 *Termin uspešno zakazan!*\n\n"
            f"📅 {data['datum']} u {data['vreme']}\n"
            f"🐾 {data['usluga']}\n"
            f"👤 {data['ime']}\n"
            f"📱 {data['telefon']}\n\n"
            f"✅ U slučaju promene ili otkazivanja termina, molimo pozovite nas na broj:\n"
            f"📞 069/188-3389"
        )
    else:
        await message.answer("❌ Greška pri zakazivanju. Pokušajte ponovo sa /zakazi")

    await state.clear()

# ==================== OTKAZIVANJE IZ PROCESA ====================
@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Zakazivanje je otkazano.\n\n"
        "Ako želite da zakažete novi termin, kliknite dugme ispod.",
        reply_markup=welcome_keyboard()
    )
    await callback.answer("Zakazivanje otkazano.")