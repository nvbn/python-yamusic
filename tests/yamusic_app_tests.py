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

import unittest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from yamusic.app import cursor, Search
from itertools import islice


class CursorTestCase(unittest.TestCase):
    def setUp(self):
        self.artists = (
            'notfoundableartist',
            'royksopp', 'liars', 'portishead'
        )
        self.not_fount_artist = self.artists[0]
        self.albums = (
            'notofoundableshitalbum',
            'junior', 'jade motel',
        )
        self.not_found_album = self.albums[0]
        self.tracks = (
            'song 2', 'paranoid android', 'castle'
        )

    def test_artist(self):
        for artist in self.artists:
            artist_list = list(
                islice(cursor.search(Search.TYPE_ARTISTS, artist), 1)
            )
            if artist == self.not_fount_artist:
                self.assertEqual(
                    len(artist_list), 0,
                    'Not found not work!'
                )
            else:
                self.assertEqual(
                    len(artist_list), 1,
                    'Search artist not work!'
                )
                artist_obj = artist_list[0]
                albums = list(artist_obj.get_albums())
                self.assertEqual(
                    len(albums) > 0, True,
                    'get_album not work!'
                )
                for album in albums:
                    tracks = list(album.get_tracks())
                    self.assertEqual(
                        len(tracks) > 0, True,
                        'get_tracks from album not work!'
                    )

    def test_albums(self):
        for album in self.albums:
            album_list = list(
                islice(cursor.search(Search.TYPE_ALBUMS, album), 1)
            )
            if album == self.not_found_album:
                self.assertEqual(
                    len(album_list), 0,
                    'Not found not work!'
                )
            else:
                self.assertEqual(
                    len(album_list), 1,
                    'Search album not work!'
                )
                album_obj = album_list[0]
                tracks = list(album_obj.get_tracks())
                self.assertEqual(
                    len(tracks) > 0, True,
                    'get_tracks from album not work!'
                )

    def test_tracks(self):
        for track in self.tracks:
            track = cursor.search(Search.TYPE_TRACKS, track, single=True)
            self.assertEqual(
                len(track.title) > 0, True,
                'Track search not work!'
            )
            self.assertEqual(
                len(track.open().read(200)), 200,
                'Track downloading not work!'
            )

if __name__ == '__main__':
    unittest.main()
