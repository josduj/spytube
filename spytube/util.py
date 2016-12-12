import os
import codecs
try:
	import configparser
except ImportError:
	import ConfigParser as configparser
import logging

log = logging.getLogger(__name__)

CONFIG = None
CONFIG_DIR = os.path.expanduser("~/.config/spytube")
CONFIG_FILE = os.path.join(CONFIG_DIR, "spytube.ini")


def init_config_dir():
	if not os.path.isdir(CONFIG_DIR):
	    os.makedirs(CONFIG_DIR)
	    log.info("created config directory %s.", CONFIG_DIR)

	if not os.path.isfile(CONFIG_FILE):
		save_options(CONFIG_FILE, get_default_config())

def get_default_config():
    return {
    	"DEFAULT": {
            "spotify_client_id": "",
            "spotify_client_secret": "",
            "spotify_redirect_uri": "http://localhost:8888/callback",
            "spotify_username": "",
            "youtube_api_key": "",
            "music_folder_path": "~/Music"
            }
		}

def load_config():
	log.debug("loading config")
	options = get_default_config()
	config = configparser.ConfigParser()
	try:
	    config.read(CONFIG_FILE)
	except Exception as e:
		log.warn("could not read config file: %s. using default options" % e)
		pass
	else:
		for option_name, option_value in config.items('DEFAULT'):
			if option_value is not None:
			    options['DEFAULT'][option_name] = option_value
	return options


def save_options(config_file, options):
	config = configparser.ConfigParser()
	
	section = "DEFAULT"
	for k, v in options.options(section).items():
		config.set(section, k, str(v))

	with codecs.open(config_file, "w", encoding="utf-8") as f:
	    config.write(f)

	log.info("configuration written to %s" % config_file)

def init():
	init_config_dir()
	global CONFIG
	CONFIG = load_config()