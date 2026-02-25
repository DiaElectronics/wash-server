#!/usr/bin/env python3
"""OpenRBT Wirenboard Deploy — Wizard UI."""

import curses
import threading

from steps import STEPS, state

TITLE = "OpenRBT Wirenboard Deploy"

# Box drawing
DTL, DTR, DBL, DBR = "\u2554", "\u2557", "\u255a", "\u255d"
DHZ, DVT = "\u2550", "\u2551"
# T-junctions for horizontal divider
TL, TR = "\u2560", "\u2563"


def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLUE)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_CYAN)
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_BLACK)
    curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_WHITE)
    return {
        "bg":      curses.color_pair(1),
        "title":   curses.color_pair(2) | curses.A_BOLD,
        "box":     curses.color_pair(3),
        "sel":     curses.color_pair(4) | curses.A_BOLD,
        "norm":    curses.color_pair(5),
        "err":     curses.color_pair(6) | curses.A_BOLD,
        "ok":      curses.color_pair(7) | curses.A_BOLD,
        "shadow":  curses.color_pair(8),
        "footer":  curses.color_pair(10),
    }


def fill(win, y, x, h, w, attr):
    for row in range(h):
        try:
            win.addstr(y + row, x, " " * w, attr)
        except curses.error:
            pass


def draw_box(win, y, x, h, w):
    try:
        win.addstr(y, x, DTL + DHZ * (w - 2) + DTR)
        for row in range(1, h - 1):
            win.addstr(y + row, x, DVT)
            win.addstr(y + row, x + w - 1, DVT)
        win.addstr(y + h - 1, x, DBL + DHZ * (w - 2) + DBR)
    except curses.error:
        pass


def center(win, y, text, attr, w=None):
    if w is None:
        _, w = win.getmaxyx()
    x = max(0, (w - len(text)) // 2)
    try:
        win.addstr(y, x, text, attr)
    except curses.error:
        pass


def put(win, y, x, text, attr):
    try:
        win.addstr(y, x, text, attr)
    except curses.error:
        pass


# ---------------------------------------------------------------------------
# Layout:
#
#  ╔═══════════════════════════════════════════════════╗
#  ║          OpenRBT Wirenboard Deploy                ║
#  ╠═══════════════════════════════════════════════════╣
#  ║  ✓  Welcome                                       ║
#  ║  ✓  Select Device                                 ║
#  ║  ✗  Check Prerequisites                           ║
#  ║     Format & Mount SSD                            ║
#  ║     Install Docker                                ║
#  ║  ████████░░░░░░░░░░░░░░░░░░  2/5                 ║
#  ╠═══════════════════════════════════════════════════╣
#  ║  Connecting to 192.168.50.114...                  ║
#  ║  SSH OK (wirenboard-XXXXXXX)                      ║
#  ║  Checking eMMC (/mnt/data)...                     ║
#  ║    1234MB free                                    ║
#  ║  Checking SSD (/dev/sda1)...                      ║
#  ║    /dev/sda1 not found                            ║
#  ╚═══════════════════════════════════════════════════╝
# ---------------------------------------------------------------------------

INDICATORS = {
    "pending": "   ",
    "active":  " \u25b6 ",
    "ok":      " \u2713 ",
    "fail":    " \u2717 ",
}

LOG_AREA_LINES = 8


def draw_wizard(scr, c, statuses, current, log_lines, lock):
    scr.erase()
    rows, cols = scr.getmaxyx()

    # Blue background
    fill(scr, 0, 0, rows, cols, c["bg"])

    # Footer
    fill(scr, rows - 1, 0, 1, cols, c["footer"])

    n = len(STEPS)
    box_w = min(64, cols - 4)
    # steps + progress + divider + log area + borders
    box_h = n + 2 + 1 + LOG_AREA_LINES + 2
    box_x = (cols - box_w) // 2
    box_y = max(1, (rows - box_h - 1) // 2)

    # Shadow
    for row in range(1, box_h + 1):
        put(scr, box_y + row, box_x + box_w, "  ", c["shadow"])
    put(scr, box_y + box_h, box_x + 2, " " * box_w, c["shadow"])

    # Box fill + border
    fill(scr, box_y, box_x, box_h, box_w, c["box"])
    draw_box(scr, box_y, box_x, box_h, box_w)

    # Title
    tx = box_x + (box_w - len(TITLE) - 2) // 2
    put(scr, box_y, tx, f" {TITLE} ", c["box"] | curses.A_BOLD)

    # Steps
    y = box_y + 1
    for i, (label, _) in enumerate(STEPS):
        st = statuses[i]
        ind = INDICATORS[st]

        if st == "ok":
            attr = c["ok"]
        elif st == "fail":
            attr = c["err"]
        elif st == "active":
            attr = c["sel"]
        else:
            attr = c["norm"]

        put(scr, y, box_x + 2, ind, attr)
        put(scr, y, box_x + 5, label[:box_w - 8], attr)
        y += 1

    # Progress bar
    y += 1
    completed = sum(1 for s in statuses if s == "ok")
    bar_w = box_w - 16
    filled = int(bar_w * completed / n) if n > 0 else 0
    bar = "\u2588" * filled + "\u2591" * (bar_w - filled)
    put(scr, y - 1, box_x + 4, f" {bar}  {completed}/{n} ", c["box"])

    # Horizontal divider
    divider_y = box_y + n + 2
    put(scr, divider_y, box_x, TL + DHZ * (box_w - 2) + TR, c["box"])

    # Log area
    log_top = divider_y + 1
    with lock:
        visible = log_lines[-LOG_AREA_LINES:]

    for j, line in enumerate(visible):
        text = line[:box_w - 4]
        put(scr, log_top + j, box_x + 2, text, c["box"])

    scr.refresh()


def choose_dialog(scr, c, title, items):
    """Overlay selection dialog. Returns value or None."""
    rows, cols = scr.getmaxyx()
    selected = 0
    max_label = max(len(label) for label, _ in items)
    w = min(max(max_label + 8, len(title) + 6), cols - 8)
    h = len(items) + 4
    x = (cols - w) // 2
    y = (rows - h) // 2

    while True:
        # Shadow
        for row in range(1, h + 1):
            put(scr, y + row, x + w, "  ", c["shadow"])
        put(scr, y + h, x + 2, " " * w, c["shadow"])

        fill(scr, y, x, h, w, c["box"])
        draw_box(scr, y, x, h, w)
        tx = x + (w - len(title) - 2) // 2
        put(scr, y, tx, f" {title} ", c["box"] | curses.A_BOLD)

        for i, (label, _) in enumerate(items):
            attr = c["sel"] if i == selected else c["norm"]
            line = f" {label} ".ljust(w - 6)
            put(scr, y + 2 + i, x + 3, line, attr)

        fill(scr, rows - 1, 0, 1, cols, c["footer"])
        center(scr, rows - 1, " ENTER=Select  ESC=Cancel  \u2191\u2193=Navigate ",
               c["footer"] | curses.A_BOLD, cols)

        scr.refresh()
        key = scr.getch()

        if key == 27:
            return None
        elif key == curses.KEY_UP:
            selected = (selected - 1) % len(items)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(items)
        elif key in (curses.KEY_ENTER, 10, 13):
            return items[selected][1]


def wizard(stdscr):
    curses.curs_set(0)
    c = init_colors()
    n = len(STEPS)

    if not STEPS:
        stdscr.addstr(0, 0, "No steps defined")
        stdscr.getch()
        return

    statuses = ["pending"] * n
    all_logs = [[] for _ in range(n)]  # full log per step
    locks = [threading.Lock() for _ in range(n)]

    for i, (label, fn) in enumerate(STEPS):
        statuses[i] = "active"

        result = [None]

        def log(text, _i=i):
            with locks[_i]:
                all_logs[_i].append(text)

        def worker(_fn=fn, _log=log, _res=result):
            _res[0] = _fn(_log)

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        curses.halfdelay(2)
        cancelled = False
        while t.is_alive():
            draw_wizard(stdscr, c, statuses, i, all_logs[i], locks[i])
            try:
                key = stdscr.getch()
                if key in (27, ord("q"), ord("Q")):
                    cancelled = True
            except curses.error:
                pass

        curses.cbreak()
        t.join()

        if cancelled:
            statuses[i] = "fail"
            with locks[i]:
                all_logs[i].append("Cancelled by user")
            draw_wizard(stdscr, c, statuses, i, all_logs[i], locks[i])
            _wait_key(stdscr, c, " Cancelled. Press any key. ", c["err"])
            return

        # Parse result
        res = result[0]
        if isinstance(res, tuple):
            ok = res[0]
            choose_config = res[1] if len(res) > 1 else None
        elif isinstance(res, bool):
            ok, choose_config = res, None
        else:
            ok, choose_config = False, None

        # Handle user choice (e.g. Select Device)
        if ok and choose_config:
            draw_wizard(stdscr, c, statuses, i, all_logs[i], locks[i])
            chosen = choose_dialog(stdscr, c,
                                   choose_config["title"],
                                   choose_config["items"])
            if chosen is not None:
                state[choose_config["key"]] = chosen
                with locks[i]:
                    all_logs[i].append(f"Selected: {chosen}")
            else:
                ok = False
                with locks[i]:
                    all_logs[i].append("No device selected")

        statuses[i] = "ok" if ok else "fail"
        draw_wizard(stdscr, c, statuses, i, all_logs[i], locks[i])

        if not ok:
            _wait_key(stdscr, c, " Installation failed. Press any key. ", c["err"])
            return

    # All done
    draw_wizard(stdscr, c, statuses, n - 1, all_logs[n - 1], locks[n - 1])
    _wait_key(stdscr, c, " Installation complete! Press any key. ", c["ok"])


def _wait_key(stdscr, c, message, attr):
    rows, cols = stdscr.getmaxyx()
    fill(stdscr, rows - 1, 0, 1, cols, c["footer"])
    center(stdscr, rows - 1, message, attr, cols)
    stdscr.refresh()
    curses.cbreak()
    stdscr.getch()


def main():
    curses.wrapper(wizard)


if __name__ == "__main__":
    main()
