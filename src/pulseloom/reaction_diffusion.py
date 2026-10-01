"""A pure, seeded Gray-Scott reaction-diffusion simulation.

Everything here is deterministic: given the same grid size, feed/kill
parameters, blob count and seed, `run` always returns the same grid of
concentration values.
"""

import random

DIFFUSION_A = 1.0
DIFFUSION_B = 0.5
TIME_STEP = 1.0


def _new_grid(size: int, fill: float) -> list:
    return [[fill for _ in range(size)] for _ in range(size)]


def _seed_blobs(size: int, blob_count: int, rng: random.Random) -> tuple:
    """Build the initial A/B grids with `blob_count` square perturbations of B."""
    grid_a = _new_grid(size, 1.0)
    grid_b = _new_grid(size, 0.0)

    for _ in range(blob_count):
        radius = max(1, size // 12)
        cx = rng.randint(0, size - 1)
        cy = rng.randint(0, size - 1)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                x = (cx + dx) % size
                y = (cy + dy) % size
                grid_a[y][x] = 0.5
                grid_b[y][x] = 0.25

    return grid_a, grid_b


def _laplacian(grid: list, x: int, y: int, size: int) -> float:
    center = grid[y][x]
    north = grid[(y - 1) % size][x]
    south = grid[(y + 1) % size][x]
    east = grid[y][(x + 1) % size]
    west = grid[y][(x - 1) % size]
    return north + south + east + west - 4.0 * center


def run(size: int, steps: int, feed: float, kill: float, blob_count: int, seed: int) -> list:
    """Run the simulation and return the final B-concentration grid.

    The returned grid is a list of `size` rows, each a list of `size`
    floats in roughly [0.0, 1.0].
    """
    rng = random.Random(seed)
    grid_a, grid_b = _seed_blobs(size, blob_count, rng)

    for _ in range(steps):
        next_a = _new_grid(size, 0.0)
        next_b = _new_grid(size, 0.0)
        for y in range(size):
            for x in range(size):
                a = grid_a[y][x]
                b = grid_b[y][x]
                reaction = a * b * b
                next_a[y][x] = a + (DIFFUSION_A * _laplacian(grid_a, x, y, size) - reaction + feed * (1.0 - a)) * TIME_STEP
                next_b[y][x] = b + (DIFFUSION_B * _laplacian(grid_b, x, y, size) + reaction - (kill + feed) * b) * TIME_STEP
        grid_a, grid_b = next_a, next_b

    return [[max(0.0, min(1.0, value)) for value in row] for row in grid_b]
