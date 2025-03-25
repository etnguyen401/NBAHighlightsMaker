# import sys
import os

#use zendriver to act more like a human
import asyncio
import random
import time
import zendriver as zd
from NBAHighlightsMaker.players.getplayers import read_event_ids

#function that gets the event ids/links, and for each link,
#sets the browser to go to that url and download the video
#into the data folder
#IN FUTURE, LET USER SPECIFY WHERE TO DOWNLOAD?
async def download_links(event_ids):
    data_dir = os.path.join(os.getcwd(), 'data', 'vids')
    os.makedirs(data_dir, exist_ok=True)
    # make new column in event ids to store file path
    for index, row in event_ids.iterrows():
        desc = row['DESCRIPTION']
        dl_link = row['VIDEO_LINK']    
        event_num = row['EVENTNUM']
        #start browser for each link
        browser = await zd.start(headless=True, 
                                browser_args=["--mute-audio"])
        
        # go to link
        tab = await browser.get(dl_link)
        await tab.set_download_path(data_dir)
        # wait for page to load
        await tab
        print("Sleeping before download of {}...".format(desc))
        await asyncio.sleep(random.uniform(0.5, 1.5))
        # download to correct path (might need to get 
        # another WCTIMESTRING column
        # for better names)
        await tab.download_file(dl_link, "{}.mp4".format(event_num))
        #sleep for random time
        print("Sleeping after download of {}...".format(desc))
        await asyncio.sleep(random.uniform(2.0, 4.0))

        await browser.stop()

async def test_download():
    data_dir = os.path.join(os.getcwd(), 'data', 'test')
    os.makedirs(data_dir, exist_ok=True)
    url = 'https://videos.nba.com/nba/pbp/media/2025/03/04/0022400889/14/bd1edcac-5099-e0de-053c-2c6d71808c05_1280x720.mp4'

    #start browser for each link
    browser = await zd.start(headless=True, 
                            browser_args=["--mute-audio"])
    
    # go to link
    tab = await browser.get(url)
    await tab.set_download_path(data_dir)
    # wait for page to load
    await tab
    print("Sleeping before download of {}...".format('test'))
    await asyncio.sleep(random.uniform(0.5, 1.5))
    # download to correct path (might need to get 
    # another WCTIMESTRING column
    # for better names)
    test = await tab.download_file(url, 'test.mp4')
    print("Downloaded file: ", test)
    #sleep for random time
    print("Sleeping after download of {}...".format('test'))
    await asyncio.sleep(random.uniform(2.0, 4.0))

    await browser.stop()

def main():
    # read events id file (ADD FUNCTIONALITY TO MAKE SURE IT HAS THE LINKS, NOT JUST EVENT IDS)
    event_ids = read_event_ids()
    asyncio.run(download_links(event_ids))

    #asyncio.run(test_download())


if __name__ == '__main__':
    main()