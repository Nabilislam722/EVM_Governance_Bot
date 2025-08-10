"""
Logging configuration for the Discord Governance Bot.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

class Logger:
    """Logger configuration and setup."""
    
    def __init__(self, log_level=logging.INFO):
        self.log_level = log_level
        self.log_dir = Path("../data/logs")
        self.log_dir.mkdir(exist_ok=True)
    
    def setup_logging(self):
        """Set up logging configuration."""
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Get root logger
        logger = logging.getLogger()
        logger.setLevel(self.log_level)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = self.log_dir / "governance_bot.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Error file handler
        error_log_file = self.log_dir / "errors.log"
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        # Suppress some noisy loggers
        logging.getLogger('discord').setLevel(logging.WARNING)
        logging.getLogger('websockets').setLevel(logging.WARNING)
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        
        logger.info("Logging system initialized")
        return logger
    
    def get_logger(self, name):
        """Get a named logger."""
        return logging.getLogger(name)
    
    def log_error(self, message, exception=None):
        """Log an error with optional exception details."""
        logger = logging.getLogger()
        if exception:
            logger.exception(f"{message}: {exception}")
        else:
            logger.error(message)
    
    def log_info(self, message):
        """Log an info message."""
        logger = logging.getLogger()
        logger.info(message)
    
    def log_warning(self, message):
        """Log a warning message."""
        logger = logging.getLogger()
        logger.warning(message)
