Python YaMusic Readme
=====================

This library for using yandex music in python.
Library depends on PySide(Qt for python), but it use only QtScript, if anyone find good and less library for js - i rewrite app.

Usage
-----

Import search app::
 >>> from yamusic.app import Search

Now you need to init Qt application::
 >>> from PySide.QtCore import QCoreApplication
 >>> import sys
 >>> app = QCoreApplication(sys.argv)

Init cursor (is singleton, because data depends on cookies)::
 >>> cursor = Search.cursor()

Cursor can search artists::
 >>> cursor.search(Search.TYPE_ARTISTS, 'query')

Albums::
 >>> cursor.search(Search.TYPE_ALBUMS, 'query')

And tracks::
 >>> cursor.search(Search.TYPE_TRACKS, 'query')

If single=True, search return one item::
 >>> cursor.search(Search.TYPE_TRACKS, 'query', single=True)

Else - return iterator.
For getting data from albums and artists use::
 >>> artist.get_albums()
 >>> artist.get_tracks()
 >>> album.get_tracks()

For opening track like file use::
 >>> track.open()
