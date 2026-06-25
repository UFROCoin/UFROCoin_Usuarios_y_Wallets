from abc import ABC, abstractmethod
import asyncio
import logging
import resend
from src.core.config import settings

logger = logging.getLogger(__name__)


class NotificationDeliveryError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class NotificationProviderNotConfiguredError(NotificationDeliveryError):
    def __init__(self) -> None:
        super().__init__("provider_not_configured")


class NotificationTimeoutError(NotificationDeliveryError):
    def __init__(self) -> None:
        super().__init__("timeout")


class NotificationProviderError(NotificationDeliveryError):
    def __init__(self) -> None:
        super().__init__("provider_error")

class INotificationService(ABC):
    @abstractmethod
    async def send_password_reset_link(self, email: str, reset_link: str) -> None:
        """
        Envia una notificacion de recuperacion de contrasena al usuario.
        """
        raise NotImplementedError

class NotificationService(INotificationService):
    async def send_password_reset_link(self, email: str, reset_link: str) -> None:
        if not settings.resend_api_key:
            logger.warning("Proveedor de correo no configurado; no se puede enviar correo de recuperacion.")
            raise NotificationProviderNotConfiguredError()

        resend.api_key = settings.resend_api_key
        html_body = (
            "<p>Recibimos una solicitud para restablecer tu contrasena.</p>"
            f'<p>Haz clic en el siguiente enlace: <a href="{reset_link}">{reset_link}</a></p>'
            "<p>Si no solicitaste este cambio, puedes ignorar este mensaje.</p>"
        )

        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    resend.Emails.send,
                    {
                        "from": settings.resend_from_email,
                        "to": email,
                        "subject": settings.resend_reset_subject,
                        "html": html_body,
                    },
                ),
                timeout=settings.resend_timeout_seconds,
            )
            logger.info(f"Correo de recuperación enviado exitosamente a {email} vía Resend.")
        except asyncio.TimeoutError as exc:
            logger.exception(
                "Timeout al enviar correo de recuperacion via proveedor para email=%s",
                email,
            )
            raise NotificationTimeoutError() from exc
        except Exception:
            logger.exception(
                "No fue posible enviar correo de recuperacion via proveedor para email=%s",
                email,
            )
            raise NotificationProviderError()


def get_default_notification_service() -> INotificationService:
    return NotificationService()
