import asyncio
import hashlib
import logging
import random
from typing import List, Optional

from torrent_client.algorithms.announcer import Announcer
from torrent_client.algorithms.downloader import Downloader
from torrent_client.algorithms.peer_manager import PeerManager
from torrent_client.algorithms.speed_measurer import SpeedMeasurer
from torrent_client.algorithms.uploader import Uploader
from torrent_client.file_structure import FileStructure
from torrent_client.models import Peer, TorrentInfo, DownloadInfo
from torrent_client.network import EventType, PeerTCPClient
from torrent_client.utils import import_signals


QObject, pyqtSignal = import_signals()


__all__ = ['TorrentManager']


class TorrentManager(QObject):
    if pyqtSignal:
        state_changed = pyqtSignal()

    LOGGER_LEVEL = logging.DEBUG
    SHORT_NAME_LEN = 19

    def __init__(self, torrent_info: TorrentInfo, our_peer_id: bytes, server_port: Optional[int]):
        super().__init__()

        self._torrent_info = torrent_info
        download_info = torrent_info.download_info  # type: DownloadInfo
        download_info.reset_run_state()
        download_info.reset_stats()

        short_name = download_info.suggested_name
        if len(short_name) > TorrentManager.SHORT_NAME_LEN:
            short_name = short_name[:TorrentManager.SHORT_NAME_LEN] + '..'
        self._logger = logging.getLogger('"{}"'.format(short_name))
        self._logger.setLevel(TorrentManager.LOGGER_LEVEL)

        self._executors = []  # type: List[asyncio.Task]

        self._file_structure = FileStructure(torrent_info.download_dir, torrent_info.download_info)

        self._peer_manager = PeerManager(torrent_info, our_peer_id, self._logger, self._file_structure)
        self._announcer = Announcer(torrent_info, our_peer_id, server_port, self._logger, self._peer_manager)
        self._downloader = Downloader(torrent_info, our_peer_id, self._logger, self._file_structure,
                                      self._peer_manager, self._announcer)
        self._uploader = Uploader(torrent_info, self._logger, self._peer_manager)
        self._speed_measurer = SpeedMeasurer(torrent_info.download_info.session_statistics)
        if pyqtSignal:
            self._downloader.progress.connect(self.state_changed)
            self._speed_measurer.updated.connect(self.state_changed)

    async def _verify_existing_data(self):
        """Scan local files to mark already-downloaded pieces before we announce.
        Ensures we advertise an accurate bitfield when acting as a seeder."""
        download_info = self._torrent_info.download_info
        pieces = download_info.pieces
        selected_piece_indices = [i for i, piece in enumerate(pieces) if piece.selected]

        if not selected_piece_indices:
            download_info.downloaded_piece_count = 0
            download_info.complete = False
            download_info.interesting_pieces.clear()
            return

        download_info.downloaded_piece_count = 0
        download_info.interesting_pieces.clear()

        verified_count = 0
        missing_pieces = []

        for index in selected_piece_indices:
            piece = pieces[index]
            piece_length = download_info.get_real_piece_length(index)
            offset = index * download_info.piece_length

            try:
                data = await self._file_structure.read(offset, piece_length)
            except OSError:
                data = b''

            if len(data) != piece_length:
                piece.reset_content()
                missing_pieces.append(index)
                continue

            if hashlib.sha1(data).digest() == piece.piece_hash:
                if not piece.downloaded:
                    piece.mark_as_downloaded()
                download_info.downloaded_piece_count += 1
                verified_count += 1
            else:
                piece.reset_content()
                missing_pieces.append(index)

        if missing_pieces:
            download_info.interesting_pieces.update(missing_pieces)

        download_info.complete = (
            verified_count == len(selected_piece_indices) and verified_count > 0
        )

        if verified_count:
            self._logger.info('verified %s/%s pieces already present on disk',
                              verified_count, len(selected_piece_indices))
        if missing_pieces:
            self._logger.debug('pieces pending download after verification: %s', missing_pieces)

        if pyqtSignal:
            self.state_changed.emit()

    ANNOUNCE_FAILED_SLEEP_TIME = 3

    def _shuffle_announce_tiers(self):
        for tier in self._torrent_info.announce_list:
            random.shuffle(tier)

    async def run(self):
        await self._verify_existing_data()
        self._shuffle_announce_tiers()
        while not await self._announcer.try_to_announce(EventType.started):
            await asyncio.sleep(TorrentManager.ANNOUNCE_FAILED_SLEEP_TIME)

        self._peer_manager.connect_to_peers(self._announcer.last_tracker_client.peers, True)

        self._executors += [asyncio.ensure_future(coro) for coro in [
            self._announcer.execute(),
            self._uploader.execute(),
            self._speed_measurer.execute(),
        ]]
        # print("completed")
        # self._download_info.complete = True
        self._peer_manager.invoke()
        # if pyqtSignal:
        #     self.progress.emit()
        await self._downloader.run()

    def accept_client(self, peer: Peer, client: PeerTCPClient):
        self._peer_manager.accept_client(peer, client)

    async def stop(self):
        await self._downloader.stop()
        await self._peer_manager.stop()

        executors = [task for task in self._executors if task is not None]
        for task in reversed(executors):
            task.cancel()
        if executors:
            await asyncio.wait(executors)
