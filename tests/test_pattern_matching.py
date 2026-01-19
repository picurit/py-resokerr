"""Tests for Python structural pattern matching with Ok and Err."""
import pytest

from resokerr.core import Ok, Err, Result, MessageTrace


class TestMatchTypeOnly:
    """Test pattern matching using type-only patterns."""

    def test_match_ok_type_only(self):
        """Test matching Ok using type-only pattern."""
        result: Result[int, str] = Ok(value=42)
        
        match result:
            case Ok():
                matched = "ok"
            case Err():
                matched = "err"
        
        assert matched == "ok"

    def test_match_err_type_only(self):
        """Test matching Err using type-only pattern."""
        result: Result[int, str] = Err(cause="error")
        
        match result:
            case Ok():
                matched = "ok"
            case Err():
                matched = "err"
        
        assert matched == "err"

    def test_match_type_only_with_messages(self):
        """Test type-only matching works regardless of messages."""
        ok_with_messages = Ok(value=10).with_info("Info message")
        err_with_messages = Err(cause="error").with_error("Error detail")
        
        def get_type(r: Result[int, str]) -> str:
            match r:
                case Ok():
                    return "ok"
                case Err():
                    return "err"
        
        assert get_type(ok_with_messages) == "ok"
        assert get_type(err_with_messages) == "err"

    def test_match_type_with_none_values(self):
        """Test type-only matching works with None values."""
        ok_none = Ok(value=None)
        err_none = Err(cause=None)
        
        def get_type(r: Result[int, str]) -> str:
            match r:
                case Ok():
                    return "ok"
                case Err():
                    return "err"
        
        assert get_type(ok_none) == "ok"
        assert get_type(err_none) == "err"


class TestMatchWithValueCapture:
    """Test pattern matching with value/cause capture."""

    def test_match_ok_capture_value(self):
        """Test capturing value from Ok in match pattern."""
        result: Result[int, str] = Ok(value=42)
        
        match result:
            case Ok(value=v):
                captured = v
            case Err(cause=c):
                captured = c
        
        assert captured == 42

    def test_match_err_capture_cause(self):
        """Test capturing cause from Err in match pattern."""
        result: Result[int, str] = Err(cause="Something failed")
        
        match result:
            case Ok(value=v):
                captured = v
            case Err(cause=c):
                captured = c
        
        assert captured == "Something failed"

    def test_match_ok_capture_none_value(self):
        """Test capturing None value from Ok."""
        result: Result[int, str] = Ok(value=None)
        
        match result:
            case Ok(value=v):
                captured = v
                matched_ok = True
            case Err(cause=_):
                captured = None
                matched_ok = False
        
        assert matched_ok is True
        assert captured is None

    def test_match_err_capture_exception(self):
        """Test capturing exception from Err in match pattern."""
        exception = ValueError("Invalid input")
        result: Result[int, Exception] = Err(cause=exception)
        
        match result:
            case Ok(value=v):
                captured = v
            case Err(cause=c):
                captured = c
        
        assert captured is exception
        assert isinstance(captured, ValueError)

    def test_match_ok_capture_complex_value(self):
        """Test capturing complex value from Ok."""
        data = {"user": "alice", "items": [1, 2, 3]}
        result: Result[dict, str] = Ok(value=data)
        
        match result:
            case Ok(value=v):
                captured = v
            case Err(cause=c):
                captured = {}
        
        assert captured == data
        assert captured["user"] == "alice"


class TestMatchWithMultipleFields:
    """Test pattern matching capturing multiple fields."""

    def test_match_ok_capture_value_and_messages(self):
        """Test capturing value and messages from Ok."""
        result = Ok(value=100).with_info("Step 1").with_warning("Warning 1")
        
        match result:
            case Ok(value=v, messages=msgs):
                captured_value = v
                captured_messages = msgs
            case Err():
                captured_value = None
                captured_messages = ()
        
        assert captured_value == 100
        assert len(captured_messages) == 2

    def test_match_err_capture_cause_and_messages(self):
        """Test capturing cause and messages from Err."""
        result = Err(cause="Failed").with_error("Details").with_info("Context")
        
        match result:
            case Err(cause=c, messages=msgs):
                captured_cause = c
                captured_messages = msgs
            case Ok():
                captured_cause = None
                captured_messages = ()
        
        assert captured_cause == "Failed"
        assert len(captured_messages) == 2

    def test_match_with_metadata_capture(self):
        """Test capturing metadata in match pattern."""
        metadata = {"request_id": "abc-123"}
        result = Ok(value=42, metadata=metadata)
        
        match result:
            case Ok(value=v, metadata=m):
                captured_value = v
                captured_metadata = m
            case Err():
                captured_value = None
                captured_metadata = None
        
        assert captured_value == 42
        assert captured_metadata["request_id"] == "abc-123"


class TestMatchInFunctions:
    """Test pattern matching in function contexts."""

    def test_function_with_match_returns_correct_type(self):
        """Test function using match returns correct type."""
        def process(result: Result[int, str]) -> str:
            match result:
                case Ok(value=v):
                    return f"Success: {v}"
                case Err(cause=c):
                    return f"Error: {c}"
        
        assert process(Ok(value=42)) == "Success: 42"
        assert process(Err(cause="failed")) == "Error: failed"

    def test_function_with_conditional_match(self):
        """Test match with guard conditions."""
        def categorize(result: Result[int, str]) -> str:
            match result:
                case Ok(value=v) if v is not None and v > 100:
                    return "high"
                case Ok(value=v) if v is not None and v > 0:
                    return "positive"
                case Ok(value=v) if v == 0:
                    return "zero"
                case Ok():
                    return "other ok"
                case Err():
                    return "error"
        
        assert categorize(Ok(value=150)) == "high"
        assert categorize(Ok(value=50)) == "positive"
        assert categorize(Ok(value=0)) == "zero"
        assert categorize(Ok(value=-10)) == "other ok"
        assert categorize(Err(cause="error")) == "error"

    def test_match_in_list_processing(self):
        """Test match when processing list of Results."""
        results: list[Result[int, str]] = [
            Ok(value=1),
            Err(cause="error1"),
            Ok(value=2),
            Err(cause="error2"),
            Ok(value=3),
        ]
        
        successes = []
        errors = []
        
        for result in results:
            match result:
                case Ok(value=v):
                    successes.append(v)
                case Err(cause=c):
                    errors.append(c)
        
        assert successes == [1, 2, 3]
        assert errors == ["error1", "error2"]


class TestMatchExhaustiveness:
    """Test that match patterns can be exhaustive."""

    def test_match_with_wildcard_fallback(self):
        """Test match with wildcard pattern as fallback."""
        def handle(result: Result[int, str]) -> str:
            match result:
                case Ok():
                    return "ok"
                case _:
                    return "not ok"
        
        assert handle(Ok(value=42)) == "ok"
        assert handle(Err(cause="error")) == "not ok"

    def test_match_both_types_is_exhaustive(self):
        """Test that matching both Ok and Err covers all cases."""
        def handle(result: Result[int, str]) -> str:
            match result:
                case Ok():
                    return "ok"
                case Err():
                    return "err"
            # No unreachable code needed
        
        # Both types are handled
        assert handle(Ok(value=42)) == "ok"
        assert handle(Err(cause="error")) == "err"


class TestMatchVsIsOkPattern:
    """Compare match patterns with is_ok()/is_err() patterns."""

    def test_match_equivalent_to_is_ok(self):
        """Test that match produces same results as is_ok()."""
        def using_is_ok(result: Result[int, str]) -> bool:
            return result.is_ok()
        
        def using_match(result: Result[int, str]) -> bool:
            match result:
                case Ok():
                    return True
                case Err():
                    return False
        
        ok = Ok(value=42)
        err = Err(cause="error")
        
        assert using_is_ok(ok) == using_match(ok)
        assert using_is_ok(err) == using_match(err)

    def test_match_equivalent_to_isinstance(self):
        """Test that match produces same results as isinstance()."""
        def using_isinstance(result: Result[int, str]) -> str:
            if isinstance(result, Ok):
                return f"Value: {result.value}"
            elif isinstance(result, Err):
                return f"Cause: {result.cause}"
            return "Unknown"
        
        def using_match(result: Result[int, str]) -> str:
            match result:
                case Ok(value=v):
                    return f"Value: {v}"
                case Err(cause=c):
                    return f"Cause: {c}"
        
        ok = Ok(value=42)
        err = Err(cause="error")
        
        assert using_isinstance(ok) == using_match(ok)
        assert using_isinstance(err) == using_match(err)
