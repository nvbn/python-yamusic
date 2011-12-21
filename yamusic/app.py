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


def fix_json_single_quotes(text):
    def replace_quotes(match):
        if match.group(1)[0] == "'":
            return '"%s"'%(match.group(2).replace(r"\'","'").replace('"',r'\"'))
        else:
            return '"%s"'%(match.group(2))

    return re.sub(r"""(["'])((?:\\?.)*?)\1""", replace_quotes, text);

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


class Manager(object):

    def __init__(self, search_cls, _type, filter_fnc=None):
        self.search_cls = search_cls
        self.type = _type
        self._filter_fnc = filter_fnc

    @property
    def filter_result(self):
        if not self._filter_fnc:
            raise ValueError
        if not hasattr(self, '_filter_result'):
            self._filter_result = self._filter_fnc()
        return self._filter_result

    def _get_titles(self, *args, **kwargs):
        """Get title for search

        Keyword Arguments:
        *args -- classes for search
        **kwargs -- search fields

        Returns: str
        """
        titles = []
        for cls, cls_name in map(
            lambda arg: (arg, arg.__name__.lower()), args
        ):
            cls_dict = dict(filter(
                lambda (name, val):
                val and cls_name in name, kwargs.items()
            ))
            title = cls_dict.get(cls_name + '__title', '')
            id = cls_dict.get(cls_name + '__id', None)
            obj = cls_dict.get(cls_name)
            if not title:
                if id and not obj:
                    obj = cls.objects.get(id=id)
                if obj:
                    title = obj.title
            titles.append(title)
        return ' '.join(titles)

    def _search(self, single, title='', **kwargs):
        titles = self._get_titles(*self.search_cls, **kwargs)
        if title:
            titles = ' '.join([titles, title])
        return cursor.search(self.type, titles, single=single)

    def all(self):
        return list(self.filter_result)

    def filter(self, title='', **kwargs):
        return Manager(
            self.search_cls,
            self.type,
            lambda: self._search(False, title, **kwargs)
        )

    def get(self, title='', **kwargs):
        if 'id' in kwargs:
            raise ValueError
        return self._search(True, title, **kwargs)

    def __getitem__(self, item):
        if type(item) is slice:
            return list(islice(
                self.filter_result, item.start, item.stop, item.step
            ))
        else:
            return list(islice(self.filter_result, item, item + 1))[0]

    def __iter__(self):
        return self.filter_result

    def __len__(self):
        return len(self.all())


class ArtistManager(Manager):

    def __init__(self):
        super(ArtistManager, self).__init__([], TYPE_ARTISTS)

    def get(self, id=None, **kwargs):
        if id:
            artist = Artist(id=id)
            artist.get_data()
            return artist
        else:
            return super(ArtistManager, self).get(**kwargs)


class Artist(Cached):
    """Artist item"""
    CACHE = 'ARTISTS_CACHE'
    objects = ArtistManager()

    def __init__(self, id=None, title=None):
        self.id = id
        self.title = title

    def __unicode__(self):
        return self.title

    def get_albums(self):
        """Lazy get artist albums"""
        if not hasattr(self, '_albums'):
            self.get_data()
        return self._albums

    def get_data(self):
        self._albums = []
        data = cursor.open(
            'http://music.yandex.ru/fragment/artist/%d/tracks' %
            int(self.id)
        ).read()
        soup = BeautifulSoup(data)
        self.title = cursor._remove_html(
            soup.find(
                'h1', cursor._class_filter('b-title__title')
            ).__unicode__()
        )
        for album in soup.findAll(
            'div', cursor._class_filter('b-album-control')
        ):
            try:
                album_data = json.loads(fix_json_single_quotes(album['onclick'][7:]))
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

    def get_tracks(self):
        """Lazy get artist tracks"""
        if hasattr(self, '_tracks'):
            return self._tracks
        tracks = []
        for album in self.get_albums():
            tracks += album.get_tracks()
        self._tracks = tracks
        return self._tracks


class AlbumManager(Manager):

    def __init__(self):
        super(AlbumManager, self).__init__([Artist], TYPE_ALBUMS)

    def get(self, id=None, **kwargs):
        if id:
            album = Album(id=id)
            album.get_data()
            return album
        else:
            return super(AlbumManager, self).get(**kwargs)


class Album(Cached):
    """Album item"""
    CACHE = 'ALBUMS_CACHE'
    objects = AlbumManager()

    def __init__(self, id=None, title=None, cover=None,
                 artist__id=None, artist__title=None,
                 artist=None):
        self.id = id
        self.title = title
        self.cover = cover
        if artist__id or artist__title:
            self.artist = Artist.get(
                id=artist__id,
                title=artist__title,
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
        if not hasattr(self, '_tracks'):
            self.get_data()
        return self._tracks

    def get_data(self):
        data = cursor.open(
            'http://music.yandex.ru/fragment/album/%d' %
            int(self.id)
        ).read()
        soup = BeautifulSoup(data)
        self._tracks = []
        artist_soup = soup.find(
            'div', cursor._class_filter('b-title__artist')
        ).find('a')
        self.artist__id = artist_soup['href'].split('/')[-1]
        self.artist__title = cursor._remove_html(artist_soup.__unicode__())
        self.artist = Artist.get(
            id=self.artist__id,
            title=self.artist__title,
        )
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
        self.title = cursor._remove_html(
            soup.find(
                'h1', cursor._class_filter('b-title__title')
            ).__unicode__()
        )

    def __unicode__(self):
        return u'%s - %s' % (self.artist, self.title)


class TrackManager(Manager):

    def __init__(self):
        super(TrackManager, self).__init__((Artist, Album), TYPE_TRACKS)

    def get(self, id=None, storage_dir=None, **kwargs):
        album = kwargs.get('album', None)
        album__id = kwargs.get('album__id', None)
        album__title = kwargs.get('album__title', None)
        if not album:
            if album__id:
                album = Album.objects.get(id=album__id)
            elif album__title:
                album = Album.objects.get(title=album__title)
        if id and storage_dir:
            return Track(id, storage_dir, **kwargs)
        elif id and album:
            track = Track(id=id, album=album)
            track.get_data()
            return track
        else:
            return super(TrackManager, self).get(**kwargs)


class Track(Cached):
    """Track item"""
    CACHE = "TRACKS_CACHE"
    objects = TrackManager()

    def __init__(self, id=None, title=None, artist__id=None,
                 artist__title=None, album__id=None, album__title=None,
                 album__cover=None, duration=None, storage_dir=None,
                 artist=None, album=None):
        self.id = int(id)
        self.title = title
        if artist__id or artist__title:
            self.artist = Artist.get(
                id=artist__id,
                title=artist__title,
            )
        if album__id or album__title or album__cover:
            self.album = Album.get(
                id=album__id,
                title=album__title,
                cover=album__cover,
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
            int(self.id),
        )

    def get_data(self):
        self.artist = self.album.artist
        soup = BeautifulSoup(
            cursor.open(
                'http://music.yandex.ru/fragment/track/%d/album/%d' % (
                    self.id,
                    self.album.id,
                )
            ).read()
        )
        data = soup.find('div', cursor._class_filter('b-track b-track_type_track js-track'))
        for attr, val in cursor._parse_track(data).items():
            setattr(self, attr, val)

    def open(self):
        """Open track like urlopen"""
        return cursor.open(self.url)


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

    def _parse_track(self, data):
        track = json.loads(data['onclick'][7:])
        return {
            'id': track['id'],
            'title': track['title'],
            'artist__id': track['artist_id'],
            'artist__title': track['artist'],
            'album__id': track['album_id'],
            'album__title': track['album'],
            'album__cover': track['cover'],
            'storage_dir': track['storage_dir']
        }

    def _get_tracks(self, soup):
        for track in soup.findAll('div', self._class_filter('b-track')):
            yield Track.get(**self._parse_track(track))

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
                artist__id=artist_a['href'].split('/')[-1],
                artist__title=self._remove_html(artist_a.__unicode__())
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
