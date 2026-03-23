from time import sleep
import traceback
import argparse
import signal
import sys
import os

pid_file="/run/zpui.pid"
backup_pid_file="/run/zpui_pid.pid"

service_file = "zpui.service"

def cli():
    parser = argparse.ArgumentParser(description='ZPUI commandline')

    parser.add_argument(
            '--pid',
            '-p',
            help=f'Direction to PID file (default: {pid_file}, backup: {backup_pid_file})',
            dest='pid',
            default=None)

    subparsers = parser.add_subparsers(help='ZPUI cli subcommand help', dest="command", required=True)

    # commands
    restart_p = subparsers.add_parser('restart', help='Restart system-wide ZPUI instance (using systemctl)')
    start_p = subparsers.add_parser('start', help='Start system-wide ZPUI instance (using systemctl)')
    stop_p = subparsers.add_parser('stop', help='Stop system-wide ZPUI instance (using systemctl)')
    log_p = subparsers.add_parser('log', help='Show logs from the system-wide ZPUI instance (using journalctl)')
    fg_p = subparsers.add_parser('fg', help='Bring system-wide ZPUI instance to foreground (after suspend)')
    threads_p = subparsers.add_parser('threads', help='Make system-wide ZPUI instance print current state of all its threads (into standard output)')
    rconsole_p = subparsers.add_parser('rc', help='Log into Python shell on a system-wide ZPUI instance')

    args = parser.parse_args()
    if not args.pid:
        try:
            with open(pid_file, 'r') as pid_file_f:
                pid = pid_file_f.read().strip()
        except:
            try:
                with open(backup_pid_file, 'r') as backup_pid_file_f:
                    pid = backup_pid_file_f.read().strip()
            except:
                print(f"Failed to read both PID files: {pid_file} and {backup_pid_file}!")
                traceback.print_exc()
                sys.exit(1)
    else:
        pid = args.pid
    pid = int(pid)
    command = args.command
    print(f"Command: {command}, PID: {repr(pid)}")
    # now seeing which command got called
    if command == "threads":
        os.kill(pid, signal.SIGUSR1)
    elif command == "fg":
        # working around a bug where an ongoing Enter press accidentally re-minimizes ZPUI
        sleep(1)
        os.kill(pid, signal.SIGCONT)
    elif command == "rc":
        try:
            from rfoo.utils import rconsole
        except:
            print("Rfoo not installed! After installing rfoo, you might need to restart ZPUI before it's picked up")
            print("Learn more at:")
            print("https://zpui.readthedocs.io/en/latest/hacking_ui.html#attaching-to-the-zpui-instance")
            sys.exit(2)
        else:
            os.kill(pid, signal.SIGUSR2) # sending signal to ZPUI
            sleep(0.1) # small delay just in case
            rconsole.interact(port=9377)
    elif command in ["start", "stop", "restart"]:
        print(f"Trying to run `systemctl {command} {service_file}`")
        os.system(f"systemctl {command} {service_file}")
    elif command == "log":
        print(f"Trying to run `journalctl -fu {service_file}`")
        os.system(f"journalctl -fu {service_file}")

if __name__ == "__main__":
    cli()
