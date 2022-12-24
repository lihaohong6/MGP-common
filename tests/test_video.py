from unittest import TestCase

from mgp_common.video import get_nc_info


class TestVideo(TestCase):

    def test_get_nc_info(self):
        info = get_nc_info("sm15282013")
        self.assertEqual(info.uploaded.day, 11)
