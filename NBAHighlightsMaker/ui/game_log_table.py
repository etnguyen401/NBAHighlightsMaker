"""Widget displaying a game log, allowing the user to select a game and actions to create a video of all relevant events.

This module contains the GameLogTable class, a widget which displays a list of all games
the selected player participated in. The user can select a game from the table and
which event types they want to include in the video. When a game is selected, the "Create Video" 
button is enabled, allowing the user to start the process of downloading all of the clips and 
stitching them together to form one video. Once the process is completed, a pop-up will inform 
the user that the video has been created and if they want to open it immediately.

"""


from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QCheckBox, QPushButton, QTableWidget, QWidget, QTableWidgetItem, QMessageBox
from NBAHighlightsMaker.editor.editor import VideoMaker
from NBAHighlightsMaker.common.enums import EventMsgType
import os
import shutil
import asyncio
# HARDCODE FILE PATH FOR NOW
#data_dir = os.path.join(os.getcwd(), 'data', 'vids')

class GameLogTable(QWidget):
    """Widget to display the selected player's game log, select a game and event types wanted, and create the video.
    
    Allows the user to select a game and create a video of highlights based on selected actions.
    Manages UI elements for table display, action selection, progress updates on getting links and video
    for each event, and video creation.

    Args:
        data_retriever (DataRetriever): Object used to get player data.
        downloader (Downloader): Object used to download video clips.

    Attributes:
        data_retriever (DataRetriever): Object used to get player data.
        downloader (Downloader): Object used to download video clips.
        video_maker (VideoMaker): Object used to concatenate all clips and add fade effects between clips.
        curr_game_log (pandas.DataFrame): The dataframe with the game log for the currently selected player.
        player_id (int): The id for the currently selected player.
        game_id (str): The id for the currently selected game.
        get_links_task (asyncio.Task): Asyncio task to fetch all relevant video links.
        download_task (asyncio.Task): Asyncio task to download video clips.
        edit_task (asyncio.Task): Asyncio task to edit the final video.
        create_video_flag (bool): Flag indicating if video creation is in progress.
        layout (QVBoxLayout): Main vertical layout for the widget.
        table_widget (QTableWidget): Table widget displaying the game log.
        select_all_button (QCheckBox): Checkbox to select/deselect all actions.
        checkboxes (dict): Dictionary of checkboxes for each possible action.
        layout_checkboxes (QHBoxLayout): Horizontal layout for the checkboxes.
        create_video_button (QPushButton): Button to start video creation.
        cancel_button (QPushButton): Button to cancel everything.
        progress_bar_label (QLabel): Label to display the progress bar description.
        progress_bar (QProgressBar): Progress bar for visuals of task progress.
    """
    def __init__(self, data_retriever, downloader, data_dir):
        super().__init__()
        
        self.data_retriever = data_retriever
        self.downloader = downloader
        self.data_dir = data_dir
        self.video_maker = VideoMaker(self.update_progress_bar, data_dir)

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
        self.table_widget.setSortingEnabled(True)
        # enable button if row is selected
        self.table_widget.itemSelectionChanged.connect(self.handle_row_selection)
        # select all button
        self.select_all_button = QCheckBox("Select All")
        self.select_all_button.setChecked(True)
        self.select_all_button.clicked.connect(self.handle_select_all_click)

        #make dictionary of checkboxes for each action, 
        # make them checked as default, add to layout
        self.layout_checkboxes = QHBoxLayout()
        actions = [
            "FG Made", "Assists", "FG Missed", "Free Throw Attempts",
            "Rebounds", "Fouls Committed", "Fouls Drawn", "Turnovers",
            "Steals", "Blocks"
        ]
        self.checkboxes = {}
        for action in actions:
            checkbox = QCheckBox(action)
            checkbox.setChecked(True)
            self.checkboxes[action] = checkbox
            self.layout_checkboxes.addWidget(checkbox)

        # self.fg_made_box = QCheckBox("FG Made")
        # self.assists_box = QCheckBox("Assists")
        # self.fg_missed_box = QCheckBox("FG Missed")
        # self.fta_box = QCheckBox("Free Throw Attempts")
        # self.rebound_box = QCheckBox("Rebounds")
        # self.fouls_committed_box = QCheckBox("Fouls Committed")
        # self.fouls_drawn_box = QCheckBox("Fouls Drawn")
        # self.turnover_box = QCheckBox("Turnovers")
        # self.steal_box = QCheckBox("Steals")
        # self.block_box = QCheckBox("Blocks")

        # #enable all
        # self.fg_made_box.setChecked(True)
        # self.assists_box.setChecked(True)
        # self.fg_missed_box.setChecked(True)
        # self.fta_box.setChecked(True)
        # self.rebound_box.setChecked(True)
        # self.fouls_committed_box.setChecked(True)
        # self.fouls_drawn_box.setChecked(True)
        # self.turnover_box.setChecked(True)
        # self.steal_box.setChecked(True)
        # self.block_box.setChecked(True)

        #add checkboxes to horizontal layout
        # self.layout_checkboxes.addWidget(self.fg_made_box)
        # self.layout_checkboxes.addWidget(self.fg_missed_box)
        # self.layout_checkboxes.addWidget(self.assists_box)
        # self.layout_checkboxes.addWidget(self.fta_box)
        # self.layout_checkboxes.addWidget(self.rebound_box)
        # self.layout_checkboxes.addWidget(self.fouls_committed_box)
        # self.layout_checkboxes.addWidget(self.fouls_drawn_box)
        # self.layout_checkboxes.addWidget(self.turnover_box)
        # self.layout_checkboxes.addWidget(self.steal_box)
        # self.layout_checkboxes.addWidget(self.block_box)

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
        
        #add objects to layout
        self.layout.addWidget(self.table_widget)
        self.layout.addWidget(self.select_all_button)
        self.layout.addLayout(self.layout_checkboxes)
        self.layout.addWidget(self.progress_bar_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.create_video_button)
        self.layout.addWidget(self.cancel_button)

    def update_progress_bar(self, value, description):
        """Updates the progress bar value and label with the specified value and description.

        Args:
            value (int): Progress bar value (0-100).
            description (str): Text description that is displayed above the progress bar.
        """
        self.progress_bar.setValue(value)
        self.progress_bar_label.setText(description)

    def handle_row_selection(self):
        """Handles selection changes in the table widget.

        Update the currently selected game and enable the 'Create Video' button if a row is selected, 
        only when a video isn't being created.
        """
        selected_items = self.table_widget.selectedItems()
        
        #self.game_id = self.curr_game_log.iloc[self.table_widget.currentRow()]['Game_ID']
        if selected_items:
            self.game_id = selected_items[0].text()
            #print("Game ID Selected: ", self.game_id)
        #print("Type of game id:", type(self.game_id))
        
        #print("Selected game id from selected_items:", selected_items[0].text())
        #print("Selected game id from int selected_items:", int(selected_items[0].text()))
        
        # print("Current Row: ", self.table_widget.currentRow())
        # print("Selected game id from current row:", self.game_id)
        # need flag when highlighting different items while create video process occurring
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
        """Sets all action checkboxes to be checked or unchecked based on the 'Select All' checkbox state.
        
        """
        # if it's checked, and the user clicks it, uncheck all  
        checked = self.select_all_button.isChecked()
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(checked)
        # self.fg_made_box.setChecked(checked)
        # self.assists_box.setChecked(checked)
        # self.fg_missed_box.setChecked(checked)
        # self.fta_box.setChecked(checked)
        # self.rebound_box.setChecked(checked)
        # self.fouls_committed_box.setChecked(checked)
        # self.fouls_drawn_box.setChecked(checked)
        # self.turnover_box.setChecked(checked)
        # self.steal_box.setChecked(checked)
        # self.block_box.setChecked(checked)

    def cleanup(self):
        """Resets UI elements to their initial state.

        Re-enables the create video button, removes the progress bar updates on the UI,
        disables the cancel button, and resets any internal flags.
        """
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
        self.progress_bar_label.setVisible(False)
        self.update_progress_bar(0, "")
        
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Cancel")

        self.create_video_flag = False
    
    def clean_data_dir(self):
        """Deletes all files in the data directory.

        """
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
        # create/recreate data folder
        os.makedirs(self.data_dir)

    def cancel_tasks(self):
        """Cancels any ongoing tasks for getting links, downloading, or editing the video.
        
        """
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
        """Gets event links, downloads all clips needed, and stitches them together.

        Clears the data directory, filters the needed events using what the user selected,
        gets links to all of these events and downloads them, and concatenates the clips together.
        During this whole process, the user is updated with progress information. Once the video is
        completed, the user is informed that the video has been created successfully.

        Raises:
            Exception: If any step fails, display a message box to the user and cleans up UI state.
        """
        # print("Player ID:", self.player_id)
        # print("Game ID:", self.game_id)
        # delete data folder if it exists

        
        # create/recreate data folder
        self.clean_data_dir()
        
        self.create_video_button.setEnabled(False)
        self.create_video_flag = True
        # make a set to store the boxes checked
        boxes_checked = set()
        
        # if self.fg_made_box.isChecked() or self.assists_box.isChecked():
        #     boxes_checked.add(1)
        # if self.fg_missed_box.isChecked() or self.block_box.isChecked():
        #     boxes_checked.add(2)
        # if self.fta_box.isChecked():
        #     boxes_checked.add(3)
        # if self.rebound_box.isChecked():
        #     boxes_checked.add(4)
        # if self.turnover_box.isChecked() or self.steal_box.isChecked():
        #     boxes_checked.add(5)
        # if self.fouls_committed_box.isChecked() or self.fouls_drawn_box.isChecked():
        #     boxes_checked.add(6)

        # check which boxes are checked, add corresponding event types to boxes_checked
        if self.checkboxes["FG Made"].isChecked() or self.checkboxes["Assists"].isChecked():
            boxes_checked.add(EventMsgType.FIELD_GOAL_MADE.value)
        if self.checkboxes["FG Missed"].isChecked() or self.checkboxes["Blocks"].isChecked():
            boxes_checked.add(EventMsgType.FIELD_GOAL_MISSED.value)
        if self.checkboxes["Free Throw Attempts"].isChecked():
            boxes_checked.add(EventMsgType.FREE_THROW_ATTEMPT.value)
        if self.checkboxes["Rebounds"].isChecked():
            boxes_checked.add(EventMsgType.REBOUND.value)
        if self.checkboxes["Turnovers"].isChecked() or self.checkboxes["Steals"].isChecked():
            boxes_checked.add(EventMsgType.TURNOVER.value)
        if self.checkboxes["Fouls Committed"].isChecked() or self.checkboxes["Fouls Drawn"].isChecked():
            boxes_checked.add(EventMsgType.FOUL.value)
        
        # get all event ids relating to the player
        event_ids = self.data_retriever.get_event_ids(self.game_id, self.player_id, boxes_checked)
        
        # if self.fg_made_box.isChecked() and not self.assists_box.isChecked():
        #     event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 1) & (event_ids['PLAYER1_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 1)]
        # if self.assists_box.isChecked() and not self.fg_made_box.isChecked():
        #     event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 1) & (event_ids['PLAYER2_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 1)]
        # if self.steal_box.isChecked() and not self.turnover_box.isChecked():
        #     event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 5) & (event_ids['PLAYER2_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 5)]
        # if self.turnover_box.isChecked() and not self.steal_box.isChecked():
        #     event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 5) & (event_ids['PLAYER1_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 5)]
        # if self.block_box.isChecked() and not self.fg_missed_box.isChecked():
        #     event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 2) & (event_ids['PLAYER3_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 2)]
        # if self.fouls_committed_box.isChecked() and not self.fouls_drawn_box.isChecked():
        #     event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 6) & (event_ids['PLAYER1_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 6)]
        # if self.fouls_drawn_box.isChecked() and not self.fouls_committed_box.isChecked():
        #     event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == 6) & (event_ids['PLAYER2_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != 6)]
        
        
        # check edge cases where only one action is selected, filter out unwanted events
        if self.checkboxes["FG Made"].isChecked() and not self.checkboxes["Assists"].isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == EventMsgType.FIELD_GOAL_MADE.value) & (event_ids['PLAYER1_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != EventMsgType.FIELD_GOAL_MADE.value)]
        elif self.checkboxes["Assists"].isChecked() and not self.checkboxes["FG Made"].isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == EventMsgType.FIELD_GOAL_MADE.value) & (event_ids['PLAYER2_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != EventMsgType.FIELD_GOAL_MADE.value)]
        
        if self.checkboxes["Fouls Committed"].isChecked() and not self.checkboxes["Fouls Drawn"].isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == EventMsgType.FOUL.value) & (event_ids['PLAYER1_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != EventMsgType.FOUL.value)]
        elif self.checkboxes["Fouls Drawn"].isChecked() and not self.checkboxes["Fouls Committed"].isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == EventMsgType.FOUL.value) & (event_ids['PLAYER2_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != EventMsgType.FOUL.value)]
        
        if self.checkboxes["Steals"].isChecked() and not self.checkboxes["Turnovers"].isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == EventMsgType.TURNOVER.value) & (event_ids['PLAYER2_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != EventMsgType.TURNOVER.value)]
        elif self.checkboxes["Turnovers"].isChecked() and not self.checkboxes["Steals"].isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == EventMsgType.TURNOVER.value) & (event_ids['PLAYER1_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != EventMsgType.TURNOVER.value)]
        
        if self.checkboxes["Blocks"].isChecked() and not self.checkboxes["FG Missed"].isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == EventMsgType.FIELD_GOAL_MISSED.value) & (event_ids['PLAYER3_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != EventMsgType.FIELD_GOAL_MISSED.value)]
        elif self.checkboxes["FG Missed"].isChecked() and not self.checkboxes["Blocks"].isChecked():
            event_ids = event_ids.loc[((event_ids['EVENTMSGTYPE'] == EventMsgType.FIELD_GOAL_MISSED.value) & (event_ids['PLAYER1_ID'] == self.player_id)) | (event_ids['EVENTMSGTYPE'] != EventMsgType.FIELD_GOAL_MISSED.value)]

        # after filter, check if event_ids is empty
        # if empty, show error message to user and return
        if event_ids.empty:
            QMessageBox.critical(self, "Error: No Clips Found", "No clips found for the selected game and actions. Please try again.")
            self.cleanup()
            return
        
        self.progress_bar_label.setVisible(True)
        self.progress_bar.setVisible(True)
        self.update_progress_bar(0, "Getting Links...")

        self.get_links_task = asyncio.create_task(self.data_retriever.get_download_links_async(self.game_id, event_ids, self.update_progress_bar))
        try:
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
        
        self.update_progress_bar(0, "Downloading clips...")
        # call download_links to download all the vids
        self.download_task = asyncio.create_task(self.downloader.download_files(event_ids, self.update_progress_bar))
        try:
            self.cancel_button.setEnabled(True)
            event_ids = await self.download_task
            #event_ids.to_csv('event_ids_with_filepath.csv', index = False)
        except asyncio.CancelledError:
            print("Downloading was cancelled by user")
            # might have downloaded some files, delete data folder
            self.clean_data_dir()
            self.cleanup()
            return
        except Exception as e:
            print(f"An error occurred while downloading: {e}")
            self.cleanup()
            QMessageBox.critical(self, "An error occurred while downloading:", f"{e}\nPlease try creating the video again.")

        self.update_progress_bar(0, "Editing video...")
        # edit the videos together

        # logger = MyProgressBarLogger()
        # logger.progress_bar_values.connect(self.update_progress_bar)

        # make cancel button click stop moviepy editing
        # self.cancel_button.clicked.connect(logger.cancel)

        self.edit_task = asyncio.create_task(self.video_maker.make_final_vid(event_ids['FILE_PATH'].tolist()))
        try:
            self.cancel_button.setEnabled(True)
            await self.edit_task
        except IOError as e:
            print(f"IOError caught in game_log_table: {e}")
            #self.video_maker.cancel_editing()
            self.clean_data_dir()
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
            await asyncio.sleep(0.1)
            self.clean_data_dir()
            self.cleanup()
            return
        except Exception as e:
            print(f"An error occurred while editing: {e}")
            #self.video_maker.cancel_editing()
            #self.clean_data_dir()
            self.cleanup()
            return
        # if no exceptions raised
        else:
            reply = QMessageBox.information(self, "Success", "Video created successfully! Would you like to open the file?", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                os.startfile(os.path.join(self.data_dir, "final_vid.mp4"))

        # clean up
        self.cleanup()

    # fetch game log, fill table with it
    def update_table(self, player_id, season, season_type):
        """Gets and displays the game log on the UI.

        Given the player ID, season, and season type, get the game log
        and fill the table widget with the relevant data for the user to view.

        Args:
            player_id (int): The NBA player ID.
            season (str): The season string (i.e. "2020-21").
            season_type (str): The type of season (i.e. "Regular Season", "Playoffs", etc).
        """
        # set current game id to None
        self.game_id = None

        # set sort to false so sorting while updating table doesn't cause
        # white spaces in cells
        self.table_widget.setSortingEnabled(False)
        # disable updates for now so you can update all at once later
        self.table_widget.setUpdatesEnabled(False)
        # block signals for now, don't need to emit signals while updating
        self.table_widget.blockSignals(True)

        # clear table
        self.table_widget.clear()

        # get game log for player
        # FIND WAY TO GET GAME ID WITHOUT DISPLAYING IT LATER
        self.curr_game_log = self.data_retriever.get_game_log(player_id, season, season_type)
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
        
        self.table_widget.setUpdatesEnabled(True)
        self.table_widget.blockSignals(False)
