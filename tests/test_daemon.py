import os
import subprocess
import sys

from pulseloom.daemon import (
    is_process_alive,
    read_pid_file,
    remove_pid_file,
    run_loop,
    write_pid_file,
)
from pulseloom.generator import generate_frame
from pulseloom.metrics import Metrics


class _FakeSampler:
    """Yields a fixed list of readings, then repeats the last one forever."""

    def __init__(self, readings):
        self._readings = readings

    def stream(self):
        for reading in self._readings:
            yield reading
        while True:
            yield self._readings[-1]


def test_is_process_alive_true_for_current_process():
    assert is_process_alive(os.getpid()) is True


def test_is_process_alive_false_for_exited_process():
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    pid = proc.pid
    proc.wait()  # reap it, so the pid is no longer even a zombie
    assert is_process_alive(pid) is False


def test_pid_file_round_trip(tmp_path):
    pid_file = tmp_path / "sub" / "pulseloom.pid"

    assert read_pid_file(pid_file) is None

    write_pid_file(pid_file, 4321)
    assert read_pid_file(pid_file) == 4321

    remove_pid_file(pid_file)
    assert read_pid_file(pid_file) is None
    remove_pid_file(pid_file)  # removing a missing file is a no-op, not an error


def test_read_pid_file_ignores_garbage_content(tmp_path):
    pid_file = tmp_path / "pulseloom.pid"
    pid_file.write_text("not-a-pid\n")
    assert read_pid_file(pid_file) is None


def test_run_loop_writes_the_last_sampled_frame(tmp_path):
    output_file = tmp_path / "frame.svg"
    readings = [
        Metrics(cpu=0.1, memory=0.2, disk=0.0),
        Metrics(cpu=0.9, memory=0.5, disk=0.3),
    ]
    sampler = _FakeSampler(readings)
    calls = {"count": 0}

    def should_continue():
        calls["count"] += 1
        return calls["count"] <= len(readings)

    run_loop(output_file, seed=7, sampler=sampler, should_continue=should_continue)

    assert output_file.exists()
    assert output_file.read_text() == generate_frame(readings[-1], seed=7)
    assert not output_file.with_name("frame.svg.tmp").exists()


def test_run_loop_creates_parent_directories(tmp_path):
    output_file = tmp_path / "nested" / "dir" / "frame.svg"
    sampler = _FakeSampler([Metrics(cpu=0.0, memory=0.0, disk=0.0)])

    run_loop(output_file, sampler=sampler, should_continue=lambda: True if not output_file.exists() else False)

    assert output_file.exists()


def test_run_loop_writes_nothing_when_should_continue_is_already_false(tmp_path):
    output_file = tmp_path / "frame.svg"
    sampler = _FakeSampler([Metrics(cpu=0.0, memory=0.0, disk=0.0)])

    run_loop(output_file, sampler=sampler, should_continue=lambda: False)

    assert not output_file.exists()
