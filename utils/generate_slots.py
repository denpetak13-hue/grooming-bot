from services.sheets_service import SheetsService
from datetime import datetime, timedelta

sheets = SheetsService()

WORKING_DAYS = [0, 1, 2, 3, 4, 5]  # Pon-Sub
START_HOUR = 9
END_HOUR = 17

async def generateSlots():

    await sheets.init()

    sheet = sheets.sheet

    rows = sheet.get_all_records()

    existing_slots = set()

    for row in rows:

        key = f"{row.get('Datum')}_{row.get('Vreme')}"

        existing_slots.add(key)

    today = datetime.now()

    # GENERATE NEXT 14 DAYS

    for i in range(14):

        current_day = today + timedelta(days=i)

        # SKIP SUNDAY

        if current_day.weekday() not in WORKING_DAYS:
            continue

        formatted_date = current_day.strftime("%Y-%m-%d")

        for hour in range(START_HOUR, END_HOUR):

            formatted_time = f"{hour:02d}:00"

            slot_key = f"{formatted_date}_{formatted_time}"

            # SKIP DUPLICATES

            if slot_key in existing_slots:
                continue

            # CREATE SLOT

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

            print(
                f"✅ Dodat termin: {formatted_date} {formatted_time}"
            )

    print("🚀 Generisanje termina završeno.")