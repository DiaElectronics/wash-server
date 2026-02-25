LABEL = "Format & Mount SSD"

from utils import ssh_run
from steps.common import state, _sudo, SSD_DEV, SSD_MOUNT, DOCKER_DATA_ROOT


def run(log):
    ip = state.get("target_ip")
    if not ip:
        log("No target selected")
        return False

    rc, out = _sudo(ip, f"blkid -o value -s TYPE {SSD_DEV}")
    current_fs = out[0].strip() if rc == 0 and out else ""

    rc, out = ssh_run(ip, f"mount | grep '{SSD_DEV}'")
    already_mounted = rc == 0 and any(SSD_MOUNT in l for l in out)

    if current_fs == "ext4" and already_mounted:
        log(f"Already ext4 at {SSD_MOUNT}")
    else:
        if rc == 0 and out:
            log(f"Unmounting {SSD_DEV}...")
            _sudo(ip, f"umount {SSD_DEV} 2>/dev/null || true")

        if current_fs != "ext4":
            log(f"Formatting {SSD_DEV} as ext4...")
            rc, _ = _sudo(ip, f"mkfs.ext4 -L SSD -F {SSD_DEV}", timeout=120)
            if rc != 0:
                log("Format failed")
                return False

        log(f"Mounting at {SSD_MOUNT}...")
        _sudo(ip, f"mkdir -p {SSD_MOUNT}")
        rc, _ = _sudo(ip, f"mount {SSD_DEV} {SSD_MOUNT}")
        if rc != 0:
            log("Mount failed")
            return False

    log("Checking fstab...")
    rc, _ = ssh_run(ip, f"grep '{SSD_MOUNT}' /etc/fstab")
    if rc != 0:
        fstab_line = f"{SSD_DEV}  {SSD_MOUNT}  ext4  defaults,noatime,nofail  0  2"
        _sudo(ip, f"bash -c 'echo \"{fstab_line}\" >> /etc/fstab'")
        log("  Added to fstab (nofail)")

    log("Creating directories...")
    for d in ["/mnt/data/pg-critical-data", DOCKER_DATA_ROOT]:
        _sudo(ip, f"mkdir -p {d}")
        log(f"  {d}")
    for d in ["pg-growing-data", "logs", "minio"]:
        _sudo(ip, f"mkdir -p {SSD_MOUNT}/{d}")
        log(f"  {SSD_MOUNT}/{d}")

    rc, out = ssh_run(ip, f"df -h {SSD_MOUNT}")
    if out and len(out) > 1:
        log(out[-1].strip())

    log("Disks ready")
    return True
