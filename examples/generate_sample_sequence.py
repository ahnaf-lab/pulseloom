"""Generate an example frame sequence on disk, without needing a live machine.

Runs the pure `generate_frame_sequence` API over a handful of synthetic
metrics samples and writes the resulting SVG frames to `examples/output/`, so
you can see what a blended sequence looks like without running the daemon.
"""

from pathlib import Path

from pulseloom import Metrics, generate_frame_sequence

SAMPLE_SEQUENCE = [
    Metrics(cpu=0.05, memory=0.20, disk=0.00),  # idle
    Metrics(cpu=0.85, memory=0.35, disk=0.60),  # a build kicks off
    Metrics(cpu=0.40, memory=0.90, disk=0.10),  # memory pressure as it links
]

SEED = 42
STEPS_PER_GAP = 6


def main() -> None:
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(exist_ok=True)

    frames = generate_frame_sequence(SAMPLE_SEQUENCE, seed=SEED, steps_per_gap=STEPS_PER_GAP)
    for index, svg in enumerate(frames):
        (output_dir / f"frame-{index:04d}.svg").write_text(svg)

    print(f"wrote {len(frames)} frames to {output_dir}")


if __name__ == "__main__":
    main()
