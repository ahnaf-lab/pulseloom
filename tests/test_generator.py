import pytest

from pulseloom import Metrics, generate_frame
from pulseloom.generator import generate_blended_frames, generate_frame_sequence
from pulseloom.render import Palette


def test_same_metrics_and_seed_are_deterministic():
    metrics = Metrics(cpu=0.7, memory=0.3, disk=0.5)
    first = generate_frame(metrics, seed=42)
    second = generate_frame(metrics, seed=42)
    assert first == second


def test_different_seed_changes_output():
    metrics = Metrics(cpu=0.7, memory=0.3, disk=0.5)
    a = generate_frame(metrics, seed=1)
    b = generate_frame(metrics, seed=2)
    assert a != b


def test_different_metrics_change_output():
    seed = 7
    low = generate_frame(Metrics(cpu=0.0, memory=0.0, disk=0.0), seed=seed)
    high = generate_frame(Metrics(cpu=1.0, memory=1.0, disk=1.0), seed=seed)
    assert low != high


def test_output_is_well_formed_svg_with_expected_size():
    metrics = Metrics(cpu=0.2, memory=0.4, disk=0.6)
    svg = generate_frame(metrics, seed=99)
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    # grid is 48 cells at 8px each
    assert 'width="384"' in svg
    assert 'height="384"' in svg


def test_custom_palette_changes_output_but_stays_deterministic():
    metrics = Metrics(cpu=0.7, memory=0.3, disk=0.5)
    palette = Palette(background=(0, 0, 0), cpu_color=(10, 20, 30), memory_color=(40, 50, 60), disk_color=(70, 80, 90))

    default_svg = generate_frame(metrics, seed=42)
    custom_svg = generate_frame(metrics, seed=42, palette=palette)
    custom_svg_again = generate_frame(metrics, seed=42, palette=palette)

    assert custom_svg != default_svg
    assert custom_svg == custom_svg_again
    assert "#000000" in custom_svg


def test_metrics_reject_out_of_range_values():
    with pytest.raises(ValueError):
        Metrics(cpu=1.5, memory=0.0, disk=0.0)


def test_metrics_reject_non_numeric_values():
    with pytest.raises(TypeError):
        Metrics(cpu="high", memory=0.0, disk=0.0)


# A fixed sequence of samples, reused across the blending tests below so the
# whole pipeline is exercised against the same deterministic inputs.
SAMPLE_SEQUENCE = [
    Metrics(cpu=0.1, memory=0.2, disk=0.0),
    Metrics(cpu=0.8, memory=0.3, disk=0.4),
    Metrics(cpu=0.5, memory=0.9, disk=0.6),
]


def test_generate_blended_frames_is_deterministic():
    a, b = SAMPLE_SEQUENCE[0], SAMPLE_SEQUENCE[1]
    first = generate_blended_frames(a, b, seed=11, steps_per_gap=5)
    second = generate_blended_frames(a, b, seed=11, steps_per_gap=5)
    assert first == second


def test_generate_blended_frames_count_and_ending():
    a, b = SAMPLE_SEQUENCE[0], SAMPLE_SEQUENCE[1]
    frames = generate_blended_frames(a, b, seed=11, steps_per_gap=5)
    assert len(frames) == 5
    assert frames[-1] == generate_frame(b, seed=11)


def test_generate_blended_frames_ease_through_distinct_intermediate_states():
    a, b = SAMPLE_SEQUENCE[0], SAMPLE_SEQUENCE[1]
    frames = generate_blended_frames(a, b, seed=11, steps_per_gap=4)
    # Every eased step should look different from the one before it, since
    # the underlying grids and color bias are both still moving toward b.
    assert len(set(frames)) == len(frames)


def test_generate_frame_sequence_on_fixed_sample_sequence():
    seed = 11
    steps_per_gap = 4
    frames = generate_frame_sequence(SAMPLE_SEQUENCE, seed=seed, steps_per_gap=steps_per_gap)

    expected_count = 1 + (len(SAMPLE_SEQUENCE) - 1) * steps_per_gap
    assert len(frames) == expected_count

    # The sequence starts exactly on the first sample's own frame...
    assert frames[0] == generate_frame(SAMPLE_SEQUENCE[0], seed=seed)
    # ...and lands exactly on each later sample's own frame at the seams.
    assert frames[steps_per_gap] == generate_frame(SAMPLE_SEQUENCE[1], seed=seed)
    assert frames[2 * steps_per_gap] == generate_frame(SAMPLE_SEQUENCE[2], seed=seed)


def test_generate_frame_sequence_is_deterministic():
    first = generate_frame_sequence(SAMPLE_SEQUENCE, seed=3, steps_per_gap=3)
    second = generate_frame_sequence(SAMPLE_SEQUENCE, seed=3, steps_per_gap=3)
    assert first == second


def test_generate_frame_sequence_empty_input():
    assert generate_frame_sequence([], seed=1) == []


def test_generate_frame_sequence_single_sample():
    frames = generate_frame_sequence([SAMPLE_SEQUENCE[0]], seed=1)
    assert frames == [generate_frame(SAMPLE_SEQUENCE[0], seed=1)]
