"""Gets the NBA player data, game logs, and links for different clips.

This module contains the class DataRetriever, which gets player data and
game logs using the nba_api library. It also gets the links for the different
clips of the events the user wants to see. 
"""
import os
import random
import pandas as pd
import asyncio
import aiohttp
import json

class DataRetriever:
    """Fetches NBA player data, game logs, and links for different clips.

    This class uses the nba_api library to get player information and game logs, based
    on the respective parameters. It also gets the links for the different clips of the 
    events the user wants to see.

    Args:
        ua (UserAgent): UserAgent object from the fake_useragent library, used to generates random user agents.
        data_dir (str): Directory path for storing data files for future use.
    
    Attributes:
        headers (dict): HTTP headers used for requests to get video links.
        ua (UserAgent): UserAgent object from the fake_useragent library; used to generates random user agents.
        counter (int): Counter for tracking progress for getting links, used in progress bar UI.
        data_dir (str): Directory path for storing data files for future use.
    """
    def __init__(self, ua, data_dir):
        self.headers = {
            'Host': 'stats.nba.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true',
            'Connection': 'keep-alive',
            'Referer': 'https://stats.nba.com/',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
        self.ua = ua
        self.counter = 0
        self.data_dir = os.path.join(data_dir, 'csv')

    def get_all_players(self):
        """Retrieves a DataFrame of all NBA players in history, and saves the data.
        
        Returns:
            pandas.DataFrame: DataFrame containing the following columns:
                - id (str): Player ID
                - full_name (str): Full name of the player
        """
        file_path = os.path.join(self.data_dir, 'players_all.csv')
        
        if not os.path.exists(file_path):
            from nba_api.stats.static import players
            nba_players = players.get_players()
            df = pd.DataFrame(nba_players)[['id', 'full_name']]
            df.to_csv(file_path, index = False)
            print('All Players data created.')
            return df
        else:
            all_players = pd.read_csv(file_path)
            print('All Players data already exists.')
            return all_players
    
    def get_game_log(self, player_id, season, season_type):  
        """Retrieves a list of games played for a given player, year, and season type.

        Args:
            player_id (int): NBA player ID.
            season (str): NBA season represented by years (i.e "2020-21").
            season_type (str): NBA season type (i.e "Regular Season", "Playoffs", ...).

        Returns:
            pandas.DataFrame: Filtered DataFrame with the following columns:
                - Game_ID (str): Unique ID for the game.
                - GAME_DATE (str): Date of the game.
                - MATCHUP (str): Teams playing in the game.
                - WL (str): Win/Loss outcome for the player.
                - MIN (int): Minutes played.
                - FGM (int): Field Goals Made.
                - FGA (int): Field Goals Attempted.
                - FTM (int): Free Throws Made.
                - FTA (int): Free Throws Attempted.
                - REB (int): Rebounds.
                - AST (int): Assists.
                - STL (int): Steals.
                - BLK (int): Blocks.
                - TOV (int): Turnovers.
                - PF (int): Personal fouls.
                - PTS (int): Total points scored.
        """
        from nba_api.stats.endpoints import playergamelog
        game_log = playergamelog.PlayerGameLog(player_id = player_id, season = season, season_type_all_star = season_type)
        game_log = game_log.get_data_frames()[0]
        
        # only get rows where video is available, and the specified columns
        game_log = game_log.loc[game_log['VIDEO_AVAILABLE'] == 1, ['Game_ID', 'GAME_DATE', 'MATCHUP', 'WL', 'MIN', 'FGM', 'FGA', 'FTM', 'FTA', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']]
        # need to reset index after filtering, as pandas preserves old index
        # set drop = true so old index not put as column
        game_log = game_log.reset_index(drop = True)
        
        return game_log

    def get_event_ids(self, game_id, player_id, wanted_actions, wanted_action_options):
        """Retrieves events for a player in a specific game, filtered by event types desired by the user.

            Args:
                game_id (str): NBA game ID.
                player_id (int): NBA player ID.
                wanted_actions (set): Set of event types that the user wants to see.
                wanted_action_options (set): Set of specific options for certain event types, e.g 'Field Goals Made', 'Fouls Committed'.
                
            Returns:
                pandas.DataFrame: DataFrame of filtered events with the following columns:
                    - actionNumber (int): Unique event number within the game.
                    - actionType (int): Type of event (i.e field goal, rebound).
                    - subType (str): More specific information about the event.
                    - personId (int): ID of the main player involved in the event.
                    - description (str): Description of the event.
                    - shotResult (str): Result of the shot (i.e Made, Missed).
                    - assistPersonId (int): ID of the person who assisted the field goal.
                    - foulDrawnPersonId (int): ID of the person who drew the foul.
                    - blockPersonId (int): ID of the person who blocked the shot.
        """
        from nba_api.live.nba.endpoints import playbyplay
        try:
            pbp = playbyplay.PlayByPlay(game_id=game_id)
            df = pd.DataFrame(pbp.actions.get_dict())
            # choose rows that have the selected actions and involve the specified player
            # or are assists made by the player, only if assistes are wanted
            # or are fouls drawn by the player, only if fouls are wanted
            filtered_df = df.loc[
            (
                (df['actionType'].isin(wanted_actions)) & (df['personId'] == player_id)
            )
            |
                ((df['assistPersonId'] == player_id) & ('assists' in (wanted_actions)))
            |
                ((df['foulDrawnPersonId'] == player_id) & ('foul' in (wanted_actions)))
            , ['actionNumber', 'actionType', 'subType', 'personId', 'description', 'shotResult', 'assistPersonId', 'foulDrawnPersonId', 'blockPersonId']
            ]

            def filtering_helper(action_1, action_2, wanted_action_set, df, specified_action_vals, 
                                secondary_col, secondary_col_val):
                """Helper function to filter unneeded rows based on chosen action types and secondary conditions.
                
                There are situations where there are options for certain event types (e.g Field Goals Made/Missed) where
                and the user only selects one of the options. This function helps filter out the unwanted rows.
                
                Args:
                    action_1 (str): Primary action type to filter using.
                    action_2 (str): Secondary action type to filter using.
                    wanted_action_set (set): Set of wanted actions.
                    df (pandas.DataFrame): DataFrame to filter.
                    specified_action_vals (set): Set of specific action values to filter using.
                    secondary_col (str): Secondary column that we use the value from to filter out either action_1 or action_2.
                    secondary_col_val (any): The value that we match so we can filter the row out.
                
                Returns:
                    pandas.DataFrame: Filtered DataFrame.
                """
                if action_1 in wanted_action_set and action_2 not in wanted_action_set:
                    df = df[
                        ~((df['actionType'].isin(specified_action_vals)) & (df[secondary_col] == secondary_col_val))
                    ]
                elif action_2 in wanted_action_set and action_1 not in wanted_action_set:
                    df = df[
                        ~((df['actionType'].isin(specified_action_vals)) & (df[secondary_col] != secondary_col_val))
                    ]
                return df
            
            # if field goal made checked only, filter out missed shots
            # filter again for specific cases
            # if field goal made checked, and field goal missed not checked, only keep made shots
            # so select rows where it's a made shot or it's not a field goal attempt
            filtered_df = filtering_helper('Field Goals Made', 'Field Goals Missed', wanted_action_options, filtered_df,
                                {'2pt', '3pt'}, 'shotResult', 'Missed')
            
            # filter for fouls committed/drawn
            # if fouls committed is checked and fouls drawn isn't
            # only keep rows where the actionType is foul and the person who committed it isn't the player
            filtered_df = filtering_helper('Fouls Drawn', 'Fouls Committed', wanted_action_options, filtered_df,
                                        {'foul'}, 'personId', player_id)

            # filter for free throws made/missed
            filtered_df = filtering_helper('Free Throws Made', 'Free Throws Missed', wanted_action_options, filtered_df,
                                            {'freethrow'}, 'shotResult', 'Missed')
            
            # avoid duplicates when there is an offensive foul
            # select rows where it's not a turnover that has subtype offensive foul
            if 'foul' in wanted_actions and 'turnover' in wanted_actions:
                filtered_df = filtered_df[
                    ~((filtered_df['actionType'] == 'turnover') & (filtered_df['subType'] == 'offensive foul'))
                ]
            return filtered_df
        except json.JSONDecodeError:
            raise
        except Exception:
            raise
    
    async def get_download_link(self, session, game_id, row, event_ids, 
                                update_progress_bar, semaphore, lock):
        """Asynchronously fetches the video download link and description for an event.

        Generates a random user agent, sleeps for a random duration to stagger requests, and limits
        how many requests are happening at a time using a semaphore. Then, it makes a request to get the event link,
        updates the event_ids dataframe with the video link and description, and updates the progress bar.
        If the request fails, an error message is saved for that try, and this process is retried until max_retries is exceeded.

        Args:
            session (aiohttp.ClientSession): A session object used for the HTTP requests.
            game_id (str): The NBA game ID specified.
            row (pandas.Series): Row of data for the event containing actionNumber, etc.
            event_ids (pandas.DataFrame): DataFrame to update with video links and the description.
            update_progress_bar (Callable): Function to update the progress bar in the UI.
            semaphore (asyncio.Semaphore): Semaphore to limit concurrency.
            lock (asyncio.Lock): Lock to update the counter and dataframe event_ids safely.

        Raises:
            Exception: If maximum retries are exceeded for a request, raises an exception with details.
        """
        retry_count = 0
        error_msg_string = ''
        while retry_count < 3:
            async with semaphore:
                print(f"Retry count: {retry_count + 1}")
                self.headers['User-Agent'] = self.ua.random
                print("Headers: ", self.headers)
                time = random.uniform(0, 2.0)
                print(f"Sleeping for {time:.2f} seconds before getting link for {row.actionNumber}...")
                await asyncio.sleep(time)
                event_num = row.actionNumber
                if (row.actionType == 'steal') or (row.actionType == 'block'):
                    event_num -= 1
                elif row.actionType == 'turnover' and row.subType == 'offensive foul':
                    event_num -= 2
                url = 'https://stats.nba.com/stats/videoeventsasset?GameEventID={}&GameID={}'.format(event_num, game_id)
                print("Getting link for url: ", url)
                try:
                    async with session.get(url, headers=self.headers, timeout=5) as response:
                        if response.status == 200:
                            r_json = await response.json()
                            video_link = r_json['resultSets']['Meta']['videoUrls'][0]['lurl']
                            async with lock:
                                # add the link and description to event_ids
                                # 1st part of loc filters rows, 2nd part is for columns
                                event_ids.loc[event_ids['actionNumber'] == row.actionNumber, 'VIDEO_LINK'] = video_link
                                self.counter += 1
                                value = int((self.counter) / len(event_ids) * 100)
                                update_progress_bar(value, "Get link for: {}".format(row.description))
                            print("Sleeping...")
                            await asyncio.sleep(random.uniform(0, 1.0))
                            return
                        elif response.status == 429:
                            print(f"Rate limit exceeded for {row.actionNumber}. Retrying after a delay...")
                            error_msg_string += f"Retry {retry_count + 1} failed: Rate limit exceeded, Response Status: {response.status}\n"
                            await asyncio.sleep(random.uniform(3, 7))
                            # Retry the download after waiting
                            retry_count += 1
                        else:
                            print(f"Failed to get link for {row.actionNumber}, Response Status: {response.status}")
                            error_msg_string += f"Retry {retry_count + 1} failed: Response Status: {response.status}\n"
                            retry_count += 1
                except aiohttp.ClientConnectionError as e:
                    print(f"Client Connection error: {e}")
                    error_msg_string += f"Retry {retry_count + 1} failed: Client Connection error.\n"
                    retry_count += 1
                except aiohttp.ClientResponseError as e:
                    print(f"Response error: {e}")
                    error_msg_string += f"Try #{retry_count + 1} failed: Client Response error.\n"
                    retry_count += 1
                except aiohttp.ClientError as e:
                    print(f"Client error: {e}")
                    error_msg_string += f"Try #{retry_count + 1} failed: Client error.\n"
                    retry_count += 1
                except asyncio.TimeoutError as e:
                    print(f"Timeout error: {e}")
                    error_msg_string += f"Try #{retry_count + 1} failed: Timeout error.\n"
                    retry_count += 1
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    error_msg_string += f"Try #{retry_count + 1} failed: Unexpected error.\n"
                    retry_count += 1
        print(f"Max retries exceeded for {row.actionNumber}. Skipping.")
        raise Exception(f"Max retries exceeded while getting link for event {row.actionNumber}: {row.description}.\n\n{error_msg_string}")
        
    async def get_download_links_async(self, game_id, event_ids, update_progress_bar):
        """Creates a task for each event to fetch video download links and execute the tasks.

        Creates a ClientSession, and using that, creates a task for each event to fetch the video download link.
        The tasks are then run concurrently, but limited by a semaphore so only three requests happen at a time.
        As each task completes, the event_ids DataFrame is updated with the video links and descriptions.

        Args:
            game_id (str): NBA game ID.
            event_ids (pandas.DataFrame): DataFrame of event IDs.
            update_progress_bar (Callable): Function to update the progress bar.

        Returns:
            pandas.DataFrame: DataFrame with the following columns:
                - actionNumber (int): Unique event number within the game.
                - actionType (int): Type of event (i.e field goal, rebound).
                - subType (str): More specific information about the event.
                - personId (int): ID of the main player involved in the event.
                - description (str): Description of the event.
                - shotResult (str): Result of the shot (i.e Made, Missed).
                - assistPersonId (int): ID of the person who assisted the field goal.
                - foulDrawnPersonId (int): ID of the person who drew the foul.
                - blockPersonId (int): ID of the person who blocked the shot.
                - VIDEO_LINK (str): The download link for the event.
        """
        # make new columns for vid link and desc
        event_ids['VIDEO_LINK'] = ''
        # limit the number of concurrent requests
        semaphore = asyncio.Semaphore(3)
        async with aiohttp.ClientSession(
            headers = self.headers,
        ) as session:
            tasks = []
            lock = asyncio.Lock()
            for row in event_ids.itertuples(index=True):
                tasks.append(self.get_download_link(session, game_id, row, event_ids, 
                                                    update_progress_bar, semaphore, 
                                                    lock))
            try:
                await asyncio.gather(*tasks)
            except Exception:
                raise
            finally:
                self.counter = 0
        print("Finished getting download links.")
        return event_ids


