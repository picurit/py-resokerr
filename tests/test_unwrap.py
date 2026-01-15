"""Tests for unwrap methods in Ok and Err classes."""
import pytest
from typing import Optional

from resokerr.core import Ok, Err


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
