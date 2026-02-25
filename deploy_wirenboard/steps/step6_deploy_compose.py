LABEL = "Deploy Docker Compose"

import os
from utils import ssh_run, SSH_USER, SSH_PASS
from steps.common import state, _sudo, SSD_MOUNT

DEPLOY_DIR = "/mnt/data/wash-server"
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES_TO_UPLOAD = [
    "docker-compose.yml",
    "prometheus.yml",
]


def _scp(ip, local_path, remote_path):
    """Upload a file via scp."""
    import subprocess
    scp_opts = [
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "PubkeyAuthentication=no",
    ]
    proc = subprocess.run(
        ["sshpass", "-p", SSH_PASS, "scp", *scp_opts,
         local_path, f"{SSH_USER}@{ip}:{remote_path}"],
        capture_output=True, text=True, timeout=30,
    )
    return proc.returncode, proc.stderr.strip()


def run(log):
    ip = state.get("target_ip")
    if not ip:
        log("No target selected")
        return False

    # Create directories
    log("Creating directories...")
    dirs = [
        DEPLOY_DIR,
        f"{DEPLOY_DIR}/stations",
        f"{DEPLOY_DIR}/ssh",
        f"{SSD_MOUNT}/pgdata",
        f"{SSD_MOUNT}/minio",
    ]
    for d in dirs:
        rc, _ = _sudo(ip, f"mkdir -p {d}")
        if rc != 0:
            log(f"Failed to create {d}")
            return False

    _sudo(ip, f"chown -R {SSH_USER}:{SSH_USER} {DEPLOY_DIR}")

    # Updater expects lea-central-wash/ next to compose dir
    _sudo(ip, "ln -sfn wash-server /mnt/data/lea-central-wash")

    # Upload files
    for fname in FILES_TO_UPLOAD:
        local = os.path.join(SCRIPT_DIR, fname)
        if not os.path.exists(local):
            log(f"Missing local file: {fname}")
            return False
        log(f"Uploading {fname}...")
        rc, err = _scp(ip, local, f"{DEPLOY_DIR}/{fname}")
        if rc != 0:
            log(f"Failed to upload {fname}: {err}")
            return False

    # Pull images
    log("Pulling images (this may take a while)...")
    rc, out = ssh_run(
        ip,
        f"cd {DEPLOY_DIR} && docker compose pull 2>&1",
        timeout=600,
    )
    for line in out[-5:]:
        log(f"  {line}")
    if rc != 0:
        log("Pull failed")
        return False

    # Start
    log("Starting services...")
    rc, out = ssh_run(
        ip,
        f"cd {DEPLOY_DIR} && docker compose up -d 2>&1",
        timeout=300,
    )
    for line in out[-5:]:
        log(f"  {line}")
    if rc != 0:
        log("Failed to start services")
        return False

    # Verify
    log("Verifying...")
    rc, out = ssh_run(ip, "docker ps --format '{{.Names}}: {{.Status}}'")
    for line in out:
        log(f"  {line}")

    log("Deploy complete")
    return True
