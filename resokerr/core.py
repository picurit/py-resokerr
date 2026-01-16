from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import (
    Any,
    Callable,
    Dict,
    final,
    Generic,
    Mapping,
    Optional,
    overload,
    Protocol,
    runtime_checkable,
    Self,
    TypeAlias,
    TypeVar,
    Tuple,
    Union,
)

# Class generics
V = TypeVar('V')    # Value type
E = TypeVar('E')    # Error type
M = TypeVar('M')    # Message type

# Methods generics
T = TypeVar('T')    # Transformation result type (used in map methods)

class TraceSeverityLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

@dataclass(frozen=True)
class MessageTrace(Generic[M]):
    """Immutable message trace with severity tracking and generic message types."""
    message: M
    severity: TraceSeverityLevel
    code: Optional[str] = None
    details: Optional[Mapping[str, Any]] = None
    stack_trace: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Ensure details are immutable by converting to MappingProxyType."""
        if self.details is not None and not isinstance(self.details, MappingProxyType):
            # Create a copy to prevent external modifications
            object.__setattr__(self, 'details', MappingProxyType(dict(self.details)))

    @classmethod
    def info(cls, message: M, code: Optional[str] = None,
             details: Optional[Mapping[str, Any]] = None,
             stack_trace: Optional[str] = None) -> MessageTrace[M]:
        """Factory method for info messages."""
        return cls(message=message, severity=TraceSeverityLevel.INFO, code=code, details=details, stack_trace=stack_trace)
    
    @classmethod
    def warning(cls, message: M, code: Optional[str] = None,
                details: Optional[Mapping[str, Any]] = None,
                stack_trace: Optional[str] = None) -> MessageTrace[M]:
        """Factory method for warning messages."""
        return cls(message=message, severity=TraceSeverityLevel.WARNING, code=code, details=details, stack_trace=stack_trace)
    
    @classmethod
    def error(cls, message: M, code: Optional[str] = None,
              details: Optional[Mapping[str, Any]] = None,
              stack_trace: Optional[str] = None) -> MessageTrace[M]:
        """Factory method for error messages."""
        return cls(message=message, severity=TraceSeverityLevel.ERROR, code=code, details=details, stack_trace=stack_trace)

    def _serialize_message(self) -> Any:
        """Serialize the generic message
        
        Handles different message types:
        - Primitives (str, int, float, bool, None): returned as-is
        - Objects implementing Serializable protocol: calls to_dict()
        - Other types: converted to string representation
        
        Returns:
            A serializable value representing the message.
        """
        # Primitives are already JSON-serializable
        if self.message is None or isinstance(self.message, (str, int, float, bool)):
            return self.message
        # Use internal Serializable protocol check for objects with to_dict()
        if isinstance(self.message, Serializable):
            return self.message.to_dict()
        # Fallback: convert to string representation
        return str(self.message)

    @staticmethod
    def is_serializable(obj: Any) -> bool:
        """Check if an object can be serialized via to_dict().
        
        This method checks whether an object implements a `to_dict()` method
        that can be used for serialization. Useful for determining how a
        custom message type will be handled during serialization.
        
        Args:
            obj: The object to check for serialization capability.
        
        Returns:
            True if the object has a to_dict() method, False otherwise.
        
        Example:
            >>> class MyMessage:
            ...     def to_dict(self):
            ...         return {"data": "value"}
            >>> MessageTrace.is_serializable(MyMessage())
            True
            >>> MessageTrace.is_serializable("plain string")
            False
        """
        return isinstance(obj, Serializable)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize MessageTrace to a dictionary.
        
        Creates a serializable dictionary representation of the
        MessageTrace instance. Optional fields (code, details, stack_trace)
        are only included if they have non-None values.
        
        Returns:
            A dictionary with the following structure:
            {
                "message": <serialized message>,
                "severity": <severity string value>,
                "code": <optional>,
                "details": <optional>,
                "stack_trace": <optional>
            }
        
        Example:
            >>> msg = MessageTrace.info("Operation completed", code="OP_001")
            >>> msg.to_dict()
            {'message': 'Operation completed', 'severity': 'info', 'code': 'OP_001'}
        """
        result: Dict[str, Any] = {
            "message": self._serialize_message(),
            "severity": self.severity.value,
        }
        
        # Only include optional fields if they have values
        if self.code is not None:
            result["code"] = self.code
        if self.details is not None:
            result["details"] = dict(self.details)  # Convert MappingProxyType to dict
        if self.stack_trace is not None:
            result["stack_trace"] = self.stack_trace
        
        return result

# Protocols
@runtime_checkable
class Serializable(Protocol):
    """Protocol for objects that can be serialized to a dictionary.
    
    Objects implementing this protocol provide a `to_dict()` method
    that returns a JSON-serializable dictionary representation.
    """
    def to_dict(self) -> Dict[str, Any]: ...

class HasMessages(Protocol[M]):
    """Protocol for objects that have a messages attribute."""
    @property
    def messages(self) -> Tuple[MessageTrace[M], ...]: ...
    
    def _get_messages_by_severity(self, severity: TraceSeverityLevel) -> Tuple[MessageTrace[M], ...]: ...

class HasErrorMessages(Protocol[M]):
    """Protocol for objects that can handle error messages."""
    @property
    def messages(self) -> Tuple[MessageTrace[M], ...]: ...
    
    @property
    def error_messages(self) -> Tuple[MessageTrace[M], ...]: ...
    
    def has_errors(self) -> bool: ...

class HasInfoMessages(Protocol[M]):
    """Protocol for objects that can handle info messages."""
    @property
    def messages(self) -> Tuple[MessageTrace[M], ...]: ...
    
    @property
    def info_messages(self) -> Tuple[MessageTrace[M], ...]: ...
    
    def has_info(self) -> bool: ...

class HasWarningMessages(Protocol[M]):
    """Protocol for objects that can handle warning messages."""
    @property
    def messages(self) -> Tuple[MessageTrace[M], ...]: ...
    
    @property
    def warning_messages(self) -> Tuple[MessageTrace[M], ...]: ...
    
    def has_warnings(self) -> bool: ...
    
class HasMetadata(Protocol):
    """Protocol for objects that have a metadata attribute."""
    @property
    def metadata(self) -> Optional[Mapping[str, Any]]: ...

class HasValue(Protocol[V]):
    """Protocol for objects that have a value attribute."""
    @property
    def value(self) -> Optional[V]: ...

class HasCause(Protocol[E]):
    """Protocol for objects that have a cause attribute."""
    @property
    def cause(self) -> Optional[E]: ...

class HasMappableValue(Protocol[V, M]):
    """Protocol for Ok-like objects that support value mapping."""
    @property
    def value(self) -> Optional[V]: ...
    @property
    def messages(self) -> Tuple[MessageTrace[M], ...]: ...
    @property
    def metadata(self) -> Optional[Mapping[str, Any]]: ...

class HasMappableCause(Protocol[E, M]):
    """Protocol for Err-like objects that support cause mapping."""
    @property
    def cause(self) -> Optional[E]: ...
    @property
    def messages(self) -> Tuple[MessageTrace[M], ...]: ...
    @property
    def metadata(self) -> Optional[Mapping[str, Any]]: ...

# Mixins
class BaseMixinMessageCollector(Generic[M]):
    """Base class for handling messages.
    
    Expects inheriting classes to provide a 'messages' attribute of type Tuple[MessageTrace[M], ...]
    """
    
    def _get_messages_by_severity(self: HasMessages[M], severity: TraceSeverityLevel) -> Tuple[MessageTrace[M], ...]:
        """Get messages filtered by severity."""
        return tuple(message for message in self.messages if message.severity == severity)

class ErrorCollectorMixin(BaseMixinMessageCollector[M]):
    """Mixin for collecting error messages."""
    
    @property
    def error_messages(self: HasErrorMessages[M]) -> Tuple[MessageTrace[M], ...]:
        """Get error messages."""
        return self._get_messages_by_severity(TraceSeverityLevel.ERROR)
    
    def has_errors(self: HasErrorMessages[M]) -> bool:
        """Check if there are any error messages."""
        return len(self.error_messages) > 0

class InfoCollectorMixin(BaseMixinMessageCollector[M]):
    """Mixin for collecting info messages."""
    
    @property
    def info_messages(self: HasInfoMessages[M]) -> Tuple[MessageTrace[M], ...]:
        """Get info messages."""
        return self._get_messages_by_severity(TraceSeverityLevel.INFO)
    
    def has_info(self: HasInfoMessages[M]) -> bool:
        """Check if there are any info messages."""
        return len(self.info_messages) > 0

class WarningCollectorMixin(BaseMixinMessageCollector[M]):
    """Mixin for collecting warning messages."""
    
    @property
    def warning_messages(self: HasWarningMessages[M]) -> Tuple[MessageTrace[M], ...]:
        """Get warning messages."""
        return self._get_messages_by_severity(TraceSeverityLevel.WARNING)
    
    def has_warnings(self: HasWarningMessages[M]) -> bool:
        """Check if there are any warning messages."""
        return len(self.warning_messages) > 0
    
class MetadataMixin:
    """Mixin for handling metadata.
    
    Expects inheriting classes to provide a 'metadata' attribute of type Optional[Dict[str, Any]].
    """
    
    def has_metadata(self: HasMetadata) -> bool:
        """Check if metadata is present."""
        return self.metadata is not None

class StatusMixin:
    """Provides status checking methods."""
    
    def is_ok(self) -> bool:
        """Check if this is a successful result."""
        return isinstance(self, Ok)
    
    def is_err(self) -> bool:
        """Check if this is an error result."""
        return isinstance(self, Err)

class UnwrapValueMixin(Generic[V]):
    """Mixin for unwrapping values from Ok instances.
    
    Provides methods to extract the contained value with various
    fallback strategies when the value is None.
    """
    
    @overload
    def unwrap(self: HasValue[V]) -> Optional[V]: ...
    
    @overload
    def unwrap(self: HasValue[V], default: V) -> V: ...
    
    def unwrap(self: HasValue[V], default: Optional[V] = None) -> Optional[V]:
        """Unwrap the contained value.
        
        Returns the contained value if present, otherwise returns the
        provided default (or None if no default is provided).
        
        Args:
            default: Optional default value to return if value is None.
                     Must be of the same type as the value.
        
        Returns:
            The contained value, the default, or None.
        """
        if self.value is not None:
            return self.value
        return default

class UnwrapCauseMixin(Generic[E]):
    """Mixin for unwrapping causes from Err instances.
    
    Provides methods to extract the contained cause with various
    fallback strategies when the cause is None.
    """
    
    @overload
    def unwrap(self: HasCause[E]) -> Optional[E]: ...
    
    @overload
    def unwrap(self: HasCause[E], default: E) -> E: ...
    
    def unwrap(self: HasCause[E], default: Optional[E] = None) -> Optional[E]:
        """Unwrap the contained cause.
        
        Returns the contained cause if present, otherwise returns the
        provided default (or None if no default is provided).
        
        Args:
            default: Optional default value to return if cause is None.
                     Must be of the same type as the cause.
        
        Returns:
            The contained cause, the default, or None.
        """
        if self.cause is not None:
            return self.cause
        return default

class MapValueMixin(Generic[V, M]):
    """Mixin for mapping/transforming values in Ok instances.
    
    Provides the `map` method to apply a transformation function to the
    contained value, returning a new Ok instance with the transformed value.
    Messages and metadata are preserved unchanged.
    """
    
    def map(self: HasMappableValue[V, M], f: Callable[[V], T]) -> Ok[T, M]:
        """Apply a transformation function to the contained value.
        
        If the value is present (not None), applies the function `f` to it
        and returns a new Ok instance with the transformed value.
        If the value is None, returns a new Ok instance with None value.
        
        Messages and metadata are preserved in the new instance.
        
        Args:
            f: A callable that takes a value of type V and returns type T.
               Only called if value is not None.
        
        Returns:
            A new Ok instance with the transformed value (or None).
        
        Example:
            >>> ok = Ok(value=5)
            >>> doubled = ok.map(lambda x: x * 2)
            >>> doubled.value
            10
        """
        if self.value is not None:
            return Ok(
                value=f(self.value),
                messages=self.messages,
                metadata=self.metadata
            )
        return Ok(
            value=None,
            messages=self.messages,
            metadata=self.metadata
        )


class MapCauseMixin(Generic[E, M]):
    """Mixin for mapping/transforming causes in Err instances.
    
    Provides the `map` method to apply a transformation function to the
    contained cause, returning a new Err instance with the transformed cause.
    Messages and metadata are preserved unchanged.
    """
    
    def map(self: HasMappableCause[E, M], f: Callable[[E], T]) -> Err[T, M]:
        """Apply a transformation function to the contained cause.
        
        If the cause is present (not None), applies the function `f` to it
        and returns a new Err instance with the transformed cause.
        If the cause is None, returns a new Err instance with None cause.
        
        Messages and metadata are preserved in the new instance.
        
        Args:
            f: A callable that takes a cause of type E and returns type T.
               Only called if cause is not None.
        
        Returns:
            A new Err instance with the transformed cause (or None).
        
        Example:
            >>> err = Err(cause=ValueError("bad"))
            >>> mapped = err.map(lambda e: str(e))
            >>> mapped.cause
            'bad'
        """
        if self.cause is not None:
            return Err(
                cause=f(self.cause),
                messages=self.messages,
                metadata=self.metadata
            )
        return Err(
            cause=None,
            messages=self.messages,
            metadata=self.metadata
        )


@final
@dataclass(frozen=True, slots=True)
class Ok(Generic[V, M],
         MetadataMixin,
         InfoCollectorMixin[M],
         WarningCollectorMixin[M],
         UnwrapValueMixin[V],
         MapValueMixin[V, M],
         StatusMixin,):
    """Represents a successful result.
    
    `Ok` instances represent successful operations and can contain:
    - A value of type V (optional)
    - INFO messages: informational breadcrumbs about the operation
    - WARNING messages: non-critical issues that don't prevent success
    - Metadata: additional context about the operation
    
    By design, `Ok` instances CANNOT contain ERROR messages, as errors
    indicate failure and should be represented by `Err` instances.
    """
    value: Optional[V]
    messages: Tuple[MessageTrace[M], ...] = field(default_factory=tuple)
    metadata: Optional[Mapping[str, Any]] = None
    
    def __post_init__(self) -> None:
        # Ensure messages are immutable tuples.
        if not isinstance(self.messages, tuple):
            object.__setattr__(self, 'messages', tuple(self.messages))

        # Downgrade ERROR messages to WARNING (Ok cannot contain ERROR severity).
        # This preserves the message content while maintaining semantic correctness.
        converted_messages: list[MessageTrace[M]] = []
        for msg in self.messages:
            if msg.severity == TraceSeverityLevel.ERROR:
                # Merge existing details with downgrade info
                original_details = dict(msg.details) if msg.details else {}
                downgrade_info = {
                    "downgraded": {
                        "from": TraceSeverityLevel.ERROR.value,
                        "reason": "Ok instances cannot contain ERROR messages"
                    }
                }
                merged_details = {**original_details, **downgrade_info}

                converted_messages.append(MessageTrace(
                    message=msg.message,
                    severity=TraceSeverityLevel.WARNING,
                    code=msg.code,
                    details=merged_details,
                    stack_trace=msg.stack_trace
                ))
            else:
                converted_messages.append(msg)

        object.__setattr__(self, 'messages', tuple(converted_messages))

        # Ensure metadata is immutable by converting to MappingProxyType.
        if self.metadata is not None and not isinstance(self.metadata, MappingProxyType):
            # Create a copy to prevent external modifications
            object.__setattr__(self, 'metadata', MappingProxyType(dict(self.metadata)))

    def has_value(self) -> bool:
        """Check if value is present."""
        return self.value is not None
    
    def with_info(self, message: M, code: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  stack_trace: Optional[str] = None) -> Self:
        """Add an info message and return a new Ok instance."""
        new_message = MessageTrace[M].info(message, code, details, stack_trace)
        return Ok(
            value=self.value,
            messages=self.messages + (new_message,),
            metadata=self.metadata
        )
    
    def with_warning(self, message: M, code: Optional[str] = None,
                     details: Optional[Dict[str, Any]] = None,
                     stack_trace: Optional[str] = None) -> Self:
        """Add a warning message and return a new Ok instance."""
        new_message = MessageTrace[M].warning(message, code, details, stack_trace)
        return Ok(
            value=self.value,
            messages=self.messages + (new_message,),
            metadata=self.metadata
        )
    
    def with_metadata(self, metadata: Mapping[str, Any]) -> Self:
        """Return a new Ok instance with replaced metadata."""
        return Ok(
            value=self.value,
            messages=self.messages,
            metadata=metadata
        )

@final
@dataclass(frozen=True, slots=True)
class Err(Generic[E, M],
          MetadataMixin,
          ErrorCollectorMixin[M],
          InfoCollectorMixin[M],
          WarningCollectorMixin[M],
          UnwrapCauseMixin[E],
          MapCauseMixin[E, M],
          StatusMixin,):
    """Represents an error result.
    
    Err instances represent failed operations and can contain:
    - A cause of type E (optional): the error/exception that caused the failure
    - ERROR messages: details about what went wrong
    - WARNING messages: non-critical issues encountered during the operation
    - INFO messages: diagnostic breadcrumbs leading to the error
    - Metadata: additional context about the failure
    
    Err instances can contain multiple message types to provide rich
    diagnostic information for debugging and error reporting.
    """
    cause: Optional[E]
    messages: Tuple[MessageTrace[M], ...] = field(default_factory=tuple)
    metadata: Optional[Mapping[str, Any]] = None
    
    def __post_init__(self) -> None:
        # Ensure messages are immutable tuples.
        if not isinstance(self.messages, tuple):
            object.__setattr__(self, 'messages', tuple(self.messages))
        
        # Ensure metadata is immutable by converting to MappingProxyType.
        if self.metadata is not None and not isinstance(self.metadata, MappingProxyType):
            # Create a copy to prevent external modifications
            object.__setattr__(self, 'metadata', MappingProxyType(dict(self.metadata)))
    
    def has_cause(self) -> bool:
        """Check if cause is present."""
        return self.cause is not None
    
    def with_error(self, message: M, code: Optional[str] = None,
                   details: Optional[Dict[str, Any]] = None,
                   stack_trace: Optional[str] = None) -> Self:
        """Add an error message and return a new Err instance."""
        new_message = MessageTrace[M].error(message, code, details, stack_trace)
        return Err(
            cause=self.cause,
            messages=self.messages + (new_message,),
            metadata=self.metadata
        )
    
    def with_info(self, message: M, code: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  stack_trace: Optional[str] = None) -> Self:
        """Add an info message and return a new Err instance."""
        new_message = MessageTrace[M].info(message, code, details, stack_trace)
        return Err(
            cause=self.cause,
            messages=self.messages + (new_message,),
            metadata=self.metadata
        )
    
    def with_warning(self, message: M, code: Optional[str] = None,
                     details: Optional[Dict[str, Any]] = None,
                     stack_trace: Optional[str] = None) -> Self:
        """Add a warning message and return a new Err instance."""
        new_message = MessageTrace[M].warning(message, code, details, stack_trace)
        return Err(
            cause=self.cause,
            messages=self.messages + (new_message,),
            metadata=self.metadata
        )
    
    def with_metadata(self, metadata: Mapping[str, Any]) -> Self:
        """Return a new Err instance with replaced metadata."""
        return Err(
            cause=self.cause,
            messages=self.messages,
            metadata=metadata
        )
    
# Type alias
ResultBase: TypeAlias = Union[Ok[V, M], Err[E, M]] # Flexible and generic result type for complex scenarios
Result: TypeAlias = Union[Ok[V, str], Err[E, str]] # Common and typical result type with string messages

__all__ = [
    "Ok",
    "Err",
    "Result",
    "ResultBase",
    "MessageTrace",
    "TraceSeverityLevel",
]
