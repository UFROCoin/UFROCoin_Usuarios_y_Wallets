from abc import ABC, abstractmethod
import logging
import resend
from src.core.config import settings

logger = logging.getLogger(__name__)

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
            logger.warning("RESEND_API_KEY no configurada; se omite envio de correo.")
            return

        resend.api_key = settings.resend_api_key
        html_body = (
            "<p>Recibimos una solicitud para restablecer tu contrasena.</p>"
            f'<p>Haz clic en el siguiente enlace: <a href="{reset_link}">{reset_link}</a></p>'
            "<p>Si no solicitaste este cambio, puedes ignorar este mensaje.</p>"
        )

        try:
            resend.Emails.send(
                {
                    "from": settings.resend_from_email,
                    "to": email,
                    "subject": settings.resend_reset_subject,
                    "html": html_body,
                }
            )
            logger.info(f"Correo de recuperación enviado exitosamente a {email} vía Resend.")
        except Exception:
            logger.exception(
                "No fue posible enviar correo de recuperacion via Resend para email=%s",
                email,
            )


def get_default_notification_service() -> INotificationService:
    return NotificationService()
