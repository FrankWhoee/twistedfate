from requests import get
from bs4 import BeautifulSoup
from datetime import datetime,timedelta

events_cache = []
cache_last_updated = datetime.fromtimestamp(0)

def fetch_events():
    global events_cache
    global cache_last_updated

    cookies = {'tz-cookie': 'America%2FLos_Angeles'}

    req = get("https://www.aceodds.com/bet365-live-streaming/basketball/ebasketball-h2h-gg-league-4x5mins.html", cookies=cookies)

    soup = BeautifulSoup(req.content, features="html.parser")

    table = soup.find(class_="table-responsive-sm").find_all("tr")

    events = []

    date = ""

    for row in table:
        cols = row.find_all("td")
        if len(cols) == 1:
            date = cols[0].get_text()
            date = date.replace("- Today's Matchups", "").strip()
            date = datetime.strptime(date, "%a, %d %B %Y")
        elif len(cols) == 2:
            time = cols[0].get_text().split(":")
            hour = int(time[0])
            minute = int(time[1])

            event = cols[1]
            link = event.find("a").attrs["href"]
            title = event.find("a").attrs["title"]

            time = datetime.fromtimestamp(date.timestamp())
            time = time.replace(hour=hour, minute=minute)
            events.append({
                "time": time,
                "link": link,
                "title": title
            })

    events[0] = {
        "link": "youtube.com",
        "title": "HOGGY VS RANES",
        "time": datetime.fromtimestamp(1725856331)
    }

    events_cache = events
    cache_last_updated = datetime.now()
    return events

def get_events():
    global cache_last_updated
    global events_cache
    
    if datetime.now() - cache_last_updated >= timedelta(minutes=5):
        return fetch_events()
    else:
        return events_cache