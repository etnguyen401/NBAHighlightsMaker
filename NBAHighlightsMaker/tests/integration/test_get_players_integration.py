import pytest
from NBAHighlightsMaker.players.getplayers import DataRetriever
from fake_useragent import UserAgent
from NBAHighlightsMaker.common.enums import EventMsgType
import os

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

# playbyplayv2 from the nba_api library currently doesn't work, so this won't work either
def test_get_event_ids_integration(make_data):
    _, data_retriever = make_data  

    # use a kevin durant's player id
    game_id = "0022401088"
    player_id = "201142"
    boxes_checked = set()
    boxes_checked.add(EventMsgType.FIELD_GOAL_MADE.value)

    # call to get event ids
    event_ids_df = data_retriever.get_event_ids(game_id, player_id, boxes_checked)
    
    # check that the size is exactly 5 fgm on this game
    assert len(event_ids_df) == 5, "The dataframe should be length 5."

    # check that the columns we need exist
    expected_columns = {'EVENTNUM', 'EVENTMSGTYPE', 'HOMEDESCRIPTION', 'PLAYER1_ID', 'PLAYER2_ID', 'PLAYER3_ID', 'VIDEO_AVAILABLE_FLAG'}
    assert expected_columns == set(event_ids_df.columns), "The DataFrame should contain the expected columns."