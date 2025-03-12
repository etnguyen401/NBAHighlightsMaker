import os
import random
from nba_api.stats.static import players
from nba_api.stats.library.parameters import Season
from nba_api.stats.library.parameters import SeasonType
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import playbyplayv2
from nba_api.stats.endpoints import videoeventsasset
import pandas as pd
import requests
import time 

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
    'x-nba-stats-origin': 'stats',
    'Referer': 'https://stats.nba.com/',
}

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0'
]

def get_active_players():
    # get_players returns a list of dictionaries, each representing a player.
    if not os.path.exists('players.csv'):
        nba_players = players.get_players()
        df = pd.DataFrame(nba_players)
        active_players = df[df['is_active'] == True]
        active_players.to_csv('players.csv', index = False)
        print('Active Players data created.')
        time.sleep(1)
    else:
        print('Active Players data already exists.')

def get_player_id(full_name):
    if not os.path.exists('players.csv'):
        get_active_players()
    players = pd.read_csv('players.csv')
    player = players[players['full_name'] == full_name]

    if player.empty:
        return None
    else:
        print(player.iloc[0]['id'])
        time.sleep(1)
        return player.iloc[0]['id']
        
def get_game_log(player_id, season = Season.default, season_type = SeasonType.regular):
    if not os.path.exists('game_log.csv'):
        game_log = playergamelog.PlayerGameLog(player_id = player_id, season = season, season_type_all_star = season_type)
        game_log = game_log.get_data_frames()[0]
        game_log.to_csv('game_log.csv', index = False)
        time.sleep(1)
        return game_log
    else:
        #read as string so leading zeroes still there
        game_log = pd.read_csv('game_log.csv', converters = {'Game_ID': str})
        print("Game Log read from file.")    
        return game_log

# in future, user selects what game they want to see highlights from
# for now, we'll just use the first game in the game log
def get_game_id(game_log):
    return game_log.iloc[0]['Game_ID']

def get_event_ids(game_id, player_id):
    if not os.path.exists('event_ids.csv'):
        event_ids = playbyplayv2.PlayByPlayV2(game_id = game_id)
        event_ids = event_ids.get_data_frames()[0]
        # player2 id would be when something bad happens to player2
        # select rows where player1 id is the player we want and video is available
        # later provide an option for user to choose actions that they want (i.e field goals, assists, rebounds, blocks)
        event_ids = event_ids.loc[((event_ids['PLAYER1_ID'] == player_id) | (event_ids['PLAYER2_ID'] == player_id)) & (event_ids['VIDEO_AVAILABLE_FLAG'] == 1)]
        # filter to only get the event rows
        event_ids = event_ids['EVENTNUM']
        event_ids.to_csv('event_ids.csv', index = False)
        time.sleep(1)
        print("Got from API and saved to csv.")
        return event_ids
    else:
        # make sure to read event ids as strings so leading zeroes preserved
        event_ids = pd.read_csv('event_ids.csv')
        print("Read event ids from file.")
        return event_ids

def read_event_ids():
    event_ids = pd.read_csv('event_ids.csv')
    print("Read event ids from file.")
    return event_ids

#make another function to only get one link
# so you can retry if it fails later
def get_download_link(event_id, game_id):
    print("Getting download link: ")
    # get the download link
    
def get_download_links(game_id, event_ids):
    # add another column to event_ids for the download link
    event_ids['VIDEO_LINK'] = ''
    event_ids['DESCRIPTION'] = ''
    # for each event id
    for event_id in event_ids['EVENTNUM']:
        # get the download link and description
        #video_event = get_download_link(event_id, game_id)
        url = 'https://stats.nba.com/stats/videoeventsasset?GameEventID={}&GameID={}'.format(event_id, game_id)
        # randomize user agent
        headers['User-Agent'] = random.choice(user_agents)
        try:
            print("Requesting for event id: ", event_id)
            r = requests.get(url, headers=headers)
            # check if request was successful
            r.raise_for_status()
            # convert to json
            r_json = r.json()
            video_link = r_json['resultSets']['Meta']['videoUrls'][0]['lurl']
            desc = r_json['resultSets']['playlist'][0]['dsc']
            video_event = {'video': video_link, 'desc': desc}
            # add the link and description to event_ids
            # 1st part of loc filters rows, 2nd part is for columns
            event_ids.loc[event_ids['EVENTNUM'] == event_id, 'VIDEO_LINK'] = video_event['video']
            event_ids.loc[event_ids['EVENTNUM'] == event_id, 'DESCRIPTION'] = video_event['desc']
            # sleep
            print("Sleeping...")
            time.sleep(random.uniform(2.0, 4.0))
        except requests.exceptions.HTTPError as e:
            print("HTTP error: ", e)
        except requests.exceptions.ConnectionError as e:
            print("Connection error: ", e)
        except requests.exceptions.Timeout as e:
            print("Timeout error: ", e)
        except requests.exceptions.RequestException as e:
            print("Something else error: ", e)
    
    # update our file
    event_ids.to_csv('event_ids.csv', index = False)
    return event_ids

def test():
    nba_players = players.get_players()
    print("Number of players fetched: {}".format(len(nba_players)))
    nba_players[:5]

def main():
    get_active_players()
    player_id = get_player_id('Kevin Durant')
    game_log = get_game_log(player_id)
    game_id = get_game_id(game_log)
    print("Game ID: ", game_id)
    event_ids = get_event_ids(game_id, player_id)
    dl_links = get_download_links(game_id, event_ids)
    
if __name__ == '__main__':
    # test()
    main()
    
