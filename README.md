# ⚡ WIFITE for windows ⚡

An automated WiFi discovery, testing, and connection utility for Windows featuring a cyberpunk/terminal-hacker interface.

Scans for nearby wireless access points, tests open networks first, iterates through high-frequency default/public passwords across secured networks, logs all successful connections to a local loot report, and automatically reconnects you to the highest quality network with active internet.

---

## 📸 Overview

```text
  ╦ ╦┬┌─┐┬  ┌┬┐┌─┐  ╔═╗┬ ┬┌┬┐┌─┐  ╔═╗┌─┐┌┐┌┌┐┌┌─┐┌─┐┌┬┐
  ║║║│├┤ │   │ ├┤   ╠═╣│ │ │ │ │  ║  │ │││││││├┤ │   │
  ╚╩╝┴└  ┴   ┴ └─┘  ╩ ╩└─┘ ┴ └─┘  ╚═╝└─┘┘└┘┘└┘└─┘└─┘ ┴
```

* **Matrix-style UI** powered by `rich` and `pyfiglet`.
* **Live AP Radar:** Real-time signal bars (`████████░░`), security badges (WPA2, WPA3, Open), and encryption status.
* **Non-Stopping Multi-Target Scan:** Tests all in-range networks sequentially rather than quitting at the first hit.
* **SSID-Adaptive Wordlists:** Dynamically derives hotspot-specific guesses based on network names alongside common presets.
* **Loot Table & Export:** Generates an on-screen summary table and persists successful logins into `cracked_networks.txt`.
* **Smart Auto-Fallback:** Connects back to the strongest verified access point with working Internet when complete.

---

## 🚀 Features

- **Forced Beacon Refresh:** Issues direct `netsh wlan scan` calls to avoid Windows adapter cache lag.
- **Two-Stage Strategy:**
  1. **Phase 1 (Open APs):** Rapid connection checks against open public hotspots.
  2. **Phase 2 (Secured APs):** Targeted common dictionary attempts (WPA2-PSK / WPA3-SAE / WPA-PSK).
- **Signal Filtering:** Ignores weak broadcasts (<15% signal) to prevent wasted connection timeouts.
- **Internet Verification:** Performs live connectivity handshakes via DNS ping checking.

---

## 🛠️ Prerequisites & Installation

### Requirements

- **OS:** Windows 10 / Windows 11
- **Python:** 3.10+
- **Privileges:** Administrator permissions (required by Windows `netsh` for WLAN profile creation)

### Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Nikhilrathour/Project-wifite.git
   cd Project-wifite
   ```
2. **Install Python dependencies:**

   ```bash
   pip install rich pyfiglet
   ```

---

## 💻 Usage

> [!IMPORTANT]
> **Always run your terminal (PowerShell or Command Prompt) as Administrator**, otherwise Windows will block network profile injection.

### Standard Scan (All Networks)

Scans every network, tests open hotspots, runs wordlists on secured networks, and outputs the loot table:

```powershell
python wifi_connect.py
```

### Target a Specific Network Only

Focus brute-force attempts on a single access point:

```powershell
python wifi_connect.py --target "CafeWiFi"
```

### Open Networks Only

Quick scan that only checks and connects to open, unencrypted networks:

```powershell
python wifi_connect.py --open-only
```

### Custom Wordlist

Load an external dictionary file (one password per line, minimum 8 characters):

```powershell
python wifi_connect.py --extra-passwords extra_passwords.txt
```

### Disable Final Auto-Reconnect

Keep your interface disconnected after completing the scan rather than jumping onto the best cracked network:

```powershell
python wifi_connect.py --no-reconnect
```

---

## 📁 Project Structure

```text
Project wifite/
├── wifi_connect.py       # Core discovery, connection, and terminal UI script
├── extra_passwords.txt    # Optional list for custom password entries
├── cracked_networks.txt  # Auto-generated loot file with saved successes
└── README.md             # Project documentation
```

---

## 📋 Command-Line Options

| Flag                  | Argument         | Description                                                                  |
| --------------------- | ---------------- | ---------------------------------------------------------------------------- |
| `--open-only`       | *None*         | Only attempts connections to open / unencrypted networks.                    |
| `--target`          | `"<SSID>"`     | Focuses execution only on the specified SSID.                                |
| `--extra-passwords` | `"<file.txt>"` | Loads supplementary passwords into the attack buffer.                        |
| `--no-reconnect`    | *None*         | Disables automatic connection to the best access point at script completion. |

---

## ⚖️ Legal Disclaimer

This utility is developed for personal convenience, educational network auditing, and diagnostics under authorized conditions. Attempting to access unauthorized private networks without permission is illegal in many jurisdictions. Use responsibly and only test access points you own or have explicit authorization to join.
