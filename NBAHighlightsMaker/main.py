import sys
from NBAHighlightsMaker.players.getplayers import DataRetriever
from NBAHighlightsMaker.ui.ui import HighlightsUI
from PySide6.QtWidgets import (QApplication)

#make classes and start up the ui
def startup():
    data_retriever = DataRetriever()
    app = QApplication(sys.argv)
    window = HighlightsUI(data_retriever)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    startup()
