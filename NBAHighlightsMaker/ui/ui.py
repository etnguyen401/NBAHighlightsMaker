#import sys
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QLabel, QWidget)
#from PySide6.QtCore import Qt, QStringListModel
#import pandas as pd 
#from NBAHighlightsMaker.players.getplayers import DataRetriever
from NBAHighlightsMaker.ui.player_search import PlayerSearchBox
from NBAHighlightsMaker.ui.game_log_table import GameLogTable

class HighlightsUI(QMainWindow):
    def __init__(self, data_retriever):
        super().__init__()
        self.setWindowTitle("NBAHighlightsMaker")
        self.setGeometry(300, 300, 540, 500)

        self.data_retriever = data_retriever
        
        # set to vertical box layout
        self.layout = QVBoxLayout()

        # create player search widget
        self.player_search_widget = PlayerSearchBox(self.data_retriever)
        # make search box label
        player_search_label = QLabel("Search for a Player:")
        player_search_label.setBuddy(self.player_search_widget)
        
        # make table widget
        self.table_widget = GameLogTable(self.data_retriever)
        game_log_label = QLabel("Game Log:")
        game_log_label.setBuddy(self.table_widget)

        self.player_search_widget.info_given.connect(self.table_widget.update_table)

        # layout order:
        self.layout.addWidget(player_search_label)
        self.layout.addWidget(self.player_search_widget)
        self.layout.addWidget(game_log_label)
        self.layout.addWidget(self.table_widget)

        # set central widget that holds our layout
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = HighlightsUI()
#     window.show()
#     sys.exit(app.exec())