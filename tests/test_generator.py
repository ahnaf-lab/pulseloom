import pytest

from pulseloom import Metrics, generate_frame


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


def test_metrics_reject_out_of_range_values():
    with pytest.raises(ValueError):
        Metrics(cpu=1.5, memory=0.0, disk=0.0)


def test_metrics_reject_non_numeric_values():
    with pytest.raises(TypeError):
        Metrics(cpu="high", memory=0.0, disk=0.0)
