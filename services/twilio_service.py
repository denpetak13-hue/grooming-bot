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
            
            clean_phone = phone.replace(" ", "").replace("-", "")
            if clean_phone.startswith("0"):
                clean_phone = "+381" + clean_phone[1:]
            elif not clean_phone.startswith("+"):
                clean_phone = "+381" + clean_phone

            message = (
                f"🐾 *Podsetnik za grooming*\n\n"
                f"Poštovani {name},\n\n"
                f"Vaš termin je **sutra**:\n"
                f"📅 {date} u {time}\n\n"
                f"Vidimo se! 🐶\n"
                f"{settings.BUSINESS_NAME}"
            )

            client.messages.create(
                from_=f"whatsapp:{settings.TWILIO_PHONE_NUMBER}",
                to=f"whatsapp:{clean_phone}",
                body=message
            )

            logger.info("WhatsApp reminder poslat", phone=clean_phone, date=date)
            return True

        except Exception as e:
            logger.error("Greška pri slanju WhatsApp reminder-a", error=str(e), phone=phone)
            return False