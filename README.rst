Python YaMusic Readme
=====================

This library for using yandex music in python with orm and cursor.

Using ORM
---------

Import models:
 >>> from yamusic.app import Artist, Album, Track

Use filter for iterate result:
 >>> Track.objects.filter(title='this must be', artist__title='royksopp', album__title='junior')
 >>> Album.objects.filter(artist__title='royksopp', title='junior')
 >>> Artist.objects.filter(title='royksopp')

For managing iterated filter result you can use:
 >>> Track.objects.filter(artist__title='unkle').all()
 >>> Album.objects.filter(artist__title='a place')[1:5:2]
 >>> Artist.objects.filter(title='the')[5]

If you want to get single item use *get* instead *filter*:
 >>> Track.objects.get(title='this must be', artist__title='royksopp', album__title='junior')
 >>> Album.objects.get(artist__title='royksopp', title='junior')
 >>> Artist.objects.get(title='royksopp')

You can get *Album* and *Artist* by *id*:
 >>> Artist.objects.get(id=49522)
 >>> Album.objects.get(id=34596)

For getting track you need *id* and on of *album*, *album__id* or *album__title*
 >>> Track.objects.get(id=id, album__id=album__id)

Or if you only need play use *id* and *storage_dir*:
 >>> Track.objects.get(id=id, storage_dir=storage_dir)

Using cursor [deprecated]
-------------------------

Import search app:
 >>> from yamusic.app import Search, cursor

Cursor can search artists:
 >>> cursor.search(Search.TYPE_ARTISTS, 'query')

Albums:
 >>> cursor.search(Search.TYPE_ALBUMS, 'query')

And tracks:
 >>> cursor.search(Search.TYPE_TRACKS, 'query')

If single=True, search return one item:
 >>> cursor.search(Search.TYPE_TRACKS, 'query', single=True)

Else - return iterator.

Work with search result
-----------------------

For getting data from albums and artists use:
 >>> artist.get_albums()
 >>> artist.get_tracks()
 >>> album.get_tracks()

For opening track like file use:
 >>> track.open()

For fast getting data objects have:
 >>> track.artist
 >>> track.album
 >>> track.title
 >>> album.artist
 >>> album.title
 >>> artist.title

Other you can find in source.
