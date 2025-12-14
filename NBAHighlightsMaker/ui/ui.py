"""Main window container for NBAHighlightsMaker.

Defines the HighlightsUI class, a subclass of QMainWindow,
which sets up the main application window and other widgets that
are within that window.
"""
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QWidget
from PySide6.QtGui import QIcon, QFont
from NBAHighlightsMaker.ui.player_search import PlayerSearchBox
from NBAHighlightsMaker.ui.game_log_table import GameLogTable
import sys
import os

class HighlightsUI(QMainWindow):
    """Main window for the application.

    Sets up the main window and its child widgets:  
    The player search and the game log table widgets.

    Args:
        data_retriever (DataRetriever): Used to get player and game data.
        downloader (Downloader): Used to download video clips.

    Attributes:
        layout (QVBoxLayout): Main vertical box layout for the application.
        player_search_widget (PlayerSearchBox): Widget for entering information on the desired player and game.
        table_widget (GameLogTable): Widget for displaying the game log, arranged in a table.
    """
    def __init__(self, data_retriever, downloader, data_dir):
        super().__init__()
        # x, y, width, height
        self.setGeometry(300, 300, 600, 700)
        self.setWindowTitle("NBAHighlightsMaker")

        icon_path = ""

        if hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, "resources", "favicon.ico")
        else:
            icon_path = "resources/favicon.ico"

        icon = QIcon(icon_path)
        self.setWindowIcon(icon)
        
        # set to vertical box layout
        self.layout = QVBoxLayout()
        # set spacing between widgets
        self.layout.setSpacing(0)
        # create player search widget
        self.player_search_widget = PlayerSearchBox(data_retriever)

        heading_font = QFont()
        heading_font.setBold(True)
        heading_font.setPointSize(11)
        heading_font.setUnderline(True)
        # make search box label
        player_search_label = QLabel("Enter Player Name and Season Info:")
        player_search_label.setFont(heading_font)

        # make table widget
        self.table_widget = GameLogTable(data_retriever, downloader, data_dir)
        game_log_label = QLabel("Game Log:")
        game_log_label.setFont(heading_font)

        self.player_search_widget.player_info_given.connect(self.table_widget.update_table)

        # layout order:
        self.layout.addWidget(player_search_label)
        self.layout.addWidget(self.player_search_widget)
        self.layout.addWidget(game_log_label)
        self.layout.addWidget(self.table_widget)

        # set central widget that holds our layout
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
