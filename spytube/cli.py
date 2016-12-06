from . import util, spotify, youtube
import youtube_dl
import os
import sys
import requests
import argparse
import logging

log = logging.getLogger('spytube')
logging.basicConfig(level=50)		# CRITICAL 50, ERROR 40, WARNING 30, INFO 20, DEBUG 10, NOTSET 0

try:
	from mutagen.mp3 import MP3
	from mutagen.id3 import ID3, APIC, TIT2, TIT3, TPE1, TPE2, TALB, TPOS, TRCK, COMM
except ImportError:
    log.critical("unable to import mutagen. install it to add id3 tags") 

VERSION = "0.1.4"


class Spytube(object):
	def __init__(self, **kwargs):
		self.kwargs = kwargs
		self.folder_path = os.path.expanduser(kwargs["path"] or util.CONFIG["DEFAULT"]["music_folder_path"])
		if kwargs["token"]:
			self.sp = spotify.Spotify(token = kwargs["token"])
		else:
			self.sp = spotify.Spotify(util.CONFIG["DEFAULT"]["spotify_username"],
									util.CONFIG["DEFAULT"]["spotify_client_id"],
			 						util.CONFIG["DEFAULT"]["spotify_client_secret"],
			 						util.CONFIG["DEFAULT"]["spotify_redirect_uri"])
		self.yt = youtube.Youtube(util.CONFIG["DEFAULT"]["youtube_api_key"])
		self.sp_tracklist = None

	def start(self):
		if self.sp:
			log.debug("initialized spotipy")
			try:
				self.sp_tracklist = self.sp.get_tracklist(self.kwargs["link"])

				if self.sp_tracklist:
					log.info('got %s "%s" by "%s"' % 
						(self.sp_tracklist.type, self.sp_tracklist.name, self.sp_tracklist.owner or self.sp_tracklist.artist))
					self.make_folder()
					self.download_songs()
			
			except Exception as e:
				log.critical(e)
		else:
			log.critical("could not initialize spotify")


	def make_folder(self):
		"""
		if -u or --add-username:
			adds "by username" to folder name (only for playlists)
		if -d or --add-date:
			for playlist - adds last edit date (useful for Discover Weekly)
			for album - adds publish date
		if -f or --add-folder:
			for playlist - make separate folder if date (-d) exists
			for albums - save album in artist folder (Artist/Album(date))
			for one track - makes artist folder

		redo later?
		"""
		if self.kwargs["name"] != None:
			self.folder_path += "/" + self.kwargs["name"]
		else:
			joinstr = ["/" , "/" if self.kwargs["add_folder"] else " - ", " - "]
			names = []
			if (self.kwargs["add_folder"] and self.sp_tracklist.type == "track") or self.sp_tracklist.type == "album":
				names += [self.sp_tracklist.artist]
			if self.sp_tracklist.name:
				n = self.sp_tracklist.name
				if self.kwargs["add_username"] and self.sp_tracklist.type == "playlist":
					n += " by " + self.sp_tracklist.owner
				names += [n]
			if self.kwargs["add_date"] and self.sp_tracklist.date:
				names += [self.sp_tracklist.date[:10]]
			for i,n in enumerate(names):
				self.folder_path += joinstr[i] + n
		if not os.path.isdir(self.folder_path):
			os.makedirs(self.folder_path)
			log.info("created directory %s" % self.folder_path)
		os.chdir(self.folder_path)
		log.debug("changing working directory to %s" % self.folder_path)

	def ydl_hook(self, d):
		if d['status'] == 'finished':
			log.info("converting to mp3")
		# if d['status'] == 'downloading':
		# 	self.logger.info("downloading")
		
	def download_songs(self):
		for i,song in enumerate(self.sp_tracklist.tracklist):
			log.info("%i/%i %s - %s (%i sec)" % 
				(i+1,self.sp_tracklist.size, song.artist, song.title, song.duration))
			filename = (song.artist + " - " + song.title).replace("/","_")

			if os.path.exists(filename + ".mp3"):
				self.song_info(i+1, song)
				log.info('song with that name already exists. skipping')
			else:
				log.info("searching youtube")
				r = self.get_song(song)
				if r:
					ydl_opts = {
					    'format': 'bestaudio/best',
					    'outtmpl': filename + '.%(ext)s',
					    'postprocessors': [{
					        'key': 'FFmpegExtractAudio',
					        'preferredcodec': 'mp3',
					        'preferredquality': '192',
					    	},],
					    'logger': log,
					    'progress_hooks': [self.ydl_hook],
					}

					with youtube_dl.YoutubeDL(ydl_opts) as ydl:
						log.info("downloading %s (%s)" % (r.title, r.URL))
						ydl.download([r.URL])

					if MP3:
						self.add_metadata(filename, song)
					self.song_info(i+1, song, True)
					log.info('succesfully donloaded song')
				else:
					self.song_info(i+1, song, False)
					log.warning('error while downloading song')

	def get_song(self,song):
		results = self.yt.search(song.artist + " - " + song.title, 
			maxres=min(self.kwargs["results"] or 10,50) if self.kwargs["search_type"] else 1)
		#set maxres if specified, 10 is default, 50 is max. if search type is 0 (first result), maxres = 1
		if not results:
			log.debug("no youtube results")
			return None
		if self.kwargs["search_type"] == 1:
			log.debug("searching for song with equal duration")
			for res in results:
				if res.duration == song.duration:
					return res
		elif self.kwargs["search_type"] == 2:
			song.info()
			for i,res in enumerate(results):
				print(i+1)
				res.info()
			dec = 51
			while dec > len(results) or dec < 1:
				dec = int(input("Enter choice: "))
			return results[dec-1]
		log.debug("getting first result")
		return results[0]


	def add_metadata(self, filename, song):
		"""	
		http://id3.org/id3v2.4.0-frames
		"""
		log.info('adding metadata')
		mp3file = MP3(filename + ".mp3", ID3=ID3)

		if self.kwargs["metadata"]:
			opts = [int(o) for o in bin(self.kwargs["metadata"])[2:]]
		else:
			opts = [1,1,1] if self.sp_tracklist.type == "album" else [1,1,0]

		if opts[0]: #default
			mp3file['TIT2'] = TIT2(encoding=3, text=song.title)
			mp3file['TPE1'] = TPE1(encoding=3, text=song.artist)

		if opts[1]:	#default
			mp3file['TALB'] = TALB(encoding=3, text=song.album)
			cover = requests.get(song.cover[1]).content
			if cover:
				mp3file['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=cover)
			else:
				log.warning("Error while getting cover")

		if opts[2]:	#default for album download
			mp3file['TPE2'] = TPE2(encoding=3, text=song.album_artist)
			mp3file['TPOS'] = TPOS(encoding=3, text=str(song.disc_num))
			mp3file['TRCK'] = TRCK(encoding=3, text=str(song.track_num))
			#mp3file['TIT3'] = TIT3(encoding=3, text="Subtitle")
			#mp3file['COMM'] = COMM(encoding=3, text="Comment")		#add comment with youtube and spotify url?

		mp3file.save()

	def song_info(self, i, song, status = None):
		if not self.kwargs["verbose"]:
			if status:
				stat = "\033[92mSuccess\033[0m" 
			elif status == False: 
				stat = "\033[91m Error \033[0m"
			else:
				stat = "\033[93mSkipped\033[0m"
			print("[%s][%d/%d] %s" % (stat, i, self.sp_tracklist.size, song))

def parse_args(args):
	parser = argparse.ArgumentParser(description='Download spotify playlist/album/song from youtube')
	parser.add_argument('link', type=str,
		help='Spotify link (url or uri)')
	parser.add_argument('-s','--search-type', type=int, choices=[0,1,2],
		help='Define the search type: 0 - download first youtube result, 1 - download song with equal duration (default), 2 - prompt the user for every download')
	parser.add_argument('-r','--results', type=int,
		help='Number of results for every youtube search. (max = 50)')
	parser.add_argument('-t','--token',
		help="Spotify auth token. Use this if you don't have spotify app setup or you want to bypass using default user credentials")
	parser.add_argument('-m','--metadata', type=int,
		help='Add metadata tags. Input is decimal number from 0 to 7 representing binary options (title&artist | album&cover | other)')
	parser.add_argument('-n','--name', nargs='?', const="",
		help='Replaces folder name with the user specified one. Using only -n saves songs to default music folder or the one specified with -p. This overrides -d -u and -f arguments.')
	parser.add_argument('-p','--path',
    	help="Path to the folder where you want the files downloaded")
	parser.add_argument('-d','--add-date',action="store_true",
		help="Add a date to folder name. Adds last added song date to playlists or publish date for albums (useful for downloading Discover Weekly playlists)")
	parser.add_argument('-u','--add-username',action="store_true",
		help="Add owner name to destination folder (works only for playlists)")
	parser.add_argument('-f','--add-folder',action="store_true",
		help="Makes subfolder if possible. Name of the folder is always the first value. (For example artist/album, playlist/date, etc...)")
	parser.add_argument('-v', '--verbose', action="count",
		help="Print additional info or debugging information")

	args = parser.parse_args()
	return args

def main(args=None):
	if args is None:
		if len(sys.argv) <= 1:
			log.critical('you need to provide spotify link')
			sys.exit()
		else:	
			args = parse_args(sys.argv[1])
	if args.verbose:
		log.setLevel(20/args.verbose)
	log.debug(args)
	util.init()
	spyt = Spytube(**vars(args))
	spyt.start()		

if __name__ == "__main__":
    main()