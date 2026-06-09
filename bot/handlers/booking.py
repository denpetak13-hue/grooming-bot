from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards import consent_keyboard, welcome_keyboard
from bot.states import BookingStates
from services.sheets_service import SheetsService
from core.logger import logger
from core.security import SecurityManager

router = Router()
sheets = SheetsService()


@router.message(BookingStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(ime=message.text.strip())
    await state.set_state(BookingStates.waiting_for_phone)
    await message.answer("📱 *Unesite broj telefona:*")


@router.message(BookingStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()

    if not SecurityManager.validate_phone(phone):
        await message.answer(
            "❌ Broj telefona nije ispravan. Unesite broj ponovo, npr. 0691883389."
        )
        return

    await state.update_data(telefon=phone)
    await state.set_state(BookingStates.waiting_for_consent)
    await message.answer(
        "🔔 *Želite li WhatsApp podsetnik dan pre termina?*",
        reply_markup=consent_keyboard(),
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

    # EC-02: FSM state is stored in MemoryStorage and is lost on restart.
    # If datum or vreme are missing, the session expired; restart the flow.
    if not data.get("datum") or not data.get("vreme"):
        await message.answer(
            "❌ Sesija je istekla (bot je možda restartovan).\n\n"
            "Molimo počnite ponovo sa /zakazi"
        )
        await state.clear()
        return

    email = message.text.strip()

    if email == "/":
        email = ""

    if email and ("@" not in email or "." not in email.split("@")[-1]):
        await message.answer(
            "❌ Email nije ispravan. Unesite email ponovo ili napišite / ako nemate."
        )
        return

    try:
        success = await sheets.reserve_slot(
            data.get("datum"),
            data.get("vreme"),
            {**data, "email": email, "chat_id": message.chat.id},
        )
    except Exception as e:
        logger.error("Tehnicka greska pri rezervaciji", error=str(e))
        await message.answer(
            "❌ Tehnička greška pri zakazivanju. Molimo pokušajte ponovo sa /zakazi"
        )
        await state.clear()
        return

    if success is True:
        await message.answer(
            f"🎉 *Termin uspešno zakazan!*\n\n"
            f"📅 {data['datum']} u {data['vreme']}\n"
            f"🐾 {data['usluga']}\n"
            f"👤 {data['ime']}\n"
            f"📱 {data['telefon']}\n\n"
            f"✅ U slučaju promene ili otkazivanja termina, molimo pozovite nas na broj:\n"
            f"📞 069/188-3389"
        )
    elif success == "taken":
        await message.answer(
            "❌ Ovaj termin je upravo rezervisan od strane drugog korisnika.\n\n"
            "Molimo izaberite drugi termin sa /zakazi"
        )
    else:
        await message.answer(
            "❌ Termin nije pronađen. Molimo pokušajte ponovo sa /zakazi"
        )

    await state.clear()

# Phase 6 / RC-06: The cancel_booking handler that was here is dead code.
# commands_router is registered first in run.py and always wins for
# F.data == "cancel_booking". The duplicate handler is removed.
