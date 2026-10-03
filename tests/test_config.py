import pytest

from pulseloom.config import load_config
from pulseloom.render import DEFAULT_PALETTE, Palette


def test_load_config_defaults_when_file_is_missing(tmp_path):
    config = load_config(tmp_path / "does-not-exist.ini")

    assert config.seed == 0
    assert config.blend_steps == 8
    assert config.palette == DEFAULT_PALETTE


def test_load_config_reads_general_section(tmp_path):
    config_file = tmp_path / "config.ini"
    config_file.write_text(
        "[pulseloom]\n"
        "interval = 2.5\n"
        "seed = 7\n"
        "output = out.svg\n"
        "pid_file = out.pid\n"
        "blend_steps = 12\n"
    )

    config = load_config(config_file)

    assert config.interval == 2.5
    assert config.seed == 7
    assert config.output.name == "out.svg"
    assert config.pid_file.name == "out.pid"
    assert config.blend_steps == 12


def test_load_config_reads_palette_section(tmp_path):
    config_file = tmp_path / "config.ini"
    config_file.write_text(
        "[palette]\n"
        "background = #000000\n"
        "cpu_color = #ff2d55\n"
        "memory_color = #34c759\n"
        "disk_color = #0a84ff\n"
    )

    config = load_config(config_file)

    assert config.palette == Palette(
        background=(0, 0, 0),
        cpu_color=(0xFF, 0x2D, 0x55),
        memory_color=(0x34, 0xC7, 0x59),
        disk_color=(0x0A, 0x84, 0xFF),
    )


def test_load_config_partial_palette_falls_back_per_field(tmp_path):
    config_file = tmp_path / "config.ini"
    config_file.write_text("[palette]\ncpu_color = #112233\n")

    config = load_config(config_file)

    assert config.palette.cpu_color == (0x11, 0x22, 0x33)
    assert config.palette.memory_color == DEFAULT_PALETTE.memory_color
    assert config.palette.disk_color == DEFAULT_PALETTE.disk_color
    assert config.palette.background == DEFAULT_PALETTE.background


def test_load_config_rejects_malformed_color(tmp_path):
    config_file = tmp_path / "config.ini"
    config_file.write_text("[palette]\ncpu_color = not-a-color\n")

    with pytest.raises(ValueError):
        load_config(config_file)


def test_load_config_ignores_unrelated_sections(tmp_path):
    config_file = tmp_path / "config.ini"
    config_file.write_text("[unrelated]\nkey = value\n")

    config = load_config(config_file)

    assert config.palette == DEFAULT_PALETTE
    assert config.seed == 0
