"""The pure generator: (metrics, seed) -> one reaction-diffusion frame as SVG."""

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


def generate_frame(metrics: Metrics, seed: int) -> str:
    """Deterministically turn a metrics vector and seed into one SVG frame.

    Calling this twice with equal `metrics` and `seed` always produces the
    exact same SVG string. Different metrics or a different seed produce a
    different frame.
    """
    if not isinstance(seed, int):
        raise TypeError(f"seed must be an int, got {type(seed).__name__}")

    feed = FEED_BASE + FEED_RANGE * metrics.cpu
    kill = KILL_BASE + KILL_RANGE * metrics.memory
    blob_count = 1 + round(metrics.disk * (MAX_BLOBS - 1))

    grid = run_simulation(
        size=GRID_SIZE,
        steps=STEPS,
        feed=feed,
        kill=kill,
        blob_count=blob_count,
        seed=seed,
    )

    return render_svg(grid, metrics.cpu, metrics.memory, metrics.disk)
