import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    """
    Configure structured JSON logging for the application.
    """
    logger = logging.getLogger()
    
    # Remove existing handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)
        
    handler = logging.StreamHandler(sys.stdout)
    
    # Custom format with common fields
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"}
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Set default level
    logger.setLevel(logging.INFO)
    
    # Silence noisy libraries
    logging.getLogger("uvicorn.access").disabled = True # We can enable this if we want access logs
