# -*- coding: utf-8 -*-
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License
#    as published by the Free Software Foundation.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
import urllib2
import cookielib
from itertools import imap, islice
from hashlib import md5
import json
import re

TYPE_TRACKS = 0
TYPE_ALBUMS = 1
TYPE_ARTISTS = 2

class Manager(object):

    def __init__(self, _type):
        self.type = _type

    def filter(self, title=None, storage_dir=None, id=None):  # TODO: work like django
        if not title:
            raise NotImplemented
        return cursor.search(self.type, title)

    def get(self, title, storage_dir=None, id=None):
        if not title:
            raise NotImplemented
        return cursor.search(self.type, title, single=True)


class Cached(object):
    """Simple cache for avoiding duplicates"""
    CACHE = ''

    @classmethod
    def get(cls, **kwargs):
        id = kwargs.get('id', -1)
        if id in getattr(Search, cls.CACHE):
            return getattr(Search, cls.CACHE)[id]
        result = cls(**kwargs)
        if result.id:
            getattr(Search, cls.CACHE)[id] = result
        return result

    def __unicode__(self):
        return ''

    def __repr__(self):
        return '<%s: %s>' % (
            self.__class__.__name__,
            self.__unicode__()
        )


class Track(Cached):
    """Track item"""
    CACHE = "TRACKS_CACHE"
    objects = Manager(TYPE_TRACKS)

    def __init__(self, id=None, title=None, artist_id=None,
                 artist_title=None, album_id=None, album_title=None,
                 album_cover=None, duration=None, storage_dir=None,
                 artist=None, album=None):
        self.id = int(id)
        self.title = title
        if artist_id or artist_title:
            self.artist = Artist.get(
                id=artist_id,
                title=artist_title,
            )
        if album_id or album_title or album_cover:
            self.album = Album.get(
                id=album_id,
                title=album_title,
                cover=album_cover,
            )
        self.duration = duration
        self.storage_dir = storage_dir
        if artist:
            self.artist = artist
        if album:
            self.album = album

    def __unicode__(self):
        return u'%s - %s' % (self.artist, self.title)

    @property
    def url(self):
        """Calculate track url"""
        if not self.storage_dir:
            raise AttributeError('Storage dir required!')
        info_path_data = cursor.open(
            'http://storage.music.yandex.ru/get/%s/2.xml' % self.storage_dir
        ).read()
        info_path_soup = BeautifulStoneSoup(info_path_data)
        file_path_data = cursor.open(
            'http://storage.music.yandex.ru/download-info/%s/%s' % (
                self.storage_dir,
                info_path_soup.find('track')['filename'],
            )
        ).read()
        file_path_soup = BeautifulStoneSoup(file_path_data).find('download-info')
        path = file_path_soup.find('path').text
        return 'http://%s/get-mp3/%s/%s%s?track-id=%d&region=225&from=service-search' % (
            file_path_soup.find('host').text,
            cursor.get_key(path[1:] + file_path_soup.find('s').text),
            file_path_soup.find('ts').text,
            path,
            self.id,
        )

    def open(self):
        """Open track like urlopen"""
        return cursor.open(self.url)


class Album(Cached):
    """Album item"""
    CACHE = 'ALBUMS_CACHE'
    objects = Manager(TYPE_ALBUMS)

    def __init__(self, id=None, title=None, cover=None,
                 artist_id=None, artist_title=None,
                 artist=None):
        self.id = id
        self.title = title
        self.cover = cover
        if artist_id or artist_title:
            self.artist = Artist.get(
                id=artist_id,
                title=artist_title,
            )
        if artist:
            self.artist = artist

    def set_tracks(self, tracks):
        """Set tracks to album"""
        self._tracks = []
        for track in tracks:
            self._tracks.append(
                Track.get(
                    id=track['id'],
                    title=track['title'],
                    artist=self.artist,
                    album=self,
                    duration=track['duration'],
                    storage_dir=track['storage_dir'],
                )
            )

    def get_tracks(self):
        """Lazy get album tracks"""
        if hasattr(self, '_tracks'):
            return self._tracks
        self._tracks = []
        data = cursor.open('http://music.yandex.ru/fragment/album/%d' % int(self.id)).read()
        soup = BeautifulSoup(data)
        for track in soup.findAll('div', cursor._class_filter('b-track')):
            track_data = json.loads(track['onclick'][7:])
            self._tracks.append(Track.get(
                id=track_data['id'],
                title=track_data['title'],
                artist=self.artist,
                album=self,
                storage_dir=track_data['storage_dir'],
                duration=track_data['duration']
            ))
        return self._tracks

    def __unicode__(self):
        return u'%s - %s' % (self.artist, self.title)


class Artist(Cached):
    """Artist item"""
    CACHE = 'ARTISTS_CACHE'
    objects = Manager(TYPE_ARTISTS)

    def __init__(self, id=None, title=None):
        self.id = id
        self.title = title

    def __unicode__(self):
        return self.title

    def get_albums(self):
        """Lazy get artist albums"""
        if hasattr(self, '_albums'):
            return self._albums
        self._albums = []
        data = cursor.open('http://music.yandex.ru/fragment/artist/%d/tracks' % int(self.id)).read()
        soup = BeautifulSoup(data)
        for album in soup.findAll('div', cursor._class_filter('b-album-control')):
            try:
                album_data = json.loads(album['onclick'][7:].replace("'", '"'))
                album = Album.get(
                    id=album_data.get('id'),
                    title=album_data.get('title'),
                    artist=self,
                    cover=album_data.get('cover')
                )
                self._albums.append(album)
                album.set_tracks(album_data.get('tracks'))
            except ValueError:
                pass
        return self._albums

    def get_tracks(self):
        """Lazy get artist tracks"""
        if hasattr(self, '_tracks'):
            return self._tracks
        tracks = []
        for album in self.get_albums():
            tracks += album.get_tracks()
        self._tracks = tracks
        return self._tracks


class Search(object):
    """Main search class"""
    TYPE_TRACKS = TYPE_TRACKS
    TYPE_ALBUMS = TYPE_ALBUMS
    TYPE_ARTISTS = TYPE_ARTISTS
    TYPES = {
        TYPE_TRACKS: 'tracks',
        TYPE_ALBUMS: 'albums',
        TYPE_ARTISTS: 'artists',
    }
    URL = 'http://music.yandex.ru/fragment/search?text=%(text)s&type=%(type)s&page=%(page)d'
    TRACKS_CACHE = {}
    ALBUMS_CACHE = {}
    ARTISTS_CACHE = {}

    def __init__(self):
        self._opener = self._cookie_jar = None
        self.authenticated = False

    @property
    def cookie_jar(self):
        if not self._cookie_jar:
            self._cookie_jar = cookielib.CookieJar()
        return self._cookie_jar

    @property
    def opener(self):
        if not self._opener:
            self._opener = urllib2.build_opener(
                urllib2.HTTPCookieProcessor(self.cookie_jar)
            )
        return self._opener

    def open(self, url):
        """Open with cookies"""
        return self.opener.open(url)

    def get_key(self, key):
        """Get secret key for track loading"""
        return md5('XGRlBW9FXlekgbPrRHuSiA' + key.replace('\r\n', '\n')).hexdigest()

    def _class_filter(self, cls_name):
        """Create BeautifulSoup class filter"""
        return {'class': re.compile(r'\b%s\b' % cls_name)}

    def _remove_html(self, data):
        p = re.compile(r'<.*?>')
        try:
            return p.sub('', data)
        except TypeError:
            return data

    def _get_tracks(self, soup):
        for track in soup.findAll('div', self._class_filter('b-track')):
            track = json.loads(track['onclick'][7:])  # remove return
            yield Track.get(
                id=track['id'],
                title=track['title'],
                artist_id=track['artist_id'],
                artist_title=track['artist'],
                album_id=track['album_id'],
                album_title=track['album'],
                album_cover=track['cover'],
                storage_dir=track['storage_dir']
            )

    def _get_albums(self, soup):
        for album in soup.findAll('div', self._class_filter('b-albums')):
            cover_a = album.find('div', self._class_filter('b-albums__cover')).find('a')
            artist_a = album.find('a',
                self._class_filter('b-link_class_albums-title-link')
            )
            yield Album.get(
                id=cover_a['href'].split('/')[-1],
                title=self._remove_html(album.find('a',
                    self._class_filter('b-link_class_albums-title-link')
                ).__unicode__()),
                cover=cover_a.find('img')['src'],
                artist_id=artist_a['href'].split('/')[-1],
                artist_title=self._remove_html(artist_a.__unicode__())
            )

    def _get_artists(self, soup):
        for artist in imap(
            lambda obj: obj.find('a'),
            soup.findAll('div', self._class_filter('b-artist-group'))
        ):
            yield Artist.get(
                id=artist['href'].split('/')[-1],
                title=self._remove_html(artist.__unicode__())
            )

    def _get(self, type, soup):
        if type == self.TYPE_TRACKS:
            return self._get_tracks(soup)
        elif type == self.TYPE_ALBUMS:
            return self._get_albums(soup)
        elif type == self.TYPE_ARTISTS:
            return self._get_artists(soup)

    def _get_result(self, type, text):  # start from 0!
        pages_count = 1
        current_page = 0
        while pages_count > current_page:
            result = self.open(self.URL % {
                'text': text,
                'type': self.TYPES[type],
                'page': current_page,
            }).read()
            soup = BeautifulSoup(result)
            try:
                try:
                    pages_count = int(soup.findAll('a', self._class_filter('b-pager__page'))[-1].text)  # start form 1!
                except UnicodeEncodeError:  # fix work with ... page
                    pages_count = int(soup.findAll('a', self._class_filter('b-pager__page'))[-2].text)  # start form 1!
                current_page = int(soup.find('b', self._class_filter('b-pager__current')).text)  # start from 1!
            except IndexError:
                current_page += 1  # if only one page
            for obj in self._get(type, soup):
                yield obj

    def search(self, type, text, single=False):
        if type not in self.TYPES:
            raise AttributeError('Wrong type')
        result = self._get_result(type, text)
        if single:
            return list(islice(result, 1))[0]
        else:
            return result

cursor = Search()
