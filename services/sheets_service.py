import gspread
from google.oauth2.service_account import Credentials
from core.config import settings
from core.logger import logger
from datetime import datetime, timedelta

class SheetsService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sheet = None
        return cls._instance

    async def init(self):
        if self._sheet:
            return
        try:
            creds_dict = {
                "type": "service_account",
                "project_id": "booking-bot-496211",
                "private_key": settings.GOOGLE_PRIVATE_KEY.replace("\\n", "\n"),
                "client_email": settings.GOOGLE_SERVICE_ACCOUNT_EMAIL,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            credentials = Credentials.from_service_account_info(creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
            client = gspread.authorize(credentials)
            self._sheet = client.open_by_key(settings.GOOGLE_SHEET_ID).sheet1
            logger.info("✅ SheetsService uspešno povezan")
        except Exception as e:
            logger.error("❌ Sheets greška", error=str(e))
            raise

    async def get_free_dates(self) -> list[str]:
        await self.init()
        records = self._sheet.get_all_records()
        free_dates = [str(row.get('Datum', '')).strip() for row in records 
                     if str(row.get('Status', '')).strip() in ['', ' ', 'None']]
        return sorted(list(set(free_dates)))

    async def get_free_times(self, date: str) -> list[str]:
        await self.init()
        records = self._sheet.get_all_records()
        return [str(row.get('Vreme', '')).strip() for row in records 
                if str(row.get('Datum', '')).strip() == date and 
                str(row.get('Status', '')).strip() in ['', ' ', 'None']]

    async def reserve_slot(self, date: str, time: str, data: dict):
        await self.init()
        records = self._sheet.get_all_records()
        
        for i, row in enumerate(records):
            if str(row.get('Datum', '')).strip() == date and str(row.get('Vreme', '')).strip() == time:
                row_num = i + 2
                values = [
                    date, time, "Zakazan",
                    data.get('usluga', ''), data.get('ime', ''), 
                    data.get('telefon', ''), data.get('email', ''),
                    data.get('consent', 'Da'), 
                    str(data.get('chat_id', '')),
                    ""   # ReminderSent (kolona J)
                ]
                self._sheet.update(f"A{row_num}:J{row_num}", [values])
                logger.info("✅ Termin zakazan", date=date, time=time)
                return True
        return False

    # === REMINDER METODE ===
    async def get_tomorrows_appointments(self):
        await self.init()
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
        records = self._sheet.get_all_records()
        
        appointments = []
        for i, row in enumerate(records):
            if (str(row.get('Datum', '')).strip() == tomorrow and
                str(row.get('Status', '')).strip() == "Zakazan" and
                str(row.get('WhatsAppConsent', '')).strip().upper() == "DA" and
                str(row.get('ReminderSent', '')).strip() != "Da"):
                
                appointments.append({
                    'datum': tomorrow,
                    'vreme': str(row.get('Vreme', '')).strip(),
                    'ime': str(row.get('Ime', '')).strip(),
                    'telefon': str(row.get('Telefon', '')).strip(),
                    'row_num': i + 2
                })
        return appointments

    async def mark_reminder_sent(self, row_num: int):
        await self.init()
        self._sheet.update_cell(row_num, 10, "Da")   # Kolona J (10. kolona)
        logger.info("Reminder označen kao poslat", row=row_num)