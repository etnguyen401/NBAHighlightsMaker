from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

class GameLogTable(QTableWidget):
    def __init__(self, data_retriever):
        super().__init__()
        self.data_retriever = data_retriever
        self.curr_game_log = None
        self.setSortingEnabled(True)
        # make table widget not editable
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        # only be able to select one row at a time
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
    
    # fetch game log, fill table with it
    def update_table(self, player_id):
        # get game log for player
        self.curr_game_log = self.data_retriever.get_game_log(player_id)[['GAME_DATE', 'WL', 'MIN', 'MATCHUP', 'Game_ID', 'PTS', 'REB', 'AST', 'STL', 'BLK']]
       
        # set number of rows and columns
        self.setRowCount(len(self.curr_game_log))
        self.setColumnCount(len(self.curr_game_log.columns))

        # set column headers
        self.setHorizontalHeaderLabels(self.curr_game_log.columns)

        #iterate over each row, get both row index and row data
        for i, row in self.curr_game_log.iterrows():
            for j, value in enumerate(row):
                self.setItem(i, j, QTableWidgetItem(str(value)))
        
        # resize columns to remove excess white space
        self.resizeColumnsToContents()
        # resize rows to remove excess white space
        self.resizeRowsToContents()
        