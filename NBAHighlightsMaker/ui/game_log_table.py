from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QPushButton, QTableWidget, QWidget, QTableWidgetItem

class GameLogTable(QWidget):
    def __init__(self, data_retriever):
        super().__init__()
        self.data_retriever = data_retriever
        self.curr_game_log = None
        self.curr_game = None

        self.layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        self.table_widget.setSortingEnabled(True)
        # make table widget not editable
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        # only be able to select one row at a time
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSelectionMode(QTableWidget.SingleSelection)
        
        # enable button if row is selected
        self.table_widget.itemSelectionChanged.connect(self.handle_row_selection)
        
        #make create video button
        self.create_video_button = QPushButton("Create Video")
        self.create_video_button.setEnabled(False)
        
        #add objects to layout
        self.layout.addWidget(self.table_widget)
        self.layout.addWidget(self.create_video_button)

    def handle_row_selection(self):
        selected_items = self.table_widget.selectedItems()
        if selected_items:
            self.create_video_button.setEnabled(True)  
        else:
            self.create_video_button.setEnabled(False)
    
    # fetch game log, fill table with it
    def update_table(self, player_id):
        # get game log for player
        self.curr_game_log = self.data_retriever.get_game_log(player_id)[['GAME_DATE', 'WL', 'MIN', 'MATCHUP', 'Game_ID', 'PTS', 'REB', 'AST', 'STL', 'BLK']]
       
        # set number of rows and columns
        self.table_widget.setRowCount(len(self.curr_game_log))
        self.table_widget.setColumnCount(len(self.curr_game_log.columns))

        # set column headers
        self.table_widget.setHorizontalHeaderLabels(self.curr_game_log.columns)

        #iterate over each row, get both row index and row data
        for i, row in self.curr_game_log.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem()
                # if it's a number, store it as a number
                if isinstance(value, (int, float)):
                    item.setData(Qt.EditRole, value)  
                # else, store it as a string
                else:
                    item.setText(str(value))  # Store as text for non-numeric data
                self.table_widget.setItem(i, j, item)
        
        # resize columns to remove excess white space
        self.table_widget.resizeColumnsToContents()
        # resize rows to remove excess white space
        self.table_widget.resizeRowsToContents()

        # deselect if row is clicked from previous player chosen
        self.table_widget.clearSelection()
        