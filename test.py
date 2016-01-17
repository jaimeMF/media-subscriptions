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


class TestMediaSubs(unittest.TestCase):
    def setUp(self):
        if os.path.exists(lasts_filename):
            os.remove(lasts_filename)

    def tearDown(self):
        if os.path.exists(lasts_filename):
            os.remove(lasts_filename)

    def test_subscriptions(self):
        config = ms.build_config()
        config.add_section('test')
        dl = ms.SubscriptionDownloader(config)
        dl.lasts_filename = lasts_filename
        dl.add_info_extractor(PlaylistIE())

        def download_subs(*ns):
            config['test']['url'] = 'pl:{}'.format(','.join(map(str, ns)))
            dl.download_subscription('test')

        dl.run_youtube_dl = mock.Mock()
        dl_mock = dl.download_entry = mock.Mock(side_effect=dl.download_entry)

        def entry(n):
            return 'test', {'url': 't:{}'.format(n)}, config['test']

        def call_entry(n):
            return mock.call(*entry(n))

        download_subs(1)
        dl_mock.assert_called_with(*entry(1))

        dl_mock.reset_mock()
        download_subs(1)
        dl_mock.assert_not_called()

        dl_mock.reset_mock()
        download_subs(1, 2, 3)
        dl_mock.assert_has_calls([call_entry(2), call_entry(3)])


if __name__ == '__main__':
    unittest.main()
