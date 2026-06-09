import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from core.logger import logger
from services.sheets_service import SheetsService

# ==================== CONFIG ====================

BELGRADE_TZ = ZoneInfo("Europe/Belgrade")

HEADERS = [
    "Datum",
    "Vreme",
    "Status",
    "Usluga",
    "Ime",
    "Telefon",
    "Email",
    "WhatsAppConsent",
    "ChatID",
    "ReminderSent",
]

WORKING_DAYS = [0, 1, 2, 3, 4, 5]  # Pon-Sub

START_HOUR = 9
END_HOUR = 17

DAYS_AHEAD = 30

# ==================== DATE HELPERS ====================


def _normalize_date(value: str) -> str:
    """Normalize any supported date format to YYYY-MM-DD for key comparison."""
    value = str(value or "").strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return value


def _parse_date(value: str):
    """Parse DD.MM.YYYY or YYYY-MM-DD to a date object, or None on failure."""
    value = str(value or "").strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _format_date(value: datetime) -> str:
    return value.strftime("%d.%m.%Y")


# ==================== GENERATOR ====================


async def generateSlots():
    """Generate free appointment slots for the next DAYS_AHEAD days.

    Raises on any unrecoverable error so callers can decide whether to
    crash or continue (e.g. run.py catches and keeps the bot running).
    """
    logger.info("Pokretanje generateSlots...")

    sheets = SheetsService()
    await sheets.init()
    sheet = sheets.sheet

    logger.info("Sheet povezan", title=sheet.title)

    # ---- Ensure headers ------------------------------------------------
    # Phase 3: wrap synchronous gspread calls with asyncio.to_thread()
    first_row = await asyncio.to_thread(sheet.row_values, 1)

    if not first_row:
        await asyncio.to_thread(sheet.append_row, HEADERS)
        logger.info("Dodata zaglavlja u prazan Sheet.")
    elif first_row[: len(HEADERS)] != HEADERS:
        # Do NOT auto-insert (EC-06): inserting a row shifts all indices and
        # corrupts concurrent reservations. Only warn so the operator can fix
        # the sheet manually.
        logger.warning(
            "Zaglavlja Sheet-a se razlikuju od ocekivanih - proveri tabelu rucno.",
            found=first_row[: len(HEADERS)],
            expected=HEADERS,
        )

    # ---- Load all existing rows ----------------------------------------
    rows = await asyncio.to_thread(sheet.get_all_records)

    # ---- Phase 5: Delete past slobodne termine -------------------------
    today_date = datetime.now(tz=BELGRADE_TZ).date()
    rows_to_delete = []

    for i, row in enumerate(rows):
        parsed = _parse_date(row.get("Datum"))
        if (
            parsed is not None
            and parsed < today_date
            and str(row.get("Status", "")).strip().lower() == "slobodno"
        ):
            rows_to_delete.append(i + 2)  # +2: 1-based index + header row

    if rows_to_delete:
        logger.info("Brisanje starih slobodnih termina...", count=len(rows_to_delete))
        # Delete bottom-to-top so row indices remain valid after each deletion
        for row_num in reversed(rows_to_delete):
            await asyncio.to_thread(sheet.delete_rows, row_num)
        logger.info("Stari slobodni termini obrisani.")
        # Reload after deletion so existing_slots set is accurate
        rows = await asyncio.to_thread(sheet.get_all_records)

    # ---- Build set of already-present slots ----------------------------
    existing_slots: set[str] = set()
    for row in rows:
        key = f"{_normalize_date(row.get('Datum'))}_{str(row.get('Vreme', '')).strip()}"
        existing_slots.add(key)

    # ---- Generate new slots -------------------------------------------
    # Phase 2: use Belgrade-aware datetime so dates are correct on Render (UTC)
    today = datetime.now(tz=BELGRADE_TZ)
    new_rows: list[list] = []

    for day_offset in range(DAYS_AHEAD):
        current_day = today + timedelta(days=day_offset)

        if current_day.weekday() not in WORKING_DAYS:
            continue

        formatted_date = _format_date(current_day)
        normalized_date = _normalize_date(formatted_date)

        for hour in range(START_HOUR, END_HOUR):
            formatted_time = f"{hour:02d}:00"
            slot_key = f"{normalized_date}_{formatted_time}"

            if slot_key in existing_slots:
                continue

            new_rows.append([
                formatted_date,  # Datum
                formatted_time,  # Vreme
                "slobodno",      # Status
                "",              # Usluga
                "",              # Ime
                "",              # Telefon
                "",              # Email
                "",              # WhatsAppConsent
                "",              # ChatID
                "",              # ReminderSent
            ])

    if new_rows:
        # Phase 3: one batch API call instead of N individual append_row() calls.
        # Reduces 240 HTTP requests to 1, eliminating event-loop blocking time
        # and Google Sheets API quota exhaustion.
        await asyncio.to_thread(sheet.append_rows, new_rows)
        logger.info("Termini generisani.", count=len(new_rows))
    else:
        logger.info("Svi termini vec postoje, nista nije dodato.")


if __name__ == "__main__":
    asyncio.run(generateSlots())
