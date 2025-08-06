from PySide6.QtWidgets import QComboBox, QCompleter, QLabel, QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import QStringListModel, Qt, Signal
#from NBAHighlightsMaker.players.getplayers import DataRetriever

class PlayerSearchBox(QWidget):
    """
    Widget where users can search for a player, select a season, and load their game log.
    This info is then emitted and used to update the game log table.
    """
    # make signal to emit player id when item selected
    player_info_given = Signal(int, str, str)
    def __init__(self, data_retriever):
        super().__init__()
        
        self.search_box_label = QLabel("Search for a Player:")
        self.search_box = QComboBox(self)
        self.search_box.setEditable(True)
        self.search_box.setPlaceholderText("Type or select a player's name...")
        #self.search_box.lineEdit().setPlaceholderText("Type or select a player's name...")
        self.data_retriever = data_retriever

        # get players and fill box with them
        self.players = self.data_retriever.get_all_players()
        
        # add completer for autocomplete
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.search_box.setCompleter(self.completer)
        
        # fill completer and search box with player names
        self.update_search_box_and_completer()

        # box to select season
        self.season_box_label = QLabel("Select the Year:")
        self.season_box = QComboBox(self)
        self.season_box.addItems(["2025-26", "2024-25", "2023-24", 
                                  "2022-23", "2021-22", "2020-21", 
                                  "2019-20", "2018-19", "2017-18", 
                                  "2016-17", "2015-16", "2014-15", 
                                  "2013-14", "2012-13"])
        # box to select season type
        self.season_type_label = QLabel("Select a Season Type:")
        self.season_type_box = QComboBox(self)
        self.season_type_box.addItems(["Regular Season", "Playoffs",
                                       "All Star", "Pre Season"])
        # button to load game log
        self.load_game_log_button = QPushButton("Load Game Log")
        
        # call function when load button clicked
        self.load_game_log_button.clicked.connect(self.handle_load_button_clicked)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.search_box_label)
        self.layout.addWidget(self.search_box)
        self.layout.addWidget(self.season_box_label)
        self.layout.addWidget(self.season_box)
        self.layout.addWidget(self.season_type_label)
        self.layout.addWidget(self.season_type_box)
        self.layout.addWidget(self.load_game_log_button)

    def update_search_box_and_completer(self) -> None:
        player_names = self.players["full_name"].to_numpy()
        self.search_box.addItems(player_names)

        model = QStringListModel(player_names)
        self.completer.setModel(model)

    # def emit_player_id(self, index):
    #     # get player id, then emit it
    #     player_id = self.players.iloc[index]['id']
    #     self.player_selected.emit(player_id)
    
    def handle_load_button_clicked(self) -> None:
        # get player id and season from boxes
        player_id = self.players.iloc[self.search_box.currentIndex()]['id']
        #print("Player ID: ", player_id)
        season = self.season_box.currentText()
        #print("Season: ", season)
        season_type = self.season_type_box.currentText()
        #print("Season Type: ", season_type)
        # emit signal with player id, season, and season type
        self.player_info_given.emit(player_id, season, season_type)
    