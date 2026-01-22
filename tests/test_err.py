"""Tests for Err class."""
import pytest
from types import MappingProxyType
from typing import Any, Dict

from resokerr.core import Err, MessageTrace, TraceSeverityLevel


class TestErrCreation:
    """Test Err instantiation and basic properties."""

    def test_err_with_cause(self):
        """Test creating an Err with a cause."""
        err = Err(cause="Something went wrong")
        assert err.cause == "Something went wrong"
        assert err.has_cause()
        assert err.is_err()
        assert not err.is_ok()

    def test_err_without_cause(self):
        """Test creating an Err without a cause (None)."""
        err = Err(cause=None)
        assert err.cause is None
        assert not err.has_cause()
        assert err.is_err()

    def test_err_with_exception_cause(self):
        """Test Err with exception as cause."""
        exception = ValueError("Invalid input")
        err = Err(cause=exception)
        assert err.cause == exception
        assert isinstance(err.cause, ValueError)

    def test_err_with_complex_cause(self):
        """Test Err with complex data structure as cause."""
        cause = {"error_type": "ValidationError", "details": ["field1", "field2"]}
        err = Err(cause=cause)
        assert err.cause == cause
        assert err.cause["error_type"] == "ValidationError"

    def test_err_with_empty_messages(self):
        """Test Err with no messages."""
        err = Err(cause="Error")
        assert err.messages == ()
        assert len(err.messages) == 0

    def test_err_with_metadata(self):
        """Test Err with metadata."""
        metadata = {"timestamp": "2026-01-09", "request_id": "abc-123"}
        err = Err(cause="Error", metadata=metadata)
        assert err.metadata == metadata
        assert err.has_metadata()


class TestErrImmutability:
    """Test that Err instances are immutable."""

    def test_err_is_frozen(self):
        """Test that Err is frozen and cannot be modified."""
        err = Err(cause="Error")
        
        with pytest.raises(AttributeError):
            err.cause = "New error"
        
        with pytest.raises(AttributeError):
            err.messages = (MessageTrace.error("New"),)

    def test_messages_are_tuple(self):
        """Test that messages are stored as immutable tuple."""
        messages = [MessageTrace.error("Error 1"), MessageTrace.error("Error 2")]
        err = Err(cause="Error", messages=messages)
        
        assert isinstance(err.messages, tuple)
        assert len(err.messages) == 2

    def test_metadata_converted_to_mapping_proxy(self):
        """Test that metadata dict is converted to immutable MappingProxyType."""
        metadata: Dict[str, Any] = {"key": "value"}
        err = Err(cause="Error", metadata=metadata)
        
        assert isinstance(err.metadata, MappingProxyType)
        # Store original value
        original_value = err.metadata["key"]
        # Modify original dict shouldn't affect Err after creation
        metadata["key"] = "modified"
        assert err.metadata["key"] == original_value
        assert err.metadata["key"] == "value"


class TestErrSuccessMessageConversion:
    """Test that SUCCESS messages are converted to INFO in Err instances."""

    def test_success_message_converted_to_info(self):
        """Test that SUCCESS severity messages are converted to INFO."""
        success_msg = MessageTrace.success("This is a success", code="SUCCESS_001")
        err = Err(cause="Error", messages=[success_msg])

        assert len(err.messages) == 1
        assert err.messages[0].severity == TraceSeverityLevel.INFO
        assert err.messages[0].message == "This is a success"
        assert err.messages[0].code == "SUCCESS_001"

    def test_success_conversion_adds_details(self):
        """Test that success conversion adds details about the conversion."""
        success_msg = MessageTrace.success("Success message")
        err = Err(cause="Error", messages=[success_msg])

        assert err.messages[0].details is not None
        assert "_converted_from" in err.messages[0].details
        assert err.messages[0].details["_converted_from"]["from"] == "success"
        assert "Err instances cannot contain SUCCESS messages" in err.messages[0].details["_converted_from"]["reason"]

    def test_success_conversion_preserves_existing_details(self):
        """Test that existing details are preserved during conversion."""
        original_details = {"operation": "create", "id": 123}
        success_msg = MessageTrace.success("Created successfully", details=original_details)
        err = Err(cause="Error", messages=[success_msg])

        assert err.messages[0].details["operation"] == "create"
        assert err.messages[0].details["id"] == 123
        assert "_converted_from" in err.messages[0].details

    def test_mixed_severity_messages_with_success(self):
        """Test Err with mixed severity messages including SUCCESS."""
        messages = [
            MessageTrace.info("Info message"),
            MessageTrace.success("Success message"),
            MessageTrace.error("Error message"),
            MessageTrace.warning("Warning message")
        ]
        err = Err(cause="Error", messages=messages)

        assert len(err.messages) == 4
        # First message should remain INFO
        assert err.messages[0].severity == TraceSeverityLevel.INFO
        # Second message should be converted from SUCCESS to INFO
        assert err.messages[1].severity == TraceSeverityLevel.INFO
        assert "_converted_from" in err.messages[1].details
        # Third message should remain ERROR
        assert err.messages[2].severity == TraceSeverityLevel.ERROR
        # Fourth message should remain WARNING
        assert err.messages[3].severity == TraceSeverityLevel.WARNING

    def test_multiple_success_messages_all_converted(self):
        """Test that multiple SUCCESS messages are all converted in Err."""
        messages = [
            MessageTrace.success("Success 1"),
            MessageTrace.success("Success 2"),
            MessageTrace.success("Success 3")
        ]
        err = Err(cause="Error", messages=messages)

        assert len(err.messages) == 3
        assert all(msg.severity == TraceSeverityLevel.INFO for msg in err.messages)
        assert all("_converted_from" in msg.details for msg in err.messages)

    def test_err_has_no_success_messages(self):
        """Test that Err cannot contain SUCCESS messages (they are converted)."""
        success_msg = MessageTrace.success("Success")
        err = Err(cause="Error", messages=[success_msg])

        # Err does not have success_messages property - it's not a mixin
        # But verify the message was converted to INFO
        assert len(err.info_messages) == 1
        assert err.messages[0].severity == TraceSeverityLevel.INFO


class TestErrMessageMethods:
    """Test Err message addition methods."""

    def test_with_error(self):
        """Test adding an error message."""
        err1 = Err(cause="Original error")
        err2 = err1.with_error("Error message", code="ERR_001")
        
        # Original should be unchanged
        assert len(err1.messages) == 0
        # New instance should have the message
        assert len(err2.messages) == 1
        assert err2.messages[0].severity == TraceSeverityLevel.ERROR
        assert err2.messages[0].message == "Error message"
        assert err2.messages[0].code == "ERR_001"

    def test_with_info(self):
        """Test adding an info message to Err."""
        err1 = Err(cause="Error")
        err2 = err1.with_info("Info message", code="INFO_001")
        
        assert len(err2.messages) == 1
        assert err2.messages[0].severity == TraceSeverityLevel.INFO
        assert err2.messages[0].message == "Info message"

    def test_with_warning(self):
        """Test adding a warning message to Err."""
        err1 = Err(cause="Error")
        err2 = err1.with_warning("Warning message", code="WARN_001")
        
        assert len(err2.messages) == 1
        assert err2.messages[0].severity == TraceSeverityLevel.WARNING
        assert err2.messages[0].message == "Warning message"

    def test_with_error_chaining(self):
        """Test chaining multiple with_error calls."""
        err = (Err(cause="Root cause")
               .with_error("Error 1")
               .with_error("Error 2")
               .with_error("Error 3"))
        
        assert len(err.messages) == 3
        assert err.messages[0].message == "Error 1"
        assert err.messages[1].message == "Error 2"
        assert err.messages[2].message == "Error 3"

    def test_mixed_message_chaining(self):
        """Test chaining mixed message types."""
        err = (Err(cause="Error")
               .with_info("Attempting operation")
               .with_warning("Warning encountered")
               .with_error("Operation failed"))
        
        assert len(err.messages) == 3
        assert err.messages[0].severity == TraceSeverityLevel.INFO
        assert err.messages[1].severity == TraceSeverityLevel.WARNING
        assert err.messages[2].severity == TraceSeverityLevel.ERROR

    def test_with_error_includes_details(self):
        """Test adding error message with details."""
        details = {"field": "email", "constraint": "unique"}
        err = Err(cause="Validation error").with_error("Duplicate email", details=details)
        
        assert err.messages[0].details == details

    def test_with_metadata(self):
        """Test replacing metadata."""
        err1 = Err(cause="Error", metadata={"old": "data"})
        err2 = err1.with_metadata({"new": "data"})
        
        assert err1.metadata["old"] == "data"
        assert err2.metadata["new"] == "data"
        assert "old" not in err2.metadata


class TestErrMessageFiltering:
    """Test Err message filtering by severity."""

    def test_error_messages_property(self):
        """Test retrieving only error messages."""
        messages = [
            MessageTrace.error("Error 1"),
            MessageTrace.info("Info 1"),
            MessageTrace.error("Error 2")
        ]
        err = Err(cause="Error", messages=messages)
        
        error_msgs = err.error_messages
        assert len(error_msgs) == 2
        assert error_msgs[0].message == "Error 1"
        assert error_msgs[1].message == "Error 2"

    def test_info_messages_property(self):
        """Test retrieving only info messages."""
        messages = [
            MessageTrace.error("Error 1"),
            MessageTrace.info("Info 1"),
            MessageTrace.info("Info 2")
        ]
        err = Err(cause="Error", messages=messages)
        
        info_msgs = err.info_messages
        assert len(info_msgs) == 2
        assert info_msgs[0].message == "Info 1"
        assert info_msgs[1].message == "Info 2"

    def test_warning_messages_property(self):
        """Test retrieving only warning messages."""
        messages = [
            MessageTrace.error("Error 1"),
            MessageTrace.warning("Warning 1"),
            MessageTrace.warning("Warning 2")
        ]
        err = Err(cause="Error", messages=messages)
        
        warn_msgs = err.warning_messages
        assert len(warn_msgs) == 2
        assert warn_msgs[0].message == "Warning 1"
        assert warn_msgs[1].message == "Warning 2"

    def test_has_errors(self):
        """Test has_errors() method."""
        err1 = Err(cause="Error")
        assert not err1.has_errors()
        
        err2 = err1.with_error("Error message")
        assert err2.has_errors()

    def test_has_info(self):
        """Test has_info() method."""
        err1 = Err(cause="Error")
        assert not err1.has_info()
        
        err2 = err1.with_info("Info message")
        assert err2.has_info()

    def test_has_warnings(self):
        """Test has_warnings() method."""
        err1 = Err(cause="Error")
        assert not err1.has_warnings()
        
        err2 = err1.with_warning("Warning message")
        assert err2.has_warnings()


class TestErrProtocolCompliance:
    """Test that Err complies with the defined protocols."""

    def test_has_messages_protocol(self):
        """Test HasMessages protocol compliance."""
        err = Err(cause="Error", messages=[MessageTrace.error("Error")])
        
        assert hasattr(err, 'messages')
        assert isinstance(err.messages, tuple)
        assert hasattr(err, '_get_messages_by_severity')

    def test_has_error_messages_protocol(self):
        """Test HasErrorMessages protocol compliance."""
        err = Err(cause="Error")
        
        assert hasattr(err, 'error_messages')
        assert hasattr(err, 'has_errors')
        assert callable(err.has_errors)

    def test_has_info_messages_protocol(self):
        """Test HasInfoMessages protocol compliance."""
        err = Err(cause="Error")
        
        assert hasattr(err, 'info_messages')
        assert hasattr(err, 'has_info')
        assert callable(err.has_info)

    def test_has_warning_messages_protocol(self):
        """Test HasWarningMessages protocol compliance."""
        err = Err(cause="Error")
        
        assert hasattr(err, 'warning_messages')
        assert hasattr(err, 'has_warnings')
        assert callable(err.has_warnings)

    def test_has_metadata_protocol(self):
        """Test HasMetadata protocol compliance."""
        err = Err(cause="Error", metadata={"key": "value"})
        
        assert hasattr(err, 'metadata')
        assert hasattr(err, 'has_metadata')
        assert callable(err.has_metadata)
        assert err.has_metadata()

    def test_status_mixin(self):
        """Test StatusMixin methods."""
        err = Err(cause="Error")
        
        assert hasattr(err, 'is_ok')
        assert hasattr(err, 'is_err')
        assert err.is_ok() is False
        assert err.is_err() is True


class TestErrComposition:
    """Test that Err uses composition, not inheritance."""

    def test_err_is_not_result_subclass(self):
        """Test that Err is not a subclass of any Result base class."""
        err = Err(cause="Error")
        
        # Err should not inherit from a Result base class
        assert Err.__bases__ != ()
        # Check that there's no Result base class in MRO
        base_names = [base.__name__ for base in Err.__mro__]
        assert 'Result' not in base_names
        assert 'ResultBase' not in base_names

    def test_err_cannot_be_converted_to_ok(self):
        """Test that Err cannot be directly converted to Ok."""
        err = Err(cause="Error")
        
        # There should be no method to convert Err to Ok
        assert not hasattr(err, 'to_ok')
        assert not hasattr(err, 'as_ok')

    def test_err_final_class(self):
        """Test that Err is decorated with @final (cannot be subclassed)."""
        # While we can't enforce @final at runtime in Python < 3.11,
        # we can check that the decorator is present
        assert hasattr(Err, '__final__') or '@final' in str(Err)


class TestErrWithExceptions:
    """Test Err with real Python exceptions."""

    def test_err_with_value_error(self):
        """Test Err storing a ValueError."""
        try:
            int("not a number")
        except ValueError as e:
            err = Err(cause=e)
            assert isinstance(err.cause, ValueError)
            assert "invalid literal" in str(err.cause).lower()

    def test_err_with_custom_exception(self):
        """Test Err with custom exception class."""
        class CustomException(Exception):
            def __init__(self, code: str, message: str):
                self.code = code
                self.message = message
                super().__init__(message)
        
        custom_exc = CustomException("E001", "Custom error")
        err = Err(cause=custom_exc)
        assert err.cause.code == "E001"
        assert err.cause.message == "Custom error"

    def test_err_with_exception_and_error_messages(self):
        """Test Err with both exception cause and error messages."""
        exception = RuntimeError("Runtime problem")
        err = (Err(cause=exception)
               .with_error("Failed to process data")
               .with_error("Validation failed"))
        
        assert isinstance(err.cause, RuntimeError)
        assert len(err.error_messages) == 2
