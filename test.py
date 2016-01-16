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


def patch_lasts_filename():
    return mock.patch.object(ms, 'lasts_filename', 'test_lasts.json')


class TestMediaSubs(unittest.TestCase):
    @patch_lasts_filename()
    def setUp(self):
        self.filename = ms.lasts_filename
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    @patch_lasts_filename()
    def test_subscriptions(self):
        config = ms.build_config()
        config.add_section('test')
        config = config['test']
        dl = ms.SubscriptionDownloader('test', config)
        dl.add_info_extractor(PlaylistIE())

        def download_subs(*ns):
            config['url'] = 'pl:{}'.format(','.join(map(str, ns)))
            dl.download_subscription()

        dl.run_youtube_dl = unittest.mock.Mock()
        dl_mock = dl.download_entry = unittest.mock.Mock(side_effect=dl.download_entry)

        def entry(n):
            return {'url': 't:{}'.format(n)}
        call = unittest.mock.call

        download_subs(1)
        dl_mock.assert_called_with(entry(1))

        dl_mock.reset_mock()
        download_subs(1)
        dl_mock.assert_not_called()

        dl_mock.reset_mock()
        download_subs(1, 2, 3)
        dl_mock.assert_has_calls([call(entry(2)), call(entry(3))])


if __name__ == '__main__':
    unittest.main()
