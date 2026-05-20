from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from bot.keyboards import welcome_keyboard, service_keyboard
from bot.states import BookingStates
from core.logger import logger

router = Router()


# ==================== START KOMANDA ====================
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🐾 *Dobrodošli u Grooming Salon Bot!* 🐶\n\n"
        "Profesionalno zakazivanje termina za vašeg ljubimca.",
        reply_markup=welcome_keyboard()
    )


# ==================== BILO KOJA PORUKA (ako nije u procesu) ====================
@router.message(StateFilter(None))
async def any_message(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🐾 *Zdravo!* Dobrodošli nazad.\n\n"
        "👉 Kliknite dugme ispod da zakažete termin.",
        reply_markup=welcome_keyboard()
    )


# ==================== KLIK NA DUGME "ZAKAZI TERMIN" ====================
@router.callback_query(F.data == "start_booking")
async def callback_start_booking(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingStates.waiting_for_service)
    
    # Bolje koristimo edit_text da ne pravi novu poruku
    await callback.message.edit_text(
        "💇‍♀️ *Izaberite uslugu:*",
        reply_markup=service_keyboard()
    )
    await callback.answer()


# ==================== DIREKTNA KOMANDA /ZAKAZI ====================
@router.message(Command("zakazi"))
async def cmd_zakazi(message: Message, state: FSMContext):
    await state.set_state(BookingStates.waiting_for_service)
    await message.answer(
        "💇‍♀️ *Izaberite uslugu:*",
        reply_markup=service_keyboard()
    )
    logger.info(f"Nova rezervacija započeta: {message.chat.id}")

# ==================== OTKAZIVANJE ZAKAZIVANJA ====================
@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Zakazivanje je otkazano.\n\n"
        "Ako želite da zakažete novi termin, kliknite dugme ispod.",
        reply_markup=welcome_keyboard()
    )
    await callback.answer("Zakazivanje otkazano.")