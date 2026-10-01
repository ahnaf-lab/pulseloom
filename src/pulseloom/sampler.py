"""Samples live CPU, memory and disk activity into Metrics vectors.

Uses psutil so the same code works across Linux, macOS and Windows.
"""

import time
from typing import Callable, Iterator, Optional

import psutil

from .metrics import Metrics

DEFAULT_INTERVAL = 1.0

# Read+write throughput, in bytes/sec, treated as "fully saturated" disk
# activity (1.0). There is no OS-native disk percentage to read, so this is
# derived from the byte delta between consecutive samples instead.
DISK_SATURATION_BYTES_PER_SEC = 100.0 * 1024 * 1024


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


class MetricsSampler:
    """Polls psutil at a fixed interval and emits Metrics vectors.

    CPU and memory map directly onto psutil's percentage readings. Disk
    activity has no equivalent percentage, so it is derived from the
    read+write byte delta between two samples divided by the elapsed time,
    normalized against `DISK_SATURATION_BYTES_PER_SEC`.
    """

    def __init__(
        self,
        interval: float = DEFAULT_INTERVAL,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if interval <= 0:
            raise ValueError(f"interval must be positive, got {interval}")
        self._interval = interval
        self._clock = clock
        self._last_disk_bytes: Optional[int] = None
        self._last_time: Optional[float] = None

    @property
    def interval(self) -> float:
        return self._interval

    def sample(self) -> Metrics:
        """Take one sample of current CPU/memory/disk activity.

        The very first call establishes psutil's internal CPU baseline and
        this sampler's disk-throughput baseline, so its disk reading is
        always 0.0; later calls reflect real deltas.
        """
        cpu = _clamp01(psutil.cpu_percent(interval=None) / 100.0)
        memory = _clamp01(psutil.virtual_memory().percent / 100.0)
        disk = self._sample_disk()
        return Metrics(cpu=cpu, memory=memory, disk=disk)

    def _sample_disk(self) -> float:
        counters = psutil.disk_io_counters()
        now = self._clock()

        if counters is None:
            return 0.0

        total_bytes = counters.read_bytes + counters.write_bytes

        if self._last_disk_bytes is None or self._last_time is None:
            self._last_disk_bytes = total_bytes
            self._last_time = now
            return 0.0

        elapsed = now - self._last_time
        byte_delta = total_bytes - self._last_disk_bytes
        self._last_disk_bytes = total_bytes
        self._last_time = now

        if elapsed <= 0 or byte_delta <= 0:
            return 0.0

        throughput = byte_delta / elapsed
        return _clamp01(throughput / DISK_SATURATION_BYTES_PER_SEC)

    def stream(self) -> Iterator[Metrics]:
        """Yield one Metrics vector immediately, then one every `interval` seconds, forever."""
        yield self.sample()
        while True:
            time.sleep(self._interval)
            yield self.sample()
