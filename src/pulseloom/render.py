"""Render a reaction-diffusion concentration grid to an SVG string."""

from dataclasses import dataclass
from typing import Tuple

Color = Tuple[int, int, int]

CELL_PX = 8


def _validate_color(color: Color, name: str) -> None:
    if (
        not isinstance(color, tuple)
        or len(color) != 3
        or not all(isinstance(c, int) and 0 <= c <= 255 for c in color)
    ):
        raise ValueError(f"{name} must be an (r, g, b) tuple of ints in [0, 255], got {color!r}")


@dataclass(frozen=True)
class Palette:
    """The colors a frame is rendered with.

    `cpu_color`/`memory_color`/`disk_color` are base colors mixed in
    proportion to reaction-diffusion intensity and biased by how busy that
    resource is; `background` fills the empty space behind them. Defaults to
    pure red/green/blue on a near-black background, which is what earlier
    milestones hardcoded.
    """

    background: Color = (0x05, 0x06, 0x0A)
    cpu_color: Color = (255, 0, 0)
    memory_color: Color = (0, 255, 0)
    disk_color: Color = (0, 0, 255)

    def __post_init__(self) -> None:
        for name in ("background", "cpu_color", "memory_color", "disk_color"):
            _validate_color(getattr(self, name), name)


DEFAULT_PALETTE = Palette()


def _hex(color: Color) -> str:
    return "#{:02x}{:02x}{:02x}".format(*color)


def _mix_channel(
    intensity: float, biases: Tuple[float, float, float], colors: Tuple[Color, Color, Color], index: int
) -> int:
    value = sum(colors[i][index] * intensity * (0.3 + 0.7 * biases[i]) for i in range(3))
    return max(0, min(255, round(value)))


def render_svg(grid: list, cpu: float, memory: float, disk: float, palette: Palette = DEFAULT_PALETTE) -> str:
    """Render `grid` (rows of concentration floats in [0, 1]) as an SVG document.

    Colors are biased by the metrics so the same concentration pattern looks
    different depending on which resource is under load; `palette` controls
    which base colors (and background) that bias is mixed into. The default
    palette reproduces the original pure red/green/blue mapping.
    """
    size = len(grid)
    pixel_size = size * CELL_PX
    biases = (cpu, memory, disk)
    colors = (palette.cpu_color, palette.memory_color, palette.disk_color)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{pixel_size}" '
        f'height="{pixel_size}" viewBox="0 0 {pixel_size} {pixel_size}">',
        f'<rect width="{pixel_size}" height="{pixel_size}" fill="{_hex(palette.background)}"/>',
    ]

    for y, row in enumerate(grid):
        for x, intensity in enumerate(row):
            if intensity <= 0.02:
                continue
            r = _mix_channel(intensity, biases, colors, 0)
            g = _mix_channel(intensity, biases, colors, 1)
            b = _mix_channel(intensity, biases, colors, 2)
            parts.append(
                f'<rect x="{x * CELL_PX}" y="{y * CELL_PX}" '
                f'width="{CELL_PX}" height="{CELL_PX}" fill="rgb({r},{g},{b})"/>'
            )

    parts.append("</svg>")
    return "".join(parts)
