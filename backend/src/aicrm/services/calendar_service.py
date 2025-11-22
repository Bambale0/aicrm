"""
Сервис для работы с календарями (Google Calendar, Outlook)
"""
import logging
from typing import Dict, Any, List

from ..core.config import settings

logger = logging.getLogger(__name__)


class CalendarService:
    """Сервис для интеграции с календарями"""

    def __init__(self):
        self.google_credentials = {
            "client_id": settings.google_calendar_client_id,
            "client_secret": settings.google_calendar_client_secret,
            "refresh_token": settings.google_calendar_refresh_token
        }
        self.outlook_credentials = {
            "client_id": settings.outlook_client_id,
            "client_secret": settings.outlook_client_secret,
            "tenant_id": settings.outlook_tenant_id
        }
        self.default_provider = settings.calendar_provider or "google"

    async def create_event(
        self,
        title: str,
        description: str = "",
        start_time: str = None,
        end_time: str = None,
        attendees: List[str] = None,
        calendar_id: str = "primary",
        provider: str = None
    ) -> Dict[str, Any]:
        """
        Создание события в календаре

        Args:
            title: Название события
            description: Описание
            start_time: Время начала (ISO format)
            end_time: Время окончания (ISO format)
            attendees: Список email участников
            calendar_id: ID календаря
            provider: Провайдер (google/outlook)

        Returns:
            Dict с результатом создания
        """
        provider = provider or self.default_provider

        try:
            if provider == "google":
                return await self._create_google_event(
                    title, description, start_time, end_time, attendees, calendar_id
                )
            elif provider == "outlook":
                return await self._create_outlook_event(
                    title, description, start_time, end_time, attendees, calendar_id
                )
            else:
                raise ValueError(f"Unsupported calendar provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to create calendar event: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider
            }

    async def update_event(
        self,
        event_id: str,
        updates: Dict[str, Any],
        calendar_id: str = "primary",
        provider: str = None
    ) -> Dict[str, Any]:
        """
        Обновление события в календаре

        Args:
            event_id: ID события
            updates: Поля для обновления
            calendar_id: ID календаря
            provider: Провайдер

        Returns:
            Dict с результатом обновления
        """
        provider = provider or self.default_provider

        try:
            if provider == "google":
                return await self._update_google_event(event_id, updates, calendar_id)
            elif provider == "outlook":
                return await self._update_outlook_event(event_id, updates, calendar_id)
            else:
                raise ValueError(f"Unsupported calendar provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to update calendar event {event_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "event_id": event_id,
                "provider": provider
            }

    async def send_invite(
        self,
        event_id: str,
        attendees: List[str],
        calendar_id: str = "primary",
        provider: str = None
    ) -> Dict[str, Any]:
        """
        Отправка приглашений на событие

        Args:
            event_id: ID события
            attendees: Список email участников
            calendar_id: ID календаря
            provider: Провайдер

        Returns:
            Dict с результатом отправки
        """
        provider = provider or self.default_provider

        try:
            if provider == "google":
                return await self._send_google_invite(event_id, attendees, calendar_id)
            elif provider == "outlook":
                return await self._send_outlook_invite(event_id, attendees, calendar_id)
            else:
                raise ValueError(f"Unsupported calendar provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to send calendar invites for event {event_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "event_id": event_id,
                "provider": provider
            }

    async def _create_google_event(
        self,
        title: str,
        description: str,
        start_time: str,
        end_time: str,
        attendees: List[str],
        calendar_id: str
    ) -> Dict[str, Any]:
        """Создание события в Google Calendar"""
        # Получение access token
        access_token = await self._get_google_access_token()

        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Подготовка данных события
        event_data = {
            "summary": title,
            "description": description,
            "start": {
                "dateTime": start_time,
                "timeZone": "Europe/Moscow"
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "Europe/Moscow"
            }
        }

        if attendees:
            event_data["attendees"] = [{"email": email} for email in attendees]

        # Отправка запроса
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=event_data)

            if response.is_success:
                data = response.json()
                return {
                    "success": True,
                    "provider": "google",
                    "event_id": data.get("id"),
                    "html_link": data.get("htmlLink"),
                    "status": data.get("status")
                }
            else:
                return {
                    "success": False,
                    "provider": "google",
                    "error": response.text,
                    "status_code": response.status_code
                }

    async def _update_google_event(
        self,
        event_id: str,
        updates: Dict[str, Any],
        calendar_id: str
    ) -> Dict[str, Any]:
        """Обновление события в Google Calendar"""
        access_token = await self._get_google_access_token()

        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Отправка запроса
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.patch(url, headers=headers, json=updates)

            if response.is_success:
                data = response.json()
                return {
                    "success": True,
                    "provider": "google",
                    "event_id": data.get("id"),
                    "status": data.get("status")
                }
            else:
                return {
                    "success": False,
                    "provider": "google",
                    "error": response.text,
                    "status_code": response.status_code
                }

    async def _send_google_invite(
        self,
        event_id: str,
        attendees: List[str],
        calendar_id: str
    ) -> Dict[str, Any]:
        """Отправка приглашений в Google Calendar"""
        access_token = await self._get_google_access_token()

        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Получение текущего события
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if not response.is_success:
                return {
                    "success": False,
                    "provider": "google",
                    "error": "Failed to get event",
                    "status_code": response.status_code
                }

            event_data = response.json()

            # Добавление участников
            if "attendees" not in event_data:
                event_data["attendees"] = []

            for email in attendees:
                if not any(att.get("email") == email for att in event_data["attendees"]):
                    event_data["attendees"].append({"email": email})

            # Обновление события
            update_response = await client.put(url, headers=headers, json=event_data)

            return {
                "success": update_response.is_success,
                "provider": "google",
                "event_id": event_id,
                "attendees_added": len(attendees)
            }

    async def _create_outlook_event(
        self,
        title: str,
        description: str,
        start_time: str,
        end_time: str,
        attendees: List[str],
        calendar_id: str
    ) -> Dict[str, Any]:
        """Создание события в Outlook Calendar"""
        # Получение access token
        access_token = await self._get_outlook_access_token()

        url = f"https://graph.microsoft.com/v1.0/me/calendars/{calendar_id}/events"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Подготовка данных события
        event_data = {
            "subject": title,
            "body": {
                "contentType": "HTML",
                "content": description
            },
            "start": {
                "dateTime": start_time,
                "timeZone": "Russian Standard Time"
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "Russian Standard Time"
            }
        }

        if attendees:
            event_data["attendees"] = [
                {"emailAddress": {"address": email}, "type": "required"}
                for email in attendees
            ]

        # Отправка запроса
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=event_data)

            if response.is_success:
                data = response.json()
                return {
                    "success": True,
                    "provider": "outlook",
                    "event_id": data.get("id"),
                    "web_link": data.get("webLink"),
                    "status": "created"
                }
            else:
                return {
                    "success": False,
                    "provider": "outlook",
                    "error": response.text,
                    "status_code": response.status_code
                }

    async def _update_outlook_event(
        self,
        event_id: str,
        updates: Dict[str, Any],
        calendar_id: str
    ) -> Dict[str, Any]:
        """Обновление события в Outlook Calendar"""
        access_token = await self._get_outlook_access_token()

        url = f"https://graph.microsoft.com/v1.0/me/calendars/{calendar_id}/events/{event_id}"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Отправка запроса
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.patch(url, headers=headers, json=updates)

            return {
                "success": response.is_success,
                "provider": "outlook",
                "event_id": event_id,
                "status_code": response.status_code
            }

    async def _send_outlook_invite(
        self,
        event_id: str,
        attendees: List[str],
        calendar_id: str
    ) -> Dict[str, Any]:
        """Отправка приглашений в Outlook Calendar"""
        # В Outlook приглашения отправляются автоматически при добавлении участников
        # Просто обновляем событие с новыми участниками
        updates = {
            "attendees": [
                {"emailAddress": {"address": email}, "type": "required"}
                for email in attendees
            ]
        }

        return await self._update_outlook_event(event_id, updates, calendar_id)

    async def _get_google_access_token(self) -> str:
        """Получение Google access token"""
        # В реальной реализации здесь OAuth2 flow
        # Для демо используем сохраненный refresh token
        if not self.google_credentials.get("refresh_token"):
            raise ValueError("Google refresh token not configured")

        # Обмен refresh token на access token
        token_url = "https://oauth2.googleapis.com/token"

        data = {
            "client_id": self.google_credentials["client_id"],
            "client_secret": self.google_credentials["client_secret"],
            "refresh_token": self.google_credentials["refresh_token"],
            "grant_type": "refresh_token"
        }

        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)

            if response.is_success:
                token_data = response.json()
                return token_data.get("access_token")
            else:
                raise Exception(f"Failed to get Google access token: {response.text}")

    async def _get_outlook_access_token(self) -> str:
        """Получение Outlook access token"""
        # В реальной реализации здесь OAuth2 flow
        # Для демо используем client credentials flow
        if not all(self.outlook_credentials.values()):
            raise ValueError("Outlook credentials not configured")

        token_url = f"https://login.microsoftonline.com/{self.outlook_credentials['tenant_id']}/oauth2/v2.0/token"

        data = {
            "client_id": self.outlook_credentials["client_id"],
            "client_secret": self.outlook_credentials["client_secret"],
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials"
        }

        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)

            if response.is_success:
                token_data = response.json()
                return token_data.get("access_token")
            else:
                raise Exception(f"Failed to get Outlook access token: {response.text}")

    async def list_events(
        self,
        calendar_id: str = "primary",
        start_time: str = None,
        end_time: str = None,
        provider: str = None
    ) -> Dict[str, Any]:
        """
        Получение списка событий календаря

        Args:
            calendar_id: ID календаря
            start_time: Начало периода (ISO format)
            end_time: Конец периода (ISO format)
            provider: Провайдер

        Returns:
            Dict со списком событий
        """
        provider = provider or self.default_provider

        try:
            if provider == "google":
                return await self._list_google_events(calendar_id, start_time, end_time)
            elif provider == "outlook":
                return await self._list_outlook_events(calendar_id, start_time, end_time)
            else:
                raise ValueError(f"Unsupported calendar provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to list calendar events: {e}")
            return {
                "success": False,
                "error": str(e),
                "provider": provider
            }

    async def _list_google_events(
        self,
        calendar_id: str,
        start_time: str,
        end_time: str
    ) -> Dict[str, Any]:
        """Получение событий Google Calendar"""
        access_token = await self._get_google_access_token()

        url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"

        headers = {"Authorization": f"Bearer {access_token}"}
        params = {}

        if start_time:
            params["timeMin"] = start_time
        if end_time:
            params["timeMax"] = end_time

        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)

            if response.is_success:
                data = response.json()
                return {
                    "success": True,
                    "provider": "google",
                    "events": data.get("items", [])
                }
            else:
                return {
                    "success": False,
                    "provider": "google",
                    "error": response.text,
                    "status_code": response.status_code
                }

    async def _list_outlook_events(
        self,
        calendar_id: str,
        start_time: str,
        end_time: str
    ) -> Dict[str, Any]:
        """Получение событий Outlook Calendar"""
        access_token = await self._get_outlook_access_token()

        url = f"https://graph.microsoft.com/v1.0/me/calendars/{calendar_id}/events"

        headers = {"Authorization": f"Bearer {access_token}"}
        params = {}

        if start_time:
            params["startDateTime"] = start_time
        if end_time:
            params["endDateTime"] = end_time

        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)

            if response.is_success:
                data = response.json()
                return {
                    "success": True,
                    "provider": "outlook",
                    "events": data.get("value", [])
                }
            else:
                return {
                    "success": False,
                    "provider": "outlook",
                    "error": response.text,
                    "status_code": response.status_code
                }


# Глобальный экземпляр сервиса
calendar_service = CalendarService()
