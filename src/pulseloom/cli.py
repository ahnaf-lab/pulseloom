"""`pulseloom start|stop|status`: run the daemon loop as a background process."""

import argparse
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

from .config import DEFAULT_CONFIG_FILE, load_config
from .daemon import (
    DEFAULT_BLEND_STEPS,
    DEFAULT_OUTPUT_FILE,
    DEFAULT_PID_FILE,
    DEFAULT_SEED,
    is_process_alive,
    read_pid_file,
    remove_pid_file,
    run_loop,
    write_pid_file,
)
from .sampler import DEFAULT_INTERVAL

DEFAULT_STOP_TIMEOUT = 5.0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_FILE),
        help=f"path to an INI config file for frame rate/output/palette (default: {DEFAULT_CONFIG_FILE})",
    )
    common.add_argument(
        "--pid-file",
        default=None,
        help=f"path to the daemon's pid file (default: from config file, else {DEFAULT_PID_FILE})",
    )

    parser = argparse.ArgumentParser(
        prog="pulseloom",
        description="Sample machine activity and write it out as a procedural SVG wallpaper.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", parents=[common], help="start the daemon")
    start.add_argument(
        "--interval", type=float, default=None,
        help=f"seconds between samples (default: from config file, else {DEFAULT_INTERVAL})",
    )
    start.add_argument(
        "--seed", type=int, default=None,
        help=f"generator seed (default: from config file, else {DEFAULT_SEED})",
    )
    start.add_argument(
        "--output", default=None,
        help=f"where to write the frame (default: from config file, else {DEFAULT_OUTPUT_FILE})",
    )
    start.add_argument(
        "--blend-steps", type=int, default=None,
        help=f"frames eased between consecutive samples (default: from config file, else {DEFAULT_BLEND_STEPS})",
    )
    start.add_argument(
        "--foreground", action="store_true",
        help="run in this process instead of forking into the background",
    )

    sub.add_parser("stop", parents=[common], help="stop the daemon")
    sub.add_parser("status", parents=[common], help="report whether the daemon is running")

    return parser


def cmd_start(args: argparse.Namespace, pid_file: Path) -> int:
    config = load_config(args.config)
    output_file = Path(args.output) if args.output is not None else config.output
    interval = args.interval if args.interval is not None else config.interval
    seed = args.seed if args.seed is not None else config.seed
    blend_steps = args.blend_steps if args.blend_steps is not None else config.blend_steps

    existing_pid = read_pid_file(pid_file)
    if existing_pid is not None and is_process_alive(existing_pid):
        print(f"pulseloom is already running (pid {existing_pid})", file=sys.stderr)
        return 1
    if existing_pid is not None:
        remove_pid_file(pid_file)

    if args.foreground:
        write_pid_file(pid_file, os.getpid())
        try:
            run_loop(output_file, interval=interval, seed=seed, blend_steps=blend_steps, palette=config.palette)
        finally:
            remove_pid_file(pid_file)
        return 0

    if not hasattr(os, "fork"):
        print("background mode needs a POSIX system; rerun with --foreground", file=sys.stderr)
        return 1

    pid = os.fork()
    if pid > 0:
        write_pid_file(pid_file, pid)
        print(f"pulseloom started (pid {pid}), writing frames to {output_file}")
        return 0

    # Child: detach from the parent's session and become the daemon.
    os.setsid()
    try:
        run_loop(output_file, interval=interval, seed=seed, blend_steps=blend_steps, palette=config.palette)
    finally:
        remove_pid_file(pid_file)
    os._exit(0)


def cmd_stop(pid_file: Path, timeout: float = DEFAULT_STOP_TIMEOUT) -> int:
    pid = read_pid_file(pid_file)
    if pid is None or not is_process_alive(pid):
        print("pulseloom is not running", file=sys.stderr)
        remove_pid_file(pid_file)
        return 1

    os.kill(pid, signal.SIGTERM)

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not is_process_alive(pid):
            break
        time.sleep(0.1)
    else:
        print(f"pulseloom (pid {pid}) did not stop within {timeout}s", file=sys.stderr)
        return 1

    remove_pid_file(pid_file)
    print(f"pulseloom stopped (pid {pid})")
    return 0


def cmd_status(pid_file: Path) -> int:
    pid = read_pid_file(pid_file)
    if pid is None:
        print("pulseloom is not running")
        return 1
    if is_process_alive(pid):
        print(f"pulseloom is running (pid {pid})")
        return 0
    remove_pid_file(pid_file)
    print("pulseloom is not running (stale pid file removed)")
    return 1


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    pid_file = Path(args.pid_file) if args.pid_file is not None else load_config(args.config).pid_file

    if args.command == "start":
        return cmd_start(args, pid_file)
    if args.command == "stop":
        return cmd_stop(pid_file)
    if args.command == "status":
        return cmd_status(pid_file)

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
