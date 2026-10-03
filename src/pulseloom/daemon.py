"""Daemon primitives: PID file management and the sample-generate-write loop.

Process start/stop/status orchestration lives in `cli.py`; this module holds
the pieces that don't need an OS process to exercise in tests.
"""

import errno
import os
from pathlib import Path
from typing import Callable, Optional, Union

from .generator import DEFAULT_BLEND_STEPS, generate_blended_frames, generate_frame
from .metrics import Metrics
from .render import DEFAULT_PALETTE, Palette
from .sampler import DEFAULT_INTERVAL, MetricsSampler

DEFAULT_SEED = 0
DEFAULT_STATE_DIR = Path.home() / ".pulseloom"
DEFAULT_PID_FILE = DEFAULT_STATE_DIR / "pulseloom.pid"
DEFAULT_OUTPUT_FILE = DEFAULT_STATE_DIR / "frame.svg"

PathLike = Union[str, Path]


def is_process_alive(pid: int) -> bool:
    """Return whether `pid` names a live process, using a signal-0 probe."""
    try:
        os.kill(pid, 0)
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return False
        if exc.errno == errno.EPERM:
            # Exists, just owned by someone else.
            return True
        raise
    return True


def read_pid_file(pid_file: PathLike) -> Optional[int]:
    """Return the pid stored in `pid_file`, or None if absent/unreadable."""
    try:
        text = Path(pid_file).read_text().strip()
    except FileNotFoundError:
        return None
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def write_pid_file(pid_file: PathLike, pid: int) -> None:
    pid_file = Path(pid_file)
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(pid))


def remove_pid_file(pid_file: PathLike) -> None:
    try:
        Path(pid_file).unlink()
    except FileNotFoundError:
        pass


def run_loop(
    output_file: PathLike,
    interval: float = DEFAULT_INTERVAL,
    seed: int = DEFAULT_SEED,
    sampler: Optional[MetricsSampler] = None,
    should_continue: Callable[[], bool] = lambda: True,
    blend_steps: int = DEFAULT_BLEND_STEPS,
    palette: Palette = DEFAULT_PALETTE,
) -> None:
    """Sample, generate frames and write them to `output_file`, on repeat.

    The first sample is written as-is. Every later sample is eased into from
    the previous one: `blend_steps` interpolated frames are written in quick
    succession, ending exactly on the new sample's own frame, so the texture
    flows from one state to the next instead of jump-cutting on every sample.
    `palette` controls the colors every frame is rendered with.

    Runs until `sampler.stream()` is exhausted (never, for the real sampler)
    or `should_continue()` returns False, whichever comes first. Each frame is
    written atomically: it is rendered to a temp file in the same directory
    and then moved into place, so readers never see a half-written SVG.
    """
    if sampler is None:
        sampler = MetricsSampler(interval=interval)

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = output_file.with_name(output_file.name + ".tmp")

    previous_metrics: Optional[Metrics] = None

    for metrics in sampler.stream():
        if not should_continue():
            return

        if previous_metrics is None:
            frames = [generate_frame(metrics, seed=seed, palette=palette)]
        else:
            frames = generate_blended_frames(previous_metrics, metrics, seed, blend_steps, palette)

        for svg in frames:
            tmp_file.write_text(svg)
            tmp_file.replace(output_file)

        previous_metrics = metrics
