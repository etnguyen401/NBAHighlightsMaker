from PySide6.QtWidgets import QComboBox, QCompleter, QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import QStringListModel, Qt, Signal
from NBAHighlightsMaker.players.getplayers import DataRetriever

class PlayerSearchBox(QWidget):
    # make signal to emit player id when item selected
    info_given = Signal(int, str, str)
    def __init__(self, data_retriever):
        super().__init__()

        self.search_box = QComboBox(self)
        self.search_box.setEditable(True)
        self.search_box.setPlaceholderText("Type or select a player's name...")
        self.data_retriever = data_retriever

        # get players and fill box with them
        self.players = self.data_retriever.get_active_players()
        self.update_search_box()

        # add completer for autocomplete
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.search_box.setCompleter(self.completer)
        # fill completer with player names
        self.update_completer()

        # box to select season
        self.season_box = QComboBox(self)
        self.season_box.addItems(["2024-25", "2023-24", "2022-23", 
                                  "2021-22", "2020-21", "2019-20",
                                  "2018-19", "2017-18", "2016-17",
                                  "2015-16", "2014-15", "2013-14"])
        # box to select season type
        self.season_type_box = QComboBox(self)
        self.season_type_box.addItems(["Regular Season", "Playoffs",
                                       "All Star", "Pre Season"])
        # button to load game log
        self.load_game_log_button = QPushButton("Load Game Log")
        
        # call function when load button clicked
        self.load_game_log_button.clicked.connect(self.handle_load_button_clicked)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.search_box)
        self.layout.addWidget(self.season_box)
        self.layout.addWidget(self.season_type_box)
        self.layout.addWidget(self.load_game_log_button)

    def update_search_box(self):
        player_names = self.players["full_name"].tolist()
        self.search_box.addItems(player_names)
    
    def update_completer(self):
        player_names = self.players["full_name"].tolist()
        model = QStringListModel(player_names)
        self.completer.setModel(model)

    # def emit_player_id(self, index):
    #     # get player id, then emit it
    #     player_id = self.players.iloc[index]['id']
    #     self.player_selected.emit(player_id)
    
    def handle_load_button_clicked(self):
        # get player id and season from boxes
        player_id = self.players.iloc[self.search_box.currentIndex()]['id']
        #print("Player ID: ", player_id)
        season = self.season_box.currentText()
        #print("Season: ", season)
        season_type = self.season_type_box.currentText()
        #print("Season Type: ", season_type)
        # emit signal with player id, season, and season type
        self.info_given.emit(player_id, season, season_type)
    