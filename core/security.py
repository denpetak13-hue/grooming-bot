import asyncio
from collections import defaultdict
import time
from core.logger import logger

class SecurityManager:
    _lock = asyncio.Lock()
    _user_rates = defaultdict(list)  # chat_id -> list of timestamps
    
    @staticmethod
    async def acquire_slot_lock():
        """Zaključava slot prilikom rezervacije da spreči double booking"""
        await SecurityManager._lock.acquire()
        logger.debug("Slot lock acquired")

    @staticmethod
    def release_slot_lock():
        if SecurityManager._lock.locked():
            SecurityManager._lock.release()
            logger.debug("Slot lock released")

    @staticmethod
    def check_rate_limit(chat_id: int, max_requests: int = 8, time_window: int = 60) -> bool:
        """Rate limiting - max 8 akcija po minuti po korisniku"""
        now = time.time()
        # Čistimo stare zapise
        SecurityManager._user_rates[chat_id] = [
            ts for ts in SecurityManager._user_rates[chat_id] if now - ts < time_window
        ]
        
        if len(SecurityManager._user_rates[chat_id]) >= max_requests:
            logger.warning("Rate limit reached", chat_id=chat_id)
            return False
        
        SecurityManager._user_rates[chat_id].append(now)
        return True

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Jednostavna validacija srpskog broja"""
        clean = phone.replace(" ", "").replace("-", "").replace("+", "")
        if clean.startswith("0"):
            clean = "381" + clean[1:]
        return len(clean) >= 9 and clean.isdigit()