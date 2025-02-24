import asyncio
#installed via poetry
import zendriver as zd
import time

async def main():
    browser = await zd.start()
    page = await browser.get('https://www.nowsecure.nl')

    await page.save_screenshot()
    await page.get_content()
    await page.scroll_down(150)
    elems = await page.select_all('.wrap')
    

    for elem in elems:
        await elem.flash()
    time.sleep(4)
    page2 = await browser.get('https://twitter.com', new_tab=True)
    page3 = await browser.get('https://github.com/ultrafunkamsterdam/nodriver', new_window=True)

    for p in (page, page2, page3):
        await p.bring_to_front()
        await p.scroll_down(200)
        await p   # wait for events to be processed
        await p.reload()
        if p != page3:
            await p.close()
    # # config
    # config = zd.Config()
    # config.headless = False

    # # start the browser
    # url = "https://www.nba.com/stats/events?CFID=&CFPARAMS=&ContextMeasure=FGA&GameID=0022400779&PlayerID=201142&Season=2024-25&SeasonType=Regular%20Season&TeamID=&flag=3&sct=plot&section=game"
    # browser = await zd.start(config)

    # # pass in the url somehow later
    # # this is a tab
    # page = await browser.get('https://www.nowsecure.nl')
    
    # # wait for page to load


    # # get all the tr elements with class EventsTable_row__Gs8B9

    # #for each tr element 
    #     # click on it 
    #     # get the corresponding
    #     # video link with the class name vjs-tech or id vjs_video_3_html5_api
    #     # write the link to a file

    # await browser.stop()


if __name__ == '__main__':
    asyncio.run(main())
