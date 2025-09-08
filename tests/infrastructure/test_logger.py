from app.infrastructure.logger import get_logger

def test_get_logger_returns_logger():
    logger = get_logger()
    assert logger is not None
    assert hasattr(logger, 'info')
    assert hasattr(logger, 'error')
    assert hasattr(logger, 'warning')

def test_get_logger_multiple_handlers():
    logger1 = get_logger()
    logger2 = get_logger()
    assert logger1 is logger2
