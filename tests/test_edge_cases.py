"""Additional edge case tests for comprehensive coverage."""
import pytest
from types import MappingProxyType
import sys
sys.path.insert(0, '/workspace/development/frappe-bench/apps/dendriva/dendriva/utils/py-resokerr/src')

from result import Ok, Err, Result, MessageTrace, TraceSeverityLevel


class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_ok_with_none_value_is_valid(self):
        """Test that Ok can explicitly have None as a valid value."""
        ok = Ok(value=None)
        assert ok.value is None
        assert not ok.has_value()
        assert ok.is_ok()

    def test_err_with_none_trace_is_valid(self):
        """Test that Err can have None as trace."""
        err = Err(trace=None)
        assert err.trace is None
        assert not err.has_trace()
        assert err.is_err()

    def test_empty_messages_tuple(self):
        """Test handling of empty message tuples."""
        ok = Ok(value=42, messages=())
        err = Err(trace="error", messages=())
        
        assert ok.messages == ()
        assert err.messages == ()
        assert not ok.has_info()
        assert not err.has_errors()

    def test_message_trace_with_none_details(self):
        """Test MessageTrace with explicit None details."""
        msg = MessageTrace(
            message="Test",
            severity=TraceSeverityLevel.INFO,
            details=None
        )
        assert msg.details is None

    def test_ok_preserves_message_order(self):
        """Test that messages maintain order when added."""
        ok = (Ok(value=1)
              .with_info("First")
              .with_warning("Second")
              .with_info("Third"))
        
        assert ok.messages[0].message == "First"
        assert ok.messages[1].message == "Second"
        assert ok.messages[2].message == "Third"

    def test_err_preserves_message_order(self):
        """Test that messages maintain order in Err."""
        err = (Err(trace="error")
               .with_info("First")
               .with_error("Second")
               .with_warning("Third"))
        
        assert err.messages[0].message == "First"
        assert err.messages[1].message == "Second"
        assert err.messages[2].message == "Third"

    def test_multiple_error_messages_in_ok_all_downgraded(self):
        """Test that multiple ERROR messages are all downgraded in Ok."""
        messages = [
            MessageTrace.error("Error 1"),
            MessageTrace.error("Error 2"),
            MessageTrace.error("Error 3")
        ]
        ok = Ok(value=42, messages=messages)
        
        assert len(ok.messages) == 3
        assert all(msg.severity == TraceSeverityLevel.WARNING for msg in ok.messages)
        assert all("downgraded" in msg.details for msg in ok.messages)

    def test_nested_metadata_structure(self):
        """Test complex nested metadata structures."""
        metadata = {
            "user": {
                "id": 123,
                "name": "John",
                "roles": ["admin", "user"]
            },
            "timestamp": "2026-01-09",
            "nested": {
                "level1": {
                    "level2": "deep value"
                }
            }
        }
        ok = Ok(value=42, metadata=metadata)
        
        assert ok.metadata["user"]["id"] == 123
        assert ok.metadata["nested"]["level1"]["level2"] == "deep value"

    def test_result_type_in_function_signature(self):
        """Test using Result type in function signatures."""
        def divide(a: float, b: float) -> Result[float, str]:
            if b == 0:
                return Err(trace="Division by zero")
            return Ok(value=a / b)
        
        success = divide(10, 2)
        failure = divide(10, 0)
        
        assert success.is_ok()
        assert success.value == 5.0
        assert failure.is_err()
        assert failure.trace == "Division by zero"

    def test_large_number_of_messages(self):
        """Test handling a large number of messages."""
        ok = Ok(value=42)
        for i in range(100):
            ok = ok.with_info(f"Message {i}")
        
        assert len(ok.messages) == 100
        assert ok.messages[0].message == "Message 0"
        assert ok.messages[99].message == "Message 99"

    def test_message_with_multiline_text(self):
        """Test messages with multiline text content."""
        multiline = """This is a
        multiline
        message
        with several lines"""
        
        ok = Ok(value=42).with_info(multiline)
        assert ok.messages[0].message == multiline

    def test_message_with_special_characters(self):
        """Test messages with special characters."""
        special = "Error: ñ, é, ü, 中文, 日本語, emoji 🚀"
        err = Err(trace="error").with_error(special)
        assert err.messages[0].message == special

    def test_metadata_with_callable_values(self):
        """Test metadata containing callable objects."""
        def callback():
            return "callback"
        
        metadata = {"handler": callback, "value": 42}
        ok = Ok(value=1, metadata=metadata)
        
        assert callable(ok.metadata["handler"])
        assert ok.metadata["handler"]() == "callback"

    def test_empty_string_values(self):
        """Test handling of empty strings."""
        ok = Ok(value="")
        err = Err(trace="")
        msg = MessageTrace.info("")
        
        assert ok.value == ""
        assert ok.has_value()
        assert err.trace == ""
        assert err.has_trace()
        assert msg.message == ""

    def test_boolean_values(self):
        """Test Ok with boolean values."""
        ok_true = Ok(value=True)
        ok_false = Ok(value=False)
        
        assert ok_true.value is True
        assert ok_false.value is False
        assert ok_true.has_value()
        assert ok_false.has_value()

    def test_zero_values(self):
        """Test Ok with zero values."""
        ok_zero = Ok(value=0)
        ok_zero_float = Ok(value=0.0)
        
        assert ok_zero.value == 0
        assert ok_zero_float.value == 0.0
        assert ok_zero.has_value()
        assert ok_zero_float.has_value()


class TestConcurrentUsage:
    """Test that instances are safe for concurrent access (due to immutability)."""

    def test_sharing_messages_between_instances(self):
        """Test that messages can be safely shared between Ok/Err instances."""
        shared_messages = [
            MessageTrace.info("Shared info"),
            MessageTrace.warning("Shared warning")
        ]
        
        ok1 = Ok(value=1, messages=shared_messages)
        ok2 = Ok(value=2, messages=shared_messages)
        err1 = Err(trace="error1", messages=shared_messages)
        
        # All should have the same messages (immutable)
        assert ok1.messages == ok2.messages
        assert ok1.messages == err1.messages
        
        # Modifying one shouldn't affect others
        ok3 = ok1.with_info("New message")
        assert len(ok3.messages) == 3
        assert len(ok1.messages) == 2
        assert len(ok2.messages) == 2

    def test_metadata_independence(self):
        """Test that metadata is independent between instances."""
        metadata = {"counter": 0}
        ok1 = Ok(value=1, metadata=metadata)
        
        # Modifying the original dict shouldn't affect ok1
        metadata["counter"] = 10
        assert ok1.metadata["counter"] == 0


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""

    def test_validation_scenario(self):
        """Test a realistic validation scenario."""
        def validate_user(data: dict) -> Result[dict, str]:
            result = Ok(value=data)
            
            if not data.get("email"):
                return Err(trace="Email is required")
            
            if not data.get("name"):
                result = result.with_warning("Name is missing")
            
            if not data.get("age"):
                result = result.with_warning("Age is missing")
            
            result = result.with_info("Validation complete")
            return result
        
        # Valid data
        valid = validate_user({"email": "test@test.com", "name": "John", "age": 30})
        assert valid.is_ok()
        assert valid.has_info()
        assert not valid.has_warnings()
        
        # Missing optional fields
        partial = validate_user({"email": "test@test.com"})
        assert partial.is_ok()
        assert len(partial.warning_messages) == 2
        
        # Missing required field
        invalid = validate_user({"name": "John"})
        assert invalid.is_err()
        assert "Email" in invalid.trace

    def test_pipeline_scenario(self):
        """Test a data processing pipeline scenario."""
        def parse_int(s: str) -> Result[int, str]:
            try:
                return Ok(value=int(s))
            except ValueError:
                return Err(trace=f"Cannot parse '{s}' as integer")
        
        def validate_positive(n: int) -> Result[int, str]:
            if n <= 0:
                return Err(trace="Number must be positive")
            return Ok(value=n)
        
        def process(s: str) -> Result[int, str]:
            result = parse_int(s)
            if result.is_err():
                return result
            
            return validate_positive(result.value)
        
        # Success path
        success = process("42")
        assert success.is_ok()
        assert success.value == 42
        
        # Parse failure
        parse_fail = process("abc")
        assert parse_fail.is_err()
        assert "Cannot parse" in parse_fail.trace
        
        # Validation failure
        validate_fail = process("-5")
        assert validate_fail.is_err()
        assert "positive" in validate_fail.trace

    def test_accumulating_diagnostics(self):
        """Test accumulating diagnostic information."""
        def analyze_code(code: str) -> Result[str, str]:
            result = Ok(value=code).with_info("Starting analysis")
            
            if "TODO" in code:
                result = result.with_warning("Contains TODO comments")
            
            if "FIXME" in code:
                result = result.with_warning("Contains FIXME comments")
            
            if len(code) > 1000:
                result = result.with_info("Large file detected")
            
            return result.with_info("Analysis complete")
        
        code_with_issues = """
        # TODO: Implement this function
        # FIXME: Bug in logic
        def process(): pass
        """
        
        result = analyze_code(code_with_issues)
        assert result.is_ok()
        assert len(result.info_messages) == 2
        assert len(result.warning_messages) == 2
