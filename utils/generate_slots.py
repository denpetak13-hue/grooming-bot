from datetime import datetime, timedelta

from services.sheets_service import SheetsService

# ==================== CONFIG ====================

WORKING_DAYS = [0, 1, 2, 3, 4, 5]  # Pon-Sub

START_HOUR = 9
END_HOUR = 17

DAYS_AHEAD = 30

# ==================== GENERATOR ====================

async def generateSlots():

    sheets = SheetsService()

    await sheets.init()

    sheet = sheets.sheet

    # ==================== LOAD EXISTING ====================

    rows = sheet.get_all_records()

    existing_slots = set()

    for row in rows:

        key = f"{row.get('Datum')}_{row.get('Vreme')}"

        existing_slots.add(key)

    # ==================== GENERATE ====================

    today = datetime.now()

    generated_count = 0

    for day_offset in range(DAYS_AHEAD):

        current_day = today + timedelta(days=day_offset)

        # Skip Sunday

        if current_day.weekday() not in WORKING_DAYS:
            continue

        formatted_date = current_day.strftime("%Y-%m-%d")

        for hour in range(START_HOUR, END_HOUR):

            formatted_time = f"{hour:02d}:00"

            slot_key = f"{formatted_date}_{formatted_time}"

            # Skip existing

            if slot_key in existing_slots:
                continue

            # ==================== ADD SLOT ====================

            sheet.append_row([
                formatted_date,
                formatted_time,
                "",
                "",
                "",
                "",
                "",
                ""
            ])

            generated_count += 1

            print(
                f"✅ Dodat termin: "
                f"{formatted_date} {formatted_time}"
            )

    print(
        f"🚀 Generisano {generated_count} novih termina."
    )