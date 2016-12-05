import spotipy
import spotipy.util
import logging

log = logging.getLogger(__name__)

class SpotifySong:
    def __init__(self, title, artist, duration, album, album_artist, disc_num, track_num, cover):
        self.title = title
        self.artist = artist
        self.duration = duration
        self.album = album
        self.album_artist = album_artist
        self.disc_num = disc_num
        self.track_num = track_num
        self.cover = cover

    def __str__(self):
        return "%s - %s" % (self.artist, self.title)

    def info(self):
        print("Title:\t\t%s\nArtist:\t\t%s\nDuration:\t%d\nAlbum:\t\t%s" % (self.title, self.artist, self.duration, self.album))


class SpotifyTracklist:
    def __init__(self, type, name, size, date, owner, artist, tracklist):
        self.type = type
        self.name = name    
        self.size = size
        self.owner = owner
        self.artist = artist
        self.date = date
        self.tracklist = tracklist


class Spotify:
    def __init__(self, username=None, client_id=None, client_secret=None, redirect_uri=None, token=None):
        if token:
            log.debug('using user provided token')
        else:
            log.debug('getting token form spotipy util')
            token = spotipy.util.prompt_for_user_token(username, None, client_id, client_secret, redirect_uri)
        self.spotipy = spotipy.Spotify(auth=token)

    def get_tracklist(self, link):
        if "album" in link:
            log.debug('getting album info')
            album_id = link.split('album')[1][1:]
            al = self.spotipy.album(album_id)
            return self.get_album_info(al)
        elif "playlist" in link:
            log.debug('getting playlist info')
            user_id, playlist_id = link.split('/' if 'http' in link else ':')[-3::2]
            pl = self.spotipy.user_playlist(user_id, playlist_id, fields="name,owner,tracks,next")
            return self.get_playlist_info(pl)
        elif "track" in link:
            log.debug('getting track info')
            track_id = link.split('track')[1][1:]
            tr = self.spotipy.track(track_id)
            track = self.get_track_info(tr)
            return SpotifyTracklist("track",None,1,None,None,track.artist,[track])
        else:
            log.critical('not a valid spotify link')
            return None
            

    def get_track_info(self, track, alb=None, albart=None, cov=None):
        title = track['name']
        artist = ", ".join(artist['name'] for artist in track['artists']) #multiple artists
        duration = int(round(track['duration_ms']/1000.))
        album = alb or track['album']['name']
        album_artist = albart or ", ".join(artist['name'] for artist in track['album']['artists'])
        disc_num = track['disc_number']
        track_num = track['track_number']
        cover = cov or [img['url'] for img in track['album']['images']]  #list of cover urls, 0 is largest, 1 is medium, 2 is smallest
        return SpotifySong(title,artist,duration,album,album_artist,disc_num,track_num,cover)

    def get_playlist_info(self, pl):
        name = pl['name']
        size = pl['tracks']['total']
        date = pl['tracks']['items'][0]['added_at']
        owner = pl['owner']['id']

        tr = pl['tracks']
        tracklist = [self.get_track_info(t['track']) for t in tr['items']]
        while tr['next']:
            tr = self.spotipy.next(tr)
            tracklist += [self.get_track_info(t['track']) for t in tr['items']]
        return SpotifyTracklist("playlist",name,size,date,owner,None,tracklist)

    def get_album_info(self, al):
        name = al['name']
        size = al['tracks']['total']
        date = al['release_date']
        #owner = ", ".join(c['text'] for c in al['copyrights'])
        album_artist = ", ".join(artist['name'] for artist in al['artists']) #multiple artists
        cover = [img['url'] for img in al['images']] #list of cover urls, 0 is largest, 1 is medium, 2 is smallest

        tr = al['tracks']
        tracklist = [self.get_track_info(t,name,album_artist,cover) for t in tr['items']]
        while tr['next']:
            tr = self.spotipy.next(tr)
            tracklist += [self.get_track_info(t,name,album_artist,cover) for t in tr['items']]
        return SpotifyTracklist("album",name,size,date,None,album_artist,tracklist)




