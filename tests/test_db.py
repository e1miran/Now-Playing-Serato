#!/usr/bin/env python3
''' test metadata DB '''

import os
import sys
import tempfile

import pytest

import nowplaying.db  # pylint: disable=import-error
import nowplaying.utils  # pylint: disable=import-error

if sys.platform.startswith("win"):
    pytest.skip("skipping on windows", allow_module_level=True)


@pytest.fixture
def getmetadb(bootstrap):
    ''' create a temporary directory '''
    config = bootstrap  # pylint: disable=unused-variable
    with tempfile.TemporaryDirectory() as newpath:
        metadb = nowplaying.db.MetadataDB(databasefile=os.path.join(
            newpath, 'test.db'),
                                          initialize=True)
        yield metadb


def results(expected, metadata):
    ''' take a metadata result and compare to expected '''
    for expkey in expected:
        assert expkey in metadata
        assert expkey and expected[expkey] == metadata[expkey]
        del metadata[expkey]

    assert metadata == {}


def test_empty_db(getmetadb):  # pylint: disable=redefined-outer-name
    ''' test writing false data '''
    metadb = getmetadb
    metadb.write_to_metadb(metadata=None)
    readdata = metadb.read_last_meta()

    assert readdata is None

    metadata = {'filename': 'tests/audio/15_Ghosts_II_64kb_orig.mp3'}
    metadb.write_to_metadb(metadata=metadata)
    readdata = metadb.read_last_meta()
    assert readdata is None


def test_data_db1(getmetadb):  # pylint: disable=redefined-outer-name
    ''' simple data test '''
    metadb = getmetadb

    expected = {
        'acoustidid': None,
        'album': 'Ghosts I - IV',
        'albumartist': None,
        'artist': 'Nine Inch Nails',
        'artistbio': None,
        'artistlogo': None,
        'artistthumb': None,
        'bitrate': '64000',
        'bpm': None,
        'comments': None,
        'composer': None,
        'coverurl': None,
        'date': None,
        'deck': None,
        'disc': None,
        'discsubtitle': None,
        'disc_total': None,
        'filename': 'tests/audio/15_Ghosts_II_64kb_orig.mp3',
        'genre': None,
        'isrc': None,
        'key': None,
        'label': None,
        'lang': None,
        'length': None,
        'musicbrainzalbumid': None,
        'musicbrainzartistid': None,
        'musicbrainzrecordingid': None,
        'title': '15 Ghosts II',
        'track': '15',
        'track_total': None,
    }

    metadb.write_to_metadb(metadata=expected)
    readdata = metadb.read_last_meta()

    expected.update({'dbid': 1})
    results(expected, readdata)


def test_data_db2(getmetadb):  # pylint: disable=redefined-outer-name
    ''' more complex data test '''
    metadb = getmetadb

    expected = {
        'album': 'Secret Samadhi',
        'artist': 'LĪVE',
        'bpm': 91,
        'date': '1997',
        'deck': 1,
        'filename':
        "/Users/aw/Music/songs/LĪVE/Secret Samadhi/02 Lakini's Juice.mp3",
        'genre': 'Rock',
        'key': 'C#m',
        'label': 'Radioactive Records',
        'title': 'Lakini\'s Juice',
        'coverimageraw': "Grr! I'm an image!",
    }

    metadb.write_to_metadb(metadata=expected)
    readdata = metadb.read_last_meta()

    expected = {
        'acoustidid': None,
        'album': 'Secret Samadhi',
        'albumartist': None,
        'artist': 'LĪVE',
        'artistbio': None,
        'artistlogo': None,
        'artistthumb': None,
        'bitrate': None,
        'bpm': '91',
        'comments': None,
        'composer': None,
        'coverimageraw': "Grr! I'm an image!",
        'coverurl': None,
        'date': '1997',
        'deck': '1',
        'disc': None,
        'discsubtitle': None,
        'disc_total': None,
        'filename':
        "/Users/aw/Music/songs/LĪVE/Secret Samadhi/02 Lakini's Juice.mp3",
        'genre': 'Rock',
        'isrc': None,
        'key': 'C#m',
        'label': 'Radioactive Records',
        'lang': None,
        'length': None,
        'musicbrainzalbumid': None,
        'musicbrainzartistid': None,
        'musicbrainzrecordingid': None,
        'title': 'Lakini\'s Juice',
        'track': None,
        'track_total': None,
        'dbid': 1
    }

    results(expected, readdata)


def test_data_dbid(getmetadb):  # pylint: disable=redefined-outer-name
    ''' make sure dbid increments '''
    metadb = getmetadb

    expected = {
        'artist': 'Nine Inch Nails',
        'title': '15 Ghosts II',
    }

    metadb.write_to_metadb(metadata=expected)
    readdata = metadb.read_last_meta()

    expected = {
        'artist': 'Great Artist Here',
        'title': 'Great Title Here',
    }

    metadb.write_to_metadb(metadata=expected)
    readdata = metadb.read_last_meta()

    assert readdata['dbid'] == 2