LABEL = "Install Docker"

from utils import ssh_run, SSH_USER, SSH_PASS
from steps.common import state, _sudo, DOCKER_DATA_ROOT, DAEMON_JSON


def run(log):
    ip = state.get("target_ip")
    if not ip:
        log("No target selected")
        return False

    rc, out = ssh_run(ip, "docker --version")
    if rc == 0:
        log("Removing old Docker...")
        _sudo(ip, "systemctl stop docker docker.socket 2>/dev/null || true")
        _sudo(ip, "apt-get purge -y docker-ce docker-ce-cli "
              "docker-buildx-plugin docker-compose-plugin "
              "docker-ce-rootless-extras docker-model-plugin "
              "containerd.io 2>&1 || true", timeout=120)
        _sudo(ip, f"rm -rf /var/lib/docker /var/lib/containerd {DOCKER_DATA_ROOT}")
        _sudo(ip, "apt-get autoremove -y 2>&1 || true", timeout=60)

    log("Updating packages...")
    rc, _ = _sudo(ip, "apt-get update -qq", timeout=120)
    if rc != 0:
        log("apt-get update failed")
        return False

    log("Downloading Docker...")
    rc, _ = ssh_run(ip, "curl -fsSL https://get.docker.com -o /tmp/get-docker.sh", timeout=60)
    if rc != 0:
        log("Download failed")
        return False

    log("Installing Docker (this takes a few minutes)...")
    rc, _ = _sudo(ip, "sh /tmp/get-docker.sh", timeout=600)
    if rc != 0:
        log("Installation failed")
        return False

    log("Configuring Docker...")
    _sudo(ip, "systemctl stop docker docker.socket containerd 2>/dev/null || true")
    _sudo(ip, f"mkdir -p {DOCKER_DATA_ROOT}")
    _sudo(ip, "mkdir -p /etc/docker")
    ssh_run(ip,
        f"echo '{SSH_PASS}' | sudo -S tee /etc/docker/daemon.json > /dev/null << 'EOF'\n"
        f"{DAEMON_JSON}\n"
        f"EOF")

    # Move containerd to eMMC — rootfs is too small (2G)
    log("Moving containerd to /mnt/data...")
    _sudo(ip, "mkdir -p /mnt/data/containerd")
    _sudo(ip, "rsync -a /var/lib/containerd/ /mnt/data/containerd/ 2>/dev/null || true")
    _sudo(ip, "rm -rf /var/lib/containerd")
    _sudo(ip, "ln -s /mnt/data/containerd /var/lib/containerd")

    log("Starting Docker...")
    _sudo(ip, "systemctl start containerd docker")
    _sudo(ip, f"usermod -aG docker {SSH_USER}")
    ssh_run(ip, "rm -f /tmp/get-docker.sh")

    log("Verifying...")
    rc, out = ssh_run(ip, "docker --version")
    if rc != 0:
        log("Verification failed")
        return False
    log(out[0] if out else "Docker OK")

    rc, out = ssh_run(ip, "docker info 2>/dev/null | grep 'Docker Root Dir'")
    if out:
        log(out[0].strip())

    log("Docker installed")
    return True
