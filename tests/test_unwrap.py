"""Tests for unwrap methods in Ok and Err classes."""
import pytest
from typing import Any, Dict, Optional

from resokerr.core import Ok, Err


class CustomSerializable:
    """Helper class that implements to_dict() for testing."""
    def __init__(self, data: Any):
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        return {"data": self.data}

    def __repr__(self) -> str:
        return f"CustomSerializable({self.data!r})"


class NonSerializable:
    """Helper class without to_dict() for testing string fallback."""
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"NonSerializable({self.value})"


class TestOkUnwrap:
    """Test unwrap methods for Ok instances."""

    def test_unwrap_returns_value_when_present(self):
        """Test unwrap returns the contained value."""
        ok = Ok(value=42)
        assert ok.unwrap() == 42

    def test_unwrap_returns_none_when_value_is_none(self):
        """Test unwrap returns None when value is None."""
        ok = Ok(value=None)
        assert ok.unwrap() is None

    def test_unwrap_with_string_value(self):
        """Test unwrap with string value."""
        ok = Ok(value="success")
        assert ok.unwrap() == "success"

    def test_unwrap_with_complex_value(self):
        """Test unwrap with complex data structure."""
        value = {"status": "ok", "data": [1, 2, 3]}
        ok = Ok(value=value)
        result = ok.unwrap()
        assert result == value
        assert result["status"] == "ok"

    def test_unwrap_with_list_value(self):
        """Test unwrap with list value."""
        ok = Ok(value=[1, 2, 3])
        assert ok.unwrap() == [1, 2, 3]

    def test_unwrap_with_zero_value(self):
        """Test unwrap with zero (falsy but valid value)."""
        ok = Ok(value=0)
        assert ok.unwrap() == 0

    def test_unwrap_with_empty_string_value(self):
        """Test unwrap with empty string (falsy but valid value)."""
        ok = Ok(value="")
        assert ok.unwrap() == ""

    def test_unwrap_with_false_value(self):
        """Test unwrap with False (falsy but valid value)."""
        ok = Ok(value=False)
        assert ok.unwrap() is False


class TestOkUnwrapWithDefault:
    """Test unwrap with default value for Ok instances."""

    def test_unwrap_with_default_returns_value_when_present(self):
        """Test unwrap with default returns value when present."""
        ok = Ok(value=42)
        assert ok.unwrap(default=100) == 42

    def test_unwrap_with_default_returns_default_when_none(self):
        """Test unwrap with default returns default when value is None."""
        ok = Ok(value=None)
        assert ok.unwrap(default=100) == 100

    def test_unwrap_with_default_string(self):
        """Test unwrap with string default."""
        ok: Ok[Optional[str], str] = Ok(value=None)
        assert ok.unwrap(default="fallback") == "fallback"

    def test_unwrap_with_default_complex_type(self):
        """Test unwrap with complex default type."""
        default_dict = {"default": True}
        ok: Ok[Optional[dict], str] = Ok(value=None)
        assert ok.unwrap(default=default_dict) == default_dict

    def test_unwrap_with_default_zero(self):
        """Test unwrap with zero as default (falsy but valid)."""
        ok: Ok[Optional[int], str] = Ok(value=None)
        assert ok.unwrap(default=0) == 0

    def test_unwrap_with_default_empty_string(self):
        """Test unwrap with empty string as default."""
        ok: Ok[Optional[str], str] = Ok(value=None)
        assert ok.unwrap(default="") == ""

    def test_unwrap_with_none_default_when_value_exists(self):
        """Test that value is returned even with None default."""
        ok = Ok(value=42)
        assert ok.unwrap(default=None) == 42


class TestErrUnwrap:
    """Test unwrap methods for Err instances."""

    def test_unwrap_returns_cause_when_present(self):
        """Test unwrap returns the contained cause."""
        err = Err(cause="Something went wrong")
        assert err.unwrap() == "Something went wrong"

    def test_unwrap_returns_none_when_cause_is_none(self):
        """Test unwrap returns None when cause is None."""
        err = Err(cause=None)
        assert err.unwrap() is None

    def test_unwrap_with_exception_cause(self):
        """Test unwrap with exception as cause."""
        exception = ValueError("Invalid input")
        err = Err(cause=exception)
        result = err.unwrap()
        assert result == exception
        assert isinstance(result, ValueError)

    def test_unwrap_with_complex_cause(self):
        """Test unwrap with complex data structure as cause."""
        cause = {"error_type": "ValidationError", "fields": ["email", "name"]}
        err = Err(cause=cause)
        result = err.unwrap()
        assert result == cause
        assert result["error_type"] == "ValidationError"

    def test_unwrap_with_error_code_cause(self):
        """Test unwrap with error code as cause."""
        err = Err(cause=404)
        assert err.unwrap() == 404


class TestErrUnwrapWithDefault:
    """Test unwrap with default value for Err instances."""

    def test_unwrap_with_default_returns_cause_when_present(self):
        """Test unwrap with default returns cause when present."""
        err = Err(cause="Original error")
        assert err.unwrap(default="Fallback error") == "Original error"

    def test_unwrap_with_default_returns_default_when_none(self):
        """Test unwrap with default returns default when cause is None."""
        err = Err(cause=None)
        assert err.unwrap(default="Unknown error") == "Unknown error"

    def test_unwrap_with_default_exception(self):
        """Test unwrap with exception as default."""
        default_error = RuntimeError("Default error")
        err: Err[Optional[Exception], str] = Err(cause=None)
        result = err.unwrap(default=default_error)
        assert result == default_error
        assert isinstance(result, RuntimeError)

    def test_unwrap_with_default_complex_type(self):
        """Test unwrap with complex default type."""
        default_cause = {"error": "Unknown", "code": 500}
        err: Err[Optional[dict], str] = Err(cause=None)
        assert err.unwrap(default=default_cause) == default_cause


class TestUnwrapEdgeCases:
    """Test edge cases for unwrap methods."""

    def test_ok_unwrap_preserves_immutability(self):
        """Test that unwrap does not modify the Ok instance."""
        ok = Ok(value=42)
        _ = ok.unwrap()
        _ = ok.unwrap(default=100)
        
        # Original value should be preserved
        assert ok.value == 42

    def test_err_unwrap_preserves_immutability(self):
        """Test that unwrap does not modify the Err instance."""
        err = Err(cause="Error")
        _ = err.unwrap()
        _ = err.unwrap(default="Fallback")
        
        # Original cause should be preserved
        assert err.cause == "Error"

    def test_ok_unwrap_with_messages(self):
        """Test unwrap works with Ok containing messages."""
        ok = Ok(value=42).with_info("Info message").with_warning("Warning")
        assert ok.unwrap() == 42

    def test_err_unwrap_with_messages(self):
        """Test unwrap works with Err containing messages."""
        err = Err(cause="Error").with_error("Error message").with_info("Info")
        assert err.unwrap() == "Error"

    def test_ok_unwrap_with_metadata(self):
        """Test unwrap works with Ok containing metadata."""
        ok = Ok(value=42, metadata={"key": "value"})
        assert ok.unwrap() == 42
        assert ok.metadata["key"] == "value"

    def test_err_unwrap_with_metadata(self):
        """Test unwrap works with Err containing metadata."""
        err = Err(cause="Error", metadata={"key": "value"})
        assert err.unwrap() == "Error"
        assert err.metadata["key"] == "value"

    def test_ok_unwrap_chaining(self):
        """Test that Ok methods can be chained before unwrap."""
        result = (Ok(value=42)
                  .with_info("Step 1")
                  .with_warning("Step 2")
                  .unwrap())
        assert result == 42

    def test_err_unwrap_chaining(self):
        """Test that Err methods can be chained before unwrap."""
        result = (Err(cause="Error")
                  .with_error("Error detail")
                  .with_info("Context")
                  .unwrap())
        assert result == "Error"


class TestUnwrapTypeConsistency:
    """Test that unwrap methods maintain type consistency."""

    def test_ok_unwrap_returns_same_type_as_value(self):
        """Test Ok unwrap returns same type as contained value."""
        ok_int = Ok(value=42)
        ok_str = Ok(value="hello")
        ok_list = Ok(value=[1, 2, 3])
        
        assert isinstance(ok_int.unwrap(), int)
        assert isinstance(ok_str.unwrap(), str)
        assert isinstance(ok_list.unwrap(), list)

    def test_err_unwrap_returns_same_type_as_cause(self):
        """Test Err unwrap returns same type as contained cause."""
        err_str = Err(cause="error")
        err_exception = Err(cause=ValueError("error"))
        err_dict = Err(cause={"code": 500})
        
        assert isinstance(err_str.unwrap(), str)
        assert isinstance(err_exception.unwrap(), ValueError)
        assert isinstance(err_dict.unwrap(), dict)

    def test_ok_unwrap_default_is_returned_for_none_value(self):
        """Test that default of matching type is returned."""
        ok: Ok[Optional[int], str] = Ok(value=None)
        default = 100
        result = ok.unwrap(default=default)
        assert result == default
        assert isinstance(result, int)

    def test_err_unwrap_default_is_returned_for_none_cause(self):
        """Test that default of matching type is returned."""
        err: Err[Optional[str], str] = Err(cause=None)
        default = "fallback"
        result = err.unwrap(default=default)
        assert result == default
        assert isinstance(result, str)


class TestOkUnwrapAsDict:
    """Test unwrap with as_dict=True for Ok instances."""

    def test_unwrap_as_dict_with_dict_value(self):
        """Test as_dict=True with dict value returns it as-is."""
        value = {"name": "test", "count": 42}
        ok = Ok(value=value)
        result = ok.unwrap(as_dict=True)
        assert result == value
        assert isinstance(result, dict)

    def test_unwrap_as_dict_with_string_value(self):
        """Test as_dict=True with string returns it as-is (JSON primitive)."""
        ok = Ok(value="hello")
        result = ok.unwrap(as_dict=True)
        assert result == "hello"
        assert isinstance(result, str)

    def test_unwrap_as_dict_with_int_value(self):
        """Test as_dict=True with int returns it as-is (JSON primitive)."""
        ok = Ok(value=42)
        result = ok.unwrap(as_dict=True)
        assert result == 42
        assert isinstance(result, int)

    def test_unwrap_as_dict_with_list_value(self):
        """Test as_dict=True with list returns it as-is (JSON primitive)."""
        ok = Ok(value=[1, 2, 3])
        result = ok.unwrap(as_dict=True)
        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_unwrap_as_dict_with_bool_value(self):
        """Test as_dict=True with bool returns it as-is (JSON primitive)."""
        ok = Ok(value=True)
        result = ok.unwrap(as_dict=True)
        assert result is True

    def test_unwrap_as_dict_with_none_value(self):
        """Test as_dict=True with None value returns None."""
        ok = Ok(value=None)
        result = ok.unwrap(as_dict=True)
        assert result is None

    def test_unwrap_as_dict_with_serializable_object(self):
        """Test as_dict=True with object implementing to_dict()."""
        obj = CustomSerializable("test_data")
        ok = Ok(value=obj)
        result = ok.unwrap(as_dict=True)
        assert result == {"data": "test_data"}
        assert isinstance(result, dict)

    def test_unwrap_as_dict_with_non_serializable_object(self):
        """Test as_dict=True with object without to_dict() returns string."""
        obj = NonSerializable("test")
        ok = Ok(value=obj)
        result = ok.unwrap(as_dict=True)
        assert result == "NonSerializable(test)"
        assert isinstance(result, str)

    def test_unwrap_as_dict_false_returns_raw_value(self):
        """Test as_dict=False returns the raw value (default behavior)."""
        obj = CustomSerializable("test")
        ok = Ok(value=obj)
        result = ok.unwrap(as_dict=False)
        assert result is obj
        assert isinstance(result, CustomSerializable)

    def test_unwrap_as_dict_with_default_when_value_is_none(self):
        """Test as_dict=True with default when value is None."""
        default = {"default": True}
        ok: Ok[Optional[Dict[str, Any]], str] = Ok(value=None)
        result = ok.unwrap(default=default, as_dict=True)
        assert result == {"default": True}

    def test_unwrap_as_dict_with_serializable_default(self):
        """Test as_dict=True serializes the default value too."""
        default = CustomSerializable("default_data")
        ok: Ok[Optional[CustomSerializable], str] = Ok(value=None)
        result = ok.unwrap(default=default, as_dict=True)
        assert result == {"data": "default_data"}

    def test_unwrap_as_dict_ignores_default_when_value_present(self):
        """Test as_dict=True uses value, not default, when value is present."""
        obj = CustomSerializable("actual")
        default = CustomSerializable("default")
        ok = Ok(value=obj)
        result = ok.unwrap(default=default, as_dict=True)
        assert result == {"data": "actual"}

    def test_unwrap_as_dict_with_nested_structure(self):
        """Test as_dict=True with nested dict structure."""
        value = {"outer": {"inner": {"deep": 42}}, "list": [1, 2, 3]}
        ok = Ok(value=value)
        result = ok.unwrap(as_dict=True)
        assert result == value
        assert result["outer"]["inner"]["deep"] == 42


class TestErrUnwrapAsDict:
    """Test unwrap with as_dict=True for Err instances."""

    def test_unwrap_as_dict_with_string_cause(self):
        """Test as_dict=True with string cause returns it as-is."""
        err = Err(cause="error message")
        result = err.unwrap(as_dict=True)
        assert result == "error message"
        assert isinstance(result, str)

    def test_unwrap_as_dict_with_dict_cause(self):
        """Test as_dict=True with dict cause returns it as-is."""
        cause = {"error_code": 500, "message": "Internal error"}
        err = Err(cause=cause)
        result = err.unwrap(as_dict=True)
        assert result == cause
        assert isinstance(result, dict)

    def test_unwrap_as_dict_with_exception_cause(self):
        """Test as_dict=True with exception returns structured dict."""
        exception = ValueError("invalid input")
        err = Err(cause=exception)
        result = err.unwrap(as_dict=True)
        # Exceptions are serialized to structured dicts with name and message
        assert result == {"name": "ValueError", "message": "invalid input"}
        assert isinstance(result, dict)

    def test_unwrap_as_dict_with_chained_exception_cause(self):
        """Test as_dict=True with chained exception returns nested dict."""
        try:
            try:
                raise ValueError("root cause")
            except ValueError as inner:
                raise TypeError("wrapper") from inner
        except TypeError as chained:
            err = Err(cause=chained)
            result = err.unwrap(as_dict=True)

        assert isinstance(result, dict)
        assert result["name"] == "TypeError"
        assert result["message"] == "wrapper"
        assert "cause" in result
        assert result["cause"]["name"] == "ValueError"
        assert result["cause"]["message"] == "root cause"

    def test_unwrap_as_dict_with_serializable_cause(self):
        """Test as_dict=True with object implementing to_dict()."""
        obj = CustomSerializable("error_data")
        err = Err(cause=obj)
        result = err.unwrap(as_dict=True)
        assert result == {"data": "error_data"}
        assert isinstance(result, dict)

    def test_unwrap_as_dict_with_non_serializable_cause(self):
        """Test as_dict=True with object without to_dict() returns string."""
        obj = NonSerializable("error")
        err = Err(cause=obj)
        result = err.unwrap(as_dict=True)
        assert result == "NonSerializable(error)"
        assert isinstance(result, str)

    def test_unwrap_as_dict_with_none_cause(self):
        """Test as_dict=True with None cause returns None."""
        err = Err(cause=None)
        result = err.unwrap(as_dict=True)
        assert result is None

    def test_unwrap_as_dict_false_returns_raw_cause(self):
        """Test as_dict=False returns the raw cause (default behavior)."""
        obj = CustomSerializable("error")
        err = Err(cause=obj)
        result = err.unwrap(as_dict=False)
        assert result is obj
        assert isinstance(result, CustomSerializable)

    def test_unwrap_as_dict_with_default_when_cause_is_none(self):
        """Test as_dict=True with default when cause is None."""
        default = {"error": "unknown"}
        err: Err[Optional[Dict[str, Any]], str] = Err(cause=None)
        result = err.unwrap(default=default, as_dict=True)
        assert result == {"error": "unknown"}

    def test_unwrap_as_dict_with_serializable_default(self):
        """Test as_dict=True serializes the default value too."""
        default = CustomSerializable("default_error")
        err: Err[Optional[CustomSerializable], str] = Err(cause=None)
        result = err.unwrap(default=default, as_dict=True)
        assert result == {"data": "default_error"}

    def test_unwrap_as_dict_ignores_default_when_cause_present(self):
        """Test as_dict=True uses cause, not default, when cause is present."""
        obj = CustomSerializable("actual_error")
        default = CustomSerializable("default_error")
        err = Err(cause=obj)
        result = err.unwrap(default=default, as_dict=True)
        assert result == {"data": "actual_error"}

    def test_unwrap_as_dict_with_int_error_code(self):
        """Test as_dict=True with integer error code."""
        err = Err(cause=404)
        result = err.unwrap(as_dict=True)
        assert result == 404
        assert isinstance(result, int)


class TestUnwrapAsDictEdgeCases:
    """Test edge cases for unwrap with as_dict parameter."""

    def test_ok_unwrap_as_dict_preserves_immutability(self):
        """Test that unwrap(as_dict=True) doesn't modify Ok instance."""
        obj = CustomSerializable("test")
        ok = Ok(value=obj)
        _ = ok.unwrap(as_dict=True)
        # Original value should be preserved
        assert ok.value is obj
        assert isinstance(ok.value, CustomSerializable)

    def test_err_unwrap_as_dict_preserves_immutability(self):
        """Test that unwrap(as_dict=True) doesn't modify Err instance."""
        obj = CustomSerializable("error")
        err = Err(cause=obj)
        _ = err.unwrap(as_dict=True)
        # Original cause should be preserved
        assert err.cause is obj
        assert isinstance(err.cause, CustomSerializable)

    def test_ok_unwrap_as_dict_with_messages(self):
        """Test unwrap(as_dict=True) works with Ok containing messages."""
        obj = CustomSerializable("value")
        ok = Ok(value=obj).with_info("Info").with_warning("Warning")
        result = ok.unwrap(as_dict=True)
        assert result == {"data": "value"}

    def test_err_unwrap_as_dict_with_messages(self):
        """Test unwrap(as_dict=True) works with Err containing messages."""
        obj = CustomSerializable("error")
        err = Err(cause=obj).with_error("Error message")
        result = err.unwrap(as_dict=True)
        assert result == {"data": "error"}

    def test_ok_unwrap_as_dict_with_metadata(self):
        """Test unwrap(as_dict=True) works with Ok containing metadata."""
        obj = CustomSerializable("value")
        ok = Ok(value=obj, metadata={"key": "meta"})
        result = ok.unwrap(as_dict=True)
        assert result == {"data": "value"}
        # Metadata is separate from the unwrapped value
        assert ok.metadata["key"] == "meta"

    def test_err_unwrap_as_dict_with_metadata(self):
        """Test unwrap(as_dict=True) works with Err containing metadata."""
        obj = CustomSerializable("error")
        err = Err(cause=obj, metadata={"key": "meta"})
        result = err.unwrap(as_dict=True)
        assert result == {"data": "error"}
        assert err.metadata["key"] == "meta"

    def test_ok_unwrap_chaining_with_as_dict(self):
        """Test Ok methods can be chained before unwrap(as_dict=True)."""
        result = (Ok(value=CustomSerializable("chained"))
                  .with_info("Step 1")
                  .with_warning("Step 2")
                  .unwrap(as_dict=True))
        assert result == {"data": "chained"}

    def test_err_unwrap_chaining_with_as_dict(self):
        """Test Err methods can be chained before unwrap(as_dict=True)."""
        result = (Err(cause=CustomSerializable("chained_error"))
                  .with_error("Error detail")
                  .with_info("Context")
                  .unwrap(as_dict=True))
        assert result == {"data": "chained_error"}

    def test_unwrap_as_dict_explicit_false(self):
        """Test that as_dict=False explicitly works same as default."""
        obj = CustomSerializable("test")
        ok = Ok(value=obj)

        result_default = ok.unwrap()
        result_explicit_false = ok.unwrap(as_dict=False)

        assert result_default is result_explicit_false
        assert result_default is obj

    def test_unwrap_with_float_value_as_dict(self):
        """Test as_dict=True with float value (JSON primitive)."""
        ok = Ok(value=3.14159)
        result = ok.unwrap(as_dict=True)
        assert result == 3.14159
        assert isinstance(result, float)

    def test_unwrap_as_dict_with_empty_dict(self):
        """Test as_dict=True with empty dict."""
        ok = Ok(value={})
        result = ok.unwrap(as_dict=True)
        assert result == {}
        assert isinstance(result, dict)

    def test_unwrap_as_dict_with_empty_list(self):
        """Test as_dict=True with empty list."""
        ok = Ok(value=[])
        result = ok.unwrap(as_dict=True)
        assert result == []
        assert isinstance(result, list)
