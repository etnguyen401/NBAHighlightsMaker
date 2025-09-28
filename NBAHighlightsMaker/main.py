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
import time


def startup():
    """Initializes the NBA Highlights Maker application.

    Initializes the Qt application and event loop, creates the data retriever and
    downloader objects, and launches the main window.
    """
    beginning = time.time()
    app = QApplication(sys.argv)
    
    data_dir = os.path.join(os.getcwd(), 'data', 'vids')
    # integrated event loop for pyside loop and asyncio's loop
    loop = QEventLoop(app)
    
    # set loop as current asyncio event loop
    asyncio.set_event_loop(loop)
    
    start = time.time()
    ua = UserAgent(browsers=['Opera', 'Safari', 'Firefox'], platforms='desktop')
    #ua = UserAgent(browsers=['Edge'], platforms='desktop')
    print("UserAgent:", time.time() - start)
    
    start = time.time()
    data_retriever = DataRetriever(ua, data_dir)
    print("DataRetriever:", time.time() - start)
    
    start = time.time()
    downloader = Downloader(ua, data_dir)
    print("Downloader:", time.time() - start)
    
    # make the main window
    start = time.time()
    window = HighlightsUI(data_retriever, downloader, data_dir)
    print("HighlightsUI:", time.time() - start)
    window.show()

    # bring to front and activate window
    window.raise_()
    window.activateWindow()
    with loop:
        # later change this to wait for shutdown signal, then cleanup
        print("Total startup time:", time.time() - beginning)
        sys.exit(loop.run_forever())

if __name__ == "__main__":
    startup()