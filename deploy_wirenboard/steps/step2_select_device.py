LABEL = "Select Device"

from utils import get_local_ip, scan_subnet_ssh, check_ssh


def run(log):
    local_ip = get_local_ip()
    if not local_ip:
        log("Could not detect local IP")
        return False

    prefix = ".".join(local_ip.split(".")[:3])
    log(f"Scanning {prefix}.0/24 ...")

    results = scan_subnet_ssh(local_ip)
    if not results:
        log("No devices found")
        return False

    log(f"Found {len(results)} device(s), checking SSH...")

    remote = [(ip, b) for ip, b in results if ip != local_ip]
    if not remote:
        log("No remote devices")
        return False

    accessible = []
    for ip, _ in remote:
        log(f"Trying {ip}...")
        ok, info = check_ssh(ip)
        if ok:
            accessible.append((ip, info))

    if not accessible:
        log("No SSH-accessible devices")
        return False

    log(f"{len(accessible)} device(s) accessible")
    return True, {
        "key": "target_ip",
        "title": "Select target device",
        "items": [(f"{ip}  ({hostname})", ip) for ip, hostname in accessible],
    }
