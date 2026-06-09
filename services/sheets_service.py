import asyncio
import gspread
from google.oauth2.service_account import Credentials
from zoneinfo import ZoneInfo

from core.config import settings
from core.logger import logger
from core.security import SecurityManager
from datetime import datetime, timedelta

BELGRADE_TZ = ZoneInfo("Europe/Belgrade")


def _parse_date(value: str):
    """Parse DD.MM.YYYY or YYYY-MM-DD to a date object, or None on failure."""
    value = str(value or "").strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


class SheetsService:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sheet = None
        return cls._instance

    # ------------------------------------------------------------------ init

    def _force_reinit(self):
        """Reset connection state so the next init() call reconnects.

        Call this in every except block before returning so a transient API
        error does not permanently poison the singleton connection.
        """
        self._sheet = None

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

            credentials = Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/spreadsheets"],
            )

            # Phase 3: run synchronous gspread network I/O in a thread so it
            # does not block the asyncio event loop.
            # EC-08: use get_worksheet_by_id(0) instead of .sheet1 so renaming
            # the tab in Google Sheets does not break the connection.
            def _connect():
                client = gspread.authorize(credentials)
                return client.open_by_key(settings.GOOGLE_SHEET_ID).get_worksheet_by_id(0)

            self._sheet = await asyncio.to_thread(_connect)

            logger.info("SheetsService uspesno povezan")

        except Exception as e:
            logger.error("Sheets greska pri inicijalizaciji", error=str(e))
            raise

    @property
    def sheet(self):
        return self._sheet

    # -------------------------------------------------------------- read ops

    async def get_free_dates(self) -> list[str]:
        await self.init()
        try:
            records = await asyncio.to_thread(self._sheet.get_all_records)

            free_dates = [
                str(row.get("Datum", "")).strip()
                for row in records
                if str(row.get("Status", "")).strip().lower() == "slobodno"
            ]

            return sorted(
                list(set(free_dates)),
                key=lambda v: _parse_date(v) or datetime.max.date(),
            )

        except Exception as e:
            self._force_reinit()
            logger.error("Greska pri dohvatanju slobodnih datuma", error=str(e))
            return []

    async def get_free_times(self, date: str) -> list[str]:
        await self.init()
        try:
            records = await asyncio.to_thread(self._sheet.get_all_records)

            return [
                str(row.get("Vreme", "")).strip()
                for row in records
                if str(row.get("Datum", "")).strip() == date
                and str(row.get("Status", "")).strip().lower() == "slobodno"
            ]

        except Exception as e:
            self._force_reinit()
            logger.error("Greska pri dohvatanju slobodnih vremena", error=str(e))
            return []

    # ------------------------------------------------------------- write ops

    async def reserve_slot(self, date: str, time: str, data: dict):
        """Reserve a slot.

        Returns:
            True      – slot booked successfully.
            "taken"   – slot exists but is no longer free (another user booked it).
            False     – slot not found (date/time not in sheet).

        Raises on API / network errors so callers can distinguish technical
        failures from logical "not found / already taken" cases.
        """
        await self.init()
        await SecurityManager.acquire_slot_lock()

        try:
            records = await asyncio.to_thread(self._sheet.get_all_records)

            for i, row in enumerate(records):
                if (
                    str(row.get("Datum", "")).strip() == date
                    and str(row.get("Vreme", "")).strip() == time
                ):
                    # Found the row; check whether it is still free
                    if str(row.get("Status", "")).strip().lower() != "slobodno":
                        return "taken"

                    row_num = i + 2  # +2: 1-based index + header row

                    values = [
                        date,
                        time,
                        "Zakazan",
                        data.get("usluga", ""),
                        data.get("ime", ""),
                        data.get("telefon", ""),
                        data.get("email", ""),
                        data.get("consent", "Da"),
                        str(data.get("chat_id", "")),
                        "",
                    ]

                    await asyncio.to_thread(
                        self._sheet.update,
                        f"A{row_num}:J{row_num}",
                        [values],
                    )

                    logger.info("Termin zakazan", date=date, time=time)
                    return True

            return False

        except Exception as e:
            self._force_reinit()
            logger.error("Greska pri rezervaciji termina", error=str(e))
            raise

        finally:
            SecurityManager.release_slot_lock()

    # ------------------------------------------------------------ reminders

    async def get_tomorrows_appointments(self):
        await self.init()
        try:
            # Phase 2: use Belgrade-aware datetime so the reminder fires on the
            # correct calendar day regardless of the Render server's UTC clock.
            tomorrow_date = (datetime.now(tz=BELGRADE_TZ) + timedelta(days=1)).date()
            tomorrow = tomorrow_date.strftime("%d.%m.%Y")

            records = await asyncio.to_thread(self._sheet.get_all_records)

            appointments = []
            for i, row in enumerate(records):
                if (
                    _parse_date(row.get("Datum")) == tomorrow_date
                    and str(row.get("Status", "")).strip().lower() == "zakazan"
                    and str(row.get("WhatsAppConsent", "")).strip().upper() == "DA"
                    and str(row.get("ReminderSent", "")).strip().lower() != "da"
                ):
                    appointments.append({
                        "datum": tomorrow,
                        "vreme": str(row.get("Vreme", "")).strip(),
                        "ime": str(row.get("Ime", "")).strip(),
                        "telefon": str(row.get("Telefon", "")).strip(),
                        "row_num": i + 2,
                    })

            return appointments

        except Exception as e:
            self._force_reinit()
            logger.error("Greska pri dohvatanju sutrasnjih termina", error=str(e))
            return []

    async def mark_reminder_sent(self, row_num: int):
        await self.init()
        try:
            # Phase 6 / RC-11: resolve column by header name instead of a
            # hardcoded index so adding columns before ReminderSent does not
            # silently write to the wrong cell.
            headers = await asyncio.to_thread(self._sheet.row_values, 1)
            col = (headers.index("ReminderSent") + 1) if "ReminderSent" in headers else 10

            await asyncio.to_thread(self._sheet.update_cell, row_num, col, "Da")

            logger.info("Reminder oznacen kao poslat", row=row_num)

        except Exception as e:
            self._force_reinit()
            logger.error("Greska pri oznacavanju remindera", error=str(e))
