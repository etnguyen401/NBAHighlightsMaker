import requests
headers = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
    'Connection': 'keep-alive',
    'Referer': 'https://stats.nba.com/',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache'
}
event_id = '4'
game_id = '0022000103'
url = 'https://stats.nba.com/stats/videoeventsasset?GameEventID={}&GameID={}'.format(
            event_id, game_id)
r = requests.get(url, headers=headers)
json = r.json()
print(json)
video_urls = json['resultSets']['Meta']['videoUrls']
playlist = json['resultSets']['playlist']
video_event = {'video': video_urls[0]['lurl'], 'desc': playlist[0]['dsc']}
print(video_event)
