import gspread
import os
import sys
import time
from google.oauth2.service_account import Credentials
from core.config import settings
from datetime import datetime, timedelta

print("🔄 Resetujem Google Sheet sa ReminderSent kolonom...")

if os.getenv("CONFIRM_RESET_SHEET") != "yes":
    print("❌ Reset nije potvrđen. Za brisanje tabele pokrenite sa CONFIRM_RESET_SHEET=yes.")
    sys.exit(1)

# Phase 6: Show which sheet will be wiped and give the operator a chance to abort.
print(f"")
print(f"  PAZNJA: Brisem SVE podatke iz Sheet-a sa ID: {settings.GOOGLE_SHEET_ID}")
print(f"  Pritisnite Ctrl+C u roku od 5 sekundi da prekinete...")
print(f"")

try:
    time.sleep(5)
except KeyboardInterrupt:
    print("Operacija prekinuta.")
    sys.exit(0)

creds_dict = {
    "type": "service_account",
    "project_id": "booking-bot-496211",
    "private_key": settings.GOOGLE_PRIVATE_KEY.replace("\\n", "\n"),
    "client_email": settings.GOOGLE_SERVICE_ACCOUNT_EMAIL,
    "token_uri": "https://oauth2.googleapis.com/token",
}

credentials = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
client = gspread.authorize(credentials)
sheet = client.open_by_key(settings.GOOGLE_SHEET_ID).sheet1

sheet.clear()

headers = ["Datum", "Vreme", "Status", "Usluga", "Ime", "Telefon", "Email", 
           "WhatsAppConsent", "ChatID", "ReminderSent", "Napomena"]

sheet.append_row(headers)

start_date = datetime.now().date()
slot_times = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]

print("📅 Generišem termine + ReminderSent kolonu...")

for i in range(14):
    current_date = start_date + timedelta(days=i)
    if current_date.weekday() == 6:  
        continue
    
    date_str = current_date.strftime("%d.%m.%Y")
    
    for time in slot_times:
        sheet.append_row([date_str, time, "slobodno", "", "", "", "", "", "", "", ""])
    
    print(f"✓ Dodato za {date_str} - 8 termina")

print("\n✅ Sheet resetovan sa kolonom ReminderSent!")