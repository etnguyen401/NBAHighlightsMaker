import time
import requests
import pandas as pd

# Create a session
session = requests.Session()

headers = {
    'Host': 'stats.nba.com',
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
}

STATS_HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}
STATS_HEADERS2 = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Connection": "keep-alive",
    "Referer": "https://stats.nba.com/",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}
start = time.time()
response = session.get('https://stats.nba.com/stats/playbyplayv2?EndPeriod=1&GameID=0021700807&StartPeriod=1', headers=STATS_HEADERS2, timeout=5)
#response = session.get('https://stats.nba.com/stats/playergamelog?DateFrom=&DateTo=&LeagueID=&PlayerID=2544&Season=2019-20&SeasonType=Regular+Season', headers=STATS_HEADERS2, timeout=5)
print("Status code:", response.status_code)
# ...existing code...
data = response.json()
headers = data['resultSets'][0]['headers']
rows = data['resultSets'][0]['rowSet']
df = pd.DataFrame(rows, columns=headers)
df.to_csv('test_output.csv', index=False)
print(f"Time taken: {time.time() - start} seconds")
session.close()