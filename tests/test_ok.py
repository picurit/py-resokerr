"""Tests for Ok class."""
import pytest
from types import MappingProxyType
from typing import Any, Dict

from resokerr.core import Ok, MessageTrace, TraceSeverityLevel


class TestOkCreation:
    """Test Ok instantiation and basic properties."""

    def test_ok_with_value(self):
        """Test creating an Ok with a value."""
        ok = Ok(value=42)
        assert ok.value == 42
        assert ok.has_value()
        assert ok.is_ok()
        assert not ok.is_err()

    def test_ok_without_value(self):
        """Test creating an Ok without a value (None)."""
        ok = Ok(value=None)
        assert ok.value is None
        assert not ok.has_value()
        assert ok.is_ok()

    def test_ok_with_string_value(self):
        """Test Ok with string value."""
        ok = Ok(value="success")
        assert ok.value == "success"
        assert ok.has_value()

    def test_ok_with_complex_value(self):
        """Test Ok with complex data structure."""
        value = {"status": "success", "data": [1, 2, 3]}
        ok = Ok(value=value)
        assert ok.value == value
        assert ok.value["status"] == "success"

    def test_ok_with_empty_messages(self):
        """Test Ok with no messages."""
        ok = Ok(value=42)
        assert ok.messages == ()
        assert len(ok.messages) == 0

    def test_ok_with_metadata(self):
        """Test Ok with metadata."""
        metadata = {"timestamp": "2026-01-09", "user_id": 123}
        ok = Ok(value=42, metadata=metadata)
        assert ok.metadata == metadata
        assert ok.has_metadata()


class TestOkImmutability:
    """Test that Ok instances are immutable."""

    def test_ok_is_frozen(self):
        """Test that Ok is frozen and cannot be modified."""
        ok = Ok(value=42)
        
        with pytest.raises(AttributeError):
            ok.value = 100
        
        with pytest.raises(AttributeError):
            ok.messages = (MessageTrace.info("New"),)

    def test_messages_are_tuple(self):
        """Test that messages are stored as immutable tuple."""
        messages = [MessageTrace.info("Info 1"), MessageTrace.info("Info 2")]
        ok = Ok(value=42, messages=messages)
        
        assert isinstance(ok.messages, tuple)
        assert len(ok.messages) == 2

    def test_metadata_converted_to_mapping_proxy(self):
        """Test that metadata dict is converted to immutable MappingProxyType."""
        metadata: Dict[str, Any] = {"key": "value"}
        ok = Ok(value=42, metadata=metadata)
        
        assert isinstance(ok.metadata, MappingProxyType)
        # Store original value
        original_value = ok.metadata["key"]
        # Modify original dict shouldn't affect Ok after creation
        metadata["key"] = "modified"
        assert ok.metadata["key"] == original_value
        assert ok.metadata["key"] == "value"


class TestOkErrorMessageDowngrade:
    """Test that ERROR messages are downgraded to WARNING in Ok instances."""

    def test_error_message_downgraded_to_warning(self):
        """Test that ERROR severity messages are converted to WARNING."""
        error_msg = MessageTrace.error("This is an error", code="ERR_001")
        ok = Ok(value=42, messages=[error_msg])
        
        assert len(ok.messages) == 1
        assert ok.messages[0].severity == TraceSeverityLevel.WARNING
        assert ok.messages[0].message == "This is an error"
        assert ok.messages[0].code == "ERR_001"

    def test_error_downgrade_adds_details(self):
        """Test that error downgrade adds details about the conversion."""
        error_msg = MessageTrace.error("Error message")
        ok = Ok(value=42, messages=[error_msg])
        
        assert ok.messages[0].details is not None
        assert "downgraded" in ok.messages[0].details
        assert ok.messages[0].details["downgraded"]["from"] == "error"
        assert "Ok instances cannot contain ERROR messages" in ok.messages[0].details["downgraded"]["reason"]

    def test_error_downgrade_preserves_existing_details(self):
        """Test that existing details are preserved during downgrade."""
        original_details = {"field": "email", "constraint": "format"}
        error_msg = MessageTrace.error("Invalid email", details=original_details)
        ok = Ok(value=42, messages=[error_msg])
        
        assert ok.messages[0].details["field"] == "email"
        assert ok.messages[0].details["constraint"] == "format"
        assert "downgraded" in ok.messages[0].details

    def test_mixed_severity_messages(self):
        """Test Ok with mixed severity messages including ERROR."""
        messages = [
            MessageTrace.info("Info message"),
            MessageTrace.error("Error message"),
            MessageTrace.warning("Warning message")
        ]
        ok = Ok(value=42, messages=messages)
        
        assert len(ok.messages) == 3
        # First message should remain INFO
        assert ok.messages[0].severity == TraceSeverityLevel.INFO
        # Second message should be downgraded to WARNING
        assert ok.messages[1].severity == TraceSeverityLevel.WARNING
        # Third message should remain WARNING
        assert ok.messages[2].severity == TraceSeverityLevel.WARNING


class TestOkMessageMethods:
    """Test Ok message addition methods."""

    def test_with_info(self):
        """Test adding an info message."""
        ok1 = Ok(value=42)
        ok2 = ok1.with_info("Info message", code="INFO_001")
        
        # Original should be unchanged
        assert len(ok1.messages) == 0
        # New instance should have the message
        assert len(ok2.messages) == 1
        assert ok2.messages[0].severity == TraceSeverityLevel.INFO
        assert ok2.messages[0].message == "Info message"
        assert ok2.messages[0].code == "INFO_001"

    def test_with_warning(self):
        """Test adding a warning message."""
        ok1 = Ok(value=42)
        ok2 = ok1.with_warning("Warning message", code="WARN_001")
        
        assert len(ok2.messages) == 1
        assert ok2.messages[0].severity == TraceSeverityLevel.WARNING
        assert ok2.messages[0].message == "Warning message"

    def test_with_info_chaining(self):
        """Test chaining multiple with_info calls."""
        ok = (Ok(value=42)
              .with_info("Step 1")
              .with_info("Step 2")
              .with_info("Step 3"))
        
        assert len(ok.messages) == 3
        assert ok.messages[0].message == "Step 1"
        assert ok.messages[1].message == "Step 2"
        assert ok.messages[2].message == "Step 3"

    def test_with_warning_and_info_chaining(self):
        """Test chaining mixed message types."""
        ok = (Ok(value=42)
              .with_info("Starting process")
              .with_warning("Non-critical issue")
              .with_info("Process complete"))
        
        assert len(ok.messages) == 3
        assert ok.messages[0].severity == TraceSeverityLevel.INFO
        assert ok.messages[1].severity == TraceSeverityLevel.WARNING
        assert ok.messages[2].severity == TraceSeverityLevel.INFO

    def test_with_info_includes_details(self):
        """Test adding info message with details."""
        details = {"user": "john", "action": "login"}
        ok = Ok(value=42).with_info("User action", details=details)
        
        assert ok.messages[0].details == details

    def test_with_metadata(self):
        """Test replacing metadata."""
        ok1 = Ok(value=42, metadata={"old": "data"})
        ok2 = ok1.with_metadata({"new": "data"})
        
        assert ok1.metadata["old"] == "data"
        assert ok2.metadata["new"] == "data"
        assert "old" not in ok2.metadata


class TestOkMessageFiltering:
    """Test Ok message filtering by severity."""

    def test_info_messages_property(self):
        """Test retrieving only info messages."""
        messages = [
            MessageTrace.info("Info 1"),
            MessageTrace.warning("Warning 1"),
            MessageTrace.info("Info 2")
        ]
        ok = Ok(value=42, messages=messages)
        
        info_msgs = ok.info_messages
        assert len(info_msgs) == 2
        assert info_msgs[0].message == "Info 1"
        assert info_msgs[1].message == "Info 2"

    def test_warning_messages_property(self):
        """Test retrieving only warning messages."""
        messages = [
            MessageTrace.info("Info 1"),
            MessageTrace.warning("Warning 1"),
            MessageTrace.warning("Warning 2")
        ]
        ok = Ok(value=42, messages=messages)
        
        warn_msgs = ok.warning_messages
        assert len(warn_msgs) == 2
        assert warn_msgs[0].message == "Warning 1"
        assert warn_msgs[1].message == "Warning 2"

    def test_has_info(self):
        """Test has_info() method."""
        ok1 = Ok(value=42)
        assert not ok1.has_info()
        
        ok2 = ok1.with_info("Info message")
        assert ok2.has_info()

    def test_has_warnings(self):
        """Test has_warnings() method."""
        ok1 = Ok(value=42)
        assert not ok1.has_warnings()
        
        ok2 = ok1.with_warning("Warning message")
        assert ok2.has_warnings()

    def test_no_error_messages_in_ok(self):
        """Test that Ok instances don't have error messages (they're downgraded)."""
        error_msg = MessageTrace.error("Error")
        ok = Ok(value=42, messages=[error_msg])
        
        # Should be empty since errors are downgraded to warnings
        # Note: Ok doesn't have error_messages property, but we can verify
        # that the message was converted to warning
        assert len(ok.warning_messages) == 1
        assert ok.messages[0].severity == TraceSeverityLevel.WARNING


class TestOkProtocolCompliance:
    """Test that Ok complies with the defined protocols."""

    def test_has_messages_protocol(self):
        """Test HasMessages protocol compliance."""
        ok = Ok(value=42, messages=[MessageTrace.info("Info")])
        
        # Should have messages property
        assert hasattr(ok, 'messages')
        assert isinstance(ok.messages, tuple)
        
        # Should have _get_messages_by_severity
        assert hasattr(ok, '_get_messages_by_severity')

    def test_has_info_messages_protocol(self):
        """Test HasInfoMessages protocol compliance."""
        ok = Ok(value=42)
        
        assert hasattr(ok, 'info_messages')
        assert hasattr(ok, 'has_info')
        assert callable(ok.has_info)

    def test_has_warning_messages_protocol(self):
        """Test HasWarningMessages protocol compliance."""
        ok = Ok(value=42)
        
        assert hasattr(ok, 'warning_messages')
        assert hasattr(ok, 'has_warnings')
        assert callable(ok.has_warnings)

    def test_has_metadata_protocol(self):
        """Test HasMetadata protocol compliance."""
        ok = Ok(value=42, metadata={"key": "value"})
        
        assert hasattr(ok, 'metadata')
        assert hasattr(ok, 'has_metadata')
        assert callable(ok.has_metadata)
        assert ok.has_metadata()

    def test_status_mixin(self):
        """Test StatusMixin methods."""
        ok = Ok(value=42)
        
        assert hasattr(ok, 'is_ok')
        assert hasattr(ok, 'is_err')
        assert ok.is_ok() is True
        assert ok.is_err() is False


class TestOkComposition:
    """Test that Ok uses composition, not inheritance."""

    def test_ok_is_not_result_subclass(self):
        """Test that Ok is not a subclass of any Result base class."""
        ok = Ok(value=42)
        
        # Ok should not inherit from a Result base class
        # It's an independent class that composes with mixins
        assert Ok.__bases__ != ()
        # Check that there's no Result base class in MRO
        base_names = [base.__name__ for base in Ok.__mro__]
        assert 'Result' not in base_names
        assert 'ResultBase' not in base_names

    def test_ok_cannot_be_converted_to_err(self):
        """Test that Ok cannot be directly converted to Err."""
        ok = Ok(value=42)
        
        # There should be no method to convert Ok to Err
        assert not hasattr(ok, 'to_err')
        assert not hasattr(ok, 'as_err')

    def test_ok_final_class(self):
        """Test that Ok is decorated with @final (cannot be subclassed)."""
        # While we can't enforce @final at runtime in Python < 3.11,
        # we can check that the decorator is present
        assert hasattr(Ok, '__final__') or '@final' in str(Ok)
