"""The metrics vector that drives a single generated frame."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Metrics:
    """A snapshot of machine activity, each field normalized to [0.0, 1.0].

    cpu: fraction of CPU capacity currently in use.
    memory: fraction of memory currently in use.
    disk: fraction of recent disk I/O capacity in use.
    """

    cpu: float
    memory: float
    disk: float

    def __post_init__(self) -> None:
        for name in ("cpu", "memory", "disk"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)):
                raise TypeError(f"Metrics.{name} must be a number, got {type(value).__name__}")
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Metrics.{name} must be within [0.0, 1.0], got {value}")
