import sys
import asyncio
from qasync import QEventLoop
from NBAHighlightsMaker.players.getplayers import DataRetriever
from NBAHighlightsMaker.ui.ui import HighlightsUI
from PySide6.QtWidgets import (QApplication)

# make classes and start up the ui
def startup():
    app = QApplication(sys.argv)

    # integrated event loop for pyside loop and asyncio's loop
    loop = QEventLoop(app)
    # set loop as current asyncio event loop
    asyncio.set_event_loop(loop)

    data_retriever = DataRetriever()
    window = HighlightsUI(data_retriever)
    window.show()
    with loop:
        # later change this to wait for shutdown signal, then cleanup
        sys.exit(loop.run_forever())

if __name__ == "__main__":
    startup()