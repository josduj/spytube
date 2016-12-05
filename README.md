# Spytube
Command-line tool for downloading Spotify playlists, albums or songs from YouTube.

### Requirements
- Python
- avconv or ffmpeg
- [youtube_dl](https://github.com/rg3/youtube-dl)
- [spotipy](https://github.com/plamere/spotipy)
- mutagen (optional)

### Installation
`sudo apt-get install libav-tools` or `sudo apt-get install ffmpeg`

`sudo pip install youtube_dl spotipy mutagen`

`sudo pip install git+https://github.com/josduj/spytube`

After successful instalation you need to register your Spotify app and update `spytube.ini` file located in `~/config/spytube/` with your Spotify app credentials. Also, optional but highly recommended is to add your YouTube api key.

### Usage
`spytube [options] link`

Replace the link with valid Spotify URL or URI.

By default songs are downloaded to `~/Music` folder, unless differently configured in `spytube.ini` or specified with `--path` argumet.

### Options
```
positional arguments:
  link                  Spotify link (url or uri)

optional arguments:
  -h, --help            show this help message and exit
  -s {0,1,2}, --search-type {0,1,2}
                        Define the search type: 0 - download first youtube
                        result, 1 - download song with equal duration
                        (default), 2 - prompt the user for every download
  -r RESULTS, --results RESULTS
                        Number of results for every youtube search. (max = 50)
  -t TOKEN, --token TOKEN
                        Spotify auth token. Use this if you don't have spotify
                        app setup or you want to bypass using default user
                        credentials
  -m METADATA, --metadata METADATA
                        Add metadata tags. Input is decimal number from 0 to 7
                        representing binary options (title&artist |
                        album&cover | other)
  -n [NAME], --name [NAME]
                        Replaces folder name with the user specified one.
                        Using only -n saves songs to default music folder or
                        the one specified with -p. This overrides -d -u and -f
                        arguments.
  -p PATH, --path PATH  Path to the folder where you want the files downloaded
  -d, --add-date        Add a date to folder name. Adds last added song date
                        to playlists or publish date for albums (useful for
                        downloading Discover Weekly playlists)
  -u, --add-username    Add owner name to destination folder (works only for
                        playlists)
  -f, --add-folder      Makes subfolder if possible. Name of the folder is
                        always the first value. (For example artist/album,
                        playlist/date, etc...)
  -v, --verbose         Print additional info or debugging information

```