# peer2peer-File-Transfer-BitTorrent

Simulate p2p File Transfer swarms with a lightweight Python client and a simple PyQt5 desktop GUI.

## Overview

This project explores the p2p File Transfer using BitTorrent protocol and P2P networking in Python. It provides a GUI-driven client that can open .torrent files, talk to trackers, discover peers, and download/upload pieces concurrently—without relying on a centralized server.

## Features

- Open and parse .torrent files (bencoding via bencodepy)
- Announce to trackers (HTTP/UDP) and discover peers
- Peer connections over TCP (client and server)
- Concurrent piece download/upload with basic swarm management
- Seeding mode, pause, resume, and remove actions via the GUI
- Basic speed measurement and progress reporting
- Async I/O with asyncio for efficient networking
- Cross‑platform PyQt5 GUI

## Tech stack

- Python 3.8+
- PyQt5 (GUI)
- asyncio, aiohttp (networking)
- bencodepy (bencoding)

## Project structure

```
.
├─ torrent_gui.py           # GUI entry point
├─ server.py                # Local peer server/runner (if used by your setup)
├─ torrent_client/
│  ├─ algorithms/           # announcer, downloader, peer_manager, uploader, etc.
│  ├─ control/              # client/controller/manager wiring
│  └─ network/              # TCP peer server/client, tracker clients (HTTP/UDP)
└─ Torrents/                # Sample/working .torrent files
```

## Prerequisites

- Python 3.8+ (Linux, macOS, or Windows)
- A working C/C++ toolchain may help on some platforms when installing wheels

## Setup

1) Clone the repository

```bash
git clone https://github.com/c4ndY1/peer2peer-File-Transfer-BitTorrent.git
cd BitTorrent_Simulator
```

2) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

3) Install dependencies

PyQt5 is required for the GUI and may not be listed in `requirements.txt`.

```bash
pip install PyQt5
pip install -r requirements.txt
```

## Usage

Start the desktop client and manage torrents from the GUI:

```bash
# peer2peer-File-Transfer-BitTorrent

Simulate BitTorrent-style peer‑to‑peer file transfer swarms with a lightweight Python client and a modern PyQt5 GUI.

## 1. Overview

This project is a learning / demonstration client that can:
* Parse `.torrent` files (bencode)
* Announce to trackers (UDP and HTTP)
* Discover peers and exchange pieces over TCP
* Download and seed simultaneously with basic swarm logic
* Persist minimal state between runs

No DHT, PEX, or magnet links are implemented — keeping the code focused and readable.

## 2. Features

* Open multiple torrents (multi-file supported)
* Per‑torrent progress, ratio, speeds (download / upload)
* Pause / resume / remove actions
* Seeding after completion
* Automatic piece hashing & integrity checks
* Adjustable dark / light theme
* Optional multi‑instance mode for local testing

## 3. Tech Stack

| Layer | Tools |
|-------|-------|
| GUI | PyQt5 |
| Async Networking | asyncio, aiohttp |
| Encoding | bencodepy |
| Storage / State | pickle snapshots |

Python version: 3.8+ (tested on modern CPython). Earlier versions may work but are not supported.

## 4. Project Structure

```
.
├─ torrent_gui.py        # Main GUI application entry point
├─ server.py             # Simple local UDP tracker (binds :6881)
├─ torrent_client/
│  ├─ algorithms/        # Announcer, downloader, peer manager, uploader, etc.
│  ├─ control/           # Control server/client + manager (single-instance logic)
│  └─ network/           # Peer TCP server + tracker client implementations
└─ Torrents/             # Sample working torrent(s)
```

## 5. Requirements / Installation

1. Clone the repository:
```bash
git clone https://github.com/c4ndY1/peer2peer-File-Transfer-BitTorrent.git
cd peer2peer-File-Transfer-BitTorrent
```

2. Create & activate a virtual environment (recommended):
```bash
python3 -m venv .venv
source .venv/bin/activate      # Linux/macOS
# On Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install PyQt5              # Not pinned in requirements.txt
```

Linux package hints (if PyQt5 wheel fails):
```bash
sudo apt-get install -y python3-pyqt5 libqt5gui5 libqt5widgets5
```

## 6. Running the Local Tracker (optional but needed for bundled sample torrent)

The sample torrent(s) use `udp://localhost:6881/announce`. Start the simple UDP tracker in one terminal:
```bash
python3 server.py
```
Leave it running. (It auto-exits after 1 hour; restart if needed.)

## 7. Starting the GUI Client

In a second terminal (same virtualenv):
```bash
python3 torrent_gui.py [--debug] [--theme dark|light|auto] [torrent1.torrent ...]
```
Examples:
```bash
python3 torrent_gui.py            # Start empty
python3 torrent_gui.py Torrents/Torrent1  # Auto-add a torrent at launch
python3 torrent_gui.py --debug --theme light
```

### Single‑Instance Behavior
By default the client enforces a single running instance (it spawns a local control server on ports 6995‑6999). If a second instance starts it will try to forward any provided torrent filenames to the first and then exit.

### Running Multiple Instances on the Same Machine
Set the environment variable `TORRENT_GUI_ALLOW_MULTIPLE=1` to disable the single‑instance check. Each instance will attempt to bind a free peer port from 6881‑6889.

Example (two separate terminals):
```bash
export TORRENT_GUI_ALLOW_MULTIPLE=1
python3 torrent_gui.py --theme dark

# In another terminal
export TORRENT_GUI_ALLOW_MULTIPLE=1
python3 torrent_gui.py --theme light
```
If a port collision occurs the second instance picks the next available port. (Running more than 9 simultaneous instances will likely fail due to the limited port range.)

## 8. Using the GUI

Toolbar actions are intentionally minimalist:
* Add: Choose one or more `.torrent` files
* Pause / Resume: Control transfer state
* Delete: Remove torrent (does not delete downloaded files)
* Theme toggle (if exposed via args)

The list shows progress, size, ratio, speeds, and seeding state.

## 9. Creating Your Own Torrent Files

The helper function `create_torrent(file_path, torrent_path)` lives in `torrent_gui.py` (not exposed via GUI). Quick ad‑hoc usage inside a Python shell:
```python
from torrent_gui import create_torrent
create_torrent('/path/to/file.bin', 'file.bin.torrent')
```
Make sure the announce URL matches a tracker you control (e.g. keep the default `udp://localhost:6881/announce` if using `server.py`). Share the generated `.torrent` file with peers using this client.

## 10. Seeding

Once a torrent finishes downloading it automatically transitions to seeding. Ensure the original data remains in the selected download directory; moving or deleting it will break seeding integrity.

## 11. Logging & Debugging

* Use `--debug` to enable verbose logs (TRACE style for internal modules).
* Without `--debug` the client suppresses INFO/DEBUG to reduce UI noise.

## 12. Troubleshooting

| Issue | Resolution |
|-------|------------|
| PyQt5 fails to install | Upgrade pip; on Linux install system Qt libs; try `pip install "PyQt5<6"` |
| Tracker unreachable | Start `python3 server.py`; check firewall for UDP/6881 |
| No peers / stagnant download | Not enough peers seeding; verify tracker response; consider running a second instance or sharing the torrent with a friend |
| Multiple instance conflicts | Ensure `TORRENT_GUI_ALLOW_MULTIPLE=1`; free up ports 6881‑6889 and 6995‑6999 |
| State not restored | Check existence/permissions of `~/.torrent_gui_state` |

## 13. Notes & Limitations

* This is a prototype — security hardening (e.g., validating all incoming data, avoiding arbitrary pickle execution) is intentionally minimal.
* No support for magnet URIs, DHT, PEX, uTP, or advanced choking/optimistic unchoking strategies.
* Peer list from tracker ignores IPv6 peers beyond first 4 bytes (simplified packing).

## 14. Contributing

Pull requests are welcome. For substantial changes open an issue first describing motivation & approach.

## 15. License

Distributed under the terms you choose (add a LICENSE file if formal licensing is required). Until then, treat this as “source available for learning.”

## 16. Acknowledgements

* BitTorrent protocol specification & community docs
* bencodepy for concise bencode support
* PyQt5 for the GUI toolkit

---
Quick start recap:
```bash
git clone https://github.com/c4ndY1/peer2peer-File-Transfer-BitTorrent.git
cd peer2peer-File-Transfer-BitTorrent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install PyQt5
python3 server.py            # (optional tracker for local torrents)
python3 torrent_gui.py       # Start the client
```

Run two instances locally:
```bash
export TORRENT_GUI_ALLOW_MULTIPLE=1
python3 torrent_gui.py
export TORRENT_GUI_ALLOW_MULTIPLE=1
python3 torrent_gui.py --theme light
```

