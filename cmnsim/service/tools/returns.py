from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar("T")


@dataclass(frozen=True)
class Ok(Generic[T]):
    """Ok response"""

    result: T

    def __repr__(self) -> str:
        return f"Ok(result={self.result!r})"


@dataclass(frozen=True)
class Error:
    """Error response"""

    message: str
    code: int = 0

    def __repr__(self) -> str:
        return f"Error(message={self.message})"


U = TypeVar("U")
Result = Union[Ok[U], Error]
