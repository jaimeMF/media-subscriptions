import configparser
import datetime
import itertools
import json
import os
import shlex
import sqlite3
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
    def __init__(self, config):
        self.config = config
        self.db_filename = os.path.join(xdg.BaseDirectory.xdg_data_home, APP_NAME, 'media-subscriptions.db')
        self._db = None
        self.lasts_filename = os.path.join(os.path.dirname(self.db_filename), 'last.json')
        super().__init__({}, auto_init=False)

        self.add_info_extractor(ydl_ies.YoutubeUserIE())

    @property
    def db(self):
        db = self._db
        if self._db is None:
            db = self._db = sqlite3.connect(self.db_filename)
            if not db.execute('SELECT * FROM sqlite_master WHERE name="downloaded"').fetchall():
                with db:
                    db.execute('CREATE TABLE downloaded (subscription text, url text, date timestamp)')
                if os.path.exists(self.lasts_filename):
                    print('Migrating the json info to the sqlite database')
                    with open(self.lasts_filename, 'rt') as f:
                        info = json.load(f)
                    with db:
                        for name, url in info.items():
                            self.register_download(name, url)
                    os.rename(self.lasts_filename, self.lasts_filename + '.backup')
        return db

    def process_ie_result(self, ie_result, download=True, extra_info={}):
        result_type = ie_result.get('_type', 'video')
        if result_type == 'playlist':
            return ie_result
        elif result_type == 'url':
            return super().process_ie_result(ie_result, download, extra_info)

    def extract_entries(self, name, config):
        all_entries = self.extract_info(config['url'])['entries']
        last_download = self.db.execute('SELECT * FROM downloaded WHERE subscription=? LIMIT 1', (name,)).fetchone()
        if last_download is None:
            print('Last download from subscription "{}" not found, downloading only the most recent video'.format(name))
            entries = [next(all_entries)]
        else:
            entries = list(itertools.takewhile(lambda x: not self.is_downloaded(name, x['url']), all_entries))[::-1]
            print('Downloading {} videos'.format(len(entries)))
        return entries

    def download_subscription(self, name):
        print('Processing subscription "{}"'.format(name))
        config = self.config[name]
        entries = self.extract_entries(name, config)
        for entry in entries:
            self.download_entry(name, entry, config)

    def run_youtube_dl(self, args):
        # this is the only way to use the youtube-dl config file, if you
        # directly pass the args to youtube_dl.main it doesn't read it
        with unittest.mock.patch('sys.argv', ['youtube-dl'] + args):
            try:
                youtube_dl.main()
            except SystemExit as err:
                if err.code != 0:
                    raise YoutubeDLError(err.code)

    def download_entry(self, name, entry, config):
        args = []
        args.extend(['--output', os.path.join(config['download-folder'], name, youtube_dl.utils.DEFAULT_OUTTMPL)])
        extra_args = shlex.split(config['extra-args'])
        args.extend(extra_args)
        args.extend(['--', entry['url']])
        self.run_youtube_dl(args)
        self.register_download(name, entry['url'])

    def is_downloaded(self, name, url):
        res = self.db.execute('SELECT * FROM downloaded WHERE subscription=? AND url=?', (name, url))
        return res.fetchone() is not None

    def register_download(self, name, url):
        with self.db as db:
            db.execute('INSERT INTO downloaded VALUES (?, ?, ?)', (name, url, datetime.datetime.now()))


def build_config():
    defaults = {
        'download-folder': os.path.expanduser('~/Movies/subscriptions'),
        'extra-args': '',
    }
    return configparser.ConfigParser(defaults=defaults)


def main():
    config_filename = os.path.join(xdg.BaseDirectory.load_first_config(APP_NAME), 'config')

    config = build_config()
    config.read(config_filename)
    dl = SubscriptionDownloader(config)
    for name in config:
        if name == 'DEFAULT':
            continue
        dl.download_subscription(name)

if __name__ == '__main__':
    main()
