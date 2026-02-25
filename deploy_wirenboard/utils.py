"""Utility functions for deploy_wirenboard menu."""

import socket
import struct
import fcntl
import subprocess
import concurrent.futures

# Default SSH credentials
SSH_USER = "pi"
SSH_PASS = "Kirilltemp14"


def get_local_ip(iface="en0"):
    """Get local IP address for a given interface."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(
            fcntl.ioctl(
                s.fileno(),
                0xC0206921,  # SIOCGIFADDR on macOS
                struct.pack("256s", iface.encode("utf-8")),
            )[20:24]
        )
    except OSError:
        pass

    # Fallback: connect to external and read local addr
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


def check_port(ip, port=22, timeout=0.3):
    """Check if a TCP port is open. Returns (ip, banner) or None."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((ip, port))
        # Try to grab SSH banner
        try:
            s.settimeout(0.5)
            banner = s.recv(256).decode("utf-8", errors="replace").strip()
        except (socket.timeout, OSError):
            banner = ""
        s.close()
        return (ip, banner)
    except (socket.timeout, ConnectionRefusedError, OSError):
        return None


def scan_subnet_ssh(local_ip=None, port=22, timeout=0.3):
    """Scan /24 subnet for hosts with open SSH port.

    Returns list of (ip, banner) sorted by last octet.
    """
    if local_ip is None:
        local_ip = get_local_ip()
    if local_ip is None:
        return []

    prefix = ".".join(local_ip.split(".")[:3])
    targets = [f"{prefix}.{i}" for i in range(1, 255)]

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=128) as pool:
        futures = {pool.submit(check_port, ip, port, timeout): ip for ip in targets}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result is not None:
                results.append(result)

    # Sort by last octet
    results.sort(key=lambda r: int(r[0].split(".")[-1]))
    return results


def check_ssh(ip, user=SSH_USER, password=SSH_PASS, timeout=5):
    """Try SSH login with password only. Returns (ok, hostname)."""
    ssh_opts = [
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=3",
        "-o", "PubkeyAuthentication=no",
    ]
    try:
        proc = subprocess.run(
            ["sshpass", "-p", password, "ssh", *ssh_opts,
             f"{user}@{ip}", "hostname"],
            capture_output=True, text=True, timeout=timeout,
        )
        if proc.returncode == 0:
            return True, proc.stdout.strip()
        else:
            return False, proc.stderr.strip().split("\n")[-1]
    except FileNotFoundError:
        return False, "sshpass not installed (brew install sshpass)"
    except subprocess.TimeoutExpired:
        return False, "timeout"


def ssh_run(ip, cmd, user=SSH_USER, password=SSH_PASS, timeout=300):
    """Run a command on remote host via SSH. Returns (returncode, stdout_lines)."""
    ssh_opts = [
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=5",
        "-o", "PubkeyAuthentication=no",
    ]
    try:
        proc = subprocess.run(
            ["sshpass", "-p", password, "ssh", *ssh_opts,
             f"{user}@{ip}", cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        lines = proc.stdout.splitlines() + proc.stderr.splitlines()
        return proc.returncode, lines
    except FileNotFoundError:
        return -1, ["sshpass not installed (brew install sshpass)"]
    except subprocess.TimeoutExpired:
        return -1, ["timeout"]
