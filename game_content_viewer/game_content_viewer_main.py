"""A PySide6 UI window for viewing Unreal 5 project assets stored in a SQLite database."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .game_content_utils import config_file, convert_db_to_csv
from .game_content_utils import db_operations as dbo
from .remote_utils import send_to_unreal_port

# file paths
SCANNER_SCRIPT = config_file.SCANNER_SCRIPT
REFRESH_THUMBNAILS_SCRIPT = config_file.REFRESH_THUMBNAILS_SCRIPT
WNDW_ICON_PATH = config_file.WNDW_ICON_PATH
LAUNCH_UE_SCRIPT = config_file.LAUNCH_UE_SCRIPT

# save file defaults
JSON_SAVE_FILE = config_file.JSON_SAVE_FILE
THUMBNAILS_SAVE_FOLDER = config_file.THUMBNAILS_SAVE_FOLDER
UE_FOLDER_PATH_KEY = config_file.UE_FOLDER_PATH_KEY
UE_FOLDER_PATH_VALUE = config_file.load_saver()
DATA_FOLDER_PATH = config_file.DATA_FOLDER_PATH

# database defaults
TABLE_NAME = config_file.TABLE_NAME
SUMMARY_TABLE_NAME = config_file.SUMMARY_TABLE_NAME
DB_FILE_PATH = config_file.DB_FILE_PATH


class GameContentModel(QAbstractTableModel):
    """A table model for displaying Unreal project asset data from a sqlite database."""

    def __init__(self, data: list[tuple], column_names: list[str]) -> None:
        """Initializes the table model with sqlite data and column names.

        Args:
            data: List of tuples containing asset data from the sqlite database.
            column_names: List of column names from the database cursor description.

        """
        super().__init__()
        self._data = data
        self._columns = column_names

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        """Returns the number of rows in the model.

        Args:
            parent: The parent index, ignored for a flat table model.

        Returns:
            The total number of rows based on the data length.

        """
        return len(self._data)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        """Returns the number of columns in the model.

        Args:
            parent: The parent index, ignored for a flat table model.

        Returns:
            The total number of columns based on the column names length.

        """
        return len(self._columns)

    def data(
        self,
        index: QModelIndex,
        role: Qt.ItemDataRole = Qt.DisplayRole,
    ) -> str | float | int | None:
        """Returns the data for a given index and role.

        Args:
            index: The model index specifying the row and column.
            role: The data role, such as DisplayRole or UserRole for sorting.

        Returns:
            The data value as a string for DisplayRole, a numeric or lowercase string
            for UserRole, or None if the index is invalid or the role is unsupported.

        """
        if not index.isValid():
            return None

        value = self._data[index.row()][index.column()]

        if role == Qt.DisplayRole:
            return str(value)
        if role == Qt.UserRole:
            try:
                if isinstance(value, (int, float)):
                    return value
                if value and str(value).replace(".", "", 1).isdigit():
                    return float(value)
            except (ValueError, TypeError):
                pass
            return str(value).lower()
        return None

    # column and row titles
    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: Qt.ItemDataRole = Qt.DisplayRole,
    ) -> str | None:
        """Returns the header data for a given section and orientation.

        Args:
            section: The row or column index.
            orientation: The header orientation (Horizontal or Vertical).
            role: The data role, typically DisplayRole.

        Returns:
            The column name or row number as a string for DisplayRole, or None for
            other roles.

        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._columns[section])
            if orientation == Qt.Vertical:
                return str(section + 1)  # start at 1 not 0, to match id
        return None


class GameContentViewer(QWidget):
    """View a spreadsheet of all the assets in an Unreal project,
    or just the assets from a specific folder.
    This class gathers the asset data and displays it in a ui window.
    """

    def __init__(self) -> None:
        """Initialize qt ui."""
        super().__init__()
        # store the currently selected path
        self.current_file_path = None

        self.setWindowTitle("UE 5 Game Content Viewer")
        self.setWindowIcon(QIcon(WNDW_ICON_PATH))
        self.resize(900, 500)

        # main layout
        main_layout = QVBoxLayout(self)

        # top toolbar with refresh button
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        # left side of top toolbar
        self.column_filter = QComboBox()
        self.column_filter.setMaximumWidth(150)
        self.column_filter.currentIndexChanged.connect(
            lambda: self.filter_table(self.search_bar.text()),
        )
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search by asset_name...")
        self.search_bar.textChanged.connect(self.filter_table)
        self.search_bar.setMaximumWidth(230)
        self.load_db_btn = QPushButton(" Reload Spreadsheet ")
        self.load_db_btn.clicked.connect(self.load_database)
        self.status_label = QLabel("Database Loaded.")
        self.status_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.status_label.setMinimumWidth(125)

        # right side of top toolbar
        self.ue_folder_text = QTextEdit(UE_FOLDER_PATH_VALUE)
        self.ue_folder_text.setLineWrapMode(QTextEdit.NoWrap)
        self.ue_folder_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ue_folder_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.ue_folder_text.setFixedHeight(25)
        self.refresh_db_btn = QPushButton(" Refresh Database ")
        self.refresh_db_btn.clicked.connect(self.refresh_database)
        self.refresh_thumbnails_btn = QPushButton(" Refresh Thumbnails ")
        self.refresh_thumbnails_btn.clicked.connect(self.refresh_thumbnails)
        self.thumbnail_folder_btn = QPushButton("🗀")
        self.thumbnail_folder_btn.clicked.connect(lambda: self.open_folder(THUMBNAILS_SAVE_FOLDER))
        self.thumbnail_folder_btn.setFixedWidth(40)
        self.launch_ue_btn = QPushButton("UE5")
        self.launch_ue_btn.clicked.connect(self.launch_ue)
        self.launch_ue_btn.setFixedWidth(40)

        # add widgets to toolbar
        toolbar_layout.addWidget(self.column_filter, 0)
        toolbar_layout.addWidget(self.search_bar, 1)
        toolbar_layout.addWidget(self.load_db_btn, 0)
        toolbar_layout.addWidget(self.status_label, 1)
        toolbar_layout.addWidget(self.ue_folder_text, 0)
        toolbar_layout.addWidget(self.refresh_db_btn, 0)
        toolbar_layout.addWidget(self.refresh_thumbnails_btn, 0)
        toolbar_layout.addWidget(self.thumbnail_folder_btn, 0)
        toolbar_layout.addWidget(self.launch_ue_btn, 0)

        toolbar.setFixedHeight(25)
        # add toolbar to main layout
        main_layout.addWidget(toolbar)

        # create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)

        # Left side: Table view
        self.table = QTableView()
        splitter.addWidget(self.table)

        # right side: vertical layout with info/ thumbnail windows
        # and open folder button
        right_panel = QSplitter(Qt.Vertical)
        right_layout = QVBoxLayout(right_panel)

        # info window
        self.info_window = QTextEdit("Select a row...")
        self.info_window.setReadOnly(True)
        self.info_window.setLineWrapMode(QTextEdit.NoWrap)
        right_layout.addWidget(self.info_window)

        # thumbnail window
        self.thumbnail_window = QLabel("No thumbnail available.")
        self.thumbnail_window.setAlignment(Qt.AlignCenter)
        self.thumbnail_window.setMinimumHeight(50)
        right_layout.addWidget(self.thumbnail_window)

        # open folder button
        self.open_folder_btn = QPushButton("Open File Location")
        self.open_folder_btn.clicked.connect(
            lambda: self.open_folder(Path(self.current_file_path).parent),
        )
        self.open_folder_btn.setEnabled(False)
        right_layout.addWidget(self.open_folder_btn)

        # add right panel to splitter
        splitter.addWidget(right_panel)

        # set initial splitter window sizes (60% table, 40% info)
        splitter.setSizes([600 * 0.6, 600 * 0.4])

        main_layout.addWidget(splitter)

        # create summary bar at the bottom
        summary_bar = QFrame()
        summary_bar.setFixedHeight(30)
        summary_bar_layout = QHBoxLayout(summary_bar)
        summary_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.summary_label = QTextEdit()
        self.summary_label.setReadOnly(True)
        self.summary_label.setLineWrapMode(QTextEdit.NoWrap)
        self.summary_label.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.summary_label.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.output_csv_btn = QPushButton(" Output CSV ")
        self.output_csv_btn.clicked.connect(self.output_csv_file)

        summary_bar_layout.addWidget(self.output_csv_btn)
        summary_bar_layout.addWidget(self.summary_label)

        main_layout.addWidget(summary_bar)

        # load table data into ui spreadsheet
        try:
            self.load_database()
        except sqlite3.OperationalError as e:
            print(f"{e}")

    def load_database(self) -> None:
        """Load data from the sqlite database file."""
        conn = sqlite3.connect(DB_FILE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM game_content")
        column_names = [description[0] for description in cursor.description]
        data = cursor.fetchall()
        conn.close()

        source_model = GameContentModel(data, column_names)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(source_model)
        self.proxy_model.setSortRole(Qt.UserRole)  # sort numbers as numbers

        self.table.setModel(self.proxy_model)
        self.table.setSortingEnabled(True)  # enable sorting when column clicked
        # Set initial sort by id (column 0)
        self.table.sortByColumn(0, Qt.AscendingOrder)
        # hide the id column
        self.table.hideColumn(0)

        # populate column dropdown
        self.populate_columns_dropdown()

        # update info window on new selection
        self.table.selectionModel().selectionChanged.connect(self.update_info_window)

        # update status
        self.status_label.setText(f"Database Loaded: {len(data)} records.")

        self.load_summary_table_info()
        self.save_settings()

    def refresh_database(self) -> None:
        """Refresh Unreal asset data for sqlite file. (game_content.db)
        Send game_content_scanner.py script to Unreal over port.
        Unreal must be open with port activated.
        """
        self.save_settings()
        send_to_unreal_port.send(SCANNER_SCRIPT)

    def refresh_thumbnails(self) -> None:
        """Refresh asset thumbnails.
        Send game_content_thumbnails.py script to Unreal over port.
        Unreal must be open with port activated.
        """
        self.save_settings()
        send_to_unreal_port.send(REFRESH_THUMBNAILS_SCRIPT)

    def update_info_window(self) -> None:
        """Update the info window with details about the selected item/ row.
        This includes the "tag_values" column data parsed out.
        The info window is the right window displaying selected row info vertically.
        """
        indexes = self.table.selectionModel().selectedIndexes()  # get selected

        if not indexes:  # if no row selected
            self.info_window.setText("Select a row...")
            self.thumbnail_window.setText("No thumbnail.")
            self.open_folder_btn.setEnabled(False)
            self.current_file_path = None
            return

        source_index = self.proxy_model.mapToSource(indexes[0])
        row_idx = source_index.row()  # selected row

        source_model = self.proxy_model.sourceModel()

        column_count = source_model.columnCount()
        column_names = [source_model.headerData(i, Qt.Horizontal) for i in range(column_count)]
        row_data = {
            column_names[i]: source_model.data(source_model.index(row_idx, i), Qt.DisplayRole)
            for i in range(column_count)
        }

        asset_name = row_data.get("asset_name")
        if asset_name:
            self.status_label.setText(f"{asset_name}")

            disk_file_path = row_data.get("disk_file_path")
            has_valid_path = disk_file_path and disk_file_path != "None" and disk_file_path != "null"
            self.current_file_path = disk_file_path if has_valid_path else None
            self.open_folder_btn.setEnabled(has_valid_path)

            html = dbo.update_text_display(asset_name)
            self.info_window.setHtml(html)  # add row data to info window

            thumbnail_name = f"{asset_name}_Thumbnail.jpg"
            thumbnail_path = Path(THUMBNAILS_SAVE_FOLDER) / thumbnail_name
            if thumbnail_path.is_file():
                pixmap = QPixmap(str(thumbnail_path))
                pixmap = pixmap.scaled(
                    self.thumbnail_window.width(),
                    self.thumbnail_window.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.thumbnail_window.setPixmap(pixmap)
                self.thumbnail_window.setToolTip(thumbnail_name)
            else:
                self.thumbnail_window.setText("No thumbnail.")
        else:
            print("Missing asset_name for info window...")

    def populate_columns_dropdown(self) -> None:
        """Fill the column filter dropdown with available columns."""
        self.column_filter.clear()

        if self.proxy_model and self.proxy_model.sourceModel():
            model = self.proxy_model.sourceModel()
            for i in range(1, model.columnCount()):  # skip the column 0 (id)
                column_name = model.headerData(i, Qt.Horizontal)
                self.column_filter.addItem(column_name, i)

    def filter_table(self, text: str) -> None:
        """Filter the table based on the search text.

        Args:
            text: Input text from search bar.

        """
        # case insensitive search. wildcard search
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy_model.setFilterWildcard(f"*{text}*")

        # use selected column from dropdown
        if self.column_filter.currentData() is not None:
            column_index = self.column_filter.currentData()
            self.proxy_model.setFilterKeyColumn(column_index)

        # update top bar status to show visible row count in table
        filtered_count = self.proxy_model.rowCount()
        total_count = self.proxy_model.sourceModel().rowCount()
        self.status_label.setText(f"Showing {filtered_count} of {total_count} records.")

    def load_summary_table_info(self) -> None:
        """Load "content_summary" table and update the bottom summary bar with data."""
        try:
            conn = sqlite3.connect(DB_FILE_PATH)
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT metric_name, metric_value FROM {SUMMARY_TABLE_NAME}
                ORDER BY CAST(metric_value AS REAL) DESC
            """)
            summary_data = cursor.fetchall()
            conn.close()

            if not summary_data:
                return

            html_parts = []
            for name, value in summary_data:
                html_parts.append(f"<b>{name}</b>: {value}&nbsp;&nbsp;")
            html_content = "".join(html_parts)

            self.summary_label.setHtml(str(html_content))

        except sqlite3.OperationalError as e:
            print(f"{e}")

    def output_csv_file(self) -> None:
        """Convert sqlite .db file tables to csv files.
        Output .csv files to "data" folder alongside .db file.
        """
        convert_db_to_csv.sqlite_to_csv(DB_FILE_PATH, DATA_FOLDER_PATH)
        self.status_label.setText("Output CSV files...")

    def open_folder(self, folder_path: str | Path) -> None:
        """Open folder path."""
        subprocess.Popen(f'explorer "{folder_path}"', shell=True)
        self.status_label.setText(f"Open Folder... {folder_path}")

    def json_saver(self, save_key: str, save_value: str) -> None:
        """Reads the save file, a json containing a dictionary with file/ folder paths.
        Creates the save file if missing.

        Args:
            save_key: Json dictionary key (title/ name).
            save_value: Json dictionary value (folder/ file path).

        """
        Path(JSON_SAVE_FILE).parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(JSON_SAVE_FILE) as f:
                json_dict = json.load(f)
        except FileNotFoundError:
            json_dict = {}

        json_dict[save_key] = save_value  # update save file dict

        with open(JSON_SAVE_FILE, "w") as f:
            json.dump(json_dict, f, indent=4)

    def launch_ue(self) -> None:
        """Launch Unreal Engine using the "launch_ue.cmd" script.
        Update paths in script to match your project and engine version.
        """
        try:
            subprocess.Popen(LAUNCH_UE_SCRIPT, shell=True)
            self.status_label.setText("Launching UE5...")
        except Exception as e:
            self.status_label.setText(f"Error launching UE: {e}")

    def save_settings(self, save_message: bool = False) -> None:
        """Updates save_file.json with settings info.
        Specifically, updates the ue_folder_path inputed by user.

        Args:
            save_message: Turn on/ off save message for method.

        """
        ue_folder_path_input = self.ue_folder_text.toPlainText()
        self.json_saver("ue_folder_path", ue_folder_path_input)
        if save_message:
            self.status_label.setText(f"Saving UE5 folder path... '{ue_folder_path_input}'")
            print(f"Saving UE5 folder path... '{ue_folder_path_input}'")

    def closeEvent(self, event) -> None:
        """Save settings when class closes.

        Args:
            event (QCloseEvent): The close event object.

        """
        self.save_settings()


def main() -> None:
    """Entry point for the GameContentViewer application.

    Initializes the Qt application, creates and displays the
    GameContentViewer window, and starts the main event loop.
    """
    app = QApplication(sys.argv)
    viewer = GameContentViewer()
    viewer.show()
    sys.exit(app.exec())
