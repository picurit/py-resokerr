"""Tests for MessageTrace class."""
import pytest
from types import MappingProxyType
from typing import Any, Dict

from resokerr.core import MessageTrace, TraceSeverityLevel, Validator


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

    def test_success_factory_method(self):
        """Test MessageTrace.success() factory method."""
        msg = MessageTrace.success("Success message", code="SUCCESS_001")
        assert msg.message == "Success message"
        assert msg.severity == TraceSeverityLevel.SUCCESS
        assert msg.code == "SUCCESS_001"

    def test_success_factory_with_all_params(self):
        """Test MessageTrace.success() with all parameters."""
        details = {"operation": "create", "count": 5}
        msg = MessageTrace.success(
            "Created records",
            code="SUCCESS_CREATE",
            details=details,
            stack_trace="create.py:42"
        )
        assert msg.message == "Created records"
        assert msg.severity == TraceSeverityLevel.SUCCESS
        assert msg.code == "SUCCESS_CREATE"
        assert msg.details["operation"] == "create"
        assert msg.stack_trace == "create.py:42"

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
        assert TraceSeverityLevel.SUCCESS.value == "success"
        assert TraceSeverityLevel.INFO.value == "info"
        assert TraceSeverityLevel.WARNING.value == "warning"
        assert TraceSeverityLevel.ERROR.value == "error"

    def test_severity_level_comparison(self):
        """Test that severity levels can be compared."""
        success_msg = MessageTrace.success("Success")
        info_msg = MessageTrace.info("Info")
        warning_msg = MessageTrace.warning("Warning")
        error_msg = MessageTrace.error("Error")

        assert success_msg.severity == TraceSeverityLevel.SUCCESS
        assert info_msg.severity == TraceSeverityLevel.INFO
        assert warning_msg.severity == TraceSeverityLevel.WARNING
        assert error_msg.severity == TraceSeverityLevel.ERROR
        assert info_msg.severity != warning_msg.severity
        assert success_msg.severity != info_msg.severity


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

class TestMessageTraceToDict:
    """Test MessageTrace.to_dict() serialization method."""

    def test_to_dict_with_string_message(self):
        """Test to_dict with a simple string message."""
        msg = MessageTrace.info("Simple message")
        result = msg.to_dict()
        
        assert result["message"] == "Simple message"
        assert result["severity"] == "info"
        assert "code" not in result
        assert "details" not in result
        assert "stack_trace" not in result

    def test_to_dict_with_all_fields(self):
        """Test to_dict includes all fields when present."""
        msg = MessageTrace(
            message="Complete message",
            severity=TraceSeverityLevel.ERROR,
            code="ERR_001",
            details={"field": "email", "reason": "invalid"},
            stack_trace="File: test.py\nLine: 42"
        )
        result = msg.to_dict()
        
        assert result["message"] == "Complete message"
        assert result["severity"] == "error"
        assert result["code"] == "ERR_001"
        assert result["details"] == {"field": "email", "reason": "invalid"}
        assert result["stack_trace"] == "File: test.py\nLine: 42"

    def test_to_dict_with_numeric_message(self):
        """Test to_dict with numeric message types."""
        int_msg = MessageTrace.info(42)
        float_msg = MessageTrace.warning(3.14)
        
        assert int_msg.to_dict()["message"] == 42
        assert float_msg.to_dict()["message"] == 3.14

    def test_to_dict_with_bool_message(self):
        """Test to_dict with boolean message."""
        msg = MessageTrace.info(True)
        assert msg.to_dict()["message"] is True

    def test_to_dict_with_none_message(self):
        """Test to_dict with None message."""
        msg = MessageTrace(message=None, severity=TraceSeverityLevel.INFO)
        assert msg.to_dict()["message"] is None

    def test_to_dict_with_object_having_to_dict_method(self):
        """Test to_dict with custom object implementing to_dict()."""
        class SerializableError:
            def __init__(self, code: str, detail: str):
                self.code = code
                self.detail = detail
            
            def to_dict(self) -> Dict[str, Any]:
                return {"code": self.code, "detail": self.detail}
        
        custom_obj = SerializableError("E001", "Something went wrong")
        msg = MessageTrace.error(custom_obj)
        result = msg.to_dict()
        
        assert result["message"] == {"code": "E001", "detail": "Something went wrong"}
        assert result["severity"] == "error"

    def test_to_dict_with_non_serializable_object_fallback_to_str(self):
        """Test to_dict falls back to str() for objects without to_dict()."""
        class NonSerializable:
            def __init__(self, value: str):
                self.value = value
            
            def __str__(self) -> str:
                return f"NonSerializable({self.value})"
        
        obj = NonSerializable("test")
        msg = MessageTrace.info(obj)
        result = msg.to_dict()
        
        assert result["message"] == "NonSerializable(test)"

    def test_to_dict_details_converted_from_mapping_proxy(self):
        """Test that MappingProxyType details are converted to regular dict."""
        from types import MappingProxyType
        
        details = MappingProxyType({"key": "value"})
        msg = MessageTrace.info("Test", details=details)
        result = msg.to_dict()
        
        # Should be a regular dict, not MappingProxyType
        assert isinstance(result["details"], dict)
        assert not isinstance(result["details"], MappingProxyType)
        assert result["details"]["key"] == "value"

    def test_to_dict_returns_new_dict_instance(self):
        """Test that to_dict returns a new dict each time (immutability)."""
        msg = MessageTrace.info("Test", details={"key": "value"})
        
        dict1 = msg.to_dict()
        dict2 = msg.to_dict()
        
        assert dict1 is not dict2
        assert dict1["details"] is not dict2["details"]

    def test_to_dict_severity_enum_to_string(self):
        """Test that severity enum is converted to its string value."""
        success_msg = MessageTrace.success("Success")
        info_msg = MessageTrace.info("Info")
        warning_msg = MessageTrace.warning("Warning")
        error_msg = MessageTrace.error("Error")

        assert success_msg.to_dict()["severity"] == "success"
        assert info_msg.to_dict()["severity"] == "info"
        assert warning_msg.to_dict()["severity"] == "warning"
        assert error_msg.to_dict()["severity"] == "error"


class TestMessageTraceSerializationInResults:
    """Test MessageTrace serialization when used within Ok and Err results."""

    def test_serialize_messages_from_ok_result(self):
        """Test serializing messages from an Ok result."""
        from resokerr import Ok
        
        result = (Ok(value="success")
            .with_info("Step 1 completed", code="STEP_1")
            .with_warning("Minor issue detected", details={"field": "optional"})
        )
        
        serialized = [msg.to_dict() for msg in result.messages]
        
        assert len(serialized) == 2
        assert serialized[0]["message"] == "Step 1 completed"
        assert serialized[0]["severity"] == "info"
        assert serialized[0]["code"] == "STEP_1"
        assert serialized[1]["message"] == "Minor issue detected"
        assert serialized[1]["severity"] == "warning"
        assert serialized[1]["details"]["field"] == "optional"

    def test_serialize_messages_from_err_result(self):
        """Test serializing messages from an Err result."""
        from resokerr import Err
        
        result = (Err(cause=ValueError("Invalid input"))
            .with_error("Validation failed", code="VAL_001")
            .with_info("Input received", details={"input_length": 10})
        )
        
        serialized = [msg.to_dict() for msg in result.messages]
        
        assert len(serialized) == 2
        assert serialized[0]["message"] == "Validation failed"
        assert serialized[0]["severity"] == "error"
        assert serialized[1]["message"] == "Input received"
        assert serialized[1]["severity"] == "info"

    def test_empty_messages_serialization(self):
        """Test serializing empty messages tuple."""
        from resokerr import Ok
        
        result = Ok(value=True)
        serialized = [msg.to_dict() for msg in result.messages]
        
        assert serialized == []


class TestValidatorHasToDict:
    """Test the Validator.has_to_dict() static method behavior."""

    def test_has_to_dict_with_to_dict_method(self):
        """Test that objects with to_dict() are detected correctly."""
        class ImplementsToDict:
            def to_dict(self) -> Dict[str, Any]:
                return {"key": "value"}

        class DoesNotImplementToDict:
            pass

        obj_with = ImplementsToDict()
        obj_without = DoesNotImplementToDict()

        assert Validator.has_to_dict(obj_with) is True
        assert Validator.has_to_dict(obj_without) is False

    def test_message_trace_has_to_dict(self):
        """Test that MessageTrace itself has to_dict."""
        msg = MessageTrace.info("Test message")
        assert Validator.has_to_dict(msg) is True

    def test_nested_has_to_dict_in_message_trace(self):
        """Test MessageTrace with an object that has to_dict."""
        class NestedData:
            def __init__(self, value: int):
                self.value = value

            def to_dict(self) -> Dict[str, Any]:
                return {"nested_value": self.value}

        nested = NestedData(42)
        assert Validator.has_to_dict(nested) is True

        msg = MessageTrace.info(nested)
        result = msg.to_dict()

        assert result["message"] == {"nested_value": 42}

    def test_to_dict_check_precedes_str_fallback(self):
        """Test that to_dict() is used before str() fallback."""
        class CustomWithBoth:
            def to_dict(self) -> Dict[str, Any]:
                return {"from": "to_dict"}

            def __str__(self) -> str:
                return "from __str__"

        obj = CustomWithBoth()
        msg = MessageTrace.info(obj)
        result = msg.to_dict()

        # Should use to_dict(), not __str__()
        assert result["message"] == {"from": "to_dict"}

    def test_primitives_do_not_have_to_dict(self):
        """Test that primitives don't have to_dict() method."""
        assert Validator.has_to_dict("string") is False
        assert Validator.has_to_dict(42) is False
        assert Validator.has_to_dict(3.14) is False
        assert Validator.has_to_dict(True) is False
        assert Validator.has_to_dict(None) is False

    def test_dict_does_not_have_to_dict(self):
        """Test that dict doesn't have to_dict method (it's not the protocol)."""
        assert Validator.has_to_dict({}) is False
        assert Validator.has_to_dict({"key": "value"}) is False


class TestValidatorIsJsonPrimitive:
    """Test the Validator.is_json_primitive() static method behavior."""

    def test_string_is_json_primitive(self):
        """Test that strings are JSON primitives."""
        assert Validator.is_json_primitive("hello") is True
        assert Validator.is_json_primitive("") is True

    def test_int_is_json_primitive(self):
        """Test that integers are JSON primitives."""
        assert Validator.is_json_primitive(42) is True
        assert Validator.is_json_primitive(0) is True
        assert Validator.is_json_primitive(-1) is True

    def test_float_is_json_primitive(self):
        """Test that floats are JSON primitives."""
        assert Validator.is_json_primitive(3.14) is True
        assert Validator.is_json_primitive(0.0) is True
        assert Validator.is_json_primitive(-1.5) is True

    def test_bool_is_json_primitive(self):
        """Test that booleans are JSON primitives."""
        assert Validator.is_json_primitive(True) is True
        assert Validator.is_json_primitive(False) is True

    def test_none_is_json_primitive(self):
        """Test that None is a JSON primitive."""
        assert Validator.is_json_primitive(None) is True

    def test_dict_is_json_primitive(self):
        """Test that dict is a JSON primitive."""
        assert Validator.is_json_primitive({}) is True
        assert Validator.is_json_primitive({"key": "value"}) is True

    def test_list_is_json_primitive(self):
        """Test that list is a JSON primitive."""
        assert Validator.is_json_primitive([]) is True
        assert Validator.is_json_primitive([1, 2, 3]) is True

    def test_object_is_not_json_primitive(self):
        """Test that custom objects are not JSON primitives."""
        class CustomObject:
            pass

        assert Validator.is_json_primitive(CustomObject()) is False

    def test_tuple_is_not_json_primitive(self):
        """Test that tuple is not a JSON primitive."""
        assert Validator.is_json_primitive(()) is False
        assert Validator.is_json_primitive((1, 2)) is False


class TestValidatorCannotBeInstantiated:
    """Test that Validator class cannot be instantiated."""

    def test_validator_cannot_be_instantiated(self):
        """Test that Validator cannot be instantiated."""
        with pytest.raises(TypeError, match="Validator cannot be instantiated"):
            Validator()
