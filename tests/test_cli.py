import os
import subprocess
import sys
import threading
from pathlib import Path

from pulseloom import cli
from pulseloom.daemon import read_pid_file, write_pid_file


def test_build_parser_start_defaults():
    args = cli.build_parser().parse_args(["start"])
    assert args.command == "start"
    assert args.foreground is False
    assert args.interval > 0
    assert args.seed == 0


def test_build_parser_stop_and_status_commands():
    parser = cli.build_parser()
    assert parser.parse_args(["stop"]).command == "stop"
    assert parser.parse_args(["status"]).command == "status"


def test_cmd_status_not_running_without_pid_file(tmp_path, capsys):
    pid_file = tmp_path / "pulseloom.pid"

    code = cli.cmd_status(pid_file)

    assert code == 1
    assert "not running" in capsys.readouterr().out


def test_cmd_status_running_for_a_live_pid(tmp_path, capsys):
    pid_file = tmp_path / "pulseloom.pid"
    write_pid_file(pid_file, os.getpid())

    code = cli.cmd_status(pid_file)

    assert code == 0
    assert "running" in capsys.readouterr().out


def test_cmd_status_cleans_up_a_stale_pid_file(tmp_path):
    pid_file = tmp_path / "pulseloom.pid"
    dead_proc = subprocess.Popen([sys.executable, "-c", "pass"])
    dead_pid = dead_proc.pid
    dead_proc.wait()  # reap it, so it's not even a zombie anymore
    write_pid_file(pid_file, dead_pid)

    code = cli.cmd_status(pid_file)

    assert code == 1
    assert not pid_file.exists()


def test_cmd_stop_not_running_without_pid_file(tmp_path, capsys):
    pid_file = tmp_path / "pulseloom.pid"

    code = cli.cmd_stop(pid_file)

    assert code == 1
    assert "not running" in capsys.readouterr().err


def test_cmd_stop_terminates_a_running_process(tmp_path):
    pid_file = tmp_path / "pulseloom.pid"
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    write_pid_file(pid_file, proc.pid)

    # Reap it the moment it exits, in the background: this test is the
    # process's direct parent, so without a concurrent wait() it would sit
    # as a zombie (still visible to kill(pid, 0)) until cmd_stop times out.
    reaper = threading.Thread(target=proc.wait)
    reaper.start()

    code = cli.cmd_stop(pid_file, timeout=5.0)
    reaper.join(timeout=5)

    assert code == 0
    assert not pid_file.exists()
    assert proc.returncode != 0


def test_cmd_start_foreground_runs_the_loop_under_a_pid_file(tmp_path, monkeypatch):
    pid_file = tmp_path / "pulseloom.pid"
    output_file = tmp_path / "frame.svg"
    recorded = {}

    def fake_run_loop(output, interval, seed, blend_steps):
        recorded["output"] = Path(output)
        recorded["interval"] = interval
        recorded["seed"] = seed
        recorded["blend_steps"] = blend_steps
        recorded["pid_file_existed_during_run"] = pid_file.exists()

    monkeypatch.setattr(cli, "run_loop", fake_run_loop)

    args = cli.build_parser().parse_args(
        [
            "start", "--foreground",
            "--output", str(output_file),
            "--pid-file", str(pid_file),
            "--interval", "2",
            "--seed", "9",
        ]
    )

    code = cli.cmd_start(args, pid_file)

    assert code == 0
    assert recorded["output"] == output_file
    assert recorded["interval"] == 2.0
    assert recorded["seed"] == 9
    assert recorded["blend_steps"] == cli.DEFAULT_BLEND_STEPS
    assert recorded["pid_file_existed_during_run"] is True
    assert not pid_file.exists()  # cleaned up once the loop returns


def test_cmd_start_refuses_when_already_running(tmp_path, capsys):
    pid_file = tmp_path / "pulseloom.pid"
    write_pid_file(pid_file, os.getpid())

    args = cli.build_parser().parse_args(["start", "--foreground", "--pid-file", str(pid_file)])

    code = cli.cmd_start(args, pid_file)

    assert code == 1
    assert "already running" in capsys.readouterr().err
    assert read_pid_file(pid_file) == os.getpid()  # left untouched, it's genuinely running


def test_cmd_start_replaces_a_stale_pid_file(tmp_path, monkeypatch):
    pid_file = tmp_path / "pulseloom.pid"
    dead_proc = subprocess.Popen([sys.executable, "-c", "pass"])
    dead_pid = dead_proc.pid
    dead_proc.wait()
    write_pid_file(pid_file, dead_pid)

    monkeypatch.setattr(cli, "run_loop", lambda output, interval, seed, blend_steps: None)

    args = cli.build_parser().parse_args(["start", "--foreground", "--pid-file", str(pid_file)])
    code = cli.cmd_start(args, pid_file)

    assert code == 0
