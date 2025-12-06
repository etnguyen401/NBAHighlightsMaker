import asyncio
import aiohttp
import pytest
from NBAHighlightsMaker.players.getplayers import DataRetriever
from fake_useragent import UserAgent
from NBAHighlightsMaker.common.enums import EventMsgType
import os
import pandas as pd

@pytest.fixture(scope='session')
def make_data(tmp_path_factory):
    """Makes a temporary directory for the session and cleans up after.
    """
    # /tmp/pytest/data0
    data_dir = tmp_path_factory.mktemp('data')

    ua = UserAgent(browsers=['Opera', 'Safari', 'Firefox'], platforms='desktop')
    data_retriever = DataRetriever(ua, data_dir)
    
    return data_dir, data_retriever

def test_get_all_players_integration(make_data):

    data_dir, data_retriever = make_data
    # need csv directory to exist before storing data inside
    csv_dir = data_dir / 'csv'
    csv_dir.mkdir(parents=True, exist_ok=True)

    # make dataretriever instance

    # call to get all players
    all_players_df = data_retriever.get_all_players()
    
    # check that dataframe is bigger than 5000
    assert len(all_players_df) > 5000, "The players DataFrame should be length > 5000."
    
    # check that the columns we need exist and the unneeded ones don't
    expected_columns = {'id', 'full_name'}
    assert expected_columns == set(all_players_df.columns), "The DataFrame should contain the expected columns, nothing else."

    # check that the CSV file was created
    csv_path = os.path.join(data_dir, 'csv', 'players_all.csv')
    assert os.path.exists(csv_path), "The players_all.csv file should exist."

    # read csv and see if it equals above dataframe
    csv_df = data_retriever.get_all_players()
    assert csv_df.equals(all_players_df), "The DataFrame read from CSV should equal the original DataFrame."
    
def test_get_game_log_integration(make_data):

    _, data_retriever = make_data  

    # use a kevin durant's player id
    player_id = "201142"
    season = "2024-25"
    season_type = "Regular Season"

    # call to get game log
    game_log_df = data_retriever.get_game_log(player_id, season, season_type)
    
    # check that dataframe is bigger than 100
    assert len(game_log_df) == 62, "KD Played 62 games in the 2024-25 regular season."
    
    # check that the columns we need exist
    expected_columns = {'Game_ID', 'GAME_DATE', 'MATCHUP', 'WL', 'MIN', 'FGM', 'FGA', 'FTM', 'FTA', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS'}
    assert expected_columns == set(game_log_df.columns), "The DataFrame should contain the expected columns."

def test_get_event_ids_integration(make_data):
    _, data_retriever = make_data  

    # use kevin durant's player id
    game_id = "0022401088"
    player_id = 201142
    wanted_actions = {'2pt', '3pt'}
    wanted_actions_options = {'Field Goals Made'}

    # call to get event ids
    event_ids_df = data_retriever.get_event_ids(game_id, player_id, wanted_actions, wanted_actions_options)
    print(event_ids_df.head())
    # check that the size is exactly 5 fgm on this game
    assert len(event_ids_df) == 5, "The dataframe should be length 5."

    # check that the columns we need exist
    expected_columns = {'actionNumber', 'actionType', 'subType', 'personId', 'description', 'shotResult', 'assistPersonId', 'foulDrawnPersonId', 'blockPersonId'}
    assert expected_columns == set(event_ids_df.columns), "The DataFrame should contain the expected columns."

@pytest.mark.asyncio
async def test_get_download_link_integration(make_data):
    _, data_retriever = make_data

    # make game id
    game_id = "0042400232"

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
            'VIDEO_LINK': [""],
            'DESCRIPTION': [""],
    })

    # get the one row of dataframe to download
    row = list(event_ids.itertuples(index=True))[0]

    # make a dummy update progress bar function
    string = ""
    def update_progress_bar(value, description):
        nonlocal string
        string = f"Progress: {value}%, Description: {description}"
    
    # make semaphore
    semaphore = asyncio.Semaphore(3)

    # make lock
    lock = asyncio.Lock()
    # make aiohttp session
    async with aiohttp.ClientSession() as session:
        # call to get download link
        await data_retriever.get_download_link(session, game_id, row, event_ids, update_progress_bar, semaphore, lock)
    
    assert string == "Progress: 100%, Description: Get link for: J. McDaniels 24' 3PT  (3 PTS) (J. Randle 1 AST)"

    # check that we get a link
    assert event_ids.loc[event_ids['actionNumber'] == 8, 'VIDEO_LINK'].values[0] != "", "The VIDEO_LINK should not be empty."
    

