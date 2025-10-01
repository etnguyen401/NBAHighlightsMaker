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
from fake_useragent import UserAgent
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
    
    data_dir = os.path.join(os.getcwd(), 'data', 'vids')
    # integrated event loop for pyside loop and asyncio's loop
    loop = QEventLoop(app)
    
    # set loop as current asyncio event loop
    asyncio.set_event_loop(loop)
    
    # useragents from these browsers are more likely to succeed
    ua = UserAgent(browsers=['Opera', 'Safari', 'Firefox'], platforms='desktop')
    
    data_retriever = DataRetriever(ua, data_dir)
    
    downloader = Downloader(ua, data_dir)
    
    # make the main window
    window = HighlightsUI(data_retriever, downloader, data_dir)
    window.show()

    # bring to front and activate window to grab attention
    window.raise_()
    window.activateWindow()
    with loop:
        sys.exit(loop.run_forever())

if __name__ == "__main__":
    startup()