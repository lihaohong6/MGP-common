from unittest import TestCase

from mgp_common.vocadb import get_song_by_id, get_producer_albums


class TestVocadb(TestCase):

    def test_get_nc_info(self):
        song = get_song_by_id("21611")
        self.assertEqual(song.videos[0].uploaded.day, 11)

    def test_get_albums(self):
        albums = get_producer_albums('494', only_original=True)
        self.assertTrue('アンラッキーガールちゃんの日録' not in albums)
        albums = get_producer_albums('494', only_original=False)
        self.assertTrue('アンラッキーガールちゃんの日録' in albums)
