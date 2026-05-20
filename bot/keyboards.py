from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def welcome_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗓️ Zakazi termin", callback_data="start_booking")]
    ])

def service_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✂️ Šišanje psa/mačke", callback_data="service_Sisanje")],
        [InlineKeyboardButton(text="🛁 Kupanje + češljanje", callback_data="service_Kupanje")],
        [InlineKeyboardButton(text="🐾 Kompletan tretman", callback_data="service_Komplet tretman")],
        [InlineKeyboardButton(text="❌ Otkazi zakazivanje", callback_data="cancel_booking")]
    ])

def date_keyboard(dates: list):
    keyboard = [[InlineKeyboardButton(text=date, callback_data=f"date_{date}")] for date in dates]
    keyboard.append([InlineKeyboardButton(text="❌ Otkazi zakazivanje", callback_data="cancel_booking")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def time_keyboard(times: list):
    keyboard = [[InlineKeyboardButton(text=time, callback_data=f"time_{time}")] for time in times]
    keyboard.append([InlineKeyboardButton(text="❌ Otkazi zakazivanje", callback_data="cancel_booking")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def consent_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Da, želim", callback_data="consent_yes")],
        [InlineKeyboardButton(text="❌ Ne, hvala", callback_data="consent_no")],
        [InlineKeyboardButton(text="❌ Otkazi zakazivanje", callback_data="cancel_booking")]
    ])