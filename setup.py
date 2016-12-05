from os.path import dirname, join
from spytube.cli import VERSION

from setuptools import setup, find_packages


def read(filename):
    text = ""
    try:
        with open(join(dirname(__file__), filename)) as f:
            text = f.read()
    except Exception as e:
        text = "{0}: {1}".format(e, filename)

    return text


_name = "spytube"
_author = "josduj"
_license = "MIT"
_description = read("README.md")

setup(
    name=_name,
    description="download spotify songs from youtube",
    long_description=_description,
    keywords=["spotify", "youtube", "music", "download"],
    version=VERSION,
    license=_license,
    url="https://github.com/{0}/{1}".format(_author,_name),
    download_url="https://github.com/{0}/{1}/tarball/v{2}".format(_author,_name,VERSION),
    author=_author,
    author_email="{0}@gmail.com".format(_author),
    packages=find_packages(),
    package_data={_name: ["data/*"]},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            '{0} = {0}.cli:main'.format(_name)
        ]
    },
    install_requires=[
        'youtube_dl',
        'spotipy',
        'mutagen',
        'requests'
    ],

)

from spytube import util
util.init_config_dir()

