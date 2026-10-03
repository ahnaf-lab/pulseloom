"""Load pulseloom's optional config file: frame rate, output path and palette.

Precedence is CLI flags first, then the config file, then hardcoded defaults.
`load_config` never raises for a missing file or a missing section/key within
it, so callers can call it unconditionally and always get a usable `Config`
back, even when `path` points nowhere.

The file is plain INI, read with the standard library's `configparser`:

    [pulseloom]
    interval = 2.0
    seed = 1
    output = ~/wallpaper.svg
    pid_file = ~/.pulseloom/pulseloom.pid
    blend_steps = 8

    [palette]
    background = #05060a
    cpu_color = #ff2d55
    memory_color = #34c759
    disk_color = #0a84ff
"""

import configparser
from pathlib import Path
from typing import NamedTuple, Union

from .daemon import DEFAULT_OUTPUT_FILE, DEFAULT_PID_FILE, DEFAULT_SEED, DEFAULT_STATE_DIR
from .generator import DEFAULT_BLEND_STEPS
from .render import Color, DEFAULT_PALETTE, Palette
from .sampler import DEFAULT_INTERVAL

DEFAULT_CONFIG_FILE = DEFAULT_STATE_DIR / "config.ini"

PathLike = Union[str, Path]


class Config(NamedTuple):
    interval: float
    seed: int
    output: Path
    pid_file: Path
    blend_steps: int
    palette: Palette


def _parse_color(value: str, field: str) -> Color:
    text = value.strip()
    if len(text) == 7 and text.startswith("#"):
        try:
            return (int(text[1:3], 16), int(text[3:5], 16), int(text[5:7], 16))
        except ValueError:
            pass
    raise ValueError(f"{field} must be a '#rrggbb' hex color, got {value!r}")


def load_config(path: PathLike) -> Config:
    """Read the INI file at `path` and return a `Config`.

    A missing file, a missing section, or a missing key within a present
    section all fall back to the corresponding hardcoded default.
    """
    parser = configparser.ConfigParser()
    path = Path(path)
    if path.exists():
        parser.read(path)

    general = parser["pulseloom"] if parser.has_section("pulseloom") else {}
    colors = parser["palette"] if parser.has_section("palette") else {}

    def _color(key: str, default: Color) -> Color:
        value = colors.get(key)
        return _parse_color(value, key) if value is not None else default

    palette = Palette(
        background=_color("background", DEFAULT_PALETTE.background),
        cpu_color=_color("cpu_color", DEFAULT_PALETTE.cpu_color),
        memory_color=_color("memory_color", DEFAULT_PALETTE.memory_color),
        disk_color=_color("disk_color", DEFAULT_PALETTE.disk_color),
    )

    return Config(
        interval=float(general.get("interval", DEFAULT_INTERVAL)),
        seed=int(general.get("seed", DEFAULT_SEED)),
        output=Path(general.get("output", DEFAULT_OUTPUT_FILE)).expanduser(),
        pid_file=Path(general.get("pid_file", DEFAULT_PID_FILE)).expanduser(),
        blend_steps=int(general.get("blend_steps", DEFAULT_BLEND_STEPS)),
        palette=palette,
    )
