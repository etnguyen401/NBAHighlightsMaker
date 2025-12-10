"""Main entry point for the application.

This module starts up the application, runs the main event loop,
creates class instances used to get data for later use, 
and launches the main UI window.

Typical usage example:
    if __name__ == "__main__":
        startup()
"""
import os
import sys
import asyncio
from qasync import QEventLoop
from NBAHighlightsMaker.players.getplayers import DataRetriever
from NBAHighlightsMaker.downloader.downloader import Downloader
from NBAHighlightsMaker.ui.ui import HighlightsUI
from PySide6.QtWidgets import QApplication

def startup():
    """Initializes the NBA Highlights Maker application.

    Initializes the Qt application and event loop, creates the data retriever and
    downloader objects, and launches the main window.
    """
    app = QApplication(sys.argv)
    
    data_dir = os.path.join(os.getcwd(), 'data')
    
    # create data directory if it doesn't exist
    os.makedirs(os.path.join(data_dir, 'vids'), exist_ok=True)
    os.makedirs(os.path.join(data_dir, 'csv'), exist_ok=True)
    
    user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3.1 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15',
    ]
    
    data_retriever = DataRetriever(user_agents, data_dir)
    
    downloader = Downloader(user_agents, data_dir)
    
    # make the main window
    window = HighlightsUI(data_retriever, downloader, data_dir)
    window.show()

    # bring to front and activate window to grab attention
    window.raise_()
    window.activateWindow()

    # integrated event loop for pyside loop and asyncio's loop
    loop = QEventLoop(app)
    
    # set loop as current asyncio event loop
    asyncio.set_event_loop(loop)

    with loop:
        
        sys.exit(loop.run_forever())

if __name__ == "__main__":
    startup()