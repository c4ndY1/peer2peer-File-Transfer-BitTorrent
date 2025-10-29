#!/usr/bin/env python3

import argparse
import asyncio
import logging
import os
import sys
from contextlib import closing
from functools import partial, partialmethod
from typing import Dict, List, Optional
from PyQt5.QtCore import QSize


# noinspection PyUnresolvedReferences
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import QTabWidget, QToolBar, QStyleFactory
# noinspection PyUnresolvedReferences
from PyQt5.QtGui import QIcon, QFont, QDropEvent, QPalette, QColor
# noinspection PyUnresolvedReferences
from PyQt5.QtWidgets import QWidget, QListWidget, QAbstractItemView, QLabel, QVBoxLayout, QProgressBar, \
    QListWidgetItem, QMainWindow, QApplication, QFileDialog, QMessageBox, QDialog, QDialogButtonBox, QTreeWidget, \
    QTreeWidgetItem, QHeaderView, QHBoxLayout, QPushButton, QLineEdit, QAction

from torrent_client.control import ControlManager, ControlServer, ControlClient
from torrent_client.models import TorrentState, TorrentInfo, FileTreeNode, FileInfo
from torrent_client.utils import humanize_speed, humanize_time, humanize_size

import hashlib
import bencodepy
from pathlib import Path


class _ShortFormatter(logging.Formatter):
    """Formatter that shortens the logger name to its last component and adds milliseconds."""
    def format(self, record):
        # Add shortname attribute for use in format string
        record.shortname = record.name.split('.')[-1]
        return super().format(record)


def configure_logging(debug: bool):
    root = logging.getLogger()
    # Clear existing handlers to avoid duplicate logs when reconfiguring
    for h in list(root.handlers):
        root.removeHandler(h)

    fmt = '%(levelname)s %(asctime)s.%(msecs)03d %(shortname)s %(message)s'
    datefmt = '%H:%M:%S'
    handler = logging.StreamHandler()
    handler.setFormatter(_ShortFormatter(fmt=fmt, datefmt=datefmt))
    root.addHandler(handler)
    root.setLevel(logging.DEBUG if debug else logging.INFO)


logger = logging.getLogger(__name__)


def apply_modern_theme(app: QApplication, theme: str = 'dark'):
    """Apply a modern Fusion theme with a clean palette and minimal chrome.
    theme: 'dark' | 'light'
    """
    try:
        app.setStyle(QStyleFactory.create('Fusion'))
    except Exception:
        pass

    if theme not in ('dark', 'light'):
        theme = 'dark'

    app_font = QFont('Segoe UI', 10)
    app_font.setHintingPreference(QFont.PreferDefaultHinting)
    app.setFont(app_font)

    if theme == 'dark':
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(31, 33, 38))
        palette.setColor(QPalette.WindowText, QColor(240, 244, 255))
        palette.setColor(QPalette.Base, QColor(26, 28, 33))
        palette.setColor(QPalette.AlternateBase, QColor(36, 38, 45))
        palette.setColor(QPalette.ToolTipBase, QColor(36, 38, 45))
        palette.setColor(QPalette.ToolTipText, QColor(240, 244, 255))
        palette.setColor(QPalette.Text, QColor(237, 240, 250))
        palette.setColor(QPalette.Button, QColor(36, 38, 45))
        palette.setColor(QPalette.ButtonText, QColor(237, 240, 250))
        palette.setColor(QPalette.BrightText, QColor(245, 108, 108))
        palette.setColor(QPalette.Highlight, QColor(79, 109, 245))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        app.setPalette(palette)

        app.setStyleSheet(
            """
            QMainWindow, QWidget { background-color: #1f2126; color: #f1f5ff; }
            QStatusBar { background: transparent; border: none; }
            QToolBar { background: #242732; border: 0; padding: 8px 12px; spacing: 8px; }
            QToolBar QToolButton { background: transparent; color: #e8ebf5; padding: 6px 12px; border-radius: 6px; font-weight: 500; }
            QToolBar QToolButton:hover { background: rgba(255, 255, 255, 0.08); }
            QToolBar QToolButton:pressed { background: rgba(79, 109, 245, 0.35); }
            QListWidget { background: transparent; border: 0; }
            QListWidget::item { margin: 2px 0; padding: 0; }
            QListWidget::item:selected { background: transparent; }
            QTabWidget::pane { border: 0; }
            QTabBar::tab { background: transparent; color: #c0c7de; padding: 6px 14px; border-radius: 6px; margin: 0 6px; }
            QTabBar::tab:selected { background: rgba(79, 109, 245, 0.28); color: #f1f5ff; }
            QTabBar::tab:hover { background: rgba(255, 255, 255, 0.08); }
            QTreeWidget { border: 0; background: #1c1e23; }
            QTreeWidget::item { padding: 4px 6px; }
            QTreeWidget::item:selected { background: rgba(79, 109, 245, 0.18); }
            QHeaderView::section { background: #242732; color: #f1f5ff; border: 0; padding: 6px 10px; font-weight: 500; }
            QPushButton { border: 1px solid rgba(255, 255, 255, 0.1); background: rgba(255, 255, 255, 0.05); padding: 7px 16px; border-radius: 6px; color: #f1f5ff; }
            QPushButton:hover { background: rgba(79, 109, 245, 0.25); border-color: rgba(79, 109, 245, 0.45); }
            QPushButton:pressed { background: rgba(79, 109, 245, 0.35); }
            QLineEdit, QComboBox, QSpinBox { background: #1b1e24; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px; padding: 6px 8px; color: #e9edff; }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: rgba(79, 109, 245, 0.6); }
            QScrollBar:vertical { background: transparent; width: 12px; margin: 10px 0; }
            QScrollBar::handle:vertical { background: rgba(255, 255, 255, 0.18); border-radius: 6px; min-height: 24px; }
            QScrollBar:horizontal { background: transparent; height: 12px; margin: 0 10px; }
            QScrollBar::handle:horizontal { background: rgba(255, 255, 255, 0.18); border-radius: 6px; min-width: 24px; }
            QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
            QListWidget#seedList::item { margin: 6px 10px; border-radius: 12px; padding: 0; }
            QListWidget#seedList::item:selected { background: transparent; }
            QWidget#torrentCard { background-color: #272a35; border: 1px solid #313545; border-radius: 12px; }
            QWidget#torrentCard:hover { border-color: #526dff; }
            QWidget#torrentCard QLabel { color: #f1f5ff; }
            QWidget#torrentCard QLabel[statusRole="secondary"] { color: #c4cbeb; }
            QWidget#torrentCard QLabel[statusRole="status"] { color: #d8e0ff; }
            QWidget#torrentCard QLabel[statusRole="tertiary"] { color: #9da8cf; }
            QWidget#seedCard { background-color: rgba(79, 109, 245, 0.18); border: 1px solid rgba(79, 109, 245, 0.45); border-radius: 14px; }
            QWidget#seedCard:hover { border-color: rgba(124, 156, 255, 0.9); }
            QWidget#seedCard QLabel { color: #f8f9ff; }
            QWidget#seedCard QLabel[statusRole="secondary"] { color: rgba(240, 242, 255, 0.75); }
            QProgressBar[torrentProgress="true"] { background: rgba(255, 255, 255, 0.04); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; text-align: center; padding: 1px; color: #e9edff; }
            QProgressBar[torrentProgress="true"]::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6a8bff, stop:1 #4ad7b0); border-radius: 6px; }
            QMessageBox { background-color: #272a35; }
            """
        )
    else:
        # Light palette: start from the style default and tweak highlights
        app.setPalette(app.style().standardPalette())
        app.setStyleSheet(
            """
            QMainWindow, QWidget { background: #f6f7fb; color: #1f2228; }
            QToolBar { background: #ffffff; border: 0; padding: 8px 12px; spacing: 10px; }
            QToolBar QToolButton { background: transparent; color: #293042; padding: 6px 12px; border-radius: 6px; font-weight: 500; }
            QToolBar QToolButton:hover { background: rgba(79, 109, 245, 0.12); }
            QListWidget { border: 0; background: transparent; }
            QListWidget::item { margin: 2px 0; padding: 0; }
            QListWidget::item:selected { background: transparent; }
            QTabWidget::pane { border: 0; }
            QTabBar::tab { background: transparent; color: #4d5468; padding: 6px 16px; border-radius: 6px; margin: 0 6px; }
            QTabBar::tab:selected { background: rgba(82, 109, 255, 0.16); color: #1f2228; }
            QTabBar::tab:hover { background: rgba(82, 109, 255, 0.12); }
            QWidget#torrentCard { background: #ffffff; border: 1px solid #e2e5ee; border-radius: 12px; }
            QWidget#torrentCard:hover { border-color: #526dff; box-shadow: 0 6px 18px rgba(82, 109, 255, 0.18); }
            QWidget#torrentCard QLabel { color: #1f2228; }
            QWidget#torrentCard QLabel[statusRole="secondary"] { color: #4d5468; }
            QWidget#torrentCard QLabel[statusRole="status"] { color: #2c4bcc; }
            QWidget#torrentCard QLabel[statusRole="tertiary"] { color: #6b7285; }
            QWidget#seedCard { background: #ffffff; border: 1px solid #e2e5ee; border-radius: 12px; }
            QWidget#seedCard:hover { border-color: #526dff; box-shadow: 0 6px 18px rgba(82, 109, 255, 0.12); }
            QWidget#seedCard QLabel { color: #1f2228; }
            QWidget#seedCard QLabel[statusRole="secondary"] { color: #4d5468; }
            QProgressBar[torrentProgress="true"] { background: #eef1f8; border: 1px solid #d9deec; border-radius: 8px; text-align: center; padding: 1px; color: #1f2228; }
            QProgressBar[torrentProgress="true"]::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6a8bff, stop:1 #4ad7b0); border-radius: 6px; }
            QScrollBar:vertical { background: transparent; width: 12px; margin: 10px 0; }
            QScrollBar::handle:vertical { background: rgba(82, 109, 255, 0.35); border-radius: 6px; min-height: 24px; }
            QScrollBar:horizontal { background: transparent; height: 12px; margin: 0 10px; }
            QScrollBar::handle:horizontal { background: rgba(82, 109, 255, 0.35); border-radius: 6px; min-width: 24px; }
            QScrollBar::add-line, QScrollBar::sub-line { width: 0; height: 0; }
            QPushButton { border: 1px solid #d9deec; background: white; padding: 7px 16px; border-radius: 6px; color: #1f2228; }
            QPushButton:hover { background: rgba(79, 109, 245, 0.12); border-color: rgba(79, 109, 245, 0.3); }
            QLineEdit, QComboBox, QSpinBox { background: white; border: 1px solid #d9deec; border-radius: 6px; padding: 6px 8px; color: #1f2228; }
            """
        )

ICON_DIRECTORY = os.path.join(os.path.dirname(__file__), 'icons')
def calculate_piece_hash(data):
    """Calculate the SHA1 hash of a data chunk."""
    hasher = hashlib.sha1()
    hasher.update(data)
    return hasher.digest()

def create_torrent(file_path, torrent_path):
    """Create a torrent file from the specified file."""
    # Ensure the file exists
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    # Set piece length (512 KB for standard torrents)
    piece_length = 524288  # 512 KB
    pieces = b""

    # Read the file and compute hashes for each piece
    with open(file_path, 'rb') as f:
        while True:
            piece = f.read(piece_length)
            if not piece:
                break
            # Concatenate the SHA-1 hash of each piece
            pieces += calculate_piece_hash(piece)

    # Prepare the info dictionary for the torrent file
    info = {
        'name': os.path.basename(file_path),
        'piece length': piece_length,
        'pieces': pieces,
        'length': os.path.getsize(file_path),
    }

    # Prepare the torrent data dictionary
    # Default the announce URL to the local UDP tracker used for testing.
    # Change this if you want the torrent to use a different tracker.
    torrent_data = {
       #'announce': 'https://torrent.ubuntu.com/announce',
        'announce': 'udp://localhost:6881/announce',
        'info': info
    }

    # Encode the torrent file using bencode and save it
    with open(torrent_path, 'wb') as torrent_file:
        torrent_file.write(bencodepy.encode(torrent_data))

    logger.info('Torrent file created at: %s', torrent_path)
def load_icon(name: str):
    return QIcon(os.path.join(ICON_DIRECTORY, name + '.svg'))


file_icon = load_icon('file')
directory_icon = load_icon('directory')


def get_directory(directory: Optional[str]):
    return directory if directory is not None else os.getcwd()


class TorrentAddingDialog(QDialog):
    SELECTION_LABEL_FORMAT = 'Selected {} files ({})'

    def _traverse_file_tree(self, name: str, node: FileTreeNode, parent: QWidget):
        item = QTreeWidgetItem(parent)
        item.setCheckState(0, Qt.Checked)
        item.setText(0, name)
        if isinstance(node, FileInfo):
            item.setText(1, humanize_size(node.length))
            item.setIcon(0, file_icon)
            self._file_items.append((node, item))
            return

        item.setIcon(0, directory_icon)
        for name, child in node.items():
            self._traverse_file_tree(name, child, item)

    def _get_directory_browse_widget(self):
        widget = QWidget()
        hbox = QHBoxLayout(widget)
        hbox.setContentsMargins(0, 0, 0, 0)

        self._path_edit = QLineEdit(self._download_dir)
        self._path_edit.setReadOnly(True)
        hbox.addWidget(self._path_edit, 3)

        browse_button = QPushButton('Browse...')
        browse_button.clicked.connect(self._browse)
        hbox.addWidget(browse_button, 1)

        widget.setLayout(hbox)
        return widget

    def _browse(self):
        new_download_dir = QFileDialog.getExistingDirectory(self, 'Select download directory', self._download_dir)
        if not new_download_dir:
            return

        self._download_dir = new_download_dir
        self._path_edit.setText(new_download_dir)

    def __init__(self, parent: QWidget, filename: str, torrent_info: TorrentInfo,
                 control_thread: 'ControlManagerThread'):
        super().__init__(parent)
        self._torrent_info = torrent_info
        download_info = torrent_info.download_info
        self._control_thread = control_thread
        self._control = control_thread.control

        vbox = QVBoxLayout(self)

        self._download_dir = get_directory(self._control.last_download_dir)
        logger.debug('Download directory for adding dialog: %s', self._download_dir)
        vbox.addWidget(QLabel('Download directory:'))
        vbox.addWidget(self._get_directory_browse_widget())

        vbox.addWidget(QLabel('Announce URLs:'))

        url_tree = QTreeWidget()
        url_tree.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        url_tree.header().close()
        vbox.addWidget(url_tree)
        for i, tier in enumerate(torrent_info.announce_list):
            tier_item = QTreeWidgetItem(url_tree)
            tier_item.setText(0, 'Tier {}'.format(i + 1))
            for url in tier:
                url_item = QTreeWidgetItem(tier_item)
                url_item.setText(0, url)
        url_tree.expandAll()
        vbox.addWidget(url_tree, 1)

        file_tree = QTreeWidget()
        file_tree.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        file_tree.setHeaderLabels(('Name', 'Size'))
        file_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._file_items = []
        self._traverse_file_tree(download_info.suggested_name, download_info.file_tree, file_tree)
        file_tree.sortItems(0, Qt.AscendingOrder)
        file_tree.expandAll()
        file_tree.itemClicked.connect(self._update_checkboxes)
        vbox.addWidget(file_tree, 3)

        self._selection_label = QLabel(TorrentAddingDialog.SELECTION_LABEL_FORMAT.format(
            len(download_info.files), humanize_size(download_info.total_size)))
        vbox.addWidget(self._selection_label)

        self._button_box = QDialogButtonBox(self)
        self._button_box.setOrientation(Qt.Horizontal)
        self._button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        self._button_box.button(QDialogButtonBox.Ok).clicked.connect(self.submit_torrent)
        self._button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        vbox.addWidget(self._button_box)

        self.setFixedSize(450, 550)
        self.setWindowTitle('Adding "{}"'.format(filename))

    def _set_check_state_to_tree(self, item: QTreeWidgetItem, check_state: Qt.CheckState):
        for i in range(item.childCount()):
            child = item.child(i)
            child.setCheckState(0, check_state)
            self._set_check_state_to_tree(child, check_state)

    def _update_checkboxes(self, item: QTreeWidgetItem, column: int):
        if column != 0:
            return

        new_check_state = item.checkState(0)
        self._set_check_state_to_tree(item, new_check_state)

        while True:
            item = item.parent()
            if item is None:
                break

            has_checked_children = False
            has_partially_checked_children = False
            has_unchecked_children = False
            for i in range(item.childCount()):
                state = item.child(i).checkState(0)
                if state == Qt.Checked:
                    has_checked_children = True
                elif state == Qt.PartiallyChecked:
                    has_partially_checked_children = True
                else:
                    has_unchecked_children = True

            if not has_partially_checked_children and not has_unchecked_children:
                new_state = Qt.Checked
            elif has_checked_children or has_partially_checked_children:
                new_state = Qt.PartiallyChecked
            else:
                new_state = Qt.Unchecked
            item.setCheckState(0, new_state)

        self._update_selection_label()

    def _update_selection_label(self):
        selected_file_count = 0
        selected_size = 0
        for node, item in self._file_items:
            if item.checkState(0) == Qt.Checked:
                selected_file_count += 1
                selected_size += node.length

        ok_button = self._button_box.button(QDialogButtonBox.Ok)
        if not selected_file_count:
            ok_button.setEnabled(False)
            self._selection_label.setText('Nothing to download')
        else:
            ok_button.setEnabled(True)
            self._selection_label.setText(TorrentAddingDialog.SELECTION_LABEL_FORMAT.format(
                selected_file_count, humanize_size(selected_size)))

    def submit_torrent(self):
        self._torrent_info.download_dir = self._download_dir
        self._control.last_download_dir = os.path.abspath(self._download_dir)

        file_paths = []
        for node, item in self._file_items:
            if item.checkState(0) == Qt.Checked:
                file_paths.append(node.path)
        if not self._torrent_info.download_info.single_file_mode:
            self._torrent_info.download_info.select_files(file_paths, 'whitelist')

        self._control_thread.loop.call_soon_threadsafe(self._control.add, self._torrent_info)

        self.close()


class TorrentListWidgetItem(QWidget):
    _name_font = QFont('Segoe UI', 11)
    if hasattr(QFont, 'DemiBold'):
        _name_font.setWeight(QFont.DemiBold)
    else:
        _name_font.setBold(True)

    _stats_font = QFont('Segoe UI', 9)
    if hasattr(QFont, 'Normal'):
        _stats_font.setWeight(QFont.Normal)

    def __init__(self):
        super().__init__()
        self.setObjectName('torrentCard')

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(18, 16, 18, 16)
        vbox.setSpacing(10)

        self._name_label = QLabel()
        self._name_label.setFont(TorrentListWidgetItem._name_font)
        self._name_label.setWordWrap(True)
        vbox.addWidget(self._name_label)

        self._upper_status_label = QLabel()
        self._upper_status_label.setFont(TorrentListWidgetItem._stats_font)
        self._upper_status_label.setWordWrap(True)
        self._upper_status_label.setProperty('statusRole', 'secondary')
        vbox.addWidget(self._upper_status_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(14)
        self._progress_bar.setMaximum(1000)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setProperty('torrentProgress', True)
        vbox.addWidget(self._progress_bar)

        self._lower_status_label = QLabel()
        self._lower_status_label.setFont(TorrentListWidgetItem._stats_font)
        self._lower_status_label.setWordWrap(True)
        self._lower_status_label.setProperty('statusRole', 'status')
        vbox.addWidget(self._lower_status_label)

        self._state = None
        self._waiting_control_action = False

    @property
    def state(self) -> TorrentState:
        return self._state

    @state.setter
    def state(self, state: TorrentState):
        self._state = state
        self._update()

    @property
    def waiting_control_action(self) -> bool:
        return self._waiting_control_action

    @waiting_control_action.setter
    def waiting_control_action(self, value: bool):
        self._waiting_control_action = value
        self._update()

    def _update(self):
        state = self._state

        self._name_label.setText(state.suggested_name)  # FIXME: Avoid XSS in all setText calls

        # Clamp progress and compute percent for display
        if state.selected_size:
            progress = state.downloaded_size / state.selected_size
        else:
            progress = 0.0
        progress = max(0.0, min(1.0, progress))
        percent = progress * 100.0

        # Upper line: precise progress and total, plus ratio
        if state.downloaded_size < state.selected_size:
            upper = '{} of {}  ·  {:.1f}%  ·  Ratio: {:.2f}'.format(
                humanize_size(state.downloaded_size), humanize_size(state.selected_size), percent, state.ratio)
        else:
            upper = '{}  ·  100%  ·  Ratio: {:.2f}'.format(humanize_size(state.selected_size), state.ratio)
        self._upper_status_label.setText(upper)

        # Progress bar value and formatted percent text
        self._progress_bar.setValue(int(round(progress * 1000)))
        self._progress_bar.setFormat('{:.1f}%'.format(percent))

        if self.waiting_control_action:
            status_text = 'Waiting'
        # elif state.paused:
        #     status_text = 'Paused'
        elif state.complete:
            # Clear and friendly seeding indicator
            status_text = 'Seeding'
            if state.total_peer_count:
                status_text += ' to {} peer{}'.format(state.total_peer_count, '' if state.total_peer_count == 1 else 's')
            if state.upload_speed:
                status_text += '  ·  {}'.format(humanize_speed(state.upload_speed))
        else:
            status_text = 'Downloading from {} of {} peers'.format(
                state.downloading_peer_count, state.total_peer_count)
            if state.download_speed:
                status_text += '  ·  {}'.format(humanize_speed(state.download_speed))
            eta_seconds = state.eta_seconds
            if eta_seconds is not None:
                status_text += '  ·  {} remaining'.format(humanize_time(eta_seconds))
        self._lower_status_label.setText(status_text)


class TorrentListWidget(QListWidget):
    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setAlternatingRowColors(True)
        self.setUniformItemSizes(True)

        self.setAcceptDrops(True)

    def drag_handler(self, event: QDropEvent, drop: bool=False):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()

            if drop:
                self.files_dropped.emit([url.toLocalFile() for url in event.mimeData().urls()])
        else:
            event.ignore()

    dragEnterEvent = drag_handler
    dragMoveEvent = drag_handler
    dropEvent = partialmethod(drag_handler, drop=True)


class MainWindow(QMainWindow):
    def __init__(self, control_thread: 'ControlManagerThread'):
        super().__init__()

        self._control_thread = control_thread
        control = control_thread.control

        # Initialize QTabWidget and set tabs on top
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)  # Set tabs at the top
        self.tabs.setDocumentMode(True)
        self.setCentralWidget(self.tabs)

        # Download tab
        self.download_tab = QWidget()
        self._init_download_tab()
        self.tabs.addTab(self.download_tab, "Download")

        # Seed tab
        self.seed_tab = QWidget()
        self._init_seed_tab()
        self.tabs.addTab(self.seed_tab, "Seed")

        # Window settings
        self.setMinimumSize(920, 560)
        self.resize(1100, 680)
        self.setWindowTitle('BitTorrent Client')

        # Connect control events to MainWindow methods
        control_thread.error_happened.connect(self._error_happened)
        control.torrents_suggested.connect(self.add_torrent_files)
        control.torrent_added.connect(self._add_torrent_item)
        control.torrent_changed.connect(self._update_torrent_item)
        control.torrent_removed.connect(self._remove_torrent_item)

        self.show()
    def _init_download_tab(self):
        download_layout = QVBoxLayout(self.download_tab)
        download_layout.setContentsMargins(18, 18, 18, 18)
        download_layout.setSpacing(16)

        # Create a horizontal layout for the toolbar
        toolbar = self._create_toolbar()
        download_layout.addWidget(toolbar)  # Add toolbar directly to vertical layout

        # Set up the torrent list widget
        self._list_widget = TorrentListWidget()
        self._list_widget.setSpacing(14)
        self._list_widget.itemSelectionChanged.connect(self._update_control_action_state)
        self._list_widget.files_dropped.connect(self.add_torrent_files)
        self._torrent_to_item = {}  # Dictionary to track torrents in list

        # Add the list widget to the layout and set it to fill remaining space
        download_layout.addWidget(self._list_widget, stretch=1)

    def _init_seed_tab(self):
        # Main layout for the Seed tab, with similar adjustments for full space usage
        seed_layout = QVBoxLayout(self.seed_tab)
        seed_layout.setContentsMargins(18, 18, 18, 18)
        seed_layout.setSpacing(16)

        # add toolbar
        toolbar = self._create_toolbar_seed()
        seed_layout.addWidget(toolbar)

        self.seeded_files_list = QListWidget()
        self.seeded_files_list.setObjectName('seedList')
        self.seeded_files_list.setIconSize(QSize(32, 32))  # Increase icon size
        self.seeded_files_list.setSpacing(14)
        self.seeded_files_list.itemSelectionChanged.connect(self.update_remove_action_state)
        seed_layout.addWidget(self.seeded_files_list)

    def _create_toolbar(self):
        # Create a toolbar with actions
        toolbar = QToolBar('Actions')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))

        # Setup actions for toolbar
        self._add_action = toolbar.addAction(load_icon('add'), 'Add')
        self._add_action.triggered.connect(self._add_torrents_triggered)

        self._pause_action = toolbar.addAction(load_icon('pause'), 'Pause')
        self._pause_action.setEnabled(False)
        self._pause_action.triggered.connect(partial(self._control_action_triggered, self._control_thread.control.pause))

        self._resume_action = toolbar.addAction(load_icon('resume'), 'Resume')
        self._resume_action.setEnabled(False)
        self._resume_action.triggered.connect(partial(self._control_action_triggered, self._control_thread.control.resume))

        self._remove_action = toolbar.addAction(load_icon('remove'), 'Remove')
        self._remove_action.setEnabled(False)
        self._remove_action.triggered.connect(partial(self._control_action_triggered, self._control_thread.control.remove))

        return toolbar
    
    def _create_toolbar_seed(self):
        # Create a toolbar with actions
        toolbar = QToolBar('Actions')
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))

        # Setup actions for toolbar
        self._add_action_seed = toolbar.addAction(load_icon('add'), 'Add')
        self._add_action_seed.triggered.connect(self.add_files_seed)

        
        self._remove_action_seed = toolbar.addAction(load_icon('remove'), 'Remove')
        self._remove_action_seed.setEnabled(False)
        self._remove_action_seed.triggered.connect(self.remove_selected_item)

        # self.seeded_files_list.itemSelectionChanged.connect(self.update_remove_action_state)

        return toolbar
    def update_remove_action_state(self):
        # Enable or disable the remove action based on selection
        has_selection = len(self.seeded_files_list.selectedItems()) > 0
        self._remove_action_seed.setEnabled(has_selection)

    def remove_selected_item(self):
        # Remove the selected item from the seeded files list
        selected_items = self.seeded_files_list.selectedItems()
        if selected_items:
            for item in selected_items:
                row = self.seeded_files_list.row(item)
                self.seeded_files_list.takeItem(row)
        self.update_remove_action_state()

    def add_files_seed(self):
        # Open file dialog to select files to seed
        file_dialog = QFileDialog()
        files, _ = file_dialog.getOpenFileNames(self.seed_tab, "Select Files to Seed")

        if files:
            for file in files:
                # Convert file to torrent (this should call your method to create torrents)
                torrent_file = self.convert_to_torrent(file)
                if torrent_file:
                    self._add_torrent_item_seed(torrent_file)  # Add to seeded files list
                    QMessageBox.information(self.seed_tab, "Success", f"File added: {torrent_file}")
                else:
                    QMessageBox.warning(self.seed_tab, "Error", f"Failed to create torrent for {file}")

    def _add_torrent_item_seed(self, torrent_file):
        # Create a QListWidgetItem for the list widget
        item = QListWidgetItem()

        # Set the icon with a larger size and add spacing
        item.setIcon(load_icon('file'))
        item.setSizeHint(QSize(140, 72))  # Adjust item size for better appearance

        # Create a main widget to hold the icon, title, and description
        item_widget = QWidget()
        item_widget.setObjectName('seedCard')
        main_layout = QHBoxLayout(item_widget)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(14)

        icon_label = QLabel()
        icon_label.setPixmap(load_icon('file').pixmap(28, 28))
        icon_label.setAlignment(Qt.AlignTop)
        main_layout.addWidget(icon_label)

        # Create a sub-layout for title and description
        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)

        # Title label for the torrent name
        title_label = QLabel(os.path.basename(torrent_file))
        title_font = QFont('Segoe UI', 10)
        if hasattr(QFont, 'DemiBold'):
            title_font.setWeight(QFont.DemiBold)
        else:
            title_font.setBold(True)
        title_label.setFont(title_font)

        # Description label for additional details
        description_label = QLabel('Ready to seed')
        description_label.setFont(QFont('Segoe UI', 9))
        description_label.setProperty('statusRole', 'secondary')

        # Add title and description to the text layout
        text_layout.addWidget(title_label)
        text_layout.addWidget(description_label)

        # Add the icon and text layouts to the main layout
        main_layout.addLayout(text_layout)
        main_layout.addStretch()

        # Set the widget as the list item's widget
        self.seeded_files_list.addItem(item)
        self.seeded_files_list.setItemWidget(item, item_widget)

    def convert_to_torrent(self, file_path):
        # Open a file dialog to specify where to save the torrent file
        save_file_dialog = QFileDialog(self.seed_tab)
        save_file_path, _ = save_file_dialog.getSaveFileName(self.seed_tab, "Save Torrent File", "", "Torrent Files (*.torrent)")

        if save_file_path:
            # Simulate torrent file creation logic
            try:
                create_torrent(file_path, save_file_path)

                # After creating the .torrent, automatically add it to the control manager
                # so the client will start seeding (if the data file exists at download_dir).
                try:
                    # Use the directory of the original file as download_dir so the client
                    # will treat the file as present and start seeding.
                    download_dir = os.path.abspath(os.path.dirname(file_path))
                    torrent_info = TorrentInfo.from_file(save_file_path, download_dir=download_dir)

                    # Schedule the add on the control thread's loop
                    self._control_thread.loop.call_soon_threadsafe(self._control_thread.control.add, torrent_info)
                    QMessageBox.information(self.seed_tab, "Seeding", f"Torrent created and added for seeding: {save_file_path}")
                except Exception as add_err:
                    # If adding fails, still return the path but warn the user
                    QMessageBox.warning(self.seed_tab, "Warning", f"Torrent created but failed to start seeding: {add_err}")

                return save_file_path  # Return the path of the created torrent file
            except Exception as e:
                logger.exception('Error creating torrent file: %s', e)
                return None
        return None
    # def calculate_file_hash(self,file_path):
    #     """Calculate the SHA1 hash of the given file."""
    #     hasher = hashlib.sha1()
    #     with open(file_path, 'rb') as f:
    #         while chunk := f.read(8192):
    #             hasher.update(chunk)
    #     return hasher.digest()
    # def create_torrent(self,file_path, torrent_path):
    #     """Create a torrent file from the specified file."""
    #     # Ensure the file exists
    #     if not os.path.isfile(file_path):
    #         raise FileNotFoundError(f"The file {file_path} does not exist.")

    #     # Prepare torrent metadata
    #     info = {
    #         'name': os.path.basename(file_path),
    #         'piece length': 524288,  # 512 KB piece size
    #         'pieces': b'',
    #         'length': os.path.getsize(file_path),
    #         'files': [
    #             {
    #                 'length': os.path.getsize(file_path),
    #                 'path': [os.path.basename(file_path)]  # Just the filename for single file torrents
    #             }
    #         ]
    #     }

    #     # Read the file and generate the 'pieces' field
    #     with open(file_path, 'rb') as f:
    #         while True:
    #             piece = f.read(info['piece length'])
    #             if not piece:
    #                 break
    #             info['pieces'] += self.calculate_file_hash(piece)

    #     # Create the final torrent structure
    #     torrent_data = {
    #         'announce': 'http://tracker.example.com/announce',  # Replace with your tracker URL
    #         'info': info
    #     }

    #     # Encode the torrent file using bencode
    #     with open(torrent_path, 'wb') as torrent_file:
    #         torrent_file.write(bencodepy.encode(torrent_data))

    #     print(f"Torrent file created at: {torrent_path}")
    def _add_torrent_item(self, state: TorrentState):
        widget = TorrentListWidgetItem()
        widget.state = state

        item = QListWidgetItem()
        item.setIcon(file_icon if state.single_file_mode else directory_icon)
        item.setSizeHint(widget.sizeHint())
        item.setData(Qt.UserRole, state.info_hash)

        items_upper = 0
        for i in range(self._list_widget.count()):
            prev_item = self._list_widget.item(i)
            if self._list_widget.itemWidget(prev_item).state.suggested_name > state.suggested_name:
                break
            items_upper += 1
        self._list_widget.insertItem(items_upper, item)

        self._list_widget.setItemWidget(item, widget)
        self._torrent_to_item[state.info_hash] = item

    def _update_torrent_item(self, state: TorrentState):
        if state.info_hash not in self._torrent_to_item:
            return

        widget = self._list_widget.itemWidget(self._torrent_to_item[state.info_hash])
        if widget.state.paused != state.paused:
            widget.waiting_control_action = False
        widget.state = state

        self._update_control_action_state()

    def _remove_torrent_item(self, info_hash: bytes):
        item = self._torrent_to_item[info_hash]
        self._list_widget.takeItem(self._list_widget.row(item))
        del self._torrent_to_item[info_hash]

        self._update_control_action_state()

    def _update_control_action_state(self):
        self._pause_action.setEnabled(False)
        self._resume_action.setEnabled(False)
        self._remove_action.setEnabled(False)
        for item in self._list_widget.selectedItems():
            widget = self._list_widget.itemWidget(item)
            if widget.waiting_control_action:
                continue

            if widget.state.paused:
                self._resume_action.setEnabled(True)
            else:
                self._pause_action.setEnabled(True)
            self._remove_action.setEnabled(True)

    def _error_happened(self, description: str, err: Exception):
        QMessageBox.critical(self, description, str(err))

    def add_torrent_files(self, paths: List[str]):
        for path in paths:
            try:
                torrent_info = TorrentInfo.from_file(path, download_dir=None)
                self._control_thread.control.last_torrent_dir = os.path.abspath(os.path.dirname(path))

                if torrent_info.download_info.info_hash in self._torrent_to_item:
                    raise ValueError('This torrent is already added')
            except Exception as err:
                self._error_happened('Failed to add "{}"'.format(path), err)
                continue

            TorrentAddingDialog(self, path, torrent_info, self._control_thread).exec()

    def _add_torrents_triggered(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'Add torrents', self._control_thread.control.last_torrent_dir,
                                                'Torrent file (*.torrent);;All files (*)')
        self.add_torrent_files(paths)

    @staticmethod
    async def _invoke_control_action(action, info_hash: bytes):
        result = action(info_hash)
        if asyncio.iscoroutine(result):
            await result

    def _control_action_triggered(self, action):
        for item in self._list_widget.selectedItems():
            widget = self._list_widget.itemWidget(item)
            if widget.waiting_control_action:
                continue

            info_hash = item.data(Qt.UserRole)
            future = asyncio.run_coroutine_threadsafe(
                MainWindow._invoke_control_action(action, info_hash),
                self._control_thread.loop
            )

            def _handle_completion(fut, info_hash=info_hash):
                exc = None
                try:
                    fut.result()
                except Exception as err:  # noqa: BLE001
                    exc = err

                def _update_ui():
                    item = self._torrent_to_item.get(info_hash)
                    if item is not None:
                        widget = self._list_widget.itemWidget(item)
                        if widget is not None:
                            widget.waiting_control_action = False

                    if exc is not None:
                        QMessageBox.critical(self, 'Action failed', str(exc))

                    self._update_control_action_state()

                QTimer.singleShot(0, _update_ui)

            future.add_done_callback(_handle_completion)
            widget.waiting_control_action = True

        self._update_control_action_state()



class ControlManagerThread(QThread):
    error_happened = pyqtSignal(str, Exception)

    def __init__(self):
        super().__init__()

        self._loop = None  # type: asyncio.AbstractEventLoop
        self._control = ControlManager()
        self._control_server = ControlServer(self._control, None)
        self._stopping = False

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    @property
    def control(self) -> ControlManager:
        return self._control

    def run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        with closing(self._loop):
            self._loop.run_until_complete(self._control.start())
            self._loop.run_until_complete(self._control_server.start())

            try:
                self._control.load_state()
            except Exception as err:
                self.error_happened.emit('Failed to load program state', err)
            self._control.invoke_state_dumps()

            self._loop.run_forever()

    def stop(self):
        if self._stopping:
            return
        self._stopping = True

        stop_fut = asyncio.run_coroutine_threadsafe(asyncio.wait([self._control_server.stop(), self._control.stop()]),
                                                    self._loop)
        stop_fut.add_done_callback(lambda fut: self._loop.stop())

        self.wait()


def suggest_torrents(manager: ControlManager, filenames: List[str]):
    manager.torrents_suggested.emit(filenames)


async def find_another_daemon(filenames: List[str]) -> bool:
    try:
        async with ControlClient() as client:
            if filenames:
                await client.execute(partial(suggest_torrents, filenames=filenames))
        return True
    except RuntimeError:
        return False


def main():
    parser = argparse.ArgumentParser(description='A prototype of BitTorrent client (GUI)')
    parser.add_argument('--debug', action='store_true', help='Show debug messages')
    parser.add_argument('--theme', choices=['auto', 'dark', 'light'], default='dark', help='GUI theme')
    parser.add_argument('filenames', nargs='*', help='Torrent file names')
    args = parser.parse_args()

    # Configure global logging format (short logger names and milliseconds)
    configure_logging(args.debug)

    # If user didn't request debug mode, suppress INFO/DEBUG to keep UI quiet
    if not args.debug:
        logging.disable(logging.INFO)

    app = QApplication(sys.argv)
    app.setWindowIcon(load_icon('logo'))

    # Apply modern theme
    chosen_theme = 'dark' if args.theme == 'auto' else args.theme
    apply_modern_theme(app, chosen_theme)

    # Allow skipping the single-instance/daemon check by setting the env var
    # TORRENT_GUI_ALLOW_MULTIPLE=1. This is useful for local testing when
    # you need to run multiple GUI instances on the same machine.
    skip_daemon_check = os.environ.get('TORRENT_GUI_ALLOW_MULTIPLE') == '1'

    with closing(asyncio.get_event_loop()) as loop:
        if not skip_daemon_check and loop.run_until_complete(find_another_daemon(args.filenames)):
            if not args.filenames:
                QMessageBox.critical(None, 'Failed to start', 'Another program instance is already running')
            return

    control_thread = ControlManagerThread()
    main_window = MainWindow(control_thread)

    control_thread.start()
    app.lastWindowClosed.connect(control_thread.stop)

    main_window.add_torrent_files(args.filenames)

    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
