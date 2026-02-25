LABEL = "Welcome"


def run(log):
    log("OpenRBT Wirenboard Deploy")
    log("")
    log("This wizard will configure your Wirenboard:")
    log("  - Select target device on the network")
    log("  - Verify hardware and connectivity")
    log("  - Format & mount SSD (/mnt/ssd)")
    log("  - Install Docker (data on eMMC)")
    log("")
    log("Ready")
    return True
