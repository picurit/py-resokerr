<p align="center">
  <img src="https://raw.githubusercontent.com/picurit/py-resokerr/refs/heads/main/docs/images/Resokerr-Logo.png" alt="Resokerr" width="200">
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
err_result: Err[str, str] = Err(cause="Something went wrong")

# Result: Type alias for Ok | Err (used in function signatures)
def divide(a: int, b: int) -> Result[float, str]:
    if b == 0:
        return Err(cause="Division by zero")
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
        return Err(cause="Age cannot be negative")
    if age > 150:
        return Err(cause="Age exceeds maximum")
    return Ok(value=age)

# Handle the result
result = validate_age(25)
if result.is_ok():
    print(f"Valid age: {result.value}")
else:
    print(f"Invalid: {result.cause}")
```

### Pattern Matching with `match`

Python 3.10+ introduces structural pattern matching, which works seamlessly with `Ok` and `Err` thanks to their dataclass-based design. This provides a clean, declarative way to handle results.

#### Type-Only Matching

When you only need to check whether the result is `Ok` or `Err` without extracting values:

```python
from resokerr import Ok, Err, Result

def process(result: Result[int, str]) -> str:
    match result:
        case Ok():
            return "Operation succeeded"
        case Err():
            return "Operation failed"

# Usage
ok_result = Ok(value=42)
err_result = Err(cause="Connection timeout")

print(process(ok_result))   # "Operation succeeded"
print(process(err_result))  # "Operation failed"
```

#### Capturing Values

You can capture the contained value (for `Ok`) or cause (for `Err`) directly in the match pattern:

```python
from resokerr import Ok, Err, Result

def handle_result(result: Result[int, str]) -> str:
    match result:
        case Ok(value=v):
            return f"Success with value: {v}"
        case Err(cause=c):
            return f"Failed with cause: {c}"

# Usage
print(handle_result(Ok(value=100)))           # "Success with value: 100"
print(handle_result(Err(cause="Not found")))  # "Failed with cause: Not found"
```

#### Advanced Matching with Guards

Combine pattern matching with guard conditions for more complex logic:

```python
from resokerr import Ok, Err, Result

def categorize_age(result: Result[int, str]) -> str:
    match result:
        case Ok(value=age) if age is not None and age >= 18:
            return "adult"
        case Ok(value=age) if age is not None and age >= 0:
            return "minor"
        case Ok():
            return "unknown age"
        case Err(cause=c):
            return f"invalid: {c}"

# Usage
print(categorize_age(Ok(value=25)))                        # "adult"
print(categorize_age(Ok(value=10)))                        # "minor"
print(categorize_age(Err(cause="Age cannot be negative"))) # "invalid: Age cannot be negative"
```

#### Capturing Multiple Fields

You can capture multiple attributes in a single pattern, including messages and metadata:

```python
from resokerr import Ok, Err, Result

result = Ok(value=42).with_info("Step completed").with_warning("Low memory")

match result:
    case Ok(value=v, messages=msgs):
        print(f"Value: {v}, Messages: {len(msgs)}")  # "Value: 42, Messages: 2"
    case Err(cause=c, messages=msgs):
        print(f"Error: {c}, Messages: {len(msgs)}")
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
        return (Err(cause=e)
            .with_error(
                f"File '{filename}' not found",
                code="FILE_NOT_FOUND",
                details={"filename": filename, "error_type": "FileNotFoundError"},
                stack_trace=traceback.format_exc()
            )
            .with_info(f"Attempted to read: {filename}")
        )
    except PermissionError as e:
        return (Err(cause=e)
            .with_error(
                "Permission denied",
                code="PERMISSION_DENIED",
                details={"filename": filename}
            )
        )

# Handle errors with full context
result = risky_operation("config.txt")
if result.is_err():
    print(f"Operation failed: {result.cause}")
    
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
        return Err(cause="Invalid user ID")
    return Ok(value={"id": user_id, "name": "Alice"})

def validate_user(user: dict) -> Result[dict, str]:
    """Validate user data."""
    if "name" not in user:
        return Err(cause="User missing name field")
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
    print(f"❌ Failed: {result.cause}")
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

### Unwrapping Values and Causes

Both `Ok` and `Err` provide an `unwrap()` method to safely extract their contained value or cause with optional defaults:

```python
from resokerr import Ok, Err

# Basic unwrap - returns the value or None
ok = Ok(value=42)
value = ok.unwrap()  # Returns 42

# Unwrap with default - useful when value might be None
ok_empty = Ok(value=None)
value = ok_empty.unwrap(default=0)  # Returns 0

# Same pattern works for Err and its cause
err = Err(cause="Connection failed")
cause = err.unwrap()  # Returns "Connection failed"

err_empty = Err(cause=None)
cause = err_empty.unwrap(default="Unknown error")  # Returns "Unknown error"
```

**Important**: The `unwrap()` method is type-safe:
- On `Ok[V, M]`: returns `Optional[V]` or `V` when a default is provided
- On `Err[E, M]`: returns `Optional[E]` or `E` when a default is provided

```python
# Type-safe unwrapping
def process_result(result: Result[int, str]) -> int:
    if result.is_ok():
        # unwrap() on Ok returns the value type
        return result.unwrap(default=0)
    else:
        # unwrap() on Err returns the cause type
        error_msg = result.unwrap(default="Unknown")
        print(f"Error: {error_msg}")
        return -1
```

### Unwrapping as Serialized Dict

The `unwrap()` method accepts an optional `as_dict` parameter that returns the value or cause as a JSON-serializable representation:

```python
from resokerr import Ok, Err

# Custom class with to_dict() method
class UserData:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def to_dict(self):
        return {"name": self.name, "age": self.age}

user = UserData("Alice", 30)
ok = Ok(value=user)

# Default: returns the raw object
raw = ok.unwrap()                    # Returns UserData instance
print(type(raw))                     # <class 'UserData'>

# With as_dict=True: returns serialized representation
serialized = ok.unwrap(as_dict=True) # Returns {"name": "Alice", "age": 30}
print(type(serialized))              # <class 'dict'>
```

**Serialization rules for `as_dict=True`:**

| Type | Result |
|------|--------|
| JSON primitives (`str`, `int`, `float`, `bool`, `None`, `dict`, `list`) | Returned as-is |
| Objects with `to_dict()` method | `to_dict()` is called |
| Other objects | Converted to string via `str()` |

```python
from resokerr import Ok, Err

# JSON primitives are returned as-is
ok = Ok(value={"key": "value"})
ok.unwrap(as_dict=True)  # {"key": "value"}

# Objects without to_dict() become strings
err = Err(cause=ValueError("invalid"))
err.unwrap(as_dict=True)  # "invalid"

# Combined with default
ok_empty = Ok(value=None)
ok_empty.unwrap(default={"fallback": True}, as_dict=True)  # {"fallback": True}
```

### Transforming with Map

The `map()` method allows you to transform the contained value (for `Ok`) or cause (for `Err`) while preserving messages and metadata:

```python
from resokerr import Ok, Err

# Transform the value inside Ok
ok = Ok(value=5)
doubled = ok.map(lambda x: x * 2)
print(doubled.value)  # 10

# Chain multiple transformations
result = (Ok(value="hello")
    .with_info("Original string")
    .map(str.upper)
    .map(lambda s: s + "!")
)
print(result.value)  # "HELLO!"
print(result.info_messages[0].message)  # "Original string" - preserved!

# Transform causes in Err
err = Err(cause=ValueError("invalid input"))
string_err = err.map(lambda e: str(e))
print(string_err.cause)  # "invalid input"
```

**Key behaviors of `map()`:**

1. **Preserves immutability**: Returns a new instance, never modifies the original
2. **Preserves messages**: All info, warning, and error messages are carried over
3. **Preserves metadata**: Metadata is preserved unchanged
4. **Handles None safely**: If value/cause is `None`, returns a new instance with `None` (function is not called)

```python
# Safe handling of None values
ok_none = Ok(value=None)
mapped = ok_none.map(lambda x: x * 2)  # Function is NOT called
print(mapped.value)  # None

# Practical example: parsing and transforming data
def parse_user_age(age_str: str) -> Result[int, str]:
    try:
        age = int(age_str)
        return Ok(value=age).with_info(f"Parsed age: {age}")
    except ValueError:
        return Err(cause=f"Invalid age format: {age_str}")

# Transform successful result to calculate birth year
result = parse_user_age("30")
if result.is_ok():
    birth_year_result = result.map(lambda age: 2026 - age)
    print(f"Birth year: {birth_year_result.value}")  # Birth year: 1996
    print(f"Messages preserved: {len(birth_year_result.info_messages)}")  # 1
```

### Combining Unwrap and Map

These methods work well together for concise data processing:

```python
from resokerr import Ok, Err, Result

def fetch_temperature(city: str) -> Result[float, str]:
    temperatures = {"madrid": 25.5, "london": 15.0, "tokyo": 22.3}
    if city.lower() in temperatures:
        return Ok(value=temperatures[city.lower()])
    return Err(cause=f"Unknown city: {city}")

def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 9/5) + 32

# Get temperature in Fahrenheit with a default
result = fetch_temperature("Madrid")
fahrenheit = (
    result
    .map(celsius_to_fahrenheit)
    .unwrap(default=32.0)  # Default to freezing if city not found
)
print(f"Temperature: {fahrenheit}°F")  # Temperature: 77.9°F

# Chain operations with error handling
def get_formatted_temp(city: str) -> str:
    result = fetch_temperature(city)
    if result.is_ok():
        return result.map(lambda c: f"{c}°C / {celsius_to_fahrenheit(c):.1f}°F").unwrap()
    return f"Error: {result.unwrap()}"

print(get_formatted_temp("Tokyo"))   # 22.3°C / 72.1°F
print(get_formatted_temp("Paris"))   # Error: Unknown city: Paris
```

### Serializing Results

Both `Ok` and `Err` provide a `to_dict()` method for easy JSON serialization. This is useful for API responses, logging, or any scenario where you need to convert results to a serializable format.

```python
from resokerr import Ok, Err
import json

# Serialize an Ok result
ok = (Ok(value={"user_id": 123}, metadata={"request_id": "abc"})
    .with_info("User fetched successfully")
    .with_warning("Using cached data"))

print(json.dumps(ok.to_dict(), indent=2))
# {
#   "is_ok": true,
#   "is_err": false,
#   "value": {"user_id": 123},
#   "messages": [
#     {"message": "User fetched successfully", "severity": "info"},
#     {"message": "Using cached data", "severity": "warning"}
#   ],
#   "metadata": {"request_id": "abc"}
# }

# Serialize an Err result
err = (Err(cause="User not found", metadata={"request_id": "xyz"})
    .with_error("Database query failed", code="DB_001"))

print(json.dumps(err.to_dict(), indent=2))
# {
#   "is_ok": false,
#   "is_err": true,
#   "cause": "User not found",
#   "messages": [
#     {"message": "Database query failed", "severity": "error", "code": "DB_001"}
#   ],
#   "metadata": {"request_id": "xyz"}
# }
```

**Output structure:**

| Field | Ok | Err | Description |
|-------|-----|-----|-------------|
| `is_ok` | `true` | `false` | Boolean indicating success |
| `is_err` | `false` | `true` | Boolean indicating failure |
| `value` | ✓ | - | The success value (Ok only) |
| `cause` | - | ✓ | The error cause (Err only) |
| `messages` | ✓ | ✓ | Array of serialized MessageTrace objects |
| `metadata` | ✓ (optional) | ✓ (optional) | Only included if not None |

### Serializing Messages

`MessageTrace` instances are immutable and use internal types like `MappingProxyType` and `Enum`. To serialize them individually, use the `to_dict()` method:

```python
from resokerr import Ok, Err

# Create a result with messages
result = (Ok(value="success")
    .with_info("Step 1 completed", code="STEP_1")
    .with_warning("Minor issue detected", details={"field": "optional"})
)

# Serialize all messages to dictionaries
serialized_messages = [msg.to_dict() for msg in result.messages]
print(serialized_messages)
# [
#     {'message': 'Step 1 completed', 'severity': 'info', 'code': 'STEP_1'},
#     {'message': 'Minor issue detected', 'severity': 'warning', 'details': {'field': 'optional'}}
# ]
```

**How serialization works for values and causes:**

- **JSON primitive types** (`str`, `int`, `float`, `bool`, `None`, `dict`, `list`): Returned as-is
- **Objects with `to_dict()` method**: The method is called to serialize them
- **Other objects** (e.g., exceptions): Converted to string using `str()`

```python
from resokerr import Ok, Err

# Custom serializable value type
class UserData:
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    def to_dict(self):
        return {"name": self.name, "email": self.email}

# Objects with to_dict() are serialized automatically
user = UserData("Alice", "alice@example.com")
ok = Ok(value=user)
print(ok.to_dict()["value"])
# {'name': 'Alice', 'email': 'alice@example.com'}

# Exceptions are converted to string
err = Err(cause=ValueError("Invalid input"))
print(err.to_dict()["cause"])
# "Invalid input"
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
        return Err(cause="Empty data").with_error("Data cannot be empty", code="EMPTY_DATA")
    
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
        return (Err(cause=e)
            .with_error("Request timeout", code="TIMEOUT")
            .with_info(f"URL: {url}"))
    
    except requests.exceptions.HTTPError as e:
        return (Err(cause=e)
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
        return Err(cause="Missing email").with_error("Email is required", code="MISSING_EMAIL")
    
    if not form_data.get("password"):
        return Err(cause="Missing password").with_error("Password is required", code="MISSING_PASSWORD")
    
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
            return (Err(cause="Schema validation failed")
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
        
        return (Err(cause=e)
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
- `unwrap(default=None, as_dict=False) -> Union[V, Any]` - Extract the contained value, returning `default` if value is `None`. If `as_dict=True`, returns a JSON-serializable representation
- `map(f: Callable[[V], T]) -> Ok[T, M]` - Apply transformation function to the value, preserving messages and metadata
- `to_dict() -> Dict[str, Any]` - Serialize to a dictionary with `is_ok`, `is_err`, `value`, `messages`, and optionally `metadata`

**Properties:**
- `info_messages` - Tuple of info messages
- `warning_messages` - Tuple of warning messages

#### `Err[E, M]`

Represents a failed result.

**Attributes:**
- `cause: Optional[E]` - The error/exception that caused failure
- `messages: Tuple[MessageTrace[M], ...]` - Error, warning, and info messages
- `metadata: Optional[Mapping[str, Any]]` - Additional context

**Methods:**
- `is_ok() -> bool` - Returns `False`
- `is_err() -> bool` - Returns `True`
- `has_cause() -> bool` - Check if cause is not None
- `has_metadata() -> bool` - Check if metadata exists
- `has_errors() -> bool` - Check for error messages
- `has_info() -> bool` - Check for info messages
- `has_warnings() -> bool` - Check for warning messages
- `with_error(message, code, details, stack_trace) -> Err` - Add error message
- `with_info(message, code, details, stack_trace) -> Err` - Add info message
- `with_warning(message, code, details, stack_trace) -> Err` - Add warning message
- `with_metadata(metadata) -> Err` - Replace metadata
- `unwrap(default=None, as_dict=False) -> Union[E, Any]` - Extract the contained cause, returning `default` if cause is `None`. If `as_dict=True`, returns a JSON-serializable representation
- `map(f: Callable[[E], T]) -> Err[T, M]` - Apply transformation function to the cause, preserving messages and metadata
- `to_dict() -> Dict[str, Any]` - Serialize to a dictionary with `is_ok`, `is_err`, `cause`, `messages`, and optionally `metadata`

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
- `MessageTrace.success(message, code, details, stack_trace)` - Create SUCCESS message

**Instance Methods:**
- `to_dict() -> Dict[str, Any]` - Serialize to a dictionary. Returns a dict with `message`, `severity`, and optionally `code`, `details`, `stack_trace` (only included if not None)

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
