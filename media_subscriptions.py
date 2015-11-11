import configparser
import itertools
import json
import os
import shlex
import unittest.mock

import youtube_dl
import youtube_dl.utils
import youtube_dl.extractor as ydl_ies
import xdg.BaseDirectory


APP_NAME = 'media-subscriptions'


class YoutubeDLError(Exception):
    def __init__(self, code):
        super().__init__('youtube-dl exited with code {}'.format(code))
        self.code = code

class SubscriptionDownloader(youtube_dl.YoutubeDL):
    def __init__(self, name, config):
        self.name = name
        self.config = config
        super().__init__({}, auto_init=False)

        self.add_info_extractor(ydl_ies.YoutubeUserIE())

    def process_ie_result(self, ie_result, download=True, extra_info={}):
        result_type = ie_result.get('_type', 'video')
        if result_type == 'playlist':
            return ie_result
        elif result_type == 'url':
            return super().process_ie_result(ie_result, download, extra_info)

    def extract_entries(self):
        all_entries = self.extract_info(self.config['url'])['entries']
        last_download = load_last_downloads().get(self.name)
        if last_download is None:
            print('Last download from subscription "{}" not found, downloading only the most recent video'.format(self.name))
            entries = [next(all_entries)]
        else:
            entries = list(itertools.takewhile(lambda x: x['url'] != last_download, all_entries))[::-1]
            print('Downloading {} videos'.format(len(entries)))
        return entries

    def download_subscription(self):
        entries = self.extract_entries()
        for entry in entries:
            self.download_entry(entry)

    def download_entry(self, entry):
        args = []
        args.extend(['--output', os.path.join(self.config['download-folder'], self.name, youtube_dl.utils.DEFAULT_OUTTMPL)])
        extra_args = shlex.split(self.config['extra-args'])
        args.extend(extra_args)
        args.extend(['--', entry['url']])
        # this is the only way to use the youtube-dl config file, if you
        # directly pass the args to youtube_dl.main it doesn't read it
        with unittest.mock.patch('sys.argv', ['youtube-dl'] + args):
            try:
                youtube_dl.main()
            except SystemExit as err:
                if err.code != 0:
                    raise YoutubeDLError(err.code)
        register_last_download(self.name, entry['url'])


def load_last_downloads():
    filename = os.path.join(next(xdg.BaseDirectory.load_data_paths(APP_NAME)), 'last.json')
    if os.path.exists(filename):
        with open(filename, 'rt') as f:
            return json.load(f)
    else:
        return {}


def register_last_download(name, url):
    filename = os.path.join(xdg.BaseDirectory.save_data_path(APP_NAME), 'last.json')
    info = load_last_downloads()
    info[name] = url
    with open(filename, 'wt') as f:
        json.dump(info, f)


def process_subscription(name, config):
    print('Processing subscription "{}"'.format(name))
    dl = SubscriptionDownloader(name, config)
    dl.download_subscription()


def main():
    config_filename = os.path.join(xdg.BaseDirectory.load_first_config(APP_NAME), 'config')

    defaults = {
        'download-folder': os.path.expanduser('~/Movies/subscriptions'),
        'extra-args': '',
    }
    config = configparser.ConfigParser(defaults=defaults)
    config.read(config_filename)
    for name in config:
        if name == 'DEFAULT':
            continue
        process_subscription(name, config[name])

if __name__ == '__main__':
    main()
