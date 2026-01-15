"""Tests for the map functionality on Ok and Err instances.

This module provides comprehensive test coverage for the `map` method,
including edge cases, type transformations, and preservation of context.
"""
import pytest
from types import MappingProxyType
from typing import Optional, List, Dict, Any

from resokerr.core import Ok, Err, MessageTrace, TraceSeverityLevel


# ============================================================================
# Test Fixtures and Helpers
# ============================================================================

class CustomError(Exception):
    """Custom exception for testing cause transformations."""
    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code = code


class User:
    """Simple class for testing object transformations."""
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return False
        return self.name == other.name and self.age == other.age


# ============================================================================
# Ok.map() Tests
# ============================================================================

class TestOkMapBasic:
    """Test basic map functionality on Ok instances."""

    def test_map_int_to_int(self):
        """Test mapping an integer value to another integer."""
        ok: Ok[int, str] = Ok(value=5)
        result = ok.map(lambda x: x * 2)
        
        assert result.value == 10
        assert result.is_ok()
        assert isinstance(result, Ok)

    def test_map_int_to_string(self):
        """Test mapping an integer to a string (type transformation)."""
        ok: Ok[int, str] = Ok(value=42)
        result = ok.map(lambda x: f"Value is {x}")
        
        assert result.value == "Value is 42"
        assert isinstance(result.value, str)

    def test_map_string_to_int(self):
        """Test mapping a string to an integer."""
        ok: Ok[str, str] = Ok(value="123")
        result = ok.map(int)
        
        assert result.value == 123
        assert isinstance(result.value, int)

    def test_map_to_complex_type(self):
        """Test mapping to a complex object type."""
        ok: Ok[Dict[str, Any], str] = Ok(value={"name": "Alice", "age": 30})
        result = ok.map(lambda d: User(d["name"], d["age"]))
        
        assert result.value == User("Alice", 30)
        assert isinstance(result.value, User)

    def test_map_from_complex_type(self):
        """Test mapping from a complex object to a simple type."""
        ok: Ok[User, str] = Ok(value=User("Bob", 25))
        result = ok.map(lambda u: u.name.upper())
        
        assert result.value == "BOB"

    def test_map_list_transformation(self):
        """Test mapping a list with element-wise transformation."""
        ok: Ok[List[int], str] = Ok(value=[1, 2, 3, 4, 5])
        result = ok.map(lambda lst: [x ** 2 for x in lst])
        
        assert result.value == [1, 4, 9, 16, 25]

    def test_map_chaining(self):
        """Test chaining multiple map operations."""
        ok: Ok[int, str] = Ok(value=5)
        result = ok.map(lambda x: x * 2).map(lambda x: x + 1).map(str)
        
        assert result.value == "11"

    def test_map_with_identity_function(self):
        """Test map with identity function returns equivalent value."""
        ok: Ok[str, str] = Ok(value="unchanged")
        result = ok.map(lambda x: x)
        
        assert result.value == "unchanged"
        # Verify it's a new instance (immutability)
        assert result is not ok


class TestOkMapWithNoneValue:
    """Test map behavior when Ok.value is None."""

    def test_map_none_value_does_not_call_function(self):
        """Test that map does not call the function when value is None."""
        call_count = 0
        
        def failing_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2
        
        ok: Ok[int, str] = Ok(value=None)
        result = ok.map(failing_function)
        
        assert result.value is None
        assert call_count == 0  # Function was never called

    def test_map_none_returns_ok_with_none(self):
        """Test that mapping None returns an Ok with None value."""
        ok: Ok[int, str] = Ok(value=None)
        result = ok.map(lambda x: x * 2)
        
        assert result.value is None
        assert result.is_ok()
        assert not result.has_value()

    def test_map_none_preserves_messages(self):
        """Test that mapping None preserves existing messages."""
        ok: Ok[int, str] = Ok(
            value=None,
            messages=(MessageTrace.info("Important context"),)
        )
        result = ok.map(lambda x: x * 2)
        
        assert len(result.messages) == 1
        assert result.messages[0].message == "Important context"

    def test_map_none_preserves_metadata(self):
        """Test that mapping None preserves metadata."""
        metadata = {"source": "test", "timestamp": "2026-01-15"}
        ok: Ok[int, str] = Ok(value=None, metadata=metadata)
        result = ok.map(lambda x: x * 2)
        
        assert result.metadata is not None
        assert result.metadata["source"] == "test"


class TestOkMapPreservesContext:
    """Test that map preserves messages and metadata."""

    def test_map_preserves_info_messages(self):
        """Test that info messages are preserved after map."""
        ok = Ok(value=10).with_info("Step 1 complete", code="INFO_001")
        result = ok.map(lambda x: x * 2)
        
        assert len(result.info_messages) == 1
        assert result.info_messages[0].message == "Step 1 complete"
        assert result.info_messages[0].code == "INFO_001"

    def test_map_preserves_warning_messages(self):
        """Test that warning messages are preserved after map."""
        ok = Ok(value=10).with_warning("Deprecated usage", code="WARN_001")
        result = ok.map(lambda x: x * 2)
        
        assert len(result.warning_messages) == 1
        assert result.warning_messages[0].message == "Deprecated usage"

    def test_map_preserves_multiple_messages(self):
        """Test that multiple messages of different types are preserved."""
        ok = (Ok(value=10)
              .with_info("Info 1")
              .with_warning("Warning 1")
              .with_info("Info 2"))
        result = ok.map(lambda x: x * 2)
        
        assert len(result.messages) == 3
        assert len(result.info_messages) == 2
        assert len(result.warning_messages) == 1

    def test_map_preserves_metadata(self):
        """Test that metadata is preserved after map."""
        metadata = {"user_id": 123, "request_id": "abc-123"}
        ok: Ok[int, str] = Ok(value=10, metadata=metadata)
        result = ok.map(lambda x: x * 2)
        
        assert result.metadata is not None
        assert result.metadata["user_id"] == 123
        assert result.metadata["request_id"] == "abc-123"

    def test_map_metadata_remains_immutable(self):
        """Test that metadata remains immutable after map."""
        ok: Ok[int, str] = Ok(value=10, metadata={"key": "value"})
        result = ok.map(lambda x: x * 2)
        
        assert isinstance(result.metadata, MappingProxyType)


class TestOkMapImmutability:
    """Test that map returns new instances and preserves immutability."""

    def test_map_returns_new_instance(self):
        """Test that map returns a new Ok instance."""
        original: Ok[int, str] = Ok(value=5)
        mapped = original.map(lambda x: x * 2)
        
        assert original is not mapped
        assert original.value == 5  # Original unchanged
        assert mapped.value == 10

    def test_original_unchanged_after_map(self):
        """Test that the original Ok is completely unchanged."""
        original = (Ok(value=5)
                    .with_info("Original info")
                    .with_metadata({"key": "value"}))
        
        _ = original.map(lambda x: x * 100)
        
        assert original.value == 5
        assert len(original.messages) == 1
        assert original.metadata is not None
        assert original.metadata["key"] == "value"


class TestOkMapEdgeCases:
    """Test edge cases for Ok.map()."""

    def test_map_returning_none(self):
        """Test map function that returns None."""
        ok: Ok[int, str] = Ok(value=5)
        result = ok.map(lambda x: None)
        
        assert result.value is None
        assert result.is_ok()

    def test_map_with_exception_in_function(self):
        """Test that exceptions in map function propagate normally."""
        ok: Ok[int, str] = Ok(value=5)
        
        with pytest.raises(ZeroDivisionError):
            ok.map(lambda x: x / 0)

    def test_map_with_bool_result(self):
        """Test mapping to boolean type."""
        ok: Ok[int, str] = Ok(value=0)
        result = ok.map(lambda x: x > 0)
        
        assert result.value is False
        assert result.is_ok()

    def test_map_with_optional_result(self):
        """Test mapping that may return None conditionally."""
        ok: Ok[int, str] = Ok(value=5)
        result = ok.map(lambda x: x * 2 if x > 10 else None)
        
        assert result.value is None  # Because 5 <= 10

    def test_map_empty_string(self):
        """Test mapping with empty string value."""
        ok: Ok[str, str] = Ok(value="")
        result = ok.map(lambda s: len(s))
        
        assert result.value == 0

    def test_map_zero_value(self):
        """Test mapping with zero value (falsy but not None)."""
        ok: Ok[int, str] = Ok(value=0)
        result = ok.map(lambda x: x + 100)
        
        assert result.value == 100  # Zero was mapped, not skipped

    def test_map_false_value(self):
        """Test mapping with False value (falsy but not None)."""
        ok: Ok[bool, str] = Ok(value=False)
        result = ok.map(lambda x: not x)
        
        assert result.value is True

    def test_map_empty_list(self):
        """Test mapping with empty list (falsy but not None)."""
        ok: Ok[List[int], str] = Ok(value=[])
        result = ok.map(lambda lst: len(lst))
        
        assert result.value == 0


# ============================================================================
# Err.map() Tests
# ============================================================================

class TestErrMapBasic:
    """Test basic map functionality on Err instances."""

    def test_map_exception_to_string(self):
        """Test mapping an exception cause to a string."""
        err: Err[ValueError, str] = Err(cause=ValueError("Invalid input"))
        result = err.map(lambda e: str(e))
        
        assert result.cause == "Invalid input"
        assert result.is_err()

    def test_map_exception_to_dict(self):
        """Test mapping an exception to a dictionary."""
        custom_err = CustomError("Failed", code=42)
        err: Err[CustomError, str] = Err(cause=custom_err)
        result = err.map(lambda e: {"message": str(e), "code": e.code})
        
        assert result.cause == {"message": "Failed", "code": 42}

    def test_map_string_cause_to_exception(self):
        """Test mapping a string cause to an exception object."""
        err: Err[str, str] = Err(cause="Something went wrong")
        result = err.map(lambda s: ValueError(s))
        
        assert isinstance(result.cause, ValueError)
        assert str(result.cause) == "Something went wrong"

    def test_map_error_code_extraction(self):
        """Test extracting just an error code from an exception."""
        err: Err[CustomError, str] = Err(cause=CustomError("Error", code=500))
        result = err.map(lambda e: e.code)
        
        assert result.cause == 500

    def test_map_chaining_on_err(self):
        """Test chaining multiple map operations on Err."""
        err: Err[int, str] = Err(cause=100)
        result = err.map(lambda x: x // 2).map(lambda x: x * 3).map(str)
        
        assert result.cause == "150"


class TestErrMapWithNoneCause:
    """Test map behavior when Err.cause is None."""

    def test_map_none_cause_does_not_call_function(self):
        """Test that map does not call the function when cause is None."""
        call_count = 0
        
        def failing_function(e: Exception) -> str:
            nonlocal call_count
            call_count += 1
            return str(e)
        
        err: Err[Exception, str] = Err(cause=None)
        result = err.map(failing_function)
        
        assert result.cause is None
        assert call_count == 0

    def test_map_none_cause_returns_err_with_none(self):
        """Test that mapping None cause returns an Err with None cause."""
        err: Err[ValueError, str] = Err(cause=None)
        result = err.map(lambda e: str(e))
        
        assert result.cause is None
        assert result.is_err()
        assert not result.has_cause()

    def test_map_none_cause_preserves_error_messages(self):
        """Test that mapping None cause preserves error messages."""
        err: Err[ValueError, str] = Err(
            cause=None,
            messages=(MessageTrace.error("Critical failure", code="ERR_001"),)
        )
        result = err.map(lambda e: str(e))
        
        assert len(result.error_messages) == 1
        assert result.error_messages[0].message == "Critical failure"


class TestErrMapPreservesContext:
    """Test that map preserves messages and metadata on Err."""

    def test_map_preserves_error_messages(self):
        """Test that error messages are preserved after map."""
        err = Err(cause=ValueError("Bad")).with_error("Validation failed")
        result = err.map(lambda e: str(e))
        
        assert len(result.error_messages) == 1
        assert result.error_messages[0].message == "Validation failed"

    def test_map_preserves_info_messages(self):
        """Test that info messages are preserved after map."""
        err = Err(cause=ValueError("Bad")).with_info("Context: user input")
        result = err.map(lambda e: str(e))
        
        assert len(result.info_messages) == 1
        assert result.info_messages[0].message == "Context: user input"

    def test_map_preserves_warning_messages(self):
        """Test that warning messages are preserved after map."""
        err = Err(cause=ValueError("Bad")).with_warning("Retryable error")
        result = err.map(lambda e: str(e))
        
        assert len(result.warning_messages) == 1

    def test_map_preserves_all_message_types(self):
        """Test that all message types are preserved after map."""
        err = (Err(cause=ValueError("Error"))
               .with_error("Error message")
               .with_warning("Warning message")
               .with_info("Info message"))
        result = err.map(lambda e: str(e))
        
        assert len(result.error_messages) == 1
        assert len(result.warning_messages) == 1
        assert len(result.info_messages) == 1
        assert len(result.messages) == 3

    def test_map_preserves_metadata(self):
        """Test that metadata is preserved after map."""
        metadata = {"trace_id": "xyz-789", "retry_count": 3}
        err: Err[ValueError, str] = Err(cause=ValueError("Error"), metadata=metadata)
        result = err.map(lambda e: str(e))
        
        assert result.metadata is not None
        assert result.metadata["trace_id"] == "xyz-789"
        assert result.metadata["retry_count"] == 3


class TestErrMapImmutability:
    """Test that map returns new instances and preserves immutability."""

    def test_map_returns_new_err_instance(self):
        """Test that map returns a new Err instance."""
        original: Err[int, str] = Err(cause=100)
        mapped = original.map(lambda x: x * 2)
        
        assert original is not mapped
        assert original.cause == 100
        assert mapped.cause == 200

    def test_original_err_unchanged_after_map(self):
        """Test that the original Err is completely unchanged."""
        original = (Err(cause=ValueError("Original"))
                    .with_error("Original error")
                    .with_metadata({"key": "value"}))
        
        _ = original.map(lambda e: RuntimeError(str(e)))
        
        assert isinstance(original.cause, ValueError)
        assert len(original.messages) == 1
        assert original.metadata is not None


class TestErrMapEdgeCases:
    """Test edge cases for Err.map()."""

    def test_map_returning_none(self):
        """Test map function that returns None."""
        err: Err[int, str] = Err(cause=5)
        result = err.map(lambda x: None)
        
        assert result.cause is None
        assert result.is_err()

    def test_map_with_exception_in_function(self):
        """Test that exceptions in map function propagate normally."""
        err: Err[int, str] = Err(cause=5)
        
        with pytest.raises(ZeroDivisionError):
            err.map(lambda x: x / 0)

    def test_map_wrapped_exception(self):
        """Test wrapping one exception in another."""
        err: Err[ValueError, str] = Err(cause=ValueError("Inner"))
        result = err.map(lambda e: RuntimeError(f"Wrapped: {e}"))
        
        assert isinstance(result.cause, RuntimeError)
        assert "Wrapped" in str(result.cause)


# ============================================================================
# Type Safety and Integration Tests
# ============================================================================

class TestMapTypeSafety:
    """Test type transformation and type safety."""

    def test_ok_map_changes_value_type(self):
        """Verify that Ok.map correctly changes the value type."""
        ok: Ok[int, str] = Ok(value=42)
        result: Ok[str, str] = ok.map(str)
        
        # This is mainly a type-checking test
        assert isinstance(result.value, str)
        assert result.value == "42"

    def test_err_map_changes_cause_type(self):
        """Verify that Err.map correctly changes the cause type."""
        err: Err[Exception, str] = Err(cause=ValueError("test"))
        result: Err[str, str] = err.map(str)
        
        assert isinstance(result.cause, str)

    def test_ok_map_preserves_message_type(self):
        """Test that message type M is preserved through map."""
        # Using a custom message type
        ok: Ok[int, Dict[str, Any]] = Ok(
            value=5,
            messages=(MessageTrace.info({"key": "custom_message"}),)
        )
        result = ok.map(lambda x: x * 2)
        
        assert result.messages[0].message == {"key": "custom_message"}

    def test_err_map_preserves_message_type(self):
        """Test that message type M is preserved through map on Err."""
        err: Err[int, Dict[str, Any]] = Err(
            cause=100,
            messages=(MessageTrace.error({"error_code": 500}),)
        )
        result = err.map(str)
        
        assert result.messages[0].message == {"error_code": 500}


class TestMapIntegrationWithOtherMethods:
    """Test map integration with other Ok/Err methods."""

    def test_ok_map_then_with_info(self):
        """Test map followed by with_info on Ok."""
        ok = Ok(value=5)
        result = ok.map(lambda x: x * 2).with_info("Transformation complete")
        
        assert result.value == 10
        assert len(result.info_messages) == 1

    def test_ok_with_info_then_map(self):
        """Test with_info followed by map on Ok."""
        ok = Ok(value=5).with_info("Before transformation")
        result = ok.map(lambda x: x * 2)
        
        assert result.value == 10
        assert len(result.info_messages) == 1
        assert result.info_messages[0].message == "Before transformation"

    def test_ok_map_then_with_metadata(self):
        """Test map followed by with_metadata on Ok."""
        ok = Ok(value=5)
        result = ok.map(lambda x: x * 2).with_metadata({"computed": True})
        
        assert result.value == 10
        assert result.metadata is not None
        assert result.metadata["computed"] is True

    def test_err_map_then_with_error(self):
        """Test map followed by with_error on Err."""
        err = Err(cause=ValueError("Bad"))
        result = err.map(str).with_error("Additional context")
        
        assert result.cause == "Bad"
        assert len(result.error_messages) == 1

    def test_ok_unwrap_after_map(self):
        """Test unwrap after map on Ok."""
        ok: Ok[int, str] = Ok(value=5)
        result = ok.map(lambda x: x * 2)
        
        assert result.unwrap() == 10
        assert result.unwrap(default=0) == 10

    def test_ok_unwrap_after_map_none(self):
        """Test unwrap after map when value becomes None."""
        ok: Ok[int, str] = Ok(value=5)
        result = ok.map(lambda x: None)
        
        assert result.unwrap() is None
        assert result.unwrap(default=42) == 42

    def test_err_unwrap_after_map(self):
        """Test unwrap after map on Err."""
        err: Err[int, str] = Err(cause=100)
        result = err.map(lambda x: x * 2)
        
        assert result.unwrap() == 200


class TestMapPatterns:
    """Test common usage patterns with map."""

    def test_data_transformation_pipeline(self):
        """Test a complete data transformation pipeline."""
        # Simulate a data processing pipeline
        raw_data: Ok[str, str] = Ok(value="  42  ")
        
        result = (raw_data
                  .map(str.strip)           # Clean whitespace
                  .map(int)                 # Parse to int
                  .map(lambda x: x * 2)     # Double the value
                  .with_info("Data processed successfully"))
        
        assert result.value == 84
        assert result.has_info()

    def test_error_normalization_pattern(self):
        """Test normalizing different error types to a common format."""
        # Simulate normalizing various errors to a standard format
        err: Err[CustomError, str] = Err(cause=CustomError("DB connection failed", code=503))
        
        result = err.map(lambda e: {
            "error_type": type(e).__name__,
            "message": str(e),
            "code": e.code
        })
        
        assert result.cause == {
            "error_type": "CustomError",
            "message": "DB connection failed",
            "code": 503
        }

    def test_optional_field_extraction(self):
        """Test extracting an optional field from a result."""
        user_data: Ok[Dict[str, Any], str] = Ok(value={
            "name": "Alice",
            "email": "alice@example.com",
            "phone": None
        })
        
        name_result = user_data.map(lambda d: d.get("name"))
        phone_result = user_data.map(lambda d: d.get("phone"))
        
        assert name_result.value == "Alice"
        assert phone_result.value is None  # Extracted None from dict
