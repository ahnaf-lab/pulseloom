"""Render a reaction-diffusion concentration grid to an SVG string."""

CELL_PX = 8


def _channel(intensity: float, bias: float) -> int:
    value = 255.0 * intensity * (0.3 + 0.7 * bias)
    return max(0, min(255, round(value)))


def render_svg(grid: list, cpu: float, memory: float, disk: float) -> str:
    """Render `grid` (rows of concentration floats in [0, 1]) as an SVG document.

    Colors are biased by the metrics so the same concentration pattern looks
    different depending on which resource is under load.
    """
    size = len(grid)
    pixel_size = size * CELL_PX

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{pixel_size}" '
        f'height="{pixel_size}" viewBox="0 0 {pixel_size} {pixel_size}">',
        f'<rect width="{pixel_size}" height="{pixel_size}" fill="#05060a"/>',
    ]

    for y, row in enumerate(grid):
        for x, intensity in enumerate(row):
            if intensity <= 0.02:
                continue
            r = _channel(intensity, cpu)
            g = _channel(intensity, memory)
            b = _channel(intensity, disk)
            parts.append(
                f'<rect x="{x * CELL_PX}" y="{y * CELL_PX}" '
                f'width="{CELL_PX}" height="{CELL_PX}" fill="rgb({r},{g},{b})"/>'
            )

    parts.append("</svg>")
    return "".join(parts)
