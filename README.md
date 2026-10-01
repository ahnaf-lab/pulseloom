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
saturation throughput.

The `pulseloom` command wraps all of this into a small background daemon:
on a fixed interval it samples the machine, generates a frame and writes it
to disk, atomically, so whatever is reading the file never sees a half
written SVG. `start`/`stop`/`status` manage the daemon process through a pid
file, the same pattern most Unix daemons use.

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

Run the daemon: it samples the machine, generates a frame and writes it to
disk once per interval, forever, until stopped.

```bash
pulseloom start                      # forks into the background
pulseloom start --foreground         # or stays attached to this terminal
pulseloom status                     # "pulseloom is running (pid 1234)"
pulseloom stop                       # sends SIGTERM and waits for it to exit
```

By default frames are written to `~/.pulseloom/frame.svg` and the pid file
lives at `~/.pulseloom/pulseloom.pid`; both are configurable:

```bash
pulseloom start --output ~/wallpaper.svg --interval 2 --seed 1 \
  --pid-file ~/.pulseloom/pulseloom.pid
```

The library is also usable directly:

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
