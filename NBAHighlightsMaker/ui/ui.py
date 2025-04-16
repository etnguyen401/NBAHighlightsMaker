import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLineEdit, QLabel, QWidget, QCompleter, QComboBox
)
from PySide6.QtCore import Qt, QStringListModel
import pandas as pd
from NBAHighlightsMaker.players.getplayers import DataRetriever

class HighlightsUI(QMainWindow):
    def __init__(self, data_retriever):
        super().__init__()
        self.setWindowTitle("NBAHighlightsMaker")
        self.setGeometry(100, 100, 400, 200)

        self.data_retriever = data_retriever

        # load active players
        self.players = self.load_active_players()

        # set to vertical box layout
        self.layout = QVBoxLayout()

        # create player search box
        self.search_box = QComboBox()
        self.search_box.setEditable(True)
        self.search_box.setPlaceholderText("Type or select a player's name...")
        
        # make search box label
        player_search_label = QLabel("Search for a Player:")
        player_search_label.setBuddy(self.search_box)
        self.layout.addWidget(player_search_label)
        self.layout.addWidget(self.search_box)

        # fill dropdown with player names
        self.update_search_box()

        # add completer for autocomplete
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_box.setCompleter(self.completer)

        # fill completer with player names
        self.update_completer()

        # call function when player is selected
        self.search_box.activated.connect(self.select_player)

        # update our selected polayer
        self.selected_player_label = QLabel("Selected Player: None")
        self.layout.addWidget(self.selected_player_label)

        # set central widget that holds our layout
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

    def load_active_players(self):
        return self.data_retriever.get_active_players()

    def update_search_box(self):
        player_names = self.players["full_name"].tolist()
        self.search_box.addItems(player_names)  

    def update_completer(self):
        player_names = self.players["full_name"].tolist()
        model = QStringListModel(player_names)  
        self.completer.setModel(model)
    
    def select_player(self, index):
        # get the selected player's name
        selected_text = self.search_box.itemText(index)

        # get the row for that player
        player_row = self.players.iloc[index]

        # set label to the selected player
        self.selected_player_label.setText(f"Selected Player: {selected_text}")

        # print selected player's row of info
        print(f"Selected Player Info:\n{player_row}")
        # print player's id
        print(f"Player ID: {player_row['id']}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HighlightsUI()
    window.show()
    sys.exit(app.exec())