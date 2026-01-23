"""Tests for Ok and Err to_dict() serialization methods."""
import pytest
from typing import Any, Dict

from resokerr.core import Ok, Err, MessageTrace

class TestOkToDict:
    """Test Ok.to_dict() serialization method."""

    def test_to_dict_basic_structure(self):
        """Test that to_dict returns correct basic structure."""
        ok = Ok(value=42)
        result = ok.to_dict()

        assert result["is_ok"] is True
        assert result["is_err"] is False
        assert result["value"] == 42
        assert result["messages"] == []
        assert "metadata" not in result

    def test_to_dict_with_string_value(self):
        """Test to_dict with string value."""
        ok = Ok(value="success")
        result = ok.to_dict()

        assert result["value"] == "success"
        assert result["is_ok"] is True

    def test_to_dict_with_none_value(self):
        """Test to_dict with None value."""
        ok = Ok(value=None)
        result = ok.to_dict()

        assert result["value"] is None
        assert result["is_ok"] is True

    def test_to_dict_with_numeric_values(self):
        """Test to_dict with numeric value types."""
        int_ok = Ok(value=42)
        float_ok = Ok(value=3.14)

        assert int_ok.to_dict()["value"] == 42
        assert float_ok.to_dict()["value"] == 3.14

    def test_to_dict_with_bool_value(self):
        """Test to_dict with boolean value."""
        ok = Ok(value=True)
        result = ok.to_dict()

        assert result["value"] is True

    def test_to_dict_with_messages(self):
        """Test to_dict includes serialized messages."""
        ok = (Ok(value=42)
              .with_info("Step 1 completed", code="STEP_1")
              .with_warning("Minor issue", details={"field": "optional"}))
        result = ok.to_dict()

        assert len(result["messages"]) == 2
        assert result["messages"][0]["message"] == "Step 1 completed"
        assert result["messages"][0]["severity"] == "info"
        assert result["messages"][0]["code"] == "STEP_1"
        assert result["messages"][1]["message"] == "Minor issue"
        assert result["messages"][1]["severity"] == "warning"
        assert result["messages"][1]["details"]["field"] == "optional"

    def test_to_dict_with_metadata(self):
        """Test to_dict includes metadata when present."""
        ok = Ok(value=42, metadata={"timestamp": "2026-01-23", "user_id": 123})
        result = ok.to_dict()

        assert "metadata" in result
        assert result["metadata"]["timestamp"] == "2026-01-23"
        assert result["metadata"]["user_id"] == 123

    def test_to_dict_metadata_is_regular_dict(self):
        """Test that metadata in to_dict is a regular dict, not MappingProxyType."""
        from types import MappingProxyType

        ok = Ok(value=42, metadata={"key": "value"})
        result = ok.to_dict()

        assert isinstance(result["metadata"], dict)
        assert not isinstance(result["metadata"], MappingProxyType)

    def test_to_dict_with_object_having_to_dict_method(self):
        """Test to_dict with custom object implementing to_dict()."""
        class SerializableData:
            def __init__(self, code: str, detail: str):
                self.code = code
                self.detail = detail

            def to_dict(self) -> Dict[str, Any]:
                return {"code": self.code, "detail": self.detail}

        custom_obj = SerializableData("DATA_001", "Custom data")
        ok = Ok(value=custom_obj)
        result = ok.to_dict()

        assert result["value"] == {"code": "DATA_001", "detail": "Custom data"}

    def test_to_dict_with_non_serializable_object_fallback_to_str(self):
        """Test to_dict falls back to str() for objects without to_dict()."""
        class NonSerializable:
            def __init__(self, value: str):
                self.value = value

            def __str__(self) -> str:
                return f"NonSerializable({self.value})"

        obj = NonSerializable("test")
        ok = Ok(value=obj)
        result = ok.to_dict()

        assert result["value"] == "NonSerializable(test)"

    def test_to_dict_returns_new_dict_instance(self):
        """Test that to_dict returns a new dict each time (immutability)."""
        ok = Ok(value=42, metadata={"key": "value"})

        dict1 = ok.to_dict()
        dict2 = ok.to_dict()

        assert dict1 is not dict2
        assert dict1["metadata"] is not dict2["metadata"]

    def test_to_dict_with_all_fields(self):
        """Test to_dict with all fields present."""
        ok = (Ok(value={"data": 123}, metadata={"request_id": "abc"})
              .with_success("Operation done")
              .with_info("Processing complete")
              .with_warning("Minor warning"))
        result = ok.to_dict()

        assert result["is_ok"] is True
        assert result["is_err"] is False
        assert result["value"] == {"data": 123}
        assert len(result["messages"]) == 3
        assert result["metadata"]["request_id"] == "abc"


class TestErrToDict:
    """Test Err.to_dict() serialization method."""

    def test_to_dict_basic_structure(self):
        """Test that to_dict returns correct basic structure."""
        err = Err(cause="Something went wrong")
        result = err.to_dict()

        assert result["is_ok"] is False
        assert result["is_err"] is True
        assert result["cause"] == "Something went wrong"
        assert result["messages"] == []
        assert "metadata" not in result

    def test_to_dict_with_none_cause(self):
        """Test to_dict with None cause."""
        err = Err(cause=None)
        result = err.to_dict()

        assert result["cause"] is None
        assert result["is_err"] is True

    def test_to_dict_with_exception_cause(self):
        """Test to_dict with exception as cause (falls back to str)."""
        err = Err(cause=ValueError("Invalid input"))
        result = err.to_dict()

        # Exceptions don't have to_dict, so they're converted to string
        assert "Invalid input" in result["cause"]
        assert result["is_err"] is True

    def test_to_dict_with_messages(self):
        """Test to_dict includes serialized messages."""
        err = (Err(cause="Error")
               .with_error("Validation failed", code="VAL_001")
               .with_info("Input received", details={"length": 10}))
        result = err.to_dict()

        assert len(result["messages"]) == 2
        assert result["messages"][0]["message"] == "Validation failed"
        assert result["messages"][0]["severity"] == "error"
        assert result["messages"][0]["code"] == "VAL_001"
        assert result["messages"][1]["message"] == "Input received"
        assert result["messages"][1]["severity"] == "info"
        assert result["messages"][1]["details"]["length"] == 10

    def test_to_dict_with_metadata(self):
        """Test to_dict includes metadata when present."""
        err = Err(cause="Error", metadata={"request_id": "xyz-789", "timestamp": "2026-01-23"})
        result = err.to_dict()

        assert "metadata" in result
        assert result["metadata"]["request_id"] == "xyz-789"
        assert result["metadata"]["timestamp"] == "2026-01-23"

    def test_to_dict_metadata_is_regular_dict(self):
        """Test that metadata in to_dict is a regular dict, not MappingProxyType."""
        from types import MappingProxyType

        err = Err(cause="Error", metadata={"key": "value"})
        result = err.to_dict()

        assert isinstance(result["metadata"], dict)
        assert not isinstance(result["metadata"], MappingProxyType)

    def test_to_dict_with_object_having_to_dict_method(self):
        """Test to_dict with custom cause implementing to_dict()."""
        class SerializableError:
            def __init__(self, code: str, message: str):
                self.code = code
                self.message = message

            def to_dict(self) -> Dict[str, Any]:
                return {"code": self.code, "message": self.message}

        custom_err = SerializableError("E001", "Custom error message")
        err = Err(cause=custom_err)
        result = err.to_dict()

        assert result["cause"] == {"code": "E001", "message": "Custom error message"}

    def test_to_dict_with_non_serializable_object_fallback_to_str(self):
        """Test to_dict falls back to str() for causes without to_dict()."""
        class NonSerializableError:
            def __init__(self, code: str):
                self.code = code

            def __str__(self) -> str:
                return f"Error[{self.code}]"

        obj = NonSerializableError("E001")
        err = Err(cause=obj)
        result = err.to_dict()

        assert result["cause"] == "Error[E001]"

    def test_to_dict_returns_new_dict_instance(self):
        """Test that to_dict returns a new dict each time (immutability)."""
        err = Err(cause="Error", metadata={"key": "value"})

        dict1 = err.to_dict()
        dict2 = err.to_dict()

        assert dict1 is not dict2
        assert dict1["metadata"] is not dict2["metadata"]

    def test_to_dict_with_all_fields(self):
        """Test to_dict with all fields present."""
        err = (Err(cause={"error_type": "ValidationError"}, metadata={"request_id": "abc"})
               .with_error("Primary error")
               .with_warning("Warning context")
               .with_info("Debug info"))
        result = err.to_dict()

        assert result["is_ok"] is False
        assert result["is_err"] is True
        assert result["cause"] == {"error_type": "ValidationError"}
        assert len(result["messages"]) == 3
        assert result["metadata"]["request_id"] == "abc"


class TestOkErrToDictConsistency:
    """Test consistency between Ok and Err to_dict implementations."""

    def test_ok_err_have_inverse_boolean_flags(self):
        """Test that Ok and Err have inverse is_ok/is_err values."""
        ok = Ok(value=42)
        err = Err(cause="Error")

        ok_dict = ok.to_dict()
        err_dict = err.to_dict()

        assert ok_dict["is_ok"] is True
        assert ok_dict["is_err"] is False
        assert err_dict["is_ok"] is False
        assert err_dict["is_err"] is True

    def test_messages_serialization_identical(self):
        """Test that message serialization is consistent between Ok and Err."""
        msg = MessageTrace.info("Test message", code="TEST_001", details={"key": "value"})

        ok = Ok(value=42, messages=[msg])
        err = Err(cause="Error", messages=[msg])

        ok_msg = ok.to_dict()["messages"][0]
        err_msg = err.to_dict()["messages"][0]

        assert ok_msg == err_msg
        assert ok_msg["message"] == "Test message"
        assert ok_msg["severity"] == "info"
        assert ok_msg["code"] == "TEST_001"

    def test_metadata_serialization_identical(self):
        """Test that metadata serialization is consistent between Ok and Err."""
        metadata = {"timestamp": "2026-01-23", "request_id": "abc-123"}

        ok = Ok(value=42, metadata=metadata)
        err = Err(cause="Error", metadata=metadata)

        ok_metadata = ok.to_dict()["metadata"]
        err_metadata = err.to_dict()["metadata"]

        assert ok_metadata == err_metadata


class TestToDictJsonCompatibility:
    """Test that to_dict output is JSON-compatible."""

    def test_ok_to_dict_json_serializable(self):
        """Test that Ok.to_dict() output can be serialized to JSON."""
        import json

        ok = (Ok(value={"data": [1, 2, 3]}, metadata={"timestamp": "2026-01-23"})
              .with_info("Info message", code="INFO_001")
              .with_warning("Warning message", details={"field": "test"}))

        result = ok.to_dict()

        # Should not raise
        json_str = json.dumps(result)
        parsed = json.loads(json_str)

        assert parsed["is_ok"] is True
        assert parsed["value"]["data"] == [1, 2, 3]

    def test_err_to_dict_json_serializable(self):
        """Test that Err.to_dict() output can be serialized to JSON."""
        import json

        err = (Err(cause="Validation failed", metadata={"request_id": "abc"})
               .with_error("Error message", code="ERR_001")
               .with_info("Debug info", details={"context": "test"}))

        result = err.to_dict()

        # Should not raise
        json_str = json.dumps(result)
        parsed = json.loads(json_str)

        assert parsed["is_err"] is True
        assert parsed["cause"] == "Validation failed"

    def test_nested_serializable_objects(self):
        """Test to_dict with nested objects implementing to_dict."""
        class InnerData:
            def __init__(self, value: int):
                self.value = value

            def to_dict(self) -> Dict[str, Any]:
                return {"inner_value": self.value}

        class OuterData:
            def __init__(self, inner: InnerData):
                self.inner = inner

            def to_dict(self) -> Dict[str, Any]:
                return {"outer": self.inner.to_dict()}

        nested = OuterData(InnerData(42))
        ok = Ok(value=nested)
        result = ok.to_dict()

        assert result["value"] == {"outer": {"inner_value": 42}}


class TestToDictWithConvertedMessages:
    """Test to_dict behavior with converted messages (ERROR->WARNING in Ok, SUCCESS->INFO in Err)."""

    def test_ok_with_converted_error_messages(self):
        """Test Ok serializes converted ERROR messages correctly."""
        error_msg = MessageTrace.error("This was an error", code="ERR_001")
        ok = Ok(value=42, messages=[error_msg])

        result = ok.to_dict()

        # Error was converted to warning
        assert result["messages"][0]["severity"] == "warning"
        assert result["messages"][0]["message"] == "This was an error"
        assert "_converted_from" in result["messages"][0]["details"]

    def test_err_with_converted_success_messages(self):
        """Test Err serializes converted SUCCESS messages correctly."""
        success_msg = MessageTrace.success("This was a success", code="SUCCESS_001")
        err = Err(cause="Error", messages=[success_msg])

        result = err.to_dict()

        # Success was converted to info
        assert result["messages"][0]["severity"] == "info"
        assert result["messages"][0]["message"] == "This was a success"
        assert "_converted_from" in result["messages"][0]["details"]
