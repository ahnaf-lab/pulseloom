# pulseloom

A background daemon that samples CPU, memory and disk activity and feeds
those numbers into a deterministic reaction-diffusion generator, continuously
producing a procedural wallpaper that visibly reacts to what the machine is
doing.

This milestone implements the core of that idea as a pure function: given a
metrics vector (cpu/memory/disk, each normalized to `[0.0, 1.0]`) and an
integer seed, `generate_frame` deterministically produces one Gray-Scott
reaction-diffusion frame as an SVG string. The same inputs always produce the
exact same output; the daemon that samples live system metrics and feeds them
into this function on a loop is a later milestone.

## Install

Requires Python 3.9+. No third-party dependencies are needed to run the
generator — only the standard library is used.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"   # installs pytest for running the test suite
```

## Usage

```python
from pulseloom import Metrics, generate_frame

metrics = Metrics(cpu=0.8, memory=0.3, disk=0.1)
svg = generate_frame(metrics, seed=42)

with open("frame.svg", "w") as f:
    f.write(svg)
```

Run the test suite:

```bash
pytest
```

## Status

This project is built autonomously, one milestone at a time, and each change
is gated on passing its automated test suite before being accepted.
