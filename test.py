import json
import os
import re
import unittest
import unittest.mock as mock

import media_subscriptions as ms
from youtube_dl.extractor.common import InfoExtractor


class PlaylistIE(InfoExtractor):
    _VALID_URL = r'pl:([\d,]+)'

    def _real_extract(self, url):
        ns = map(int, re.match(self._VALID_URL, url).group(1).split(','))
        return {
            '_type': 'playlist',
            'id': 'pl',
            'title': 'Playlist',
            'entries': reversed([{'url': 't:{}'.format(x)} for x in ns]),
        }


lasts_filename = 'test_lasts.json'
db_filename = 'test_db.db'
db_filename = ':memory:'

test_files = [lasts_filename, lasts_filename + '.backup']


class TestMediaSubs(unittest.TestCase):
    def setUp(self):
        for f in test_files:
            if os.path.exists(f):
                os.remove(f)

        self.config = ms.build_config()
        self.config.add_section('test')

        self.dl = ms.SubscriptionDownloader(self.config)
        self.dl.db_filename = db_filename
        self.dl.lasts_filename = lasts_filename
        self.dl.add_info_extractor(PlaylistIE())
        self.dl.run_youtube_dl = mock.Mock()
        self.dl_mock = self.dl.download_entry = mock.Mock(side_effect=self.dl.download_entry)

    def tearDown(self):
        for f in test_files:
            if os.path.exists(f):
                os.remove(f)

    def download_subs(self, *ns):
        self.config['test']['url'] = 'pl:{}'.format(','.join(map(str, ns)))
        self.dl.download_subscription('test')

    def entry(self, n):
        return 'test', {'url': 't:{}'.format(n)}, self.config['test']

    def call_entry(self, n):
        return mock.call(*self.entry(n))

    def test_subscriptions(self):
        entry = self.entry
        call_entry = self.call_entry
        dl_mock = self.dl_mock
        self.download_subs(1)
        dl_mock.assert_called_with(*entry(1))

        dl_mock.reset_mock()
        self.download_subs(1)
        dl_mock.assert_not_called()

        dl_mock.reset_mock()
        self.download_subs(1, 2, 3)
        dl_mock.assert_has_calls([call_entry(2), call_entry(3)])

    def test_first_time(self):
        '''Test first time download

        It must only download the most recent video
        '''

        entry = self.entry
        dl_mock = self.dl_mock
        self.download_subs(1, 2, 3, 4)
        dl_mock.assert_called_once_with(*entry(4))

    def test_json_migration(self):
        """Test json to sqlite database migration"""
        with open(lasts_filename, 'wt') as f:
            json.dump({'test': 't:3'}, f)

        entry = self.entry
        dl_mock = self.dl_mock
        self.download_subs(2, 3, 4)
        dl_mock.assert_called_once_with(*entry(4))

    def test_deleted(self):
        """Test with deleded videos"""

        entry = self.entry
        call_entry = self.call_entry
        dl_mock = self.dl_mock
        self.download_subs(1)
        dl_mock.assert_called_once_with(*entry(1))
        self.download_subs(1, 2, 3)
        dl_mock.assert_has_calls([call_entry(2), call_entry(3)])

        dl_mock.reset_mock()
        self.download_subs(1, 2, 4)
        dl_mock.assert_called_once_with(*entry(4))


if __name__ == '__main__':
    unittest.main()
