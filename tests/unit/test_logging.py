"""
Unit tests for logging infrastructure.

Tests structured logging, request ID tracking, and log rotation.
"""

import pytest
import json
import tempfile
from pathlib import Path
from io import StringIO
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

from hansard_tales.utils.logging import (
    configure_logging,
    get_logger,
    generate_request_id,
    set_request_id,
    get_request_id,
    setup_file_logging,
    Logger
)


class TestRequestIDTracking:
    """Test request ID tracking functionality."""
    
    def test_generate_request_id_returns_uuid(self):
        """Test that generate_request_id returns a valid UUID string."""
        request_id = generate_request_id()
        
        assert isinstance(request_id, str)
        assert len(request_id) == 36  # UUID format: 8-4-4-4-12
        assert request_id.count('-') == 4
    
    def test_generate_request_id_unique(self):
        """Test that generate_request_id returns unique IDs."""
        id1 = generate_request_id()
        id2 = generate_request_id()
        
        assert id1 != id2
    
    def test_set_and_get_request_id(self):
        """Test setting and getting request ID."""
        test_id = "test-request-123"
        set_request_id(test_id)
        
        assert get_request_id() == test_id
    
    def test_get_request_id_default_empty(self):
        """Test that get_request_id returns empty string by default."""
        # Reset context
        set_request_id("")
        
        result = get_request_id()
        assert result == ""


class TestLoggingConfiguration:
    """Test logging configuration."""
    
    def test_configure_logging_json_format(self, capsys):
        """Test configuring logging with JSON format."""
        configure_logging(level="INFO", format="json", output="stdout")
        
        logger = get_logger("test")
        logger.info("test_message", key="value")
        
        captured = capsys.readouterr()
        
        # Parse JSON output
        log_line = captured.out.strip()
        log_data = json.loads(log_line)
        
        assert log_data["event"] == "test_message"
        assert log_data["key"] == "value"
        assert "timestamp" in log_data
        assert log_data["level"] == "info"
    
    def test_configure_logging_text_format(self, capsys):
        """Test configuring logging with text format."""
        configure_logging(level="INFO", format="text", output="stdout")
        
        logger = get_logger("test")
        logger.info("test_message", key="value")
        
        captured = capsys.readouterr()
        
        # Text format should contain the message
        assert "test_message" in captured.out
        assert "key" in captured.out
        assert "value" in captured.out
    
    def test_configure_logging_with_request_id(self, capsys):
        """Test that request ID is included in logs."""
        configure_logging(level="INFO", format="json", output="stdout")
        
        test_id = "test-request-456"
        set_request_id(test_id)
        
        logger = get_logger("test")
        logger.info("test_message")
        
        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["request_id"] == test_id


class TestLogger:
    """Test Logger class."""
    
    def setup_method(self):
        """Setup for each test."""
        configure_logging(level="DEBUG", format="json", output="stdout")
    
    def test_logger_debug(self, capsys):
        """Test debug logging."""
        logger = get_logger("test")
        logger.debug("debug_message", detail="test")
        
        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["event"] == "debug_message"
        assert log_data["level"] == "debug"
        assert log_data["detail"] == "test"
    
    def test_logger_info(self, capsys):
        """Test info logging."""
        logger = get_logger("test")
        logger.info("info_message", status="ok")
        
        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["event"] == "info_message"
        assert log_data["level"] == "info"
        assert log_data["status"] == "ok"
    
    def test_logger_warning(self, capsys):
        """Test warning logging."""
        logger = get_logger("test")
        logger.warning("warning_message", code=123)
        
        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["event"] == "warning_message"
        assert log_data["level"] == "warning"
        assert log_data["code"] == 123
    
    def test_logger_error(self, capsys):
        """Test error logging."""
        logger = get_logger("test")
        logger.error("error_message", error_code="E001")
        
        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["event"] == "error_message"
        assert log_data["level"] == "error"
        assert log_data["error_code"] == "E001"
    
    def test_logger_critical(self, capsys):
        """Test critical logging."""
        logger = get_logger("test")
        logger.critical("critical_message", severity="high")
        
        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["event"] == "critical_message"
        assert log_data["level"] == "critical"
        assert log_data["severity"] == "high"
    
    def test_logger_bind_context(self, capsys):
        """Test binding context to logger."""
        logger = get_logger("test")
        bound_logger = logger.bind(user_id="123", session_id="abc")
        
        bound_logger.info("test_message")
        
        captured = capsys.readouterr()
        log_data = json.loads(captured.out.strip())
        
        assert log_data["event"] == "test_message"
        assert log_data["user_id"] == "123"
        assert log_data["session_id"] == "abc"
    
    def test_logger_bind_preserves_context(self, capsys):
        """Test that bound context is preserved across multiple log calls."""
        # Reset request ID to avoid interference from previous tests
        set_request_id("")
        
        logger = get_logger("test")
        bound_logger = logger.bind(request_id="req-123")
        
        bound_logger.info("message1")
        bound_logger.info("message2")
        
        captured = capsys.readouterr()
        lines = captured.out.strip().split('\n')
        
        log1 = json.loads(lines[0])
        log2 = json.loads(lines[1])
        
        assert log1["request_id"] == "req-123"
        assert log2["request_id"] == "req-123"


class TestFileLogging:
    """Test file logging with rotation."""
    
    def test_setup_file_logging_creates_directory(self):
        """Test that setup_file_logging creates log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            
            setup_file_logging(str(log_dir))
            
            assert log_dir.exists()
            assert log_dir.is_dir()
    
    def test_setup_file_logging_creates_handler(self):
        """Test that setup_file_logging creates file handler."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            
            # Clear existing handlers
            root_logger = logging.getLogger()
            root_logger.handlers.clear()
            
            setup_file_logging(str(log_dir))
            
            # Verify handler was added
            assert len(root_logger.handlers) > 0
            
            # Verify it's a TimedRotatingFileHandler
            handler = root_logger.handlers[0]
            assert isinstance(handler, TimedRotatingFileHandler)
    
    def test_file_logging_configuration(self):
        """Test that file logging can be configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            
            # This should not raise an error
            configure_logging(
                level="INFO",
                format="json",
                output="file",
                log_dir=str(log_dir)
            )
            
            # Verify log directory was created
            assert log_dir.exists()


class TestLogLevels:
    """Test log level filtering."""
    
    def test_info_level_filters_debug(self, capsys):
        """Test that INFO level filters out DEBUG messages."""
        configure_logging(level="INFO", format="json", output="stdout")
        
        logger = get_logger("test")
        logger.debug("debug_message")
        logger.info("info_message")
        
        captured = capsys.readouterr()
        
        # Debug should not appear
        assert "debug_message" not in captured.out
        # Info should appear
        assert "info_message" in captured.out
    
    def test_error_level_filters_info(self, capsys):
        """Test that ERROR level filters out INFO messages."""
        configure_logging(level="ERROR", format="json", output="stdout")
        
        logger = get_logger("test")
        logger.info("info_message")
        logger.error("error_message")
        
        captured = capsys.readouterr()
        
        # Info should not appear
        assert "info_message" not in captured.out
        # Error should appear
        assert "error_message" in captured.out
