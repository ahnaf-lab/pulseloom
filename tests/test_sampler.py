import pytest

from pulseloom.metrics import Metrics
from pulseloom import sampler as sampler_module
from pulseloom.sampler import MetricsSampler


class _FakeVirtualMemory:
    def __init__(self, percent):
        self.percent = percent


class _FakeDiskCounters:
    def __init__(self, read_bytes, write_bytes):
        self.read_bytes = read_bytes
        self.write_bytes = write_bytes


class _FakePsutil:
    def __init__(self, cpu_percent=0.0, mem_percent=0.0, disk_counters=None):
        self.cpu_percent_value = cpu_percent
        self.mem_percent_value = mem_percent
        self.disk_counters_value = disk_counters

    def cpu_percent(self, interval=None):
        return self.cpu_percent_value

    def virtual_memory(self):
        return _FakeVirtualMemory(self.mem_percent_value)

    def disk_io_counters(self):
        return self.disk_counters_value


def test_sample_normalizes_cpu_and_memory_to_unit_range(monkeypatch):
    fake = _FakePsutil(cpu_percent=55.0, mem_percent=40.0, disk_counters=_FakeDiskCounters(0, 0))
    monkeypatch.setattr(sampler_module, "psutil", fake)

    metrics = MetricsSampler(interval=1.0).sample()

    assert isinstance(metrics, Metrics)
    assert metrics.cpu == pytest.approx(0.55)
    assert metrics.memory == pytest.approx(0.40)


def test_disk_activity_is_zero_on_first_sample(monkeypatch):
    fake = _FakePsutil(disk_counters=_FakeDiskCounters(1000, 2000))
    monkeypatch.setattr(sampler_module, "psutil", fake)

    metrics = MetricsSampler(interval=1.0).sample()

    assert metrics.disk == 0.0


def test_disk_activity_reflects_byte_delta_over_elapsed_time(monkeypatch):
    fake = _FakePsutil(disk_counters=_FakeDiskCounters(0, 0))
    monkeypatch.setattr(sampler_module, "psutil", fake)
    clock = iter([0.0, 1.0])
    sampler = MetricsSampler(interval=1.0, clock=lambda: next(clock))

    sampler.sample()  # establishes the baseline at t=0
    half_saturation = sampler_module.DISK_SATURATION_BYTES_PER_SEC / 2
    fake.disk_counters_value = _FakeDiskCounters(half_saturation, half_saturation)
    metrics = sampler.sample()  # t=1, full saturation worth of bytes moved

    assert metrics.disk == pytest.approx(1.0)


def test_disk_activity_is_zero_when_counters_unavailable(monkeypatch):
    fake = _FakePsutil(disk_counters=None)
    monkeypatch.setattr(sampler_module, "psutil", fake)

    metrics = MetricsSampler(interval=1.0).sample()

    assert metrics.disk == 0.0


def test_sampler_rejects_non_positive_interval():
    with pytest.raises(ValueError):
        MetricsSampler(interval=0)


def test_stream_yields_immediately_then_sleeps_for_interval(monkeypatch):
    fake = _FakePsutil(disk_counters=_FakeDiskCounters(0, 0))
    monkeypatch.setattr(sampler_module, "psutil", fake)
    sleep_calls = []
    monkeypatch.setattr(sampler_module.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    stream = MetricsSampler(interval=2.5).stream()
    first = next(stream)
    next(stream)
    next(stream)

    assert isinstance(first, Metrics)
    assert sleep_calls == [2.5, 2.5]
