"""Smoothly interpolate between consecutive reaction-diffusion frames.

Each sampled metrics reading produces its own reaction-diffusion grid, but
jumping straight from one grid to the next on every sample makes the
wallpaper cut between unrelated-looking textures. These helpers insert
linearly-interpolated steps between consecutive grids (and their matching
metrics, so the color bias eases too), so the texture visibly flows from one
state to the next instead of jumping.
"""

from .metrics import Metrics


def interpolate_grids(grid_a: list, grid_b: list, t: float) -> list:
    """Linearly interpolate two equally-sized concentration grids at `t`.

    t=0.0 returns grid_a's values, t=1.0 returns grid_b's values, and values
    in between blend each cell linearly. The endpoints are returned as exact
    copies (not computed through the lerp formula) so chaining interpolation
    across a sequence reproduces the original grids bit-for-bit at the seams.
    """
    if not 0.0 <= t <= 1.0:
        raise ValueError(f"t must be within [0.0, 1.0], got {t}")
    if len(grid_a) != len(grid_b) or any(len(ra) != len(rb) for ra, rb in zip(grid_a, grid_b)):
        raise ValueError("grids must have matching dimensions")

    if t == 0.0:
        return [row[:] for row in grid_a]
    if t == 1.0:
        return [row[:] for row in grid_b]

    return [
        [a + (b - a) * t for a, b in zip(row_a, row_b)]
        for row_a, row_b in zip(grid_a, grid_b)
    ]


def interpolate_metrics(metrics_a: Metrics, metrics_b: Metrics, t: float) -> Metrics:
    """Linearly interpolate two Metrics vectors at `t`, same semantics as `interpolate_grids`."""
    if not 0.0 <= t <= 1.0:
        raise ValueError(f"t must be within [0.0, 1.0], got {t}")

    if t == 0.0:
        return metrics_a
    if t == 1.0:
        return metrics_b

    return Metrics(
        cpu=metrics_a.cpu + (metrics_b.cpu - metrics_a.cpu) * t,
        memory=metrics_a.memory + (metrics_b.memory - metrics_a.memory) * t,
        disk=metrics_a.disk + (metrics_b.disk - metrics_a.disk) * t,
    )


def blend_steps(steps_per_gap: int) -> list:
    """Return the `t` values used to ease across one gap: steps_per_gap of them, ending at 1.0."""
    if steps_per_gap < 1:
        raise ValueError(f"steps_per_gap must be >= 1, got {steps_per_gap}")
    return [step / steps_per_gap for step in range(1, steps_per_gap + 1)]
