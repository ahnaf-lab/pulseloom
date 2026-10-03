import pytest

from pulseloom.render import DEFAULT_PALETTE, Palette, render_svg


def test_default_palette_matches_original_background():
    grid = [[0.0]]
    svg = render_svg(grid, cpu=0.0, memory=0.0, disk=0.0)
    assert 'fill="#05060a"' in svg


def test_render_svg_uses_custom_background():
    palette = Palette(background=(255, 255, 255))
    svg = render_svg([[0.0]], cpu=0.0, memory=0.0, disk=0.0, palette=palette)
    assert 'fill="#ffffff"' in svg


def test_render_svg_mixes_custom_base_colors():
    palette = Palette(cpu_color=(10, 0, 0), memory_color=(0, 20, 0), disk_color=(0, 0, 30))
    svg = render_svg([[1.0]], cpu=1.0, memory=1.0, disk=1.0, palette=palette)
    # intensity=1, bias=1 everywhere -> each channel renders at its full base value
    assert "rgb(10,20,30)" in svg


def test_palette_rejects_out_of_range_component():
    with pytest.raises(ValueError):
        Palette(cpu_color=(256, 0, 0))


def test_palette_rejects_non_tuple_color():
    with pytest.raises(ValueError):
        Palette(cpu_color=[255, 0, 0])


def test_default_palette_is_pure_rgb():
    assert DEFAULT_PALETTE.cpu_color == (255, 0, 0)
    assert DEFAULT_PALETTE.memory_color == (0, 255, 0)
    assert DEFAULT_PALETTE.disk_color == (0, 0, 255)
