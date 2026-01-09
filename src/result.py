from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Generic, Protocol, TypeAlias, TypeVar, Union, Optional, Dict, Any, Tuple

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
    details: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None

    @classmethod
    def info(cls, message: M, code: Optional[str] = None,
             details: Optional[Dict[str, Any]] = None,
             stack_trace: Optional[str] = None) -> MessageTrace[M]:
        """Factory method for info messages."""
        return cls(message=message, severity=TraceSeverityLevel.INFO, code=code, details=details, stack_trace=stack_trace)
    
    @classmethod
    def warning(cls, message: M, code: Optional[str] = None,
                details: Optional[Dict[str, Any]] = None,
                stack_trace: Optional[str] = None) -> MessageTrace[M]:
        """Factory method for warning messages."""
        return cls(message=message, severity=TraceSeverityLevel.WARNING, code=code, details=details, stack_trace=stack_trace)
    
    @classmethod
    def error(cls, message: M, code: Optional[str] = None,
              details: Optional[Dict[str, Any]] = None,
              stack_trace: Optional[str] = None) -> MessageTrace[M]:
        """Factory method for error messages."""
        return cls(message=message, severity=TraceSeverityLevel.ERROR, code=code, details=details, stack_trace=stack_trace)

# Protocols
class HasMessages(Protocol):
    """Protocol for objects that have a messages attribute."""
    @property
    def messages(self) -> Tuple[MessageTrace, ...]: ...

class HasMetadata(Protocol):
    """Protocol for objects that have a metadata attribute."""
    @property
    def metadata(self) -> Optional[Dict[str, Any]]: ...

class HasValue(Protocol[V]):
    """Protocol for objects that have a value attribute."""
    @property
    def value(self) -> Optional[V]: ...

class HasTrace(Protocol[E]):
    """Protocol for objects that have an trace attribute."""
    @property
    def trace(self) -> Optional[E]: ...

# Mixin
class BaseMixinMessageCollector(HasMessages):
    """Base class for handling messages."""
    def _get_messages_by_severity(self, severity: TraceSeverityLevel) -> Tuple[MessageTrace, ...]:
        """Get messages filtered by severity."""
        return tuple(message for message in self.messages if message.severity == severity)

class ErrorCollectorMixin(Generic[M], BaseMixinMessageCollector):
    """Mixin for collecting error messages."""
    
    @property
    def error_messages(self) -> Tuple[MessageTrace[M], ...]:
        """Get error messages."""
        return self._get_messages_by_severity(TraceSeverityLevel.ERROR)
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any error messages."""
        return len(self.error_messages) > 0

class InfoCollectorMixin(Generic[M], BaseMixinMessageCollector):
    """Mixin for collecting info messages."""
    
    @property
    def info_messages(self) -> Tuple[MessageTrace[M], ...]:
        """Get info messages."""
        return self._get_messages_by_severity(TraceSeverityLevel.INFO)
    
    @property
    def has_info(self) -> bool:
        """Check if there are any info messages."""
        return len(self.info_messages) > 0

class WarningCollectorMixin(Generic[M], BaseMixinMessageCollector):
    """Mixin for collecting warning messages."""
    
    @property
    def warning_messages(self) -> Tuple[MessageTrace[M], ...]:
        """Get warning messages."""
        return self._get_messages_by_severity(TraceSeverityLevel.WARNING)
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warning messages."""
        return len(self.warning_messages) > 0
    
class MetadataMixin(HasMetadata):
    """Mixin for handling metadata."""
    
    def has_metadata(self) -> bool:
        """Check if metadata is present."""
        return self.metadata is not None

class StatusMixin:
    """Provides status checking methods."""
    
    @property
    def is_ok(self) -> bool:
        """Check if this is a successful result."""
        return type(self) is Ok
    
    @property
    def is_err(self) -> bool:
        """Check if this is an error result."""
        return type(self) is Err

@dataclass(frozen=True)
class Ok(Generic[V, M],
         HasValue[V],
         MetadataMixin,
         InfoCollectorMixin[M],
         WarningCollectorMixin[M],
         StatusMixin,):
    """Represents a successful result."""
    value: Optional[V]
    messages: Tuple[MessageTrace[M], ...] = field(default_factory=tuple)
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        
        # Ensure messages are immutable tuples.
        if not isinstance(self.messages, tuple):
            object.__setattr__(self, 'messages', tuple(self.messages))
            
    def has_value(self) -> bool:
        """Check if value is present."""
        return self.value is not None
    
    def with_info(self, message: M, code: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  stack_trace: Optional[str] = None) -> Ok[V, M]:
        """Add an info message and return a new Ok instance."""
        new_message = MessageTrace[M].info(message, code, details, stack_trace)
        return Ok(
            value=self.value,
            messages=self.messages + (new_message,),
            metadata=self.metadata
        )
    
    def with_warning(self, message: M, code: Optional[str] = None,
                     details: Optional[Dict[str, Any]] = None,
                     stack_trace: Optional[str] = None) -> Ok[V, M]:
        """Add a warning message and return a new Ok instance."""
        new_message = MessageTrace[M].warning(message, code, details, stack_trace)
        return Ok(
            value=self.value,
            messages=self.messages + (new_message,),
            metadata=self.metadata
        )

@dataclass(frozen=True)
class Err(Generic[E, M],
          HasTrace[E],
          MetadataMixin,
          ErrorCollectorMixin[M],
          InfoCollectorMixin[M],
          WarningCollectorMixin[M],
          StatusMixin,):
    """Represents an error result."""
    trace: Optional[E]
    messages: Tuple[MessageTrace[M], ...] = field(default_factory=tuple)
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        
        # Ensure messages are immutable tuples.
        if not isinstance(self.messages, tuple):
            object.__setattr__(self, 'messages', tuple(self.messages))
    
    def has_trace(self) -> bool:
        """Check if trace is present."""
        return self.trace is not None
    
    def with_error(self, message: M, code: Optional[str] = None,
                   details: Optional[Dict[str, Any]] = None,
                   stack_trace: Optional[str] = None) -> Err[E, M]:
        """Add an error message and return a new Err instance."""
        new_message = MessageTrace[M].error(message, code, details, stack_trace)
        return Err(
            trace=self.trace,
            messages=self.messages + (new_message,),
            metadata=self.metadata
        )
    
    def with_info(self, message: M, code: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  stack_trace: Optional[str] = None) -> Err[E, M]:
        """Add an info message and return a new Err instance."""
        new_message = MessageTrace[M].info(message, code, details, stack_trace)
        return Err(
            trace=self.trace,
            messages=self.messages + (new_message,),
            metadata=self.metadata
        )
    
    def with_warning(self, message: M, code: Optional[str] = None,
                     details: Optional[Dict[str, Any]] = None,
                     stack_trace: Optional[str] = None) -> Err[E, M]:
        """Add a warning message and return a new Err instance."""
        new_message = MessageTrace[M].warning(message, code, details, stack_trace)
        return Err(
            trace=self.trace,
            messages=self.messages + (new_message,),
            metadata=self.metadata
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
