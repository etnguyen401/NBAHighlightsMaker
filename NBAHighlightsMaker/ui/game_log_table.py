"""Widget displaying a game log, allowing the user to select a game and actions to create a video of all relevant events.

This module contains the GameLogTable class, a widget which displays a list of all games
the selected player participated in. The user can select a game from the table and
which event types they want to include in the video. When a game is selected, the "Create Video" 
button is enabled, allowing the user to start the process of downloading all of the clips and 
stitching them together to form one video. Once the process is completed, a pop-up will inform 
the user that the video has been created and if they want to open it immediately.
"""
import time
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QCheckBox, QPushButton, QTableWidget, QWidget, QTableWidgetItem, QMessageBox
from NBAHighlightsMaker.editor.editor import VideoMaker
from NBAHighlightsMaker.common.enums import EventMsgType
import os
import shutil
import asyncio

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
        action_type_boxes (dict): Dictionary of checkboxes for each possible action.
        layout_action_type_boxes (QHBoxLayout): Horizontal layout for the action_type_boxes.
        create_video_button (QPushButton): Button to start video creation.
        cancel_button (QPushButton): Button to cancel everything.
        progress_bar_label (QLabel): Label to display the progress bar description.
        progress_bar (QProgressBar): Progress bar for visuals of task progress.
    """
    def __init__(self, data_retriever, downloader, data_dir):
        super().__init__()
        
        self.data_retriever = data_retriever
        self.downloader = downloader
        self.data_dir = os.path.join(data_dir, 'vids')
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

        # make dictionary of checkboxes for each action, 
        # make them checked as default, add to layout
        self.layout_action_type_boxes = QHBoxLayout()
        
        # actions = [
        #     "FG Made", "Assists", "FG Missed", "Free Throw Attempts",
        #     "Rebounds", "Fouls Committed", "Fouls Drawn", "Turnovers",
        #     "Steals", "Blocks"
        # ]
        actions = [
            "2PT", "3PT", "Assists", "Rebound", "Block",
            "Steal", "Turnover", "Foul", 
            "Freethrow", "Jumpball"
        ]
        self.action_type_boxes = {}
        self.create_checkboxes(actions, self.action_type_boxes, self.layout_action_type_boxes, True)
        # for action in actions:
        #     checkbox = QCheckBox(action)
        #     checkbox.setChecked(True)
        #     self.action_type_boxes[action] = checkbox
        #     self.layout_action_type_boxes.addWidget(checkbox)

        
        self.layout_action_options_boxes = QHBoxLayout()  
        action_options = [
            "Field Goals Made",
            "Field Goals Missed",
            "Fouls Committed",
            "Fouls Drawn",
            "Free Throws Made",
            "Free Throws Missed"
        ]
        self.action_options_boxes = {}
        self.create_checkboxes(action_options, self.action_options_boxes, self.layout_action_options_boxes, True)
        # make each of the action option boxes invisible
        # for option in action_options:
        #     checkbox = QCheckBox(option)
        #     checkbox.setChecked(True)
        #     self.action_options_boxes[option] = checkbox
        #     checkbox.setVisible(False)
        #     self.layout_action_options_boxes.addWidget(checkbox)

        #make create video button
        self.create_video_button = QPushButton("Create Video")
        self.create_video_button.setEnabled(False)
        self.create_video_button.setToolTip("Select a row to choose what game you want to make highlights of to enable this button.")
        
        # when button clicked, get game id and player id and begin download + edit
        # handle_create_vid_click is async, so use lambda to create task
        self.create_video_button.clicked.connect(
            lambda: asyncio.create_task(self.handle_create_vid_click())
        )

        # make cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_tasks)

        # make progress bar and label
        self.progress_bar_label = QLabel("")
        self.progress_bar_label.setVisible(False)
        self.progress_bar = QProgressBar(self)

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        # add objects to layout
        self.layout.addWidget(self.table_widget)
        self.layout.addWidget(self.select_all_button)
        self.layout.addLayout(self.layout_action_type_boxes)
        self.layout.addLayout(self.layout_action_options_boxes)
        self.layout.addWidget(self.progress_bar_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.create_video_button)
        self.layout.addWidget(self.cancel_button)

    def create_checkboxes(self, labels, dict, layout, setVisible):
        """Creates checkboxes for each label, adds them to the specified layout, and stores it.

        Args:
            labels (list): List of strings representing the labels for the checkboxes.
            dict (dict): Dictionary to store the created checkboxes with labels as keys.
            layout (QHBoxLayout): Layout to which the checkboxes will be added.
            setVisible (bool): Whether to set the checkboxes as visible or not.
        """
        for label in labels:
            checkbox = QCheckBox(label)
            checkbox.setChecked(True)
            checkbox.setVisible(setVisible)
            dict[label] = checkbox
            layout.addWidget(checkbox)
        
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
        
        if selected_items:
            self.game_id = selected_items[0].text()
        
        # need flag when highlighting different items while create video process occurring
        if selected_items and self.create_video_flag == False:
            self.create_video_button.setEnabled(True)  
        else:
            self.create_video_button.setEnabled(False)
    
    def handle_select_all_click(self):
        """Sets all action type checkboxes to be checked or unchecked based on the 'Select All' checkbox state.
        
        """
        # if it's checked, and the user clicks it, uncheck all  
        checked = self.select_all_button.isChecked()
        for checkbox in self.action_type_boxes.values():
            checkbox.setChecked(checked)
        for checkbox in self.action_options_boxes.values():
            checkbox.setChecked(checked)

    def cleanup(self):
        """Resets UI elements to their initial state.

        Re-enables the create video button, removes the progress bar updates on the UI,
        disables the cancel button, and resets any internal flags.
        """
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
        # create/recreate data folder
        self.clean_data_dir()

        self.create_video_button.setEnabled(False)
        self.create_video_flag = True
        # make a set to store the boxes checked
        wanted_action_options = set()
        wanted_actions = set()

        # add desired actions/options to sets
        for action in self.action_type_boxes:
            if self.action_type_boxes[action].isChecked():
                wanted_actions.add(action.lower())
                print(f"Added {action.lower()} to wanted_actions")

        for action_option in self.action_options_boxes:
            if self.action_options_boxes[action_option].isChecked():
                wanted_action_options.add(action_option)
                print(f"Added {action_option} to wanted_action_options")
        
        # get all event ids relating to the player
        event_ids = self.data_retriever.get_event_ids(self.game_id, self.player_id, wanted_actions, wanted_action_options)

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
            self.cleanup()
            return
        except Exception as e:
            print(f"An error occurred while getting links: {e}")
            print("Returning...")
            self.cleanup()
            QMessageBox.critical(self, "An error occurred while getting links:", f"{e}\nPlease try creating the video again.")
            return
        
        self.update_progress_bar(0, "Downloading clips...")
        self.download_task = asyncio.create_task(self.downloader.download_files(event_ids, self.update_progress_bar))
        try:
            self.cancel_button.setEnabled(True)
            event_ids = await self.download_task
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

        self.edit_task = asyncio.create_task(self.video_maker.make_final_vid(event_ids['FILE_PATH'].tolist()))
        try:
            self.cancel_button.setEnabled(True)
            await self.edit_task
        except IOError as e:
            print(f"IOError caught in game_log_table: {e}")
            self.clean_data_dir()
            self.cleanup()
            return
        except asyncio.CancelledError:
            print("AsyncIO CancelledError by editing task.")
            await asyncio.sleep(0.1)
            self.clean_data_dir()
            self.cleanup()
            return
        except Exception as e:
            print(f"An error occurred while editing: {e}")
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
