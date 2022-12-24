from unittest import TestCase

from mgp_common.vocadb import get_song_by_id


class TestVocadb(TestCase):

    def test_get_nc_info(self):
        song = get_song_by_id("21611")
        self.assertEqual(song.videos[0].uploaded.day, 11)
