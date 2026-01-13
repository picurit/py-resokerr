<p align="center">
  <img src="docs/images/Resokerr-Logo.png" alt="Resokerr Logo" width="200">
</p>

# Resokerr

A lightweight, pragmatic Python library for handling results using `Result/Ok/Err` types with rich message tracing and metadata support.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why resokerr?

### The Problem

In Python, error handling typically relies on exceptions and try-except blocks. While powerful, this approach has several drawbacks:

- **Implicit control flow**: Exceptions can be raised from deep within call stacks, making it hard to track where errors originate
- **Loss of context**: Once an exception is caught, valuable diagnostic information about the operation's progression is often lost
- **All-or-nothing**: Operations either succeed completely or fail completely, with no middle ground for partial success or warnings
- **Type safety**: It's difficult to represent in type hints whether a function might fail and what error types it might return

### The Solution

`resokerr` provides a simple, Pythonic way to handle results that:

✅ **Makes errors explicit**: Functions return `Result` types, making it clear they can fail  
✅ **Preserves context**: Accumulate messages (info, warnings, errors) throughout an operation  
✅ **Enables flow control**: Use simple `if result.is_ok()` checks instead of try-except blocks  
✅ **Maintains immutability**: All instances are frozen dataclasses, ensuring thread-safety  
✅ **Supports rich diagnostics**: Attach metadata, error codes, stack traces, and severity levels to messages

## What resokerr is NOT

This library is **not** an attempt to:
- Simulate Rust's `Result<T, E>` type system
- Implement functional programming paradigms in Python
- Replace Python's exception system entirely

Instead, it's a **pragmatic, Pythonic tool** for scenarios where explicit result handling provides clearer, more maintainable code than exceptions.

## Core Concepts

### Architecture: Composition over Inheritance

`resokerr` uses a **composition-based architecture** rather than traditional inheritance:

- **`Ok` and `Err` are independent classes**: They don't inherit from a common `Result` base class
- **`Result` is a type alias**: `Result = Union[Ok[V, M], Err[E, M]]` represents a union type, not a superclass
- **No polymorphic conversions**: You cannot convert `Ok` to `Err` (or vice versa) through inheritance—each represents a distinct logical state
- **Mixins provide shared behavior**: Both classes compose functionality from mixins (`ErrorCollectorMixin`, `InfoCollectorMixin`, `WarningCollectorMixin`, etc.)

This design ensures:
- ✅ Type safety: No accidental conversions between success and failure states
- ✅ Clarity: Each type has a clear, distinct purpose
- ✅ Immutability: All instances are frozen and cannot change state after creation

### The Three Core Types

```python
from resokerr import Ok, Err, Result

# Ok: Represents success
ok_result: Ok[int, str] = Ok(value=42)

# Err: Represents failure
err_result: Err[str, str] = Err(trace="Something went wrong")

# Result: Type alias for Ok | Err (used in function signatures)
def divide(a: int, b: int) -> Result[float, str]:
    if b == 0:
        return Err(trace="Division by zero")
    return Ok(value=a / b)
```

### Message Tracing

Both `Ok` and `Err` support rich message tracing with severity levels:

```python
from resokerr import Ok, MessageTrace, TraceSeverityLevel

result = (Ok(value=42)
    .with_info("Starting operation")
    .with_warning("Using default configuration")
    .with_info("Operation completed"))

# Access messages by severity
for msg in result.info_messages:
    print(f"INFO: {msg.message}")

for msg in result.warning_messages:
    print(f"WARNING: {msg.message}")
```

### Immutability

All instances are **immutable by design**:

```python
result = Ok(value=42)
# result.value = 100  # ❌ Raises AttributeError

# Instead, create new instances
new_result = result.with_info("Additional context")  # ✅ Returns new Ok instance
```

## Installation

```bash
pip install resokerr
```

Or using uv:

```bash
uv add resokerr
```

## Quick Start

### Basic Usage

```python
from resokerr import Ok, Err, Result

def validate_age(age: int) -> Result[int, str]:
    """Validate user age."""
    if age < 0:
        return Err(trace="Age cannot be negative")
    if age > 150:
        return Err(trace="Age exceeds maximum")
    return Ok(value=age)

# Handle the result
result = validate_age(25)
if result.is_ok():
    print(f"Valid age: {result.value}")
else:
    print(f"Invalid: {result.trace}")
```

### With Message Tracing

```python
from resokerr import Ok, Err, Result

def process_user_data(user_id: int) -> Result[dict, Exception]:
    """Process user data with diagnostic messages."""
    result = Ok(value={"id": user_id})
    
    # Add informational breadcrumbs
    result = result.with_info(f"Processing user {user_id}")
    
    # Simulate validation warnings
    if user_id < 1000:
        result = result.with_warning("User ID is below recommended range")
    
    # Add metadata
    result = result.with_metadata({
        "timestamp": "2026-01-13",
        "processed_by": "system"
    })
    
    return result

# Use the result
result = process_user_data(500)
if result.is_ok():
    print(f"User data: {result.value}")
    
    # Check for warnings
    if result.has_warnings():
        for warning in result.warning_messages:
            print(f"⚠️  {warning.message}")
    
    # Access metadata
    if result.has_metadata():
        print(f"Metadata: {result.metadata}")
```

### Error Handling with Context

```python
from resokerr import Err, Result
import traceback

def risky_operation(filename: str) -> Result[str, Exception]:
    """Operation that might fail with detailed error context."""
    try:
        with open(filename, 'r') as f:
            content = f.read()
        return Ok(value=content)
    except FileNotFoundError as e:
        return (Err(trace=e)
            .with_error(
                f"File '{filename}' not found",
                code="FILE_NOT_FOUND",
                details={"filename": filename, "error_type": "FileNotFoundError"},
                stack_trace=traceback.format_exc()
            )
            .with_info(f"Attempted to read: {filename}")
        )
    except PermissionError as e:
        return (Err(trace=e)
            .with_error(
                "Permission denied",
                code="PERMISSION_DENIED",
                details={"filename": filename}
            )
        )

# Handle errors with full context
result = risky_operation("config.txt")
if result.is_err():
    print(f"Operation failed: {result.trace}")
    
    # Access structured error messages
    for error in result.error_messages:
        print(f"Error: {error.message}")
        if error.code:
            print(f"Code: {error.code}")
        if error.details:
            print(f"Details: {error.details}")
```

### Type-Safe Function Chaining

```python
from resokerr import Ok, Err, Result

def fetch_user(user_id: int) -> Result[dict, str]:
    """Fetch user from database."""
    if user_id <= 0:
        return Err(trace="Invalid user ID")
    return Ok(value={"id": user_id, "name": "Alice"})

def validate_user(user: dict) -> Result[dict, str]:
    """Validate user data."""
    if "name" not in user:
        return Err(trace="User missing name field")
    return Ok(value=user)

def process_user_pipeline(user_id: int) -> Result[dict, str]:
    """Chain operations with early returns."""
    # Fetch user
    fetch_result = fetch_user(user_id)
    if fetch_result.is_err():
        return fetch_result  # Early return on error
    
    # Validate user
    validate_result = validate_user(fetch_result.value)
    if validate_result.is_err():
        return validate_result  # Early return on error
    
    # Success: return validated user
    return validate_result.with_info("User processed successfully")

# Usage
result = process_user_pipeline(123)
if result.is_ok():
    print(f"✅ Success: {result.value}")
    if result.has_info():
        print(f"Info: {result.info_messages[0].message}")
else:
    print(f"❌ Failed: {result.trace}")
```

## Advanced Features

### Custom Message Types

By default, `Result` uses string messages, but you can use any type with `ResultBase`:

```python
from resokerr import Ok, ResultBase, MessageTrace
from dataclasses import dataclass

@dataclass
class AppError:
    code: str
    message: str
    severity: int

# Use custom message type
error = AppError(code="DB_ERROR", message="Connection failed", severity=5)
msg = MessageTrace(message=error, severity=TraceSeverityLevel.ERROR)

result: ResultBase[dict, Exception, AppError] = Ok(value={"data": 123}, messages=[msg])
```

### Message Severity Levels

Messages support three severity levels:

```python
from resokerr import MessageTrace, TraceSeverityLevel

# Factory methods
info_msg = MessageTrace.info("Operation started")
warn_msg = MessageTrace.warning("Deprecated API used", code="DEPRECATED")
error_msg = MessageTrace.error("Failed to connect", code="CONN_ERR")

# Or explicit construction
custom_msg = MessageTrace(
    message="Custom message",
    severity=TraceSeverityLevel.WARNING,
    code="CUSTOM_001",
    details={"source": "api", "attempts": 3}
)
```

### Automatic Error Downgrading in Ok

`Ok` instances **cannot contain ERROR-severity messages**. Any ERROR messages are automatically downgraded to WARNING with metadata explaining the conversion:

```python
from resokerr import Ok, MessageTrace

error_msg = MessageTrace.error("This is an error")
ok = Ok(value=42, messages=[error_msg])

# The error was downgraded to warning
assert ok.messages[0].severity == TraceSeverityLevel.WARNING
assert "downgraded" in ok.messages[0].details
# Details: {"downgraded": {"from": "error", "reason": "Ok instances cannot contain ERROR messages"}}
```

This design ensures **semantic correctness**: successful results shouldn't contain error-level messages.

### Metadata Support

Attach arbitrary metadata to any result:

```python
from resokerr import Ok

result = Ok(
    value={"user_id": 123},
    metadata={
        "timestamp": "2026-01-13T10:30:00",
        "request_id": "req-abc-123",
        "processing_time_ms": 45,
        "cache_hit": True
    }
)

if result.has_metadata():
    print(f"Request ID: {result.metadata['request_id']}")
    print(f"Processing time: {result.metadata['processing_time_ms']}ms")
```

## Best Practices

### ✅ DO

- **Use `Result` in function signatures** to signal that a function can fail
- **Accumulate messages** to create diagnostic breadcrumbs
- **Check `is_ok()`/`is_err()`** for flow control instead of exceptions
- **Use early returns** for cleaner error handling
- **Attach metadata** for debugging and monitoring

```python
def good_example(data: dict) -> Result[dict, str]:
    if not data:
        return Err(trace="Empty data").with_error("Data cannot be empty", code="EMPTY_DATA")
    
    result = Ok(value=data).with_info("Data validated")
    return result.with_metadata({"validated_at": "2026-01-13"})
```

### ❌ DON'T

- Don't try to mutate `Ok` or `Err` instances (they're frozen)
- Don't use `Result` for all functions—exceptions are still appropriate for truly exceptional cases
- Don't create deep inheritance hierarchies with `Ok`/`Err`

```python
# ❌ Bad: Trying to mutate
result = Ok(value=42)
result.value = 100  # Raises AttributeError

# ✅ Good: Create new instance
result = Ok(value=42)
new_result = result.with_info("Updated")
```

## Real-World Examples

### API Response Handling

```python
from resokerr import Ok, Err, Result
import requests

def fetch_api_data(url: str) -> Result[dict, Exception]:
    """Fetch data from API with detailed error handling."""
    result = Ok(value=None).with_info(f"Fetching from {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        result = Ok(value=data)
        result = result.with_info(f"Successfully fetched {len(data)} items")
        result = result.with_metadata({
            "status_code": response.status_code,
            "response_time_ms": response.elapsed.total_seconds() * 1000
        })
        
        return result
        
    except requests.exceptions.Timeout as e:
        return (Err(trace=e)
            .with_error("Request timeout", code="TIMEOUT")
            .with_info(f"URL: {url}"))
    
    except requests.exceptions.HTTPError as e:
        return (Err(trace=e)
            .with_error(f"HTTP error: {e.response.status_code}", code="HTTP_ERROR")
            .with_metadata({"status_code": e.response.status_code}))
```

### Form Validation

```python
from resokerr import Ok, Err, Result

def validate_registration_form(form_data: dict) -> Result[dict, str]:
    """Validate user registration with accumulated warnings."""
    result = Ok(value=form_data)
    
    # Required fields
    if not form_data.get("email"):
        return Err(trace="Missing email").with_error("Email is required", code="MISSING_EMAIL")
    
    if not form_data.get("password"):
        return Err(trace="Missing password").with_error("Password is required", code="MISSING_PASSWORD")
    
    # Warnings for optional fields
    if not form_data.get("phone"):
        result = result.with_warning("Phone number not provided")
    
    if len(form_data.get("password", "")) < 12:
        result = result.with_warning("Password shorter than recommended 12 characters")
    
    return result.with_info("Form validation completed")

# Usage
form = {"email": "user@example.com", "password": "Pass123"}
result = validate_registration_form(form)

if result.is_ok():
    if result.has_warnings():
        print("⚠️  Validation passed with warnings:")
        for warning in result.warning_messages:
            print(f"  - {warning.message}")
    else:
        print("✅ Validation passed")
```

### Database Operations

```python
from resokerr import Ok, Err, Result
from typing import Optional

def save_to_database(data: dict) -> Result[int, Exception]:
    """Save data to database with transaction tracking."""
    transaction_id = None
    
    try:
        # Start transaction
        transaction_id = start_transaction()
        result = Ok(value=None).with_info(f"Transaction {transaction_id} started")
        
        # Validate data
        if not validate_schema(data):
            rollback_transaction(transaction_id)
            return (Err(trace="Schema validation failed")
                .with_error("Data schema mismatch", code="SCHEMA_ERROR")
                .with_info(f"Transaction {transaction_id} rolled back"))
        
        # Insert data
        record_id = insert_data(data)
        commit_transaction(transaction_id)
        
        result = Ok(value=record_id)
        result = result.with_info(f"Record {record_id} saved successfully")
        result = result.with_metadata({
            "transaction_id": transaction_id,
            "record_id": record_id,
            "timestamp": "2026-01-13T10:30:00"
        })
        
        return result
        
    except Exception as e:
        if transaction_id:
            rollback_transaction(transaction_id)
        
        return (Err(trace=e)
            .with_error("Database operation failed", code="DB_ERROR")
            .with_info(f"Transaction {transaction_id} rolled back if started")
            .with_metadata({"transaction_id": transaction_id}))
```

## API Reference

### Core Types

#### `Ok[V, M]`

Represents a successful result.

**Attributes:**
- `value: Optional[V]` - The success value
- `messages: Tuple[MessageTrace[M], ...]` - Info and warning messages
- `metadata: Optional[Mapping[str, Any]]` - Additional context

**Methods:**
- `is_ok() -> bool` - Returns `True`
- `is_err() -> bool` - Returns `False`
- `has_value() -> bool` - Check if value is not None
- `has_metadata() -> bool` - Check if metadata exists
- `has_info() -> bool` - Check for info messages
- `has_warnings() -> bool` - Check for warning messages
- `with_info(message, code, details, stack_trace) -> Ok` - Add info message
- `with_warning(message, code, details, stack_trace) -> Ok` - Add warning message
- `with_metadata(metadata) -> Ok` - Replace metadata

**Properties:**
- `info_messages` - Tuple of info messages
- `warning_messages` - Tuple of warning messages

#### `Err[E, M]`

Represents a failed result.

**Attributes:**
- `trace: Optional[E]` - The error/exception that caused failure
- `messages: Tuple[MessageTrace[M], ...]` - Error, warning, and info messages
- `metadata: Optional[Mapping[str, Any]]` - Additional context

**Methods:**
- `is_ok() -> bool` - Returns `False`
- `is_err() -> bool` - Returns `True`
- `has_trace() -> bool` - Check if trace is not None
- `has_metadata() -> bool` - Check if metadata exists
- `has_errors() -> bool` - Check for error messages
- `has_info() -> bool` - Check for info messages
- `has_warnings() -> bool` - Check for warning messages
- `with_error(message, code, details, stack_trace) -> Err` - Add error message
- `with_info(message, code, details, stack_trace) -> Err` - Add info message
- `with_warning(message, code, details, stack_trace) -> Err` - Add warning message
- `with_metadata(metadata) -> Err` - Replace metadata

**Properties:**
- `error_messages` - Tuple of error messages
- `info_messages` - Tuple of info messages
- `warning_messages` - Tuple of warning messages

#### `MessageTrace[M]`

Immutable message with severity tracking.

**Attributes:**
- `message: M` - The message content (any type)
- `severity: TraceSeverityLevel` - INFO, WARNING, or ERROR
- `code: Optional[str]` - Optional error/warning code
- `details: Optional[Mapping[str, Any]]` - Additional details
- `stack_trace: Optional[str]` - Optional stack trace

**Factory Methods:**
- `MessageTrace.info(message, code, details, stack_trace)` - Create INFO message
- `MessageTrace.warning(message, code, details, stack_trace)` - Create WARNING message
- `MessageTrace.error(message, code, details, stack_trace)` - Create ERROR message

#### Type Aliases

- `Result[V, E]` = `Union[Ok[V, str], Err[E, str]]` - Common result type with string messages
- `ResultBase[V, E, M]` = `Union[Ok[V, M], Err[E, M]]` - Generic result type with custom message types

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=resokerr --cov-report=html
```

## Contributing

Contributions are welcome! This library prioritizes:
- **Simplicity**: Keep the API minimal and intuitive
- **Pythonic design**: Follow Python conventions and idioms
- **Pragmatism**: Solve real problems without overengineering
- **Type safety**: Maintain strong type hints

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Built with inspiration from error handling patterns across multiple languages, adapted for Python's unique strengths and conventions.

---

**Remember**: `resokerr` is a tool in your toolbox, not a replacement for Python's exception system. Use it where explicit result handling makes your code clearer and more maintainable.
