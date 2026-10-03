import pytest

from pulseloom.blend import blend_steps, interpolate_grids, interpolate_metrics
from pulseloom.metrics import Metrics


def test_interpolate_grids_midpoint():
    grid_a = [[0.0, 2.0], [4.0, 0.0]]
    grid_b = [[1.0, 0.0], [0.0, 1.0]]
    midpoint = interpolate_grids(grid_a, grid_b, 0.5)
    assert midpoint == [[0.5, 1.0], [2.0, 0.5]]


def test_interpolate_grids_endpoints_are_exact():
    grid_a = [[0.1, 0.2], [0.3, 0.4]]
    grid_b = [[0.9, 0.8], [0.7, 0.6]]
    assert interpolate_grids(grid_a, grid_b, 0.0) == grid_a
    assert interpolate_grids(grid_a, grid_b, 1.0) == grid_b


def test_interpolate_grids_rejects_mismatched_dimensions():
    with pytest.raises(ValueError):
        interpolate_grids([[0.0, 0.0]], [[0.0, 0.0, 0.0]], 0.5)


def test_interpolate_grids_rejects_out_of_range_t():
    with pytest.raises(ValueError):
        interpolate_grids([[0.0]], [[1.0]], 1.5)


def test_interpolate_metrics_midpoint():
    a = Metrics(cpu=0.0, memory=0.2, disk=1.0)
    b = Metrics(cpu=1.0, memory=0.8, disk=0.0)
    mid = interpolate_metrics(a, b, 0.5)
    assert mid.cpu == pytest.approx(0.5)
    assert mid.memory == pytest.approx(0.5)
    assert mid.disk == pytest.approx(0.5)


def test_interpolate_metrics_endpoints_are_exact():
    a = Metrics(cpu=0.1, memory=0.2, disk=0.3)
    b = Metrics(cpu=0.9, memory=0.8, disk=0.7)
    assert interpolate_metrics(a, b, 0.0) is a
    assert interpolate_metrics(a, b, 1.0) is b


def test_interpolate_metrics_rejects_out_of_range_t():
    a = Metrics(cpu=0.0, memory=0.0, disk=0.0)
    b = Metrics(cpu=1.0, memory=1.0, disk=1.0)
    with pytest.raises(ValueError):
        interpolate_metrics(a, b, -0.1)


def test_blend_steps_ends_exactly_on_one():
    steps = blend_steps(4)
    assert steps == [0.25, 0.5, 0.75, 1.0]


def test_blend_steps_rejects_non_positive_count():
    with pytest.raises(ValueError):
        blend_steps(0)
