"""Main window container for NBAHighlightsMaker.

Defines the HighlightsUI class, an extension of QMainWindow,
which sets up the main application window and other widgets that 
are within that window.

Typical usage example:
    from NBAHighlightsMaker.ui.ui import HighlightsUI
    window = HighlightsUI(data_retriever, downloader, data_dir)
"""
#import sys
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QLabel, QWidget
#from PySide6.QtCore import Qt, QStringListModel
#import pandas as pd 
#from NBAHighlightsMaker.players.getplayers import DataRetriever
from PySide6.QtGui import QIcon
from NBAHighlightsMaker.ui.player_search import PlayerSearchBox
from NBAHighlightsMaker.ui.game_log_table import GameLogTable

class HighlightsUI(QMainWindow):
    """Main window for the application.

    Sets up the main window and its child widgets:  
    The player search and the game log table widgets.

    Args:
        data_retriever (DataRetriever): Used to get player and game data.
        downloader (Downloader): Used to download video clips.

    Attributes:
        layout (QVBoxLayout): The main vertical box layout for the application.
        player_search_widget (PlayerSearchBox): The widget for entering information on the desired player and game.
        table_widget (GameLogTable): The widget for displaying the game log, arranged in a table.
    """
    def __init__(self, data_retriever, downloader, data_dir):
        super().__init__()
        self.setWindowTitle("NBAHighlightsMaker")
        icon = QIcon("./resources/icon.png")
        self.setWindowIcon(icon)
        # x, y, width, height
        self.setGeometry(300, 300, 540, 600)

        # self.data_retriever = data_retriever
        # self.downloader = downloader

        # set to vertical box layout
        self.layout = QVBoxLayout()

        # create player search widget
        self.player_search_widget = PlayerSearchBox(data_retriever)
        # make search box label
        # player_search_label = QLabel("Search for a Player:")
        # player_search_label.setBuddy(self.player_search_widget)
        
        # make table widget
        self.table_widget = GameLogTable(data_retriever, downloader, data_dir)
        game_log_label = QLabel("Game Log:")
        game_log_label.setBuddy(self.table_widget)

        self.player_search_widget.player_info_given.connect(self.table_widget.update_table)

        # layout order:
        #self.layout.addWidget(player_search_label)
        self.layout.addWidget(self.player_search_widget)
        self.layout.addWidget(game_log_label)
        self.layout.addWidget(self.table_widget)

        # set central widget that holds our layout
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
