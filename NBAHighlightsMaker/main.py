import sys
import asyncio
from fake_useragent import UserAgent
from qasync import QEventLoop
from NBAHighlightsMaker.players.getplayers import DataRetriever
from NBAHighlightsMaker.downloader.downloader import Downloader
from NBAHighlightsMaker.ui.ui import HighlightsUI
from PySide6.QtWidgets import QApplication

# make classes and start up the ui
def startup():
    app = QApplication(sys.argv)

    # integrated event loop for pyside loop and asyncio's loop
    loop = QEventLoop(app)
    # set loop as current asyncio event loop
    asyncio.set_event_loop(loop)
    ua = UserAgent(browsers=['Opera', 'Safari', 'Firefox'], platforms='desktop')
    #ua = UserAgent(browsers=['Edge'], platforms='desktop')
    data_retriever = DataRetriever(ua)
    downloader = Downloader(ua)
    window = HighlightsUI(data_retriever, downloader)
    window.show()
    with loop:
        # later change this to wait for shutdown signal, then cleanup
        sys.exit(loop.run_forever())

if __name__ == "__main__":
    startup()