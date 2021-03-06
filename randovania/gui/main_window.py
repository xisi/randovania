import json
import os
from pathlib import Path
from typing import Optional

from PySide2 import QtCore
from PySide2.QtCore import QUrl, Signal
from PySide2.QtGui import QDesktopServices
from PySide2.QtWidgets import QMainWindow, QAction

from randovania import VERSION
from randovania.games.prime import default_data
from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.common_qt_lib import prompt_user_for_seed_log, prompt_user_for_database_file, \
    set_default_window_icon
from randovania.gui.data_editor import DataEditorWindow
from randovania.gui.iso_management_window import ISOManagementWindow
from randovania.gui.item_quantities_window import ItemQuantitiesWindow
from randovania.gui.logic_settings_window import LogicSettingsWindow
from randovania.gui.mainwindow_ui import Ui_MainWindow
from randovania.gui.seed_details_window import SeedDetailsWindow
from randovania.gui.tab_service import TabService
from randovania.gui.tracker_window import TrackerWindow
from randovania.interface_common.options import Options
from randovania.interface_common.update_checker import get_latest_version
from randovania.resolver import debug


class MainWindow(QMainWindow, Ui_MainWindow, TabService, BackgroundTaskMixin):
    newer_version_signal = Signal(str, str)
    options_changed_signal = Signal()
    is_preview_mode: bool = False

    menu_new_version: Optional[QAction] = None
    _current_version_url: Optional[str] = None
    _options: Options

    @property
    def _tab_widget(self):
        return self.tabWidget

    def __init__(self, options: Options, preview: bool):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Randovania {}".format(VERSION))
        self.is_preview_mode = preview
        self.setAcceptDrops(True)
        set_default_window_icon(self)

        if preview:
            debug._DEBUG_LEVEL = 2

        # Signals
        self.newer_version_signal.connect(self.display_new_version)
        self.background_tasks_button_lock_signal.connect(self.enable_buttons_with_background_tasks)
        self.progress_update_signal.connect(self.update_progress)
        self.stop_background_process_button.clicked.connect(self.stop_background_process)
        self.options_changed_signal.connect(self.on_options_changed)

        # Menu Bar
        self.menu_action_data_visualizer.triggered.connect(self._open_data_visualizer)
        self.menu_action_existing_seed_details.triggered.connect(self._open_existing_seed_details)
        self.menu_action_tracker.triggered.connect(self._open_tracker)
        self.menu_action_edit_new_database.triggered.connect(self._open_data_editor_default)
        self.menu_action_edit_existing_database.triggered.connect(self._open_data_editor_prompt)

        _translate = QtCore.QCoreApplication.translate
        self.tabs = []

        self.tab_windows = [
            (ISOManagementWindow, "ROM Settings"),
            (LogicSettingsWindow, "Logic Settings"),
            (ItemQuantitiesWindow, "Item Quantities"),
        ]

        for i, tab in enumerate(self.tab_windows):
            self.windows.append(tab[0](self, self, options))
            self.tabs.append(self.windows[i].centralWidget)
            self.tabWidget.insertTab(i, self.tabs[i], _translate("MainWindow", tab[1]))

        # Setting this event only now, so all options changed trigger only once
        options.on_options_changed = self.options_changed_signal.emit
        self._options = options
        self.on_options_changed()

        self.tabWidget.setCurrentIndex(0)
        get_latest_version(self.newer_version_signal.emit)

    def closeEvent(self, event):
        self.stop_background_process()
        for window in self.windows:
            window.closeEvent(event)
        super().closeEvent(event)

    def dragEnterEvent(self, event):
        for url in event.mimeData().urls():
            if os.path.splitext(url.toLocalFile())[1] == ".iso":
                event.acceptProposedAction()
                return

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            iso_path = url.toLocalFile()
            if os.path.splitext(iso_path)[1] == ".iso":
                self.get_tab(ISOManagementWindow).load_game(Path(iso_path))
                return

    def display_new_version(self, new_version: str, new_version_url: str):
        if self.menu_new_version is None:
            self.menu_new_version = QAction("", self)
            self.menu_new_version.triggered.connect(self.open_version_link)
            self.menu_bar.addAction(self.menu_new_version)

        self.menu_new_version.setText("New version available: {}".format(new_version))
        self._current_version_url = new_version_url

    def open_version_link(self):
        if self._current_version_url is None:
            raise RuntimeError("Called open_version_link, but _current_version_url is None")

        QDesktopServices.openUrl(QUrl(self._current_version_url))

    # Options
    def on_options_changed(self):
        for window in self.windows:
            window.on_options_changed()

    # Menu Actions
    def _open_data_visualizer(self):
        self._data_visualizer = DataEditorWindow(default_data.decode_default_prime2(), False)
        self._data_visualizer.show()

    def _open_data_editor_default(self):
        self._data_editor = DataEditorWindow(default_data.decode_default_prime2(), True)
        self._data_editor.show()

    def _open_data_editor_prompt(self):
        database_path = prompt_user_for_database_file(self)
        if database_path is None:
            return

        with database_path.open("r") as database_file:
            self._data_editor = DataEditorWindow(json.load(database_file), True)
            self._data_editor.show()

    def _open_existing_seed_details(self):
        json_path = prompt_user_for_seed_log(self)
        if json_path is None:
            return

        self._seed_details = SeedDetailsWindow(json_path)
        self._seed_details.show()

    def _open_tracker(self):
        self._tracker = TrackerWindow(self._options.layout_configuration)
        self._tracker.show()

    # Background Process

    def enable_buttons_with_background_tasks(self, value: bool):
        self.stop_background_process_button.setEnabled(not value)

    def update_progress(self, message: str, percentage: int):
        self.progress_label.setText(message)
        if "Aborted" in message:
            percentage = 0
        if percentage >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percentage)
        else:
            self.progress_bar.setRange(0, 0)
