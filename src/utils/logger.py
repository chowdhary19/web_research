"""
Logger - Utility for application logging.
"""
import os
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = None, log_level: str = None) -> logging.Logger:
    """
    Set up and configure a logger.
    
    Args:
        name: Logger name (defaults to root logger if None)
        log_level: Logging level (defaults to value from .env or INFO)
        
    Returns:
        Configured logger instance
    """
    # Use root logger if name not specified
    logger = logging.getLogger(name)
    
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Determine log level
    if not log_level:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    numeric_level = getattr(logging, log_level, logging.INFO)
    logger.setLevel(numeric_level)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log directory exists
    log_dir = os.getenv("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{name if name else 'app'}.log")
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger by name.
    
    Args:
        name: Name of the logger
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # If this logger hasn't been configured yet, set it up
    if not logger.handlers:
        return setup_logger(name)
        
    return logger