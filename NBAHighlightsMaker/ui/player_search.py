from PySide6.QtWidgets import QComboBox, QCompleter
from PySide6.QtCore import QStringListModel, Qt, Signal
from NBAHighlightsMaker.players.getplayers import DataRetriever

class PlayerSearchBox(QComboBox):
    # make signal to emit player id when item selected
    player_selected = Signal(int)
    def __init__(self, data_retriever):
        super().__init__()
        self.setEditable(True)
        self.setPlaceholderText("Type or select a player's name...")
        self.data_retriever = data_retriever

        # get players and fill box with them
        self.players = self.data_retriever.get_active_players()
        self.update_search_box()

        # add completer for autocomplete
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.setCompleter(self.completer)
        # fill completer with player names
        self.update_completer()

        # call function when player is selected
        self.currentIndexChanged.connect(self.emit_player_id)

    def update_search_box(self):
        player_names = self.players["full_name"].tolist()
        self.addItems(player_names)
    
    def update_completer(self):
        player_names = self.players["full_name"].tolist()
        model = QStringListModel(player_names)
        self.completer.setModel(model)

    def emit_player_id(self, index):
        # get player id, then emit it
        player_id = self.players.iloc[index]['id']
        self.player_selected.emit(player_id)
    