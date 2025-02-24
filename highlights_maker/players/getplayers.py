import os
from nba_api.stats.static import players
import pandas as pd


def get_active_players():
    # get_players returns a list of dictionaries, each representing a player.
    if not os.path.exists('players.csv'):
        nba_players = players.get_players()
        df = pd.DataFrame(nba_players)
        active_players = df[df['is_active'] == True]
        active_players.to_csv('players.csv', index = False)
        print('Active Players data created.')
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
        return player.iloc[0]['id']
        


def main():
    get_active_players()
    get_player_id('Kevin Durant')

if __name__ == '__main__':
    main()
    
