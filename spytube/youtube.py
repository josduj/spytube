import os
import requests
import logging
from BeautifulSoup import BeautifulSoup

log = logging.getLogger(__name__)

class YoutubeSong:
    def __init__(self, title, id, duration=0):
        self.title = title
        self.id = id
        self.duration = duration
        self.URL = ("http://www.youtube.com/watch?v=" + self.id)

    def info(self):
        print("Title: \t\t" + self.title)
        print("Duration: \t" + str(self.duration))
        print("URL: \t\t" + self.URL)

class Youtube:
    def __init__(self, apikey=None):
        self.apikey = apikey

    def search(self, searchstring, maxres=10):
        if self.apikey:
            return self.apisearch(searchstring, maxres)
        else:
            log.warning("no api key. using http search")
            return self.httpsearch(searchstring)[:maxres]

    def apisearch(self, searchstring, maxres):
        params = {
            'part': 'snippet',
            'q': searchstring,
            'type': 'video',
            'key': self.apikey,
            'maxResults':maxres
            }

        data = requests.get("https://www.googleapis.com/youtube/v3/search",params)
        #handle errors

        if data:
            songlist = []
            ids = []

            for song in data.json()["items"]:
                title = song["snippet"]["title"]
                id = song["id"]["videoId"]
                ids += [id]
                songlist += [YoutubeSong(title,id)]

            for song,dur in zip(songlist,self.get_durations(ids)):
                song.duration = dur

            return songlist
        else:
            log.warning("unable to get youtube api response. falling back to http search")
            return self.httpsearch(searchstring)[:maxres]

    def get_durations(self, ids):
        log.debug("getting song durations")

        params = {
            'id': ','.join(ids),
            'part': 'contentDetails',
            'key': self.apikey
            }
    
        data = requests.get("https://www.googleapis.com/youtube/v3/videos",params).json()
        for d in data["items"]:
            t = d["contentDetails"]["duration"][2:]
            t = t.replace("H","*360+").replace("M","*60+").replace("S","+")+"0"
            yield eval(t)

    def httpsearch(self, searchstring):
        params = {
            'q': searchstring,
            'sp': 'EgIQAQ%253D%253D'
            }
        html = requests.get("https://www.youtube.com/results", params)  
        soup = BeautifulSoup(html)
        songlist=[]
        for h3 in soup.findAll('h3', { 'class' : 'yt-lockup-title ' }):
            a = h3.find('a')
            span = h3.find('span')
            if span: #if span is None, search result is ad
                dur = span.text.split()[-1][:-1] #gets hour:min:sec format
                duration = sum(int(d)*(60**i) for i,d in enumerate(dur.split(':')[::-1])) #gets the time in seconds
                title = a['title']
                id = a['href'][9:]
                songlist += [YoutubeSong(title,id,duration)]
        return songlist