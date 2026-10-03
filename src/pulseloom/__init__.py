"""pulseloom: deterministic reaction-diffusion wallpaper generator."""

from .config import Config, load_config
from .daemon import run_loop
from .metrics import Metrics
from .generator import generate_blended_frames, generate_frame, generate_frame_sequence
from .render import DEFAULT_PALETTE, Palette
from .sampler import MetricsSampler

__all__ = [
    "Metrics",
    "generate_frame",
    "generate_blended_frames",
    "generate_frame_sequence",
    "MetricsSampler",
    "run_loop",
    "Palette",
    "DEFAULT_PALETTE",
    "Config",
    "load_config",
]
