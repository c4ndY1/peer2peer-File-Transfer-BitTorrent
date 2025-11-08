# peer2peer-File-Transfer-BitTorrent

Simulate BitTorrent-style peer‑to‑peer file transfer swarms with a lightweight Python client and a PyQt5 desktop GUI.

## Overview

This project explores BitTorrent and P2P networking in Python. It provides a GUI-driven client that can open .torrent files, talk to trackers, discover peers, and download/upload pieces concurrently—without relying on a centralized server.

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
├─ server.py                # Simple local UDP tracker (optional)
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
cd peer2peer-File-Transfer-BitTorrent
```

2) Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate      # Linux/macOS
# On Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
```

3) Install dependencies
```bash
pip install -r requirements.txt
pip install PyQt5              # May not be pinned in requirements.txt
```

Linux hints if PyQt5 wheel fails:
```bash
sudo apt-get install -y python3-pyqt5 libqt5gui5 libqt5widgets5
```

## Usage

Start the desktop client and manage torrents from the GUI.

Optional (for bundled sample torrents using udp://localhost:6881/announce):
```bash
python3 server.py
```

Then start the GUI:
```bash
python3 torrent_gui.py [--debug] [--theme dark|light|auto] [torrent1.torrent ...]
```

Examples:
```bash
python3 torrent_gui.py                      # Start empty
python3 torrent_gui.py Torrents/Torrent1    # Auto-add a torrent at launch
python3 torrent_gui.py --debug --theme light
```

### Single‑Instance Behavior
By default the client enforces a single running instance (local control server on ports 6995‑6999). A second instance forwards provided torrent filenames to the first and exits.

### Running Multiple Instances
Set `TORRENT_GUI_ALLOW_MULTIPLE=1` to disable the single‑instance check. Each instance will try ports 6881‑6889 for the peer server.

```bash
export TORRENT_GUI_ALLOW_MULTIPLE=1
python3 torrent_gui.py --theme dark

# Another terminal
export TORRENT_GUI_ALLOW_MULTIPLE=1
python3 torrent_gui.py --theme light
```

## Using the GUI

- Add: Choose one or more `.torrent` files
- Pause / Resume: Control transfer state
- Delete: Remove torrent (does not delete downloaded files)
- Theme toggle (if exposed via args)

Columns show progress, size, ratio, speeds, and seeding state.

## Creating Your Own Torrent Files

Quick helper (not exposed via GUI):
```python
from torrent_gui import create_torrent
create_torrent('/path/to/file.bin', 'file.bin.torrent')
```
Ensure the announce URL matches a tracker you control (e.g., `udp://localhost:6881/announce` when using server.py).

## Seeding

After completion the client seeds automatically. Keep the data in the chosen download directory to maintain integrity.

## Logging & Debugging

- Use `--debug` for verbose logs.
- Without `--debug`, INFO/DEBUG is suppressed to reduce UI noise.

## Troubleshooting

- PyQt5 fails to install: Upgrade pip; on Linux install system Qt libs; try `pip install "PyQt5<6"`.
- Tracker unreachable: Start `python3 server.py`; check firewall for UDP/6881.
- No peers: Verify tracker response; run a second instance or share the torrent with another peer.
- Multiple instance conflicts: Use `TORRENT_GUI_ALLOW_MULTIPLE=1`; free ports 6881‑6889 and 6995‑6999.
- State not restored: Check `~/.torrent_gui_state` permissions/existence.

## Notes & Limitations

- Prototype for learning; security hardening is minimal.
- No magnet URIs, DHT, PEX, uTP, or advanced choking strategies.
- IPv6 peers simplified.

## License

Add a LICENSE file if formal licensing is required. Until then, treat as source-available for learning.

## Quick start recap

```bash
git clone https://github.com/c4ndY1/peer2peer-File-Transfer-BitTorrent.git
cd peer2peer-File-Transfer-BitTorrent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install PyQt5
python3 server.py            # optional tracker for local torrents
python3 torrent_gui.py       # start the client
```

