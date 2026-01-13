"""Tests for MessageTrace class."""
import pytest
from types import MappingProxyType
from typing import Any, Dict

from resokerr.core import MessageTrace, TraceSeverityLevel


class TestMessageTraceCreation:
    """Test MessageTrace instantiation and factory methods."""

    def test_message_trace_creation_with_string_message(self):
        """Test creating a MessageTrace with a string message."""
        msg = MessageTrace(
            message="Test message",
            severity=TraceSeverityLevel.INFO
        )
        assert msg.message == "Test message"
        assert msg.severity == TraceSeverityLevel.INFO
        assert msg.code is None
        assert msg.details is None
        assert msg.stack_trace is None

    def test_message_trace_creation_with_custom_type(self):
        """Test creating a MessageTrace with a custom message type."""
        custom_msg = {"key": "value", "data": 123}
        msg = MessageTrace(
            message=custom_msg,
            severity=TraceSeverityLevel.ERROR
        )
        assert msg.message == custom_msg
        assert msg.severity == TraceSeverityLevel.ERROR

    def test_message_trace_with_all_fields(self):
        """Test creating a MessageTrace with all optional fields."""
        details = {"field1": "value1", "field2": 42}
        msg = MessageTrace(
            message="Complete message",
            severity=TraceSeverityLevel.WARNING,
            code="WARN_001",
            details=details,
            stack_trace="line 1\nline 2"
        )
        assert msg.message == "Complete message"
        assert msg.severity == TraceSeverityLevel.WARNING
        assert msg.code == "WARN_001"
        assert msg.details == details
        assert msg.stack_trace == "line 1\nline 2"

    def test_info_factory_method(self):
        """Test MessageTrace.info() factory method."""
        msg = MessageTrace.info("Info message", code="INFO_001")
        assert msg.message == "Info message"
        assert msg.severity == TraceSeverityLevel.INFO
        assert msg.code == "INFO_001"

    def test_warning_factory_method(self):
        """Test MessageTrace.warning() factory method."""
        msg = MessageTrace.warning("Warning message", code="WARN_001")
        assert msg.message == "Warning message"
        assert msg.severity == TraceSeverityLevel.WARNING
        assert msg.code == "WARN_001"

    def test_error_factory_method(self):
        """Test MessageTrace.error() factory method."""
        msg = MessageTrace.error("Error message", code="ERR_001")
        assert msg.message == "Error message"
        assert msg.severity == TraceSeverityLevel.ERROR
        assert msg.code == "ERR_001"


class TestMessageTraceImmutability:
    """Test that MessageTrace instances are immutable."""

    def test_message_trace_is_frozen(self):
        """Test that MessageTrace is frozen and cannot be modified."""
        msg = MessageTrace(message="Test", severity=TraceSeverityLevel.INFO)
        
        with pytest.raises(AttributeError):
            msg.message = "New message"
        
        with pytest.raises(AttributeError):
            msg.severity = TraceSeverityLevel.ERROR

    def test_details_converted_to_mapping_proxy(self):
        """Test that details dict is converted to immutable MappingProxyType."""
        details: Dict[str, Any] = {"key": "value", "count": 10}
        msg = MessageTrace(
            message="Test",
            severity=TraceSeverityLevel.INFO,
            details=details
        )
        
        assert isinstance(msg.details, MappingProxyType)
        # Store original value
        original_value = msg.details["key"]
        # Verify we can't modify through original dict after creation
        details["key"] = "modified"
        # The MessageTrace should still have the original value
        assert msg.details["key"] == original_value
        assert msg.details["key"] == "value"

    def test_details_immutable_when_passed_as_mapping_proxy(self):
        """Test that passing a MappingProxyType is preserved."""
        details = MappingProxyType({"key": "value"})
        msg = MessageTrace(
            message="Test",
            severity=TraceSeverityLevel.INFO,
            details=details
        )
        assert isinstance(msg.details, MappingProxyType)
        assert msg.details["key"] == "value"


class TestMessageTraceSeverityLevels:
    """Test TraceSeverityLevel enum."""

    def test_severity_level_values(self):
        """Test that severity levels have correct string values."""
        assert TraceSeverityLevel.INFO.value == "info"
        assert TraceSeverityLevel.WARNING.value == "warning"
        assert TraceSeverityLevel.ERROR.value == "error"

    def test_severity_level_comparison(self):
        """Test that severity levels can be compared."""
        info_msg = MessageTrace.info("Info")
        warning_msg = MessageTrace.warning("Warning")
        error_msg = MessageTrace.error("Error")
        
        assert info_msg.severity == TraceSeverityLevel.INFO
        assert warning_msg.severity == TraceSeverityLevel.WARNING
        assert error_msg.severity == TraceSeverityLevel.ERROR
        assert info_msg.severity != warning_msg.severity


class TestMessageTraceWithGenericTypes:
    """Test MessageTrace with various generic message types."""

    def test_with_dict_message(self):
        """Test MessageTrace with dict message type."""
        msg_dict = {"type": "validation", "field": "email"}
        msg = MessageTrace(message=msg_dict, severity=TraceSeverityLevel.ERROR)
        assert msg.message == msg_dict
        assert msg.message["type"] == "validation"

    def test_with_tuple_message(self):
        """Test MessageTrace with tuple message type."""
        msg_tuple = ("Error", 404, "Not Found")
        msg = MessageTrace(message=msg_tuple, severity=TraceSeverityLevel.ERROR)
        assert msg.message == msg_tuple
        assert msg.message[1] == 404

    def test_with_custom_class_message(self):
        """Test MessageTrace with custom class instance as message."""
        class CustomError:
            def __init__(self, code: str, description: str):
                self.code = code
                self.description = description
        
        custom_err = CustomError("E001", "Something went wrong")
        msg = MessageTrace(message=custom_err, severity=TraceSeverityLevel.ERROR)
        assert msg.message.code == "E001"
        assert msg.message.description == "Something went wrong"
