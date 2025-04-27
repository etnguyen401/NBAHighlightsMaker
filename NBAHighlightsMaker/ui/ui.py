import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLineEdit, QLabel, QWidget, QCompleter, QComboBox, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, QStringListModel
import pandas as pd
from NBAHighlightsMaker.players.getplayers import DataRetriever
from NBAHighlightsMaker.ui.player_search import PlayerSearchBox
from NBAHighlightsMaker.ui.game_log_table import GameLogTable

class HighlightsUI(QMainWindow):
    def __init__(self, data_retriever):
        super().__init__()
        self.setWindowTitle("NBAHighlightsMaker")
        self.setGeometry(300, 300, 540, 400)

        self.data_retriever = data_retriever
        
        # set to vertical box layout
        self.layout = QVBoxLayout()

        # create player search box
        self.search_box = PlayerSearchBox(self.data_retriever)
        # make search box label
        player_search_label = QLabel("Search for a Player:")
        player_search_label.setBuddy(self.search_box)
        
        # make table widget
        self.table_widget = GameLogTable(self.data_retriever)
        game_log_label = QLabel("Game Log:")
        game_log_label.setBuddy(self.table_widget)

        self.search_box.player_selected.connect(self.table_widget.update_table)

        # layout order:
        self.layout.addWidget(player_search_label)
        self.layout.addWidget(self.search_box)
        self.layout.addWidget(game_log_label)
        self.layout.addWidget(self.table_widget)

        # set central widget that holds our layout
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HighlightsUI()
    window.show()
    sys.exit(app.exec())