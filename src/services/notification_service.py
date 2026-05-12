from abc import ABC, abstractmethod
class INotificationService(ABC):
    @abstractmethod
    async def send_password_reset_link(self, email: str, reset_link: str) -> None:
        """
        Envia una notificacion de recuperacion de contrasena al usuario.
        """
        raise NotImplementedError
class ConsoleNotificationService(INotificationService):
    async def send_password_reset_link(self, email: str, reset_link: str) -> None:
        """
        Implementacion temporal para el sprint actual:
        solo imprime el enlace en consola para pruebas de frontend.
        """
        print(f"[PasswordRecovery] email={email} reset_link={reset_link}")