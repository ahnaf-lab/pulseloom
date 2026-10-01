from pulseloom.reaction_diffusion import run


def test_run_is_deterministic_for_same_seed():
    kwargs = dict(size=16, steps=5, feed=0.03, kill=0.05, blob_count=2)
    first = run(seed=5, **kwargs)
    second = run(seed=5, **kwargs)
    assert first == second


def test_run_returns_correctly_shaped_grid():
    grid = run(size=16, steps=3, feed=0.03, kill=0.05, blob_count=1, seed=0)
    assert len(grid) == 16
    assert all(len(row) == 16 for row in grid)
    assert all(0.0 <= value <= 1.0 for row in grid for value in row)
