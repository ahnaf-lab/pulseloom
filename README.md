# pulseloom

A background daemon that samples CPU, memory and disk activity and feeds
those numbers into a deterministic reaction-diffusion generator, continuously
producing a procedural wallpaper that visibly reacts to what the machine is
doing.

The generator itself is a pure function: given a metrics vector
(cpu/memory/disk, each normalized to `[0.0, 1.0]`) and an integer seed,
`generate_frame` deterministically produces one Gray-Scott reaction-diffusion
frame as an SVG string. The same inputs always produce the exact same output.

`MetricsSampler` reads live CPU, memory and disk activity via `psutil` and
turns each reading into a `Metrics` vector, so the generator can be driven by
whatever the machine is actually doing. CPU and memory map onto psutil's own
percentages; disk activity has no OS-native percentage, so it is derived from
the read+write byte delta between two samples, normalized against an assumed
saturation throughput. The daemon that runs this sampler on a loop and writes
frames to disk continuously is a later milestone.

## Install

Requires Python 3.9+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"   # installs psutil and pytest
```

`psutil` is the one third-party dependency: reading CPU/memory/disk activity
in a way that works the same on Linux, macOS and Windows is exactly what it
is for, and reimplementing that per-platform by hand would be unreasonable.
Everything else uses only the standard library.

## Usage

```python
from pulseloom import Metrics, generate_frame, MetricsSampler

# Pure generation from an explicit metrics vector:
metrics = Metrics(cpu=0.8, memory=0.3, disk=0.1)
svg = generate_frame(metrics, seed=42)

with open("frame.svg", "w") as f:
    f.write(svg)

# Or sample live machine activity at a fixed interval:
sampler = MetricsSampler(interval=1.0)
for live_metrics in sampler.stream():
    svg = generate_frame(live_metrics, seed=42)
    # ... write svg somewhere, e.g. as the next wallpaper frame
    break  # stream() runs forever; this is just an example
```

Run the test suite:

```bash
pytest
```

## Status

This project is built autonomously, one milestone at a time, and each change
is gated on passing its automated test suite before being accepted.
