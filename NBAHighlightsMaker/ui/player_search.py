"""Widget to search for a certain list of games using user input data.

This module takes information given by the user 
through the UI and emits the player ID, season, and season type
to update the GameLogTable widget with the corresponding game log.
"""
from PySide6.QtWidgets import QComboBox, QCompleter, QLabel, QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import QStringListModel, Qt, Signal

class PlayerSearchBox(QWidget):
    """Widget for selecting a player, year, and season type to find the games the user wants.

    A widget where users can search for and select a player in a combo box, 
    select a season and season type from dropdown menus, and click a load button to
    load the corresponding game log. This emits the player ID, season, and season type
    to the GameLogTable widget, which updates to show the game log according to that information.
    
    Args:
        data_retriever: DataRetriever object used to get player data.

    Attributes:
        player_info_given (Signal): Emits player ID, season, and season type for later use.
        search_box_label (QLabel): Label for the player search combo box.
        search_box (QComboBox): Combo box for desired player with autocomplete.
        completer (QCompleter): Completer to autocomplete player names.
        season_box_label (QLabel): Label for the year dropdown box.
        season_box (QComboBox): Dropdown box for selecting the year.
        season_type_label (QLabel): Label for the season type dropdown box.
        season_type_box (QComboBox): Dropdown box for selecting the season type.
        load_game_log_button (QPushButton): Button to emit selected information and load the game log.
        layout (QVBoxLayout): Main layout for the widget.
        players (pd.DataFrame): DataFrame containing all player information.
        data_retriever (DataRetriever): DataRetriever object used to get player data.
    """
    # make signal to emit info when load button clicked
    player_info_given = Signal(int, str, str)
    def __init__(self, data_retriever):
        super().__init__()
        
        self.search_box_label = QLabel("Type/Select Player Name:")
        self.search_box = QComboBox(self)
        self.search_box.setEditable(True)
        self.data_retriever = data_retriever

        # get players and fill box with them
        self.players = self.data_retriever.get_all_players()

        # add completer for autocomplete
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        # match anywhere in string
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
        """Fills the search box with player names and initializes the completer.
        """
        player_names = self.players["full_name"].to_numpy()
        self.search_box.addItems(player_names)

        model = QStringListModel(player_names)
        self.completer.setModel(model)
    
    def handle_load_button_clicked(self) -> None:
        """Gets the player ID number, season, and season type chosen by user and emits a signal with this information.
        """
        player_id = self.players.iloc[self.search_box.currentIndex()]['id']
        season = self.season_box.currentText()
        season_type = self.season_type_box.currentText()
        self.player_info_given.emit(player_id, season, season_type)
    