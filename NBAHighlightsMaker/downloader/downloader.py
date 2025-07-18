# import sys
import os
import asyncio
import aiohttp
import aiofiles
import random
#import time

# from NBAHighlightsMaker.players.getplayers import read_event_ids
#function that gets the event ids/links, and for each link,
#sets the browser to go to that url and download the video
#into the data folder
#IN FUTURE, LET USER SPECIFY WHERE TO DOWNLOAD?

class Downloader():
    def __init__(self, ua):
        self.data_dir = os.path.join(os.getcwd(), 'data', 'vids')
        os.makedirs(self.data_dir, exist_ok=True)
        # UserAgent object for random user agent
        self.ua = ua
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        }
        self.counter = 0
    
    async def download_file(self, session, event_ids, row,
                            file_path, update_progress_bar,
                            semaphore, lock):
        retry_count = 0
        error_msg_string = ''
        while retry_count < 3:
            async with semaphore:
                self.headers['User-Agent'] = self.ua.random
                time = random.uniform(0, 2.5)
                print(f"Sleeping for {time:.2f} seconds before downloading {row.EVENTNUM}.mp4...") 
                await asyncio.sleep(time)
                try:
                    async with session.get(row.VIDEO_LINK, headers=self.headers, timeout=30) as response:
                        if response.status == 200:
                            async with aiofiles.open(file_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(256000):
                                    await f.write(chunk)
                            print(f"Downloaded {row.VIDEO_LINK}")
                            async with lock:
                                # update dataframe with file path
                                event_ids.loc[row.Index, 'FILE_PATH'] = file_path
                                # update progress bar
                                self.counter += 1
                                value = int((self.counter) / len(event_ids) * 100)
                                update_progress_bar(value, f"Downloaded: {row.DESCRIPTION}")
                            return
                        elif response.status == 429:
                            print(f"Rate limit exceeded for {row.VIDEO_LINK}. Retrying after a delay...")
                            error_msg_string += f"Retry {retry_count + 1} failed: Rate limit exceeded, Response Status: {response.status}\n"
                            await asyncio.sleep(random.uniform(3, 7))
                            # Retry the download after waiting
                            retry_count += 1
                        else:
                            print(f"Failed to download {row.VIDEO_LINK}: {response.status}")
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
        print(f"Failed to download {row.VIDEO_LINK}. Skipping.")
        raise Exception(f"Max retries exceeded while getting link for event {row.EVENTNUM}: {row.HOMEDESCRIPTION}.\n\n{error_msg_string}")
        
    async def download_files(self, event_ids, update_progress_bar):
        event_ids['FILE_PATH'] = ''
        event_ids = event_ids.reset_index(drop=True)
        connector = aiohttp.TCPConnector(limit=0)
        semaphore = asyncio.Semaphore(2)
        async with aiohttp.ClientSession(
            connector = connector,
            headers = self.headers
        ) as session:
            tasks = []
            lock = asyncio.Lock()
            for row in event_ids.itertuples(index=True):
                file_path = os.path.join(self.data_dir, "{}.mp4".format(row.EVENTNUM))
                # Create download tasks
                tasks.append(self.download_file(session, event_ids, row, file_path, update_progress_bar,
                                                semaphore, lock))
            await asyncio.gather(*tasks)
        print("Finished Download")
        # reset counter
        self.counter = 0
        return event_ids
    
    # async def download_links(self, event_ids, update_progress_bar):
    #     # make new column in event ids to store file path
    #     event_ids['FILE_PATH'] = ''
    #     event_ids = event_ids.reset_index(drop=True)
    #     for index, row in event_ids.iterrows():
    #         desc = row['DESCRIPTION']
    #         dl_link = row['VIDEO_LINK']    
    #         event_num = row['EVENTNUM']
    #         #start browser for each link
    #         browser = await zd.start(headless=True, 
    #                                 browser_args=["--mute-audio"])
    #         # go to link
    #         tab = await browser.get(dl_link)
    #         await tab.set_download_path(self.data_dir)
    #         print("Sleeping before download of {}...".format(event_num))
    #         await asyncio.sleep(random.uniform(0.5, 1.5))
    #         # wait for page to load
    #         #await tab
    #         # download to correct path (might need to get 
    #         # another WCTIMESTRING column
    #         # for better names)
    #         await tab.download_file(dl_link, "{}.mp4".format(event_num))
    #         #sleep for random time
    #         value = int((index + 1) / len(event_ids) * 100)
    #         update_progress_bar(value, "Downloading: {}".format(desc))
    #         print("Sleeping after download of {}.mp4...".format(event_num))
    #         await asyncio.sleep(random.uniform(3.0, 4.0))
    #         event_ids.loc[index, 'FILE_PATH'] = os.path.join(self.data_dir, "{}.mp4".format(event_num))
    #         await browser.stop()
    #     print("Finished Download")
    #     return event_ids
    
    # async def test_download(self):
    #     data_dir = os.path.join(os.getcwd(), 'data', 'test')
    #     os.makedirs(data_dir, exist_ok=True)
    #     url = 'https://videos.nba.com/nba/pbp/media/2025/03/04/0022400889/14/bd1edcac-5099-e0de-053c-2c6d71808c05_1280x720.mp4'

    #     #start browser for each link
    #     browser = await zd.start(headless=True, 
    #                             browser_args=["--mute-audio"])
        
    #     # go to link
    #     tab = await browser.get(url)
    #     await tab.set_download_path(data_dir)
    #     # wait for page to load
    #     await tab
    #     print("Sleeping before download of {}...".format('test'))
    #     await asyncio.sleep(random.uniform(0.5, 1.5))
    #     # download to correct path (might need to get 
    #     # another WCTIMESTRING column
    #     # for better names)
    #     test = await tab.download_file(url, 'test.mp4')
    #     print("Downloaded file: ", test)
    #     #sleep for random time
    #     print("Sleeping after download of {}...".format('test'))
    #     await asyncio.sleep(random.uniform(2.0, 4.0))

    #     await browser.stop()

async def test_async_download(mySession, url, headers):
    # async with aiohttp.ClientSession() as session:
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
    ]
    # headers = {
    #     'User-Agent': random.choice(user_agents),
    # }
    # headers['User-Agent'] = random.choice(user_agents)
    #url = 'https://videos.nba.com/nba/pbp/media/2025/04/08/0022401153/403/a1486895-a7a7-e6fe-4516-da6bfbc7cc4d_1280x720.mp4'
    async with mySession.get(url, headers=headers, timeout=30) as response:
        print("Got the request.")
        if response.status == 200:
            print("Response:", response.headers)
        else:
            print(f"Failed to download {url}: {response.status}")


def main():
    # read events id file (ADD FUNCTIONALITY TO MAKE SURE IT HAS THE LINKS, NOT JUST EVENT IDS)
    # event_ids = read_event_ids()
    #downloader = Downloader()
    asyncio.run(test_async_download())

    #asyncio.run(test_download())


if __name__ == '__main__':
    main()