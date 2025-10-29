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
python3 torrent_gui.py
```

- Add a torrent: click the “Add” icon and select a `.torrent` file (or paste its path)
- Download: the client will announce to trackers and start fetching pieces from peers
- Seed: switch to the “Seed” tab and choose a file/folder to share
- Manage: pause, resume, or remove items using the toolbar controls

## Troubleshooting

- PyQt5 installation issues: ensure you’re using a virtual environment and a recent pip. On some Linux distros, installing system Qt libraries may help. As a fallback, try `pip install "PyQt5<6"`.
- Connection/Tracker errors: verify internet connectivity and that your firewall allows outbound TCP/UDP. Some networks block tracker ports.
- No peers found: try another torrent or ensure the tracker is up; DHT is not included in this client.

## Contributing

Issues and pull requests are welcome. If you’re proposing larger changes, please open an issue first to discuss the approach.

## Acknowledgements

- BitTorrent protocol documentation and community resources
- bencodepy for bencoding support
4. All the other icons like pause, resume and delete are quite intuitive and works while the file is downloading or seeding.



python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

