from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import (
    Any,
    Dict,
    Generic,
    Mapping,
    Optional,
    Protocol,
    Self,
    TypeAlias,
    TypeVar,
    Tuple,
    Union,
)

V = TypeVar('V')    # Value type
E = TypeVar('E')    # Error type
M = TypeVar('M')    # Message type

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
            object.__setattr__(self, 'details', MappingProxyType(self.details))

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

# Protocols
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

@dataclass(frozen=True)
class Ok(Generic[V, M],
         MetadataMixin,
         InfoCollectorMixin[M],
         WarningCollectorMixin[M],
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
    __match_args__ = ('value', 'messages', 'metadata')
    
    value: Optional[V]
    messages: Tuple[MessageTrace[M], ...] = field(default_factory=tuple)
    metadata: Optional[Mapping[str, Any]] = None
    
    def __post_init__(self) -> None:
        # Ensure messages are immutable tuples.
        if not isinstance(self.messages, tuple):
            object.__setattr__(self, 'messages', tuple(self.messages))
        
        # Ensure metadata is immutable by converting to MappingProxyType.
        if self.metadata is not None and not isinstance(self.metadata, MappingProxyType):
            object.__setattr__(self, 'metadata', MappingProxyType(self.metadata))
            
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

@dataclass(frozen=True)
class Err(Generic[E, M],
          MetadataMixin,
          ErrorCollectorMixin[M],
          InfoCollectorMixin[M],
          WarningCollectorMixin[M],
          StatusMixin,):
    """Represents an error result.
    
    Err instances represent failed operations and can contain:
    - A trace of type E (optional): the error/exception that caused the failure
    - ERROR messages: details about what went wrong
    - WARNING messages: non-critical issues encountered during the operation
    - INFO messages: diagnostic breadcrumbs leading to the error
    - Metadata: additional context about the failure
    
    Err instances can contain multiple message types to provide rich
    diagnostic information for debugging and error reporting.
    """
    __match_args__ = ('trace', 'messages', 'metadata')
    
    trace: Optional[E]
    messages: Tuple[MessageTrace[M], ...] = field(default_factory=tuple)
    metadata: Optional[Mapping[str, Any]] = None
    
    def __post_init__(self) -> None:
        # Ensure messages are immutable tuples.
        if not isinstance(self.messages, tuple):
            object.__setattr__(self, 'messages', tuple(self.messages))
        
        # Ensure metadata is immutable by converting to MappingProxyType.
        if self.metadata is not None and not isinstance(self.metadata, MappingProxyType):
            object.__setattr__(self, 'metadata', MappingProxyType(self.metadata))
    
    def has_trace(self) -> bool:
        """Check if trace is present."""
        return self.trace is not None
    
    def with_error(self, message: M, code: Optional[str] = None,
                   details: Optional[Dict[str, Any]] = None,
                   stack_trace: Optional[str] = None) -> Self:
        """Add an error message and return a new Err instance."""
        new_message = MessageTrace[M].error(message, code, details, stack_trace)
        return Err(
            trace=self.trace,
            messages=self.messages + (new_message,),
            metadata=self.metadata
        )
    
    def with_info(self, message: M, code: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  stack_trace: Optional[str] = None) -> Self:
        """Add an info message and return a new Err instance."""
        new_message = MessageTrace[M].info(message, code, details, stack_trace)
        return Err(
            trace=self.trace,
            messages=self.messages + (new_message,),
            metadata=self.metadata
        )
    
    def with_warning(self, message: M, code: Optional[str] = None,
                     details: Optional[Dict[str, Any]] = None,
                     stack_trace: Optional[str] = None) -> Self:
        """Add a warning message and return a new Err instance."""
        new_message = MessageTrace[M].warning(message, code, details, stack_trace)
        return Err(
            trace=self.trace,
            messages=self.messages + (new_message,),
            metadata=self.metadata
        )
    
    def with_metadata(self, metadata: Mapping[str, Any]) -> Self:
        """Return a new Err instance with replaced metadata."""
        return Err(
            trace=self.trace,
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
