"""Shared state and helpers for deploy steps."""

from utils import ssh_run, SSH_USER, SSH_PASS

state = {}

SSD_DEV = "/dev/sda1"
SSD_MOUNT = "/mnt/ssd"
DOCKER_DATA_ROOT = "/mnt/data/docker"
DAEMON_JSON = """{
  "data-root": "/mnt/data/docker",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "3"
  }
}"""


def _sudo(ip, cmd, timeout=300):
    return ssh_run(ip, f"echo '{SSH_PASS}' | sudo -S {cmd}", timeout=timeout)
