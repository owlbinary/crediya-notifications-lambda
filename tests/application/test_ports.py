import pytest
from app.application.ports import EmailNotificationPort

class ConcreteEmailNotificationPort(EmailNotificationPort):
    """Concrete implementation for testing"""
    def __init__(self):
        self.sent_messages = []
    
    def send_email_notification(self, message_body: str):
        self.sent_messages.append(message_body)
        return True

def test_email_notification_port_interface():
    """Test that EmailNotificationPort can be implemented"""
    port = ConcreteEmailNotificationPort()
    
    result = port.send_email_notification("test message")
    assert result is True
    assert len(port.sent_messages) == 1
    assert port.sent_messages[0] == "test message"

def test_email_notification_port_cannot_be_instantiated():
    """Test that abstract base class cannot be instantiated directly"""
    with pytest.raises(TypeError):
        EmailNotificationPort()
