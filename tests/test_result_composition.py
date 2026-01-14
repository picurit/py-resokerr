"""Tests for Result type aliases and composition patterns."""
import pytest

from resokerr.core import Ok, Err, Result, ResultBase, MessageTrace


class TestResultTypeAlias:
    """Test Result type alias behavior."""

    def test_result_is_type_alias_not_class(self):
        """Test that Result is a type alias, not a class."""
        # Result should be a TypeAlias (Union), not a class
        assert not isinstance(Result, type)
        # We can't instantiate Result directly
        with pytest.raises((TypeError, AttributeError)):
            Result()  # type: ignore

    def test_result_accepts_ok_instance(self):
        """Test that Result type alias can represent Ok instances."""
        ok: Result[int, Exception] = Ok(value=42)
        assert ok.is_ok()
        assert ok.value == 42

    def test_result_accepts_err_instance(self):
        """Test that Result type alias can represent Err instances."""
        err: Result[int, Exception] = Err(cause=ValueError("Error"))
        assert err.is_err()
        assert isinstance(err.cause, ValueError)

    def test_result_union_behavior(self):
        """Test that Result behaves as a union type."""
        def process_result(result: Result[int, str]) -> str:
            if result.is_ok():
                return f"Success: {result.value}"
            else:
                return f"Error: {result.cause}"
        
        ok_result = Ok(value=42)
        err_result = Err(cause="Failed")
        
        assert process_result(ok_result) == "Success: 42"
        assert process_result(err_result) == "Error: Failed"


class TestResultBaseTypeAlias:
    """Test ResultBase type alias with generic message types."""

    def test_resultbase_is_type_alias(self):
        """Test that ResultBase is a type alias."""
        assert not isinstance(ResultBase, type)

    def test_resultbase_with_custom_message_type(self):
        """Test ResultBase with custom message types."""
        class CustomMessage:
            def __init__(self, code: str, text: str):
                self.code = code
                self.text = text
        
        custom_msg = CustomMessage("M001", "Custom message")
        msg_trace = MessageTrace(message=custom_msg, severity=MessageTrace.info("").severity)
        
        ok: ResultBase[int, str, CustomMessage] = Ok(value=42, messages=[msg_trace])
        assert ok.is_ok()
        assert len(ok.messages) == 1

    def test_resultbase_flexible_types(self):
        """Test ResultBase flexibility with different types."""
        # Dict message type
        dict_msg = MessageTrace(message={"type": "info"}, severity=MessageTrace.info("").severity)
        ok1: ResultBase[str, Exception, dict] = Ok(value="success", messages=[dict_msg])
        
        # Tuple message type
        tuple_msg = MessageTrace(message=("INFO", "Message"), severity=MessageTrace.info("").severity)
        ok2: ResultBase[list, str, tuple] = Ok(value=[1, 2, 3], messages=[tuple_msg])
        
        assert ok1.is_ok()
        assert ok2.is_ok()


class TestOkErrIndependence:
    """Test that Ok and Err are independent classes with no inheritance relationship."""

    def test_ok_and_err_not_related_by_inheritance(self):
        """Test that Ok and Err don't share direct inheritance hierarchy."""
        assert not issubclass(Ok, Err)
        assert not issubclass(Err, Ok)
        
        # They may share mixin base classes (composition), but not a Result base class
        ok_bases = set(Ok.__mro__)
        err_bases = set(Err.__mro__)
        common_bases = ok_bases & err_bases
        
        # Check that there's no Result or ResultBase class in common
        result_bases = [b for b in common_bases if 'Result' in b.__name__ and b.__name__ in ('Result', 'ResultBase')]
        assert len(result_bases) == 0
        
        # Ok and Err can share mixin classes (this is composition, not inheritance hierarchy)
        # Verify they share mixins but aren't subclasses of each other
        mixin_bases = [b for b in common_bases if 'Mixin' in b.__name__]
        assert len(mixin_bases) > 0  # They should share mixins (composition)

    def test_ok_instance_not_instance_of_err(self):
        """Test that Ok instances are not instances of Err."""
        ok = Ok(value=42)
        assert not isinstance(ok, Err)

    def test_err_instance_not_instance_of_ok(self):
        """Test that Err instances are not instances of Ok."""
        err = Err(cause="Error")
        assert not isinstance(err, Ok)

    def test_cannot_create_result_base_class_instance(self):
        """Test that there's no Result base class to instantiate."""
        # Result is just a type alias, not a class
        # This should fail if someone tries to use it as a class
        with pytest.raises((NameError, TypeError)):
            # Trying to access Result as if it were a class constructor
            result = type(Result)()  # type: ignore


class TestCompositionPatterns:
    """Test composition patterns in the Result implementation."""

    def test_ok_composes_mixins(self):
        """Test that Ok composes functionality from mixins."""
        ok = Ok(value=42)
        
        # Check that Ok has methods from different mixins
        # From InfoCollectorMixin
        assert hasattr(ok, 'info_messages')
        assert hasattr(ok, 'has_info')
        
        # From WarningCollectorMixin
        assert hasattr(ok, 'warning_messages')
        assert hasattr(ok, 'has_warnings')
        
        # From MetadataMixin
        assert hasattr(ok, 'has_metadata')
        
        # From StatusMixin
        assert hasattr(ok, 'is_ok')
        assert hasattr(ok, 'is_err')

    def test_err_composes_mixins(self):
        """Test that Err composes functionality from mixins."""
        err = Err(cause="Error")
        
        # Check that Err has methods from different mixins
        # From ErrorCollectorMixin
        assert hasattr(err, 'error_messages')
        assert hasattr(err, 'has_errors')
        
        # From InfoCollectorMixin
        assert hasattr(err, 'info_messages')
        assert hasattr(err, 'has_info')
        
        # From WarningCollectorMixin
        assert hasattr(err, 'warning_messages')
        assert hasattr(err, 'has_warnings')
        
        # From MetadataMixin
        assert hasattr(err, 'has_metadata')
        
        # From StatusMixin
        assert hasattr(err, 'is_ok')
        assert hasattr(err, 'is_err')

    def test_mixin_methods_work_independently(self):
        """Test that mixin methods work independently on Ok and Err."""
        ok = Ok(value=42).with_info("Info").with_warning("Warning")
        err = Err(cause="Error").with_error("Error").with_info("Info")
        
        # Ok should have info and warnings
        assert ok.has_info()
        assert ok.has_warnings()
        
        # Err should have all three types
        assert err.has_errors()
        assert err.has_info()


class TestNoDirectConversion:
    """Test that direct conversion between Ok and Err is not possible."""

    def test_no_ok_to_err_conversion_method(self):
        """Test that Ok has no method to convert to Err."""
        ok = Ok(value=42)
        
        conversion_methods = ['to_err', 'as_err', 'into_err', 'to_error', 'as_error']
        for method in conversion_methods:
            assert not hasattr(ok, method), f"Ok should not have {method} method"

    def test_no_err_to_ok_conversion_method(self):
        """Test that Err has no method to convert to Ok."""
        err = Err(cause="Error")
        
        conversion_methods = ['to_ok', 'as_ok', 'into_ok', 'to_success', 'as_success']
        for method in conversion_methods:
            assert not hasattr(err, method), f"Err should not have {method} method"

    def test_manual_conversion_requires_new_instance(self):
        """Test that conversion requires creating new instances."""
        # Converting Ok to Err requires creating a new Err instance
        ok = Ok(value=42, messages=[MessageTrace.info("Original info")])
        
        # Manual conversion: create new Err with info from Ok
        err = Err(
            cause="Converted to error",
            messages=ok.messages,
            metadata=ok.metadata
        )
        
        # Verify they are independent
        assert ok.is_ok()
        assert err.is_err()
        assert ok is not err
        assert type(ok) != type(err)


class TestTypeChecking:
    """Test type checking and discrimination between Ok and Err."""

    def test_type_discrimination_with_is_ok(self):
        """Test discriminating between Ok and Err using is_ok()."""
        def handle_result(result: Result[int, str]) -> str:
            if result.is_ok():
                # Type checker should narrow this to Ok
                return f"Value: {result.value}"
            else:
                # Type checker should narrow this to Err
                return f"Error: {result.cause}"
        
        ok_result = Ok(value=42)
        err_result = Err(cause="Failed")
        
        assert handle_result(ok_result) == "Value: 42"
        assert handle_result(err_result) == "Error: Failed"

    def test_type_discrimination_with_isinstance(self):
        """Test discriminating using isinstance."""
        def process(result: Result[int, str]) -> str:
            if isinstance(result, Ok):
                return f"Ok with value: {result.value}"
            elif isinstance(result, Err):
                return f"Err with cause: {result.cause}"
            else:
                return "Unknown"
        
        ok_result = Ok(value=100)
        err_result = Err(cause="Error occurred")
        
        assert process(ok_result) == "Ok with value: 100"
        assert process(err_result) == "Err with cause: Error occurred"

    def test_union_type_behavior(self):
        """Test that Result behaves as a union of Ok and Err."""
        results: list[Result[int, str]] = [
            Ok(value=1),
            Err(cause="error1"),
            Ok(value=2),
            Err(cause="error2"),
        ]
        
        ok_count = sum(1 for r in results if r.is_ok())
        err_count = sum(1 for r in results if r.is_err())
        
        assert ok_count == 2
        assert err_count == 2


class TestPragmaticPythonicUsage:
    """Test pragmatic Pythonic usage patterns."""

    def test_early_return_pattern(self):
        """Test early return pattern with Result."""
        def validate_age(age: int) -> Result[int, str]:
            if age < 0:
                return Err(cause="Age cannot be negative")
            if age > 150:
                return Err(cause="Age too high")
            return Ok(value=age)
        
        result1 = validate_age(-5)
        result2 = validate_age(200)
        result3 = validate_age(25)
        
        assert result1.is_err()
        assert result2.is_err()
        assert result3.is_ok()
        assert result3.value == 25

    def test_result_chaining_pattern(self):
        """Test chaining operations with Result."""
        def divide(a: int, b: int) -> Result[float, str]:
            if b == 0:
                return Err(trace="Division by zero")
            return Ok(value=a / b)
        
        result = divide(10, 2)
        if result.is_ok():
            result = result.with_info("Division successful")
        
        assert result.is_ok()
        assert result.value == 5.0
        assert result.has_info()

    def test_accumulating_messages_pattern(self):
        """Test accumulating diagnostic messages."""
        def process_data(data: dict) -> Result[dict, str]:
            result = Ok(value=data)
            
            if "name" not in data:
                result = result.with_warning("Name field missing")
            
            if "email" not in data:
                result = result.with_warning("Email field missing")
            
            result = result.with_info("Processing complete")
            
            return result
        
        incomplete_data = {"id": 1}
        result = process_data(incomplete_data)
        
        assert result.is_ok()
        assert len(result.warning_messages) == 2
        assert result.has_info()

    def test_result_as_control_flow(self):
        """Test using Result for control flow."""
        def authenticate(username: str, password: str) -> Result[dict, str]:
            if not username:
                return Err(cause="Username required")
            if not password:
                return Err(cause="Password required")
            if username != "admin" or password != "secret":
                return Err(cause="Invalid credentials")
            
            return Ok(value={"user_id": 1, "username": username})
        
        # Test various scenarios
        result1 = authenticate("", "pass")
        result2 = authenticate("user", "")
        result3 = authenticate("user", "wrong")
        result4 = authenticate("admin", "secret")
        
        assert result1.is_err() and "Username" in result1.cause
        assert result2.is_err() and "Password" in result2.cause
        assert result3.is_err() and "Invalid" in result3.cause
        assert result4.is_ok() and result4.value["user_id"] == 1
