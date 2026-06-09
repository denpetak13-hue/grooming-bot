import asyncio

from twilio.rest import Client
from core.config import settings
from core.logger import logger


class TwilioService:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        return cls._client

    @classmethod
    async def send_whatsapp_reminder(cls, phone: str, name: str, date: str, time: str):
        try:
            client = cls.get_client()

            clean_phone = phone.replace("whatsapp:", "").replace(" ", "").replace("-", "")
            if clean_phone.startswith("0"):
                clean_phone = "+381" + clean_phone[1:]
            elif not clean_phone.startswith("+"):
                clean_phone = "+381" + clean_phone

            from_phone = settings.TWILIO_PHONE_NUMBER.strip()
            if not from_phone.startswith("whatsapp:"):
                from_phone = f"whatsapp:{from_phone}"

            body = (
                f"🐾 *Podsetnik za grooming*\n\n"
                f"Poštovani {name},\n\n"
                f"Vaš termin je **sutra**:\n"
                f"📅 {date} u {time}\n\n"
                f"Vidimo se! 🐶\n"
                f"{settings.BUSINESS_NAME}"
            )

            # Phase 3: Twilio SDK uses synchronous requests - run in thread
            # so it does not block the asyncio event loop.
            await asyncio.to_thread(
                client.messages.create,
                from_=from_phone,
                to=f"whatsapp:{clean_phone}",
                body=body,
            )

            logger.info("WhatsApp reminder poslat", phone=clean_phone, date=date)
            return True

        except Exception as e:
            logger.error("Greska pri slanju WhatsApp remindera", error=str(e), phone=phone)
            return False