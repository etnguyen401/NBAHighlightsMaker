from PySide6.QtCore import Qt, Signal, QObject
from proglog import ProgressBarLogger
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QCheckBox, QPushButton, QTableWidget, QWidget, QTableWidgetItem, QMessageBox
from NBAHighlightsMaker.downloader.downloader import Downloader
from NBAHighlightsMaker.editor.editor import VideoMaker
import os
import shutil
import asyncio
# HARDCODE FILE PATH FOR NOW
data_dir = os.path.join(os.getcwd(), 'data', 'vids')

class GameLogTable(QWidget):
    def __init__(self, data_retriever, downloader):
        super().__init__()
        
        self.data_retriever = data_retriever
        self.downloader = downloader
        self.video_maker = VideoMaker(self.update_progress_bar)

        self.curr_game_log = None
        self.player_id = None
        self.game_id = None

        self.get_links_task = None
        self.download_task = None
        self.edit_task = None

        self.create_video_flag = False

        self.layout = QVBoxLayout(self)

        self.table_widget = QTableWidget()
        
        # make table widget not editable
        self.table_widget.setEditTriggers(QTableWidget.NoEditTriggers)
        # only be able to select one row at a time
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSelectionMode(QTableWidget.SingleSelection)
        #self.table_widget.setSortingEnabled(True)
        # enable button if row is selected
        self.table_widget.itemSelectionChanged.connect(self.handle_row_selection)
        # select all button
        self.select_all_button = QCheckBox("Select All")
        self.select_all_button.setChecked(True)
        self.select_all_button.clicked.connect(self.handle_select_all_click)

        #make checkboxes
        self.layout_checkboxes = QHBoxLayout()
        self.fg_made_box = QCheckBox("FG Made")
        self.assists_box = QCheckBox("Assists")
        self.fg_missed_box = QCheckBox("FG Missed")
        self.fta_box = QCheckBox("Free Throw Attempts")
        self.rebound_box = QCheckBox("Rebounds")
        self.fouls_committed_box = QCheckBox("Fouls Committed")
        self.fouls_drawn_box = QCheckBox("Fouls Drawn")
        self.turnover_box = QCheckBox("Turnovers")
        self.steal_box = QCheckBox("Steals")
        self.block_box = QCheckBox("Blocks")

        #enable all
        self.fg_made_box.setChecked(True)
        self.assists_box.setChecked(True)
        self.fg_missed_box.setChecked(True)
        self.fta_box.setChecked(True)
        self.rebound_box.setChecked(True)
        self.fouls_committed_box.setChecked(True)
        self.fouls_drawn_box.setChecked(True)
        self.turnover_box.setChecked(True)
        self.steal_box.setChecked(True)
        self.block_box.setChecked(True)

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
        self.cancel_button.clicked.connect(self.cancel_tasks)

        #make progress bar and label
        self.progress_bar_label = QLabel("")
        self.progress_bar_label.setVisible(False)
        self.progress_bar = QProgressBar(self)
        #segmented?
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        

        #add checkboxes to horizontal layout
        self.layout_checkboxes.addWidget(self.fg_made_box)
        self.layout_checkboxes.addWidget(self.fg_missed_box)
        self.layout_checkboxes.addWidget(self.assists_box)
        self.layout_checkboxes.addWidget(self.fta_box)
        self.layout_checkboxes.addWidget(self.rebound_box)
        self.layout_checkboxes.addWidget(self.fouls_committed_box)
        self.layout_checkboxes.addWidget(self.fouls_drawn_box)
        self.layout_checkboxes.addWidget(self.turnover_box)
        self.layout_checkboxes.addWidget(self.steal_box)
        self.layout_checkboxes.addWidget(self.block_box)
        
        #add objects to layout
        self.layout.addWidget(self.table_widget)
        self.layout.addWidget(self.select_all_button)
        self.layout.addLayout(self.layout_checkboxes)
        self.layout.addWidget(self.progress_bar_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.create_video_button)
        self.layout.addWidget(self.cancel_button)

    def update_progress_bar(self, value, description):
        self.progress_bar.setValue(value)
        self.progress_bar_label.setText(description)

    def handle_row_selection(self):
        selected_items = self.table_widget.selectedItems()
        
        #self.game_id = self.curr_game_log.iloc[self.table_widget.currentRow()]['Game_ID']
        self.game_id = selected_items[0].text()
        print("Type of game id:", type(self.game_id))
        #print("Selected game id from selected_items:", selected_items[0].text())
        #print("Selected game id from int selected_items:", int(selected_items[0].text()))
        
        # print("Current Row: ", self.table_widget.currentRow())
        # print("Selected game id from current row:", self.game_id)
        
        if selected_items and self.create_video_flag == False:
            self.create_video_button.setEnabled(True)  
        else:
            self.create_video_button.setEnabled(False)

    # def handle_cancel_click(self):
    #     if self.get_links_task:
    #         self.get_links_task.cancel()
    #         self.get_links_task = None
    #         print("Getting Links cancelled.")
        
    #     if self.download_task:
    #         self.download_task.cancel()
    #         self.download_task = None
    #         print("Downloading cancelled.")
        
    #     if self.edit_task:
    #         self.edit_task.cancel()
    #         self.edit_task = None
    #         print("Creating video cancelled.")
        
    #     self.create_video_button.setEnabled(True)

    #     self.cancel_button.setEnabled(False)
    #     self.cancel_button.setText("Cancel")

    #     self.progress_bar.setVisible(False)
    #     self.progress_bar_label.setText("")
    #     self.progress_bar.setValue(0)
    
    def handle_select_all_click(self):
        # if it's checked, and the user clicks it, uncheck all  
        checked = self.select_all_button.isChecked()
        self.fg_made_box.setChecked(checked)
        self.assists_box.setChecked(checked)
        self.fg_missed_box.setChecked(checked)
        self.fta_box.setChecked(checked)
        self.rebound_box.setChecked(checked)
        self.fouls_committed_box.setChecked(checked)
        self.fouls_drawn_box.setChecked(checked)
        self.turnover_box.setChecked(checked)
        self.steal_box.setChecked(checked)
        self.block_box.setChecked(checked)

    def cleanup(self):
        # if self.get_links_task:
        #     self.get_links_task.cancel()
        #     self.get_links_task = None
        #     print("Getting Links cancelled.")
        
        # if self.download_task:
        #     self.download_task.cancel()
        #     self.download_task = None
        #     print("Downloading cancelled.")
        
        # if self.edit_task:
        #     self.edit_task.cancel()
        #     self.edit_task = None
        #     print("Creating video cancelled.")

        self.create_video_button.setEnabled(True)

        self.progress_bar.setVisible(False)
        self.progress_bar_label.setText("")
        self.progress_bar_label.setVisible(False)
        self.progress_bar.setValue(0)
        
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Cancel")

        self.create_video_flag = False
        
    def cancel_tasks(self):
        if self.get_links_task:
            self.get_links_task.cancel()
            self.get_links_task = None
            print("Getting Links task cancelled.")
        
        if self.download_task:
            self.download_task.cancel()
            self.download_task = None
            print("Downloading task cancelled.")
        
        if self.edit_task:
            self.edit_task.cancel()
            self.edit_task = None
            print("Creating video task cancelled.")

    async def handle_create_vid_click(self):
        # print("Player ID:", self.player_id)
        # print("Game ID:", self.game_id)
        # delete data folder if it exists

        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
        # create/recreate data folder
        os.makedirs(data_dir)
        
        self.create_video_button.setEnabled(False)
        self.create_video_flag = True
        # make a set to store the boxes checked
        boxes_checked = set()
        # check which boxes are checked
        if self.fg_made_box.isChecked() or self.assists_box.isChecked():
            boxes_checked.add(1)
        if self.fg_missed_box.isChecked() or self.block_box.isChecked():
            boxes_checked.add(2)
        if self.fta_box.isChecked():
            boxes_checked.add(3)
        if self.rebound_box.isChecked():
            boxes_checked.add(4)
        if self.turnover_box.isChecked() or self.steal_box.isChecked():
            boxes_checked.add(5)
        if self.fouls_committed_box.isChecked() or self.fouls_drawn_box.isChecked():
            boxes_checked.add(6)
        
        # call get events id
        # get all event ids relating to the player
        event_ids = self.data_retriever.get_event_ids(self.game_id, self.player_id, boxes_checked)
        

        self.progress_bar_label.setVisible(True)
        self.progress_bar.setVisible(True)
        
        #already got event ids, that were filtered by boxes checked relating to the player

        # check if assists, steals, blocks are checked
        # if fgm_box is checked, assists already included
        # else if fgm_box wasn't checked and asists was, filter event ids that are fgm and only get the rows
        # that have player2id = player_id
        if self.fg_made_box.isChecked() and not self.assists_box.isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 1) & (event_ids['PLAYER1_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 1)]
        if self.assists_box.isChecked() and not self.fg_made_box.isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 1) & (event_ids['PLAYER2_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 1)]
        if self.steal_box.isChecked() and not self.turnover_box.isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 5) & (event_ids['PLAYER2_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 5)]
        if self.turnover_box.isChecked() and not self.steal_box.isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 5) & (event_ids['PLAYER1_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 5)]
        if self.block_box.isChecked() and not self.fg_missed_box.isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 2) & (event_ids['PLAYER3_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 2)]
        if self.fouls_committed_box.isChecked() and not self.fouls_drawn_box.isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 6) & (event_ids['PLAYER1_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 6)]
        if self.fouls_drawn_box.isChecked() and not self.fouls_committed_box.isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 6) & (event_ids['PLAYER2_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 6)]
        # make async io task, get download links
        # event_ids.to_csv('test.csv', index = False)
        self.get_links_task = asyncio.create_task(self.data_retriever.get_download_links_async(self.game_id, event_ids, self.update_progress_bar))
        # save the event_ids returned from the task
        try:
            self.cancel_button.setText("Cancel Getting Links")
            self.cancel_button.setEnabled(True)
            event_ids = await self.get_links_task
            event_ids.to_csv('test.csv', index = False)
        except asyncio.CancelledError:
            print("Getting links was cancelled by user.")
            # the only thing that changed was the event_ids, but
            # when the user clicks create video again, event_ids will
            # be new anyways
            self.cleanup()
            return
        except Exception as e:
            print(f"An error occurred while getting links: {e}")
            print("Returning...")
            self.cleanup()
            QMessageBox.critical(self, "An error occurred while getting links:", f"{e}\nPlease try creating the video again.")
            return
        
        self.update_progress_bar(0, "")
        # call download_links to download all the vids
        self.download_task = asyncio.create_task(self.downloader.download_files(event_ids, self.update_progress_bar))
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
            self.cleanup()
            return
        except Exception as e:
            print(f"An error occurred while downloading: {e}")
            self.cleanup()
            QMessageBox.critical(self, "An error occurred while downloading:", f"{e}\nPlease try creating the video again.")

        self.update_progress_bar(0, "")
        # edit the videos together

        # logger = MyProgressBarLogger()
        # logger.progress_bar_values.connect(self.update_progress_bar)

        # make cancel button click stop moviepy editing
        # self.cancel_button.clicked.connect(logger.cancel)

        self.edit_task = asyncio.create_task(self.video_maker.make_final_vid(event_ids['FILE_PATH'].tolist()))
        try:
            self.cancel_button.setText("Cancel Creating Video")
            self.cancel_button.setEnabled(True)
            final_vid = await self.edit_task
        except IOError as e:
            print(f"IOError caught in game_log_table: {e}")
            self.video_maker.cancel_editing()
            self.cleanup()
            return
        except asyncio.CancelledError:
            print("AsyncIO CancelledError by editing task.")
            # might have created the final vid, delete the final vid only
            # CHANGE LATER TO ACCOUNT FOR USER SPECIFIED PATH
            # if os.path.exists(os.path.join(data_dir, "final_vid.mp4")):
            #     os.remove(os.path.join(data_dir, "final_vid.mp4"))
            self.video_maker.cancel_editing()
            #self.cancel_button.clicked.disconnect(logger.cancel)
            self.cleanup()
            return
        except Exception as e:
            print(f"An error occurred while editing: {e}")
            self.video_maker.cancel_editing()
            self.cleanup()
            return
        
        #when task is done, video was created successfully
        if final_vid is None:
            reply = QMessageBox.information(self, "Success", "Video created successfully! Would you like to open the file?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                os.startfile(os.path.join(data_dir, "final_vid.mp4"))
        
        # clean up
        self.cleanup()

    # fetch game log, fill table with it
    def update_table(self, player_id, season, season_type):
        self.table_widget.setSortingEnabled(False)
        # clear table
        self.table_widget.clear()

        # get game log for player
        # FIND WAY TO GET GAME ID WITHOUT DISPLAYING IT LATER
        self.curr_game_log = self.data_retriever.get_game_log(player_id, season, season_type)[['Game_ID', 'GAME_DATE', 'MATCHUP', 'WL', 'MIN', 'FGM', 'FGA', 'FTM', 'FTA', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']]
        if self.curr_game_log.empty:
            print("No game log found for player.")
            # clear table
            self.table_widget.clear()
            # clear selection
            self.table_widget.setRowCount(0)
            self.table_widget.setColumnCount(0)
            QMessageBox.critical(self, "Error: No Game Log Found", "No game log found for combination selected, please try another player/season/season type combination.")
            return
        self.player_id = player_id
        # set number of rows and columns
        self.table_widget.setRowCount(len(self.curr_game_log))
        self.table_widget.setColumnCount(len(self.curr_game_log.columns))

        # set column headers
        self.table_widget.setHorizontalHeaderLabels(self.curr_game_log.columns)

        #reset scroll bar position
        self.table_widget.verticalScrollBar().setValue(0)

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
        self.table_widget.setSortingEnabled(True)

class MyProgressBarLogger(QObject, ProgressBarLogger):
    progress_bar_values = Signal(int, str)
    def __init__(self):
        super().__init__()
        self.min_time_interval = 1.0
        #self.update_progress_bar = update_progress_bar
        self.cancelled = False

    def bars_callback(self, bar, attr, value, old_value=None):
        if self.cancelled:
            print("Raising exception for the user cancelling.")
            #raise keyboard interrupt error

            raise KeyboardInterrupt("User cancelled the editing.")
        if bar == 't' and attr == 'index':
            total = self.bars[bar]['total']
            percent = int((value / total) * 100)
            # value and total are in frames, so convert to seconds
            self.progress_bar_values.emit(percent, f"Editing - {percent}% : {(value / 60):.1f}s / {(total / 60):.1f}s")
            #self.update_progress_bar(percent, f"Editing - {percent}% : {(value / 60):.1f}s / {(total / 60):.1f}s")

    def cancel(self):
        self.cancelled = True