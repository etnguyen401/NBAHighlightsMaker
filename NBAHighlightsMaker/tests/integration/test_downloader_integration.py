import asyncio
import aiohttp
import pytest
from fake_useragent import UserAgent
import os
import pandas as pd
from NBAHighlightsMaker.downloader.downloader import Downloader

@pytest.fixture(scope='session')
def make_data(tmp_path_factory):
    """Makes a temporary directory for the session and cleans up after.
    """
    # /tmp/pytest/data0
    data_dir = tmp_path_factory.mktemp('data')

    ua = UserAgent(browsers=['Safari'], os = 'Mac OS X', platforms='desktop')
    downloader = Downloader(ua, data_dir)
    
    return data_dir, downloader

@pytest.mark.asyncio
async def test_downloader_integration(make_data):
    data_dir, downloader = make_data

    # make event_ids dataframe
    event_ids = pd.DataFrame({
            'actionNumber': [8],
            'actionType': ['3pt'],
            'subType': ['Jump Shot'],
            'personId': [1630183],
            'description': ["J. McDaniels 24' 3PT  (3 PTS) (J. Randle 1 AST)"],
            'assistPersonId': [203944],
            'foulDrawnPersonId': [""],
            'blockPersonId': [""],
            'VIDEO_LINK': ["https://videos.nba.com/nba/pbp/media/2025/05/08/0042400232/8/dfe9c790-8d47-da68-3e0e-b21f44a6c531_1280x720.mp4"],
            'FILE_PATH': [""],
    })
    # get the one row of dataframe to download
    row = list(event_ids.itertuples(index=True))[0]

    # make a dummy update progress bar function
    string = ""
    def update_progress_bar(value, description):
        nonlocal string
        string = f"Progress: {value}%, {description}"
    
    # make semaphore
    semaphore = asyncio.Semaphore(3)

    # make lock
    lock = asyncio.Lock()

    # make file path
    file_path = os.path.join(data_dir, "{}.mp4".format(row.actionNumber))

    # make aiohttp session
    async with aiohttp.ClientSession() as session:
        # call to download file
        await downloader.download_file(session, event_ids, row, file_path,
                                       update_progress_bar, semaphore, lock)
    
    # check that we get a new file path
    assert event_ids.loc[event_ids['actionNumber'] == 8, 'FILE_PATH'].values[0] != "", "The FILE_PATH should not be empty."

    # check progress bar
    assert string == f"Progress: 100%, Downloaded: {row.description}"

    # check that the file is downloaded
    assert os.path.isfile(file_path), "The downloaded file should exist."

    