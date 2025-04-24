"""
Tests for utility functions (logger, error handler).
"""
import unittest
from unittest.mock import patch, MagicMock, call
import os
import sys
import logging
import json
import tempfile

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.logger import setup_logger, get_logger
from src.utils.error_handler import handle_error, handle_api_error

class TestLogger(unittest.TestCase):
    """Test cases for logger utility functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for logs
        self.temp_dir = tempfile.mkdtemp()
        self.env_patcher = patch.dict('os.environ', {'LOG_DIR': self.temp_dir})
        self.env_patcher.start()
        
        # Clear root logger handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
        
        # Clear all loggers created during tests
        for name in logging.Logger.manager.loggerDict.keys():
            logger = logging.getLogger(name)
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
    
    def test_setup_logger(self):
        """Test logger setup function."""
        # Set up logger
        logger = setup_logger("test_logger", "DEBUG")
        
        # Verify logger configuration
        self.assertEqual(logger.name, "test_logger")
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertEqual(len(logger.handlers), 2)  # Console and file handler
        
        # Check handlers
        console_handler = None
        file_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                console_handler = handler
            elif isinstance(handler, logging.FileHandler):
                file_handler = handler
        
        self.assertIsNotNone(console_handler, "Console handler not found")
        self.assertIsNotNone(file_handler, "File handler not found")
        
        # Verify log file path
        expected_log_file = os.path.join(self.temp_dir, "test_logger.log")
        self.assertEqual(file_handler.baseFilename, expected_log_file)
    
    def test_setup_logger_default_level(self):
        """Test logger setup with default log level."""
        # Set up logger without specifying level
        logger = setup_logger("default_level_logger")
        
        # Verify logger level is INFO (default)
        self.assertEqual(logger.level, logging.INFO)
    
    def test_get_logger_new(self):
        """Test get_logger with a new logger name."""
        # Get a new logger
        logger = get_logger("new_logger")
        
        # Verify logger configuration
        self.assertEqual(logger.name, "new_logger")
        self.assertTrue(len(logger.handlers) > 0)
    
    def test_get_logger_existing(self):
        """Test get_logger with an existing logger name."""
        # Create logger first
        setup_logger("existing_logger", "INFO")
        
        # Mock setup_logger to verify it's not called again
        with patch('src.utils.logger.setup_logger') as mock_setup:
            # Get the existing logger
            logger = get_logger("existing_logger")
            
            # Verify setup_logger not called
            mock_setup.assert_not_called()
            
            # Verify correct logger returned
            self.assertEqual(logger.name, "existing_logger")
    
    @patch('logging.Logger.debug')
    @patch('logging.Logger.info')
    @patch('logging.Logger.warning')
    @patch('logging.Logger.error')
    @patch('logging.Logger.critical')
    def test_logger_levels(self, mock_critical, mock_error, mock_warning, 
                           mock_info, mock_debug):
        """Test all logger levels."""
        # Set up logger with DEBUG level
        logger = setup_logger("level_test", "DEBUG")
        
        # Log messages at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Verify all messages were logged
        mock_debug.assert_called_once_with("Debug message")
        mock_info.assert_called_once_with("Info message")
        mock_warning.assert_called_once_with("Warning message")
        mock_error.assert_called_once_with("Error message")
        mock_critical.assert_called_once_with("Critical message")
    
    def test_logger_file_output(self):
        """Test that log messages are written to file."""
        # Set up logger
        logger_name = "file_test"
        logger = setup_logger(logger_name, "INFO")
        
        # Log a test message
        test_message = "Test log message for file output"
        logger.info(test_message)
        
        # Check log file content
        log_file = os.path.join(self.temp_dir, f"{logger_name}.log")
        with open(log_file, 'r') as f:
            log_content = f.read()
            
        # Verify message is in log file
        self.assertIn(test_message, log_content)
        self.assertIn(logger_name, log_content)
        self.assertIn("INFO", log_content)


class TestErrorHandler(unittest.TestCase):
    """Test cases for error handler utility functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock logger
        self.logger_patcher = patch('logging.getLogger')
        self.mock_logger = MagicMock()
        mock_getLogger = self.logger_patcher.start()
        mock_getLogger.return_value = self.mock_logger
    
    def tearDown(self):
        """Clean up after tests."""
        self.logger_patcher.stop()
    
    def test_handle_error_basic(self):
        """Test basic error handling."""
        # Create a test exception
        error = ValueError("Test error message")
        
        # Handle the error
        result = handle_error(error)
        
        # Verify logging calls
        self.mock_logger.error.assert_called()
        self.mock_logger.debug.assert_called()
        
        # Verify result structure
        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "ValueError")
        self.assertIn("unexpected value", result["message"].lower())
        self.assertEqual(result["sources"], [])
    
    def test_handle_error_with_query(self):
        """Test error handling with query context."""
        # Create a test exception
        error = ConnectionError("Failed to connect")
        query = "test research query"
        
        # Handle the error
        result = handle_error(error, query)
        
        # Verify result includes query context
        self.assertEqual(result["query"], query)
        self.assertIn(query, result["message"])
        self.assertIn("network issues", result["message"].lower())
    
    def test_handle_error_api_key_error(self):
        """Test handling of API key errors."""
        # Create a test exception with API key error
        error = Exception("Invalid API_KEY provided")
        
        # Handle the error
        result = handle_error(error)
        
        # Verify appropriate message
        self.assertIn("authentication issue", result["message"].lower())
        self.assertIn("API key", result["message"].lower())
    
    def test_handle_error_permission_error(self):
        """Test handling of permission errors."""
        # Create a test exception with permission error
        error = Exception("Access denied to resource")
        
        # Handle the error
        result = handle_error(error)
        
        # Verify appropriate message
        self.assertIn("permission", result["message"].lower())
    
    def test_handle_api_error(self):
        """Test API-specific error handling."""
        # Handle API error
        api_name = "TestAPI"
        status_code = 429
        response_text = "Rate limit exceeded"
        
        result = handle_api_error(api_name, status_code, response_text)
        
        # Verify logging
        self.mock_logger.error.assert_called_once()
        
        # Verify result
        self.assertFalse(result["success"])
        self.assertEqual(result["error_type"], "APIError")
        self.assertEqual(result["api_name"], api_name)
        self.assertEqual(result["status_code"], status_code)
        self.assertIn("rate limit exceeded", result["message"].lower())
    
    def test_handle_api_error_custom_status(self):
        """Test API error handling with custom status code."""
        # Handle API error with unusual status code
        result = handle_api_error("CustomAPI", 418, "I'm a teapot")
        
        # Verify generic message for unknown status
        self.assertIn("Error communicating with CustomAPI", result["message"])
        self.assertIn("HTTP 418", result["message"])
    
    def test_error_type_mapping(self):
        """Test mapping of error types to user-friendly messages."""
        error_types = [
            (ConnectionError("Connection failed"), "network issues"),
            (TimeoutError("Request timed out"), "too long to respond"),
            (json.JSONDecodeError("Invalid JSON", "", 0), "processing some of the data"),
            (ValueError("Invalid value"), "unexpected value"),
            (KeyError("missing_key"), "data was missing"),
            (AttributeError("No such attribute"), "issue with one of the components"),
            (Exception("LLMProviderError: Model not found"), "AI service")
        ]
        
        for error, expected_phrase in error_types:
            result = handle_error(error)
            self.assertIn(expected_phrase, result["message"].lower())

if __name__ == '__main__':
    unittest.main()