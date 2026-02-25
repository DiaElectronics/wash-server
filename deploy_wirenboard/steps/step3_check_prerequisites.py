LABEL = "Check Prerequisites"

from utils import check_ssh, ssh_run
from steps.common import state, SSD_DEV


def run(log):
    ip = state.get("target_ip")
    if not ip:
        log("No target selected")
        return False

    log(f"Connecting to {ip}...")
    ok, hostname = check_ssh(ip)
    if not ok:
        log(f"SSH failed: {hostname}")
        return False
    log(f"SSH OK ({hostname})")

    log("Checking eMMC (/mnt/data)...")
    rc, out = ssh_run(ip, "df -BM /mnt/data | tail -1")
    if rc != 0:
        log("/mnt/data not found")
        return False
    parts = out[0].split() if out else []
    if len(parts) >= 4:
        avail_mb = int(parts[3].rstrip("M"))
        log(f"  {avail_mb}MB free")
        if avail_mb < 2000:
            log("  Less than 2GB free!")

    log(f"Checking SSD ({SSD_DEV})...")
    rc, out = ssh_run(ip, f"test -b {SSD_DEV} && echo OK")
    if rc != 0 or not any("OK" in l for l in out):
        log(f"  {SSD_DEV} not found")
        return False
    rc, out = ssh_run(ip, f"lsblk -dn -o SIZE {SSD_DEV}")
    log(f"  {out[0].strip()}" if out else "  OK")

    log("Checking internet...")
    rc, _ = ssh_run(ip, "curl -fsSL --connect-timeout 5 -o /dev/null https://get.docker.com", timeout=15)
    if rc != 0:
        log("  No internet access")
        return False
    log("  Internet OK")

    log("All prerequisites met")
    return True
