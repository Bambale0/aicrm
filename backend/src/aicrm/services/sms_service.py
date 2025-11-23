"""
Сервис для отправки SMS сообщений
"""
import logging
from typing import Dict, Any
import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """Сервис для отправки SMS через внешние провайдеры"""

    def __init__(self):
        self.provider = settings.sms_provider or "smsc"  # smsc, twilio, smsru
        self.api_key = settings.sms_api_key
        self.login = settings.sms_login
        self.password = settings.sms_password
        self.sender = settings.sms_sender or "AICRM"

        # Настройки провайдеров
        self.providers = {
            "smsc": {
                "url": "https://smsc.ru/sys/send.php",
                "params": {
                    "login": self.login,
                    "psw": self.password,
                    "sender": self.sender,
                    "charset": "utf-8",
                    "fmt": 3  # JSON ответ
                }
            },
            "twilio": {
                "url": "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                "auth": (settings.twilio_account_sid, settings.twilio_auth_token),
                "from": settings.twilio_phone_number
            },
            "smsru": {
                "url": "https://sms.ru/sms/send",
                "params": {
                    "api_id": self.api_key,
                    "from": self.sender,
                    "json": 1
                }
            }
        }

    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """
        Отправка SMS сообщения

        Args:
            phone: Номер телефона получателя
            message: Текст сообщения

        Returns:
            Dict с результатом отправки
        """
        try:
            # Нормализация номера телефона
            phone = self._normalize_phone(phone)

            # Выбор провайдера и отправка
            if self.provider == "smsc":
                result = await self._send_via_smsc(phone, message)
            elif self.provider == "twilio":
                result = await self._send_via_twilio(phone, message)
            elif self.provider == "smsru":
                result = await self._send_via_smsru(phone, message)
            else:
                raise ValueError(f"Unsupported SMS provider: {self.provider}")

            logger.info(f"SMS sent to {phone}: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return {
                "success": False,
                "error": str(e),
                "phone": phone,
                "message": message[:50] + "..." if len(message) > 50 else message
            }

    async def _send_via_smsc(self, phone: str, message: str) -> Dict[str, Any]:
        """Отправка через SMSC.ru"""
        provider_config = self.providers["smsc"]

        params = provider_config["params"].copy()
        params.update({
            "phones": phone,
            "mes": message
        })

        async with httpx.AsyncClient() as client:
            response = await client.get(provider_config["url"], params=params)
            data = response.json()

            if data.get("error"):
                return {
                    "success": False,
                    "error": data["error"],
                    "provider": "smsc",
                    "phone": phone
                }

            return {
                "success": True,
                "provider": "smsc",
                "phone": phone,
                "message_id": data.get("id"),
                "cost": data.get("cost"),
                "balance": data.get("balance")
            }

    async def _send_via_twilio(self, phone: str, message: str) -> Dict[str, Any]:
        """Отправка через Twilio"""
        provider_config = self.providers["twilio"]

        url = provider_config["url"].format(account_sid=settings.twilio_account_sid)
        data = {
            "From": provider_config["from"],
            "To": phone,
            "Body": message
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                data=data,
                auth=provider_config["auth"]
            )
            data = response.json()

            if "error_message" in data:
                return {
                    "success": False,
                    "error": data["error_message"],
                    "provider": "twilio",
                    "phone": phone
                }

            return {
                "success": True,
                "provider": "twilio",
                "phone": phone,
                "message_id": data.get("sid"),
                "status": data.get("status")
            }

    async def _send_via_smsru(self, phone: str, message: str) -> Dict[str, Any]:
        """Отправка через SMS.ru"""
        provider_config = self.providers["smsru"]

        params = provider_config["params"].copy()
        params.update({
            "to": phone,
            "text": message
        })

        async with httpx.AsyncClient() as client:
            response = await client.post(provider_config["url"], data=params)
            data = response.json()

            if data.get("status") != "OK":
                return {
                    "success": False,
                    "error": data.get("status_text", "Unknown error"),
                    "provider": "smsru",
                    "phone": phone
                }

            sms_info = data.get("sms", {})
            return {
                "success": True,
                "provider": "smsru",
                "phone": phone,
                "message_id": list(sms_info.keys())[0] if sms_info else None,
                "cost": data.get("cost"),
                "balance": data.get("balance")
            }

    async def get_balance(self) -> Dict[str, Any]:
        """Получение баланса SMS аккаунта"""
        try:
            if self.provider == "smsc":
                return await self._get_balance_smsc()
            elif self.provider == "twilio":
                return await self._get_balance_twilio()
            elif self.provider == "smsru":
                return await self._get_balance_smsru()
            else:
                return {"error": f"Balance check not supported for {self.provider}"}
        except Exception as e:
            logger.error(f"Failed to get SMS balance: {e}")
            return {"error": str(e)}

    async def _get_balance_smsc(self) -> Dict[str, Any]:
        """Получение баланса SMSC"""
        provider_config = self.providers["smsc"]
        params = {
            "login": self.login,
            "psw": self.password,
            "get": "balance",
            "fmt": 3
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(provider_config["url"], params=params)
            data = response.json()

            return {
                "provider": "smsc",
                "balance": data.get("balance"),
                "currency": "RUB"
            }

    async def _get_balance_twilio(self) -> Dict[str, Any]:
        """Получение баланса Twilio"""
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Balance.json"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token)
            )
            data = response.json()

            return {
                "provider": "twilio",
                "balance": data.get("balance"),
                "currency": data.get("currency")
            }

    async def _get_balance_smsru(self) -> Dict[str, Any]:
        """Получение баланса SMS.ru"""
        url = "https://sms.ru/my/balance"

        params = {
            "api_id": self.api_key,
            "json": 1
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()

            return {
                "provider": "smsru",
                "balance": data.get("balance"),
                "currency": "RUB"
            }

    def _normalize_phone(self, phone: str) -> str:
        """Нормализация номера телефона"""
        # Убираем все нецифровые символы
        phone = ''.join(filter(str.isdigit, phone))

        # Добавляем +7 для российских номеров если нет кода страны
        if len(phone) == 10 and phone.startswith(('9', '8')):
            phone = '7' + phone
        elif len(phone) == 11 and phone.startswith('8'):
            phone = '7' + phone[1:]

        return phone

    async def send_bulk_sms(self, recipients: list, message: str) -> Dict[str, Any]:
        """
        Массовая отправка SMS

        Args:
            recipients: Список номеров телефонов
            message: Текст сообщения

        Returns:
            Dict с результатами отправки
        """
        results = []
        total_cost = 0

        for phone in recipients:
            result = await self.send_sms(phone, message)
            results.append(result)
            if result.get("success") and result.get("cost"):
                total_cost += float(result["cost"])

        successful = sum(1 for r in results if r.get("success"))
        failed = len(results) - successful

        return {
            "total_sent": len(results),
            "successful": successful,
            "failed": failed,
            "total_cost": total_cost,
            "results": results
        }


# Глобальный экземпляр сервиса
sms_service = SMSService()
