"""The pure generator: (metrics, seed) -> one reaction-diffusion frame as SVG."""

from .blend import blend_steps, interpolate_grids, interpolate_metrics
from .metrics import Metrics
from .reaction_diffusion import run as run_simulation
from .render import render_svg

GRID_SIZE = 48
STEPS = 30

FEED_BASE = 0.014
FEED_RANGE = 0.060
KILL_BASE = 0.040
KILL_RANGE = 0.020
MAX_BLOBS = 6

DEFAULT_BLEND_STEPS = 8


def _compute_grid(metrics: Metrics, seed: int) -> list:
    if not isinstance(seed, int):
        raise TypeError(f"seed must be an int, got {type(seed).__name__}")

    feed = FEED_BASE + FEED_RANGE * metrics.cpu
    kill = KILL_BASE + KILL_RANGE * metrics.memory
    blob_count = 1 + round(metrics.disk * (MAX_BLOBS - 1))

    return run_simulation(
        size=GRID_SIZE,
        steps=STEPS,
        feed=feed,
        kill=kill,
        blob_count=blob_count,
        seed=seed,
    )


def generate_frame(metrics: Metrics, seed: int) -> str:
    """Deterministically turn a metrics vector and seed into one SVG frame.

    Calling this twice with equal `metrics` and `seed` always produces the
    exact same SVG string. Different metrics or a different seed produce a
    different frame.
    """
    grid = _compute_grid(metrics, seed)
    return render_svg(grid, metrics.cpu, metrics.memory, metrics.disk)


def generate_blended_frames(
    metrics_a: Metrics, metrics_b: Metrics, seed: int, steps_per_gap: int = DEFAULT_BLEND_STEPS
) -> list:
    """Render `steps_per_gap` SVG frames easing from `metrics_a`'s state to `metrics_b`'s.

    Each sample's own reaction-diffusion grid is computed independently (the
    same way `generate_frame` does), then the two grids and their metrics are
    linearly interpolated at `steps_per_gap` evenly spaced points. The last
    returned frame lands exactly on `generate_frame(metrics_b, seed)`, so
    chaining these across a metrics sequence produces a smooth transition
    instead of a jump cut.
    """
    grid_a = _compute_grid(metrics_a, seed)
    grid_b = _compute_grid(metrics_b, seed)

    frames = []
    for t in blend_steps(steps_per_gap):
        grid = interpolate_grids(grid_a, grid_b, t)
        metrics = interpolate_metrics(metrics_a, metrics_b, t)
        frames.append(render_svg(grid, metrics.cpu, metrics.memory, metrics.disk))
    return frames


def generate_frame_sequence(metrics_sequence: list, seed: int, steps_per_gap: int = DEFAULT_BLEND_STEPS) -> list:
    """Turn a fixed sequence of metrics samples into a smoothed sequence of SVG frames.

    The first returned frame corresponds exactly to `metrics_sequence[0]`.
    Between each subsequent pair of samples, `steps_per_gap` frames are
    inserted that ease from the previous sample's grid to the next one's,
    with the last frame of each group landing exactly on the next sample's
    own frame.
    """
    if not metrics_sequence:
        return []

    frames = [generate_frame(metrics_sequence[0], seed)]
    for metrics_a, metrics_b in zip(metrics_sequence, metrics_sequence[1:]):
        frames.extend(generate_blended_frames(metrics_a, metrics_b, seed, steps_per_gap))
    return frames
