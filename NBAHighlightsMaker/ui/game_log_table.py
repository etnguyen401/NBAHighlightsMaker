from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QPushButton, QTableWidget, QWidget, QTableWidgetItem
from NBAHighlightsMaker.downloader.downloader import Downloader
from NBAHighlightsMaker.editor.editor import VideoMaker
import os
import shutil
import asyncio
# HARDCODE FILE PATH FOR NOW
data_dir = os.path.join(os.getcwd(), 'data', 'vids')

class GameLogTable(QWidget):
    def __init__(self, data_retriever):
        super().__init__()
        
        self.data_retriever = data_retriever
        self.downloader = Downloader()
        self.video_maker = VideoMaker()
        self.curr_game_log = None

        self.player_id = None
        self.game_id = None

        self.get_links_task = None
        self.download_task = None
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
        self.create_video_button.setToolTip("Select a row to choose what game you want to make highlights of to enable this button.")
        # when button clicked, get game id and player id and begin download + edit
        self.create_video_button.clicked.connect(
            lambda: asyncio.create_task(self.handle_create_vid_click())
        )

        #make cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.handle_cancel_click)

        #add objects to layout
        self.layout.addWidget(self.table_widget)
        self.layout.addWidget(self.create_video_button)
        self.layout.addWidget(self.cancel_button)

    def handle_row_selection(self):
        selected_items = self.table_widget.selectedItems()
        self.game_id = self.curr_game_log.iloc[self.table_widget.currentRow()]['Game_ID']
        if selected_items:
            self.create_video_button.setEnabled(True)  
        else:
            self.create_video_button.setEnabled(False)

    def handle_cancel_click(self):
        if self.get_links_task:
            self.get_links_task.cancel()
            self.get_links_task = None
            print("Getting Links cancelled.")
        
        if self.download_task:
            self.download_task.cancel()
            self.download_task = None
            print("Downloading cancelled.")
        self.cancel_button.setEnabled(False)
        
    async def handle_create_vid_click(self):
        print("Player ID:", self.player_id)
        print("Game ID:", self.game_id)
        # delete data folder if it exists
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
        # create/recreate data folder
        os.makedirs(data_dir)
        
        # call get events id
        event_ids = self.data_retriever.get_event_ids(self.game_id, self.player_id)
        print(event_ids.head()) 
        # make async io task, get download links
        self.get_links_task = asyncio.create_task(self.data_retriever.get_download_links(self.game_id, event_ids))
        # save the event_ids returned from the task
        try:
            self.cancel_button.setText("Cancel Getting Links")
            self.cancel_button.setEnabled(True)
            event_ids = await self.get_links_task
            # result.to_csv('event_ids2.csv', index = False)
        except asyncio.CancelledError:
            print("Getting links was cancelled by user")
            # the only thing that changed was the event_ids, but
            # when the user clicks create video again, event_ids will
            # be new anyways
        except Exception as e:
            print(f"An error occurred: {e}")
        
        # call download_links to download all the vids
        self.download_task = asyncio.create_task(self.downloader.download_links(event_ids))
        try:
            self.cancel_button.setText("Cancel Getting Downloads")
            self.cancel_button.setEnabled(True)
            event_ids = await self.download_task
            #event_ids.to_csv('event_ids_with_filepath.csv', index = False)
        except asyncio.CancelledError:
            print("Downloading was cancelled by user")
            # might have downloaded some files, delete data folder
            if os.path.exists(data_dir):
                shutil.rmtree(data_dir)
            # create/recreate data folder
            os.makedirs(data_dir)
        except Exception as e:
            print(f"An error occurred: {e}")

        # edit the videos together
        self.edit_task = asyncio.create_task(self.video_maker.make_final_vid(event_ids['FILE_PATH'].tolist()))
        try:
            self.cancel_button.setText("Cancel Creating Video")
            self.cancel_button.setEnabled(True)
            final_vid = await self.edit_task
        except asyncio.CancelledError:
            print("Creating video was cancelled by user")
            # might have created the final vid, delete the final vid only
            # CHANGE LATER TO ACCOUNT FOR USER SPECIFIED PATH
            if os.path.exists(os.path.join(data_dir, "final_vid.mp4")):
                os.remove(os.path.join(data_dir, "final_vid.mp4"))
        except Exception as e:
            print(f"An error occurred: {e}")
        
        self.cancel_button.setEnabled(False)

    # fetch game log, fill table with it
    def update_table(self, player_id):
        # get game log for player
        self.curr_game_log = self.data_retriever.get_game_log(player_id)[['GAME_DATE', 'WL', 'MIN', 'MATCHUP', 'Game_ID', 'PTS', 'REB', 'AST', 'STL', 'BLK']]
        self.player_id = player_id
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
                    item.setText(str(value))
                self.table_widget.setItem(i, j, item)
        
        # resize columns to remove excess white space
        self.table_widget.resizeColumnsToContents()
        # resize rows to remove excess white space
        self.table_widget.resizeRowsToContents()

        # deselect if row is clicked from previous player chosen
        self.table_widget.clearSelection()
