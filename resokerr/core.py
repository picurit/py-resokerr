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
    Literal,
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
    SUCCESS = "success"
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
    def success(cls, message: M, code: Optional[str] = None,
                details: Optional[Mapping[str, Any]] = None,
                stack_trace: Optional[str] = None) -> MessageTrace[M]:
        """Factory method for success messages."""
        return cls(message=message, severity=TraceSeverityLevel.SUCCESS, code=code, details=details, stack_trace=stack_trace)

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
            "message": TypeUtils.serialize(self.message),
            "severity": self.severity.value,
        }

        # Only include optional fields if they have values
        if self.code is not None:
            result["code"] = self.code
        if self.details is not None:
            # Recursively serialize details values (they may contain complex objects)
            result["details"] = TypeUtils.serialize(dict(self.details))
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


class TypeUtils:
    """Utility class for type inspection and serialization operations.

    Provides static methods for checking object capabilities, type constraints,
    and serializing objects to JSON-compatible representations.
    This class cannot be instantiated - all methods are static utilities.
    """

    __slots__ = ()  # Prevent instantiation with instance attributes

    def __new__(cls) -> None:
        raise TypeError("TypeUtils cannot be instantiated - use static methods directly")

    @staticmethod
    def is_json_primitive(obj: Any) -> bool:
        """Check if an object is natively JSON-serializable.

        JSON primitive types are values that can be directly serialized to JSON
        without any transformation: strings, numbers, booleans, None, dicts, and lists.

        Args:
            obj: The object to check.

        Returns:
            True if the object is a JSON primitive type, False otherwise.

        Example:
            >>> TypeUtils.is_json_primitive("hello")
            True
            >>> TypeUtils.is_json_primitive(42)
            True
            >>> TypeUtils.is_json_primitive({"key": "value"})
            True
            >>> TypeUtils.is_json_primitive([1, 2, 3])
            True
            >>> TypeUtils.is_json_primitive(CustomObject())
            False
        """
        return obj is None or isinstance(obj, (str, int, float, bool, dict, list))

    @staticmethod
    def has_to_dict(obj: Any) -> bool:
        """Check if an object implements the to_dict() protocol.

        This method checks whether an object has a `to_dict()` method
        that can be used for serialization to a dictionary. Useful for
        determining how a custom message type will be handled during
        serialization.

        Args:
            obj: The object to check for to_dict() capability.

        Returns:
            True if the object has a to_dict() method, False otherwise.

        Example:
            >>> class MyMessage:
            ...     def to_dict(self):
            ...         return {"data": "value"}
            >>> TypeUtils.has_to_dict(MyMessage())
            True
            >>> TypeUtils.has_to_dict("plain string")
            False
        """
        return isinstance(obj, Serializable)
    
    @staticmethod
    def is_exception(obj: Any) -> bool:
        """Check if an object is an exception instance.

        Args:
            obj: The object to check.
        Returns:
            True if the object is an instance of BaseException, False otherwise.
        
        Example:
            >>> TypeUtils.is_exception(ValueError("invalid"))
            True
            >>> TypeUtils.is_exception("not an exception")
            False
        """
        return isinstance(obj, BaseException)

    @staticmethod
    def serialize_exception(exception: BaseException) -> Any:
        """Serialize an exception to a JSON-compatible representation.

        Args:
            exception: The exception instance to serialize.

        Returns:
            A JSON-serializable representation of the exception.

        Example:
            >>> try:
            ...     1 / 0
            ... except ZeroDivisionError as e:
            ...     TypeUtils.serialize_exception(e)
            {'type': 'ZeroDivisionError', 'message': 'division by zero'}
        """
        exception_dict = {
            'name': type(exception).__name__,
            'message': str(exception),
        }
        if exception.__cause__ is not None:
            exception_dict['cause'] = TypeUtils.serialize_exception(exception.__cause__)
        return exception_dict
    
    @staticmethod
    def serialize(obj: Any) -> Any:
        """Serialize an object to a JSON-compatible representation.

        Transforms objects to their serializable form:
        - JSON simple primitives (str, int, float, bool, None): returned as-is
        - dict: recursively serializes all values
        - list/tuple: recursively serializes all items (tuples become lists)
        - Objects implementing to_dict() protocol: calls to_dict()
        - Exceptions: serialized via serialize_exception()
        - Other types: converted to string representation

        Args:
            obj: The object to serialize.

        Returns:
            A JSON-serializable representation of the object.

        Example:
            >>> TypeUtils.serialize("hello")
            'hello'
            >>> TypeUtils.serialize({"key": CustomObj()})
            {'key': {'serialized': 'data'}}
            >>> TypeUtils.serialize([1, CustomObj(), "text"])
            [1, {'serialized': 'data'}, 'text']
        """
        # Simple primitives (not containers) - return as-is
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj

        # Dict: recursively serialize values
        if isinstance(obj, dict):
            return {key: TypeUtils.serialize(value) for key, value in obj.items()}
        
        # Recurse serialization collection types
        if isinstance(obj, (list, tuple)):
            return [TypeUtils.serialize(item) for item in obj]

        # Objects with to_dict() protocol
        if TypeUtils.has_to_dict(obj):
            serializable: Serializable = obj
            return serializable.to_dict()

        # Exceptions
        if TypeUtils.is_exception(obj):
            return TypeUtils.serialize_exception(obj)

        # Fallback: string representation
        return str(obj)


class HasMessages(Protocol[M]):
    """Protocol for objects that have a messages attribute."""
    @property
    def messages(self) -> Tuple[MessageTrace[M], ...]: ...
    
    def _get_messages_by_severity(self, severity: TraceSeverityLevel) -> Tuple[MessageTrace[M], ...]: ...

class HasSuccessMessages(Protocol[M]):
    """Protocol for objects that can handle success messages."""
    @property
    def messages(self) -> Tuple[MessageTrace[M], ...]: ...
    
    @property
    def success_messages(self) -> Tuple[MessageTrace[M], ...]: ...
    
    def has_successes(self) -> bool: ...

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

class HasErrorMessages(Protocol[M]):
    """Protocol for objects that can handle error messages."""
    @property
    def messages(self) -> Tuple[MessageTrace[M], ...]: ...
    
    @property
    def error_messages(self) -> Tuple[MessageTrace[M], ...]: ...
    
    def has_errors(self) -> bool: ...
    
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

class SuccessCollectorMixin(BaseMixinMessageCollector[M]):
    """Mixin for collecting success messages."""
    
    @property
    def success_messages(self) -> Tuple[MessageTrace[M], ...]:
        """Get success messages."""
        return self._get_messages_by_severity(TraceSeverityLevel.SUCCESS)
    
    def has_successes(self: HasSuccessMessages[M]) -> bool:
        """Check if there are any success messages."""
        return len(self.success_messages) > 0

class InfoCollectorMixin(BaseMixinMessageCollector[M]):
    """Mixin for collecting info messages."""
    
    @property
    def info_messages(self) -> Tuple[MessageTrace[M], ...]:
        """Get info messages."""
        return self._get_messages_by_severity(TraceSeverityLevel.INFO)
    
    def has_info(self: HasInfoMessages[M]) -> bool:
        """Check if there are any info messages."""
        return len(self.info_messages) > 0

class WarningCollectorMixin(BaseMixinMessageCollector[M]):
    """Mixin for collecting warning messages."""
    
    @property
    def warning_messages(self) -> Tuple[MessageTrace[M], ...]:
        """Get warning messages."""
        return self._get_messages_by_severity(TraceSeverityLevel.WARNING)
    
    def has_warnings(self: HasWarningMessages[M]) -> bool:
        """Check if there are any warning messages."""
        return len(self.warning_messages) > 0

class ErrorCollectorMixin(BaseMixinMessageCollector[M]):
    """Mixin for collecting error messages."""
    
    @property
    def error_messages(self) -> Tuple[MessageTrace[M], ...]:
        """Get error messages."""
        return self._get_messages_by_severity(TraceSeverityLevel.ERROR)
    
    def has_errors(self: HasErrorMessages[M]) -> bool:
        """Check if there are any error messages."""
        return len(self.error_messages) > 0

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

    @overload
    def unwrap(self: HasValue[V], default: Optional[V], as_dict: Literal[False]) -> Optional[V]: ...

    @overload
    def unwrap(self: HasValue[V], default: Optional[V], as_dict: Literal[True]) -> Dict[str, Any]: ...

    @overload
    def unwrap(self: HasValue[V], *, as_dict: Literal[True]) -> Dict[str, Any]: ...

    def unwrap(self: HasValue[V], default: Optional[V] = None, as_dict: bool = False) -> Union[Optional[V], Dict[str, Any]]:
        """Unwrap the contained value.

        Returns the contained value if present, otherwise returns the
        provided default (or None if no default is provided).

        Args:
            default: Optional default value to return if value is None.
                     Must be of the same type as the value.
            as_dict: If True, returns the value serialized as a dict-compatible
                     representation. JSON primitives are returned as-is, objects
                     with to_dict() have that method called, others become strings.

        Returns:
            The contained value, the default, or None. If as_dict=True, returns
            the serialized representation instead.

        Example:
            >>> ok = Ok(value={"name": "test"})
            >>> ok.unwrap()
            {'name': 'test'}
            >>> ok.unwrap(as_dict=True)
            {'name': 'test'}
        """
        result = self.value if self.value is not None else default
        if as_dict and result is not None:
            return TypeUtils.serialize(result)
        return result


class UnwrapCauseMixin(Generic[E]):
    """Mixin for unwrapping causes from Err instances.

    Provides methods to extract the contained cause with various
    fallback strategies when the cause is None.
    """

    @overload
    def unwrap(self: HasCause[E]) -> Optional[E]: ...

    @overload
    def unwrap(self: HasCause[E], default: E) -> E: ...

    @overload
    def unwrap(self: HasCause[E], default: Optional[E], as_dict: Literal[False]) -> Optional[E]: ...

    @overload
    def unwrap(self: HasCause[E], default: Optional[E], as_dict: Literal[True]) -> Any: ...

    @overload
    def unwrap(self: HasCause[E], *, as_dict: Literal[True]) -> Any: ...

    def unwrap(self: HasCause[E], default: Optional[E] = None, as_dict: bool = False) -> Union[Optional[E], Any]:
        """Unwrap the contained cause.

        Returns the contained cause if present, otherwise returns the
        provided default (or None if no default is provided).

        Args:
            default: Optional default value to return if cause is None.
                     Must be of the same type as the cause.
            as_dict: If True, returns the cause serialized as a dict-compatible
                     representation. JSON primitives are returned as-is, objects
                     with to_dict() have that method called, others become strings.

        Returns:
            The contained cause, the default, or None. If as_dict=True, returns
            the serialized representation instead.

        Example:
            >>> err = Err(cause=ValueError("invalid input"))
            >>> err.unwrap()
            ValueError('invalid input')
            >>> err.unwrap(as_dict=True)
            "ValueError('invalid input')"
        """
        result = self.cause if self.cause is not None else default
        if as_dict and result is not None:
            return TypeUtils.serialize(result)
        return result


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
         SuccessCollectorMixin[M],
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
        
        # Ensure metadata is immutable by converting to MappingProxyType.
        if self.metadata is not None and not isinstance(self.metadata, MappingProxyType):
            # Create a copy to prevent external modifications
            object.__setattr__(self, 'metadata', MappingProxyType(dict(self.metadata)))

        # Convert ERROR messages to WARNING (Ok cannot contain ERROR severity).
        # This preserves the message content while maintaining semantic correctness.
        converted_messages: list[MessageTrace[M]] = []
        for msg in self.messages:
            if msg.severity == TraceSeverityLevel.ERROR:
                # Merge existing details with converted info
                original_details = dict(msg.details) if msg.details else {}
                converted_info = {
                    "_converted_from": {
                        "from": TraceSeverityLevel.ERROR.value,
                        "reason": "Ok instances cannot contain ERROR messages"
                    }
                }
                merged_details = {**original_details, **converted_info}

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

    def has_value(self) -> bool:
        """Check if value is present."""
        return self.value is not None

    def with_success(self, message: M, code: Optional[str] = None,
                     details: Optional[Dict[str, Any]] = None,
                     stack_trace: Optional[str] = None) -> Self:
        """Add a success message and return a new Ok instance."""
        new_message = MessageTrace[M].success(message, code, details, stack_trace)
        return Ok(
            value=self.value,
            messages=self.messages + (new_message,),
            metadata=self.metadata
        )
    
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

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Ok to a dictionary.

        Creates a serializable dictionary representation of the
        Ok instance. Optional fields (metadata) are only included
        if they have non-None values.

        Returns:
            A dictionary with the following structure:
            {
                "is_ok": True,
                "is_err": False,
                "value": <serialized value>,
                "messages": [<serialized messages>],
                "metadata": <optional>
            }

        Example:
            >>> ok = Ok(value=42, messages=(MessageTrace.info("done"),))
            >>> ok.to_dict()
            {'is_ok': True, 'is_err': False, 'value': 42, 'messages': [{'message': 'done', 'severity': 'info'}]}
        """
        result: Dict[str, Any] = {
            "is_ok": True,
            "is_err": False,
            "value": TypeUtils.serialize(self.value),
            "messages": [msg.to_dict() for msg in self.messages],
        }

        if self.metadata is not None:
            # Recursively serialize metadata values (they may contain complex objects)
            result["metadata"] = TypeUtils.serialize(dict(self.metadata))

        return result


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
        
        # Convert SUCCESS messages to INFO (Err cannot contain SUCCESS severity).
        # This preserves the message content while maintaining semantic correctness.
        converted_messages: list[MessageTrace[M]] = []
        for msg in self.messages:
            if msg.severity == TraceSeverityLevel.SUCCESS:
                # Merge existing details with converted info
                original_details = dict(msg.details) if msg.details else {}
                converted_info = {
                    "_converted_from": {
                        "from": TraceSeverityLevel.SUCCESS.value,
                        "reason": "Err instances cannot contain SUCCESS messages"
                    }
                }
                merged_details = {**original_details, **converted_info}

                converted_messages.append(MessageTrace(
                    message=msg.message,
                    severity=TraceSeverityLevel.INFO,
                    code=msg.code,
                    details=merged_details,
                    stack_trace=msg.stack_trace
                ))
            else:
                converted_messages.append(msg)
        object.__setattr__(self, 'messages', tuple(converted_messages))
    
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

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Err to a dictionary.

        Creates a serializable dictionary representation of the
        Err instance. Optional fields (metadata) are only included
        if they have non-None values.

        Returns:
            A dictionary with the following structure:
            {
                "is_ok": False,
                "is_err": True,
                "cause": <serialized cause>,
                "messages": [<serialized messages>],
                "metadata": <optional>
            }

        Example:
            >>> err = Err(cause="not found", messages=(MessageTrace.error("failed"),))
            >>> err.to_dict()
            {'is_ok': False, 'is_err': True, 'cause': 'not found', 'messages': [{'message': 'failed', 'severity': 'error'}]}
        """
        result: Dict[str, Any] = {
            "is_ok": False,
            "is_err": True,
            "cause": TypeUtils.serialize(self.cause),
            "messages": [msg.to_dict() for msg in self.messages],
        }

        if self.metadata is not None:
            # Recursively serialize metadata values (they may contain complex objects)
            result["metadata"] = TypeUtils.serialize(dict(self.metadata))

        return result


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
