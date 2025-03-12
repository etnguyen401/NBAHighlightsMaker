import random
import requests

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

headers = {
    'User-Agent': '',
    'x-nba-stats-origin': 'stats',
    'Referer': 'https://stats.nba.com/',
}

headers['User-Agent'] = random.choice(user_agents)

event_id = '8'
game_id = '0022400832'
url = 'https://stats.nba.com/stats/videoeventsasset?GameEventID={}&GameID={}'.format(event_id, game_id)

try:
    r = requests.get(url, headers=headers)
    r.raise_for_status()  # Check if the request was successful
    print("Response status code:", r.status_code)
    # print("Response headers:", r.headers)
    # print("Response content:", r.text)  # Print the raw response content

    json = r.json()  # Attempt to parse the response as JSON
    # print(json)
    video_urls = json['resultSets']['Meta']['videoUrls']
    playlist = json['resultSets']['playlist']
    video_event = {'video': video_urls[0]['lurl'], 'desc': playlist[0]['dsc']}
    print(video_event)
except requests.exceptions.HTTPError as e:
    print(f"HTTP error occurred: {e}")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except requests.exceptions.JSONDecodeError as e:
    print(f"JSON decode error: {e}")
    print("Response content:", r.text)  # Print the raw response content for debugging