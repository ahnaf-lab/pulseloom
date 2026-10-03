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

Jumping straight from one sample's texture to the next tends to look like a
jump cut, since each sample's reaction-diffusion grid is computed from
scratch. To smooth that out, every sample after the first is eased into:
the daemon linearly interpolates between the previous sample's grid (and
metrics, so the color bias eases too) and the new one, writing several
in-between frames in quick succession before settling on the new sample's
own frame. `generate_frame_sequence` exposes the same blending as a pure
function over a fixed list of metrics samples, which is how it's tested.

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
lives at `~/.pulseloom/pulseloom.pid`; both are configurable on the command
line:

```bash
pulseloom start --output ~/wallpaper.svg --interval 2 --seed 1 \
  --blend-steps 8 --pid-file ~/.pulseloom/pulseloom.pid
```

`--blend-steps` controls how many eased frames are written between each pair
of samples; higher means a smoother, more gradual transition.

### Config file

The same settings can live in an INI config file instead, so you don't have
to repeat flags on every `start`. By default pulseloom reads
`~/.pulseloom/config.ini` if it exists; point it elsewhere with `--config`.
A CLI flag always overrides the matching config value, which in turn
overrides the hardcoded default:

```ini
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
```

`[palette]` controls the colors a frame is rendered with: `cpu_color`,
`memory_color` and `disk_color` are base colors mixed in proportion to
reaction-diffusion intensity and brightened the busier that resource is;
`background` fills the empty space behind them. Every color is a `#rrggbb`
hex triplet. Leaving `[palette]` out, or any key within it, falls back to the
default palette (pure red/green/blue on a near-black background) field by
field.

The library is also usable directly:

```python
from pulseloom import Metrics, generate_frame, generate_frame_sequence, MetricsSampler

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

# Or turn a fixed sequence of samples into a smoothly blended frame sequence:
samples = [Metrics(cpu=0.1, memory=0.2, disk=0.0), Metrics(cpu=0.8, memory=0.3, disk=0.4)]
frames = generate_frame_sequence(samples, seed=42, steps_per_gap=8)
```

### Example frame sequence

`examples/generate_sample_sequence.py` runs `generate_frame_sequence` over a
fixed, synthetic metrics sequence (idle, then a CPU-heavy build, then a
memory-heavy link step) and writes the resulting frames to
`examples/output/`, so you can see what a blended sequence looks like without
a live machine or the daemon running:

```bash
python examples/generate_sample_sequence.py
# wrote 13 frames to .../examples/output
```

That command produces `frame-0000.svg` through `frame-0012.svg`: one frame
for the first sample, then 6 eased frames into each of the next two samples
(`1 + 2 * 6 = 13`). Open any of them in a browser or image viewer — `frame-0000.svg`
is the idle frame, `frame-0006.svg` lands exactly on the CPU-heavy sample, and
`frame-0012.svg` lands exactly on the memory-heavy one, with the frames
between each pair easing smoothly from one texture and color bias to the
next.

Run the test suite:

```bash
pytest
```

## Status

This project is built autonomously, one milestone at a time, and each change
is gated on passing its automated test suite before being accepted.
