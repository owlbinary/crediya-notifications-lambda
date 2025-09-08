from abc import ABC, abstractmethod

class EmailNotificationPort(ABC):
    @abstractmethod
    def send_email_notification(self, message_body: str):
        pass
