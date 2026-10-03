"""`pulseloom start|stop|status`: run the daemon loop as a background process."""

import argparse
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

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
        "--pid-file",
        default=str(DEFAULT_PID_FILE),
        help=f"path to the daemon's pid file (default: {DEFAULT_PID_FILE})",
    )

    parser = argparse.ArgumentParser(
        prog="pulseloom",
        description="Sample machine activity and write it out as a procedural SVG wallpaper.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", parents=[common], help="start the daemon")
    start.add_argument(
        "--interval", type=float, default=DEFAULT_INTERVAL,
        help=f"seconds between samples (default: {DEFAULT_INTERVAL})",
    )
    start.add_argument("--seed", type=int, default=DEFAULT_SEED, help="generator seed")
    start.add_argument(
        "--output", default=str(DEFAULT_OUTPUT_FILE),
        help=f"where to write the frame (default: {DEFAULT_OUTPUT_FILE})",
    )
    start.add_argument(
        "--blend-steps", type=int, default=DEFAULT_BLEND_STEPS,
        help=f"frames eased between consecutive samples (default: {DEFAULT_BLEND_STEPS})",
    )
    start.add_argument(
        "--foreground", action="store_true",
        help="run in this process instead of forking into the background",
    )

    sub.add_parser("stop", parents=[common], help="stop the daemon")
    sub.add_parser("status", parents=[common], help="report whether the daemon is running")

    return parser


def cmd_start(args: argparse.Namespace, pid_file: Path) -> int:
    output_file = Path(args.output)

    existing_pid = read_pid_file(pid_file)
    if existing_pid is not None and is_process_alive(existing_pid):
        print(f"pulseloom is already running (pid {existing_pid})", file=sys.stderr)
        return 1
    if existing_pid is not None:
        remove_pid_file(pid_file)

    if args.foreground:
        write_pid_file(pid_file, os.getpid())
        try:
            run_loop(output_file, interval=args.interval, seed=args.seed, blend_steps=args.blend_steps)
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
        run_loop(output_file, interval=args.interval, seed=args.seed, blend_steps=args.blend_steps)
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
    pid_file = Path(args.pid_file)

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
